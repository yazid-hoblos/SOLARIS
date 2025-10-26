import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib.font_manager")
import logging
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
logging.getLogger('matplotlib').setLevel(logging.ERROR)
import sys, importlib, json, os, shlex
from typing import List, Generator
from sandbox.executor import DockerExecutor
from sandbox.local_executor import LocalExecutor
from sandbox.security import CommandValidator
from sandbox.interface import LLMInterface
from sandbox.logger import setup_logger
from utils.config import load_config
from utils.prompt import prompt
from utils.tree import tree
from utils.parser import parse_output
from model.toolset import setup_toolset


# Mapping of tool subcommands to parameters that must be supplied by the user when running via the agent.
REQUIRED_PARAMS = {
    "pangenomic_analyzer complete": ["--genomes-dir", "--hmm-file", "--target-ecs", "--ec-pfam-mapping"],
    "pangenomic_analyzer strains": ["--genomes-dir", "--hmm-file"],
    "pangenomic_analyzer pathways": ["--hmm-results", "--target-ecs"],
    "pangenomic_analyzer hmm": ["--genomes-dir"],
    "compatibility_predictor bacdive": ["--email", "--taxonomy", "--password"],
    "compatibility_predictor kegg": ["--ec-file"],
    "compatibility_predictor match": ["--email"],
    "pathway_profiler workflow": ["--module", "--genome", "--pfam-db"],
    "pathway_profiler extract-ec": ["--module"],
    "pathway_profiler get-profiles": ["--input", "--pfam-db"],
    "pathway_profiler search": ["--hmm", "--genome"],
    "pathway_profiler analyze": ["--hits", "--input", "--hmm"],
    "pathway_profiler visualize": ["--results"]
}


def _missing_required_flags(args: list):
    """Return (key, missing_flags) for the first matching tool subcommand, or (None, []).
    args: tokenized argument list (e.g. ['pangenomic_analyzer','complete','--genomes-dir','./data']).
    """
    if not args:
        return None, []
    tool = args[1]
    sub = args[2] if len(args) > 2 else None
    if len(args) > 3 and (args[3] == '--help' or args[3] == '-h'):
        return None, []
    if sub:
        key = f"{tool} {sub}"
        required = REQUIRED_PARAMS.get(key)
        if required:
            missing = []
            for flag in required:
                found = False
                for a in args[2:]:
                    if a == flag or a.startswith(flag + "="):
                        found = True
                        break
                if not found:
                    missing.append(flag)
            return key, missing
    return None, []

class Main:
    def __init__(self, filepath: str = "config/config.json"):
        self.verbose = os.getenv('BIOMERA_VERBOSE', '0') == '1'
        self.config = load_config(filepath)
        self.logger = setup_logger(self.config['logging'])
        self.toolset = setup_toolset(self.config['llm']["toolset"])
        
        # Choose executor: use local executor if USE_LOCAL_EXECUTOR env var is set
        # or if "executor" config is set to "local"
        use_local = (
            os.getenv('USE_LOCAL_EXECUTOR', '').lower() in ('1', 'true', 'yes') or
            self.config.get('executor', {}).get('type', 'docker') == 'local'
        )
        
        if use_local:
            if self.verbose:
                self.logger.info("Using LocalExecutor (dev mode)")
            executor_config = self.config.get('executor', {}).get('local', {'workspace': './workspace'})
            self.executor = LocalExecutor(executor_config)
        else:
            if self.verbose:
                self.logger.info("Using DockerExecutor")
            self.executor = DockerExecutor(self.config['docker'])
        
        self.validator = CommandValidator(self.config['security'], self.toolset)
        self.interface = LLMInterface(self.config['llm'])
        self.executed = []
        
        use_online = self.config["llm"].get("use_online", False)
        module_name = "model.online" if use_online else "model.local"
        try:
            agent_module = importlib.import_module(module_name)
            self.agent = agent_module.Agent(self.config["llm"]) if use_online else agent_module.Agent(self.config["llm"], self.toolset)
        except ImportError as e:
            self.logger.error(f"Failed to import {module_name}: {str(e)}")
            raise

    def ask(self, question = None):
        if __name__ == "__main__":
            if not sys.stdin.isatty():
                input = sys.stdin.read().strip()
            else:
                if question:
                    input = prompt(question + " > ")
                else:
                    input = prompt("Ask Agent > ")

            return self.query("user", input)
        
        return [question] if question else []
        
    def query(self, role: str, input: str, stack = 0):

        if stack > 5:
            self.logger.error("Stack overflow detected.")
            return [f"! The model is not able to iterate more than {self.config['llm']['max_iterations']} times."]

        # Show thinking message to user
        if stack == 0:
            yield "🤔 Analyzing your request..."
        
        output = self.agent.ask(role, input)

        # Normalize output: some agent implementations may return generators or lists.
        try:
            import types
            if isinstance(output, types.GeneratorType):
                output = "".join(list(output))
            elif isinstance(output, (list, tuple)):
                output = "".join(output)
        except Exception:
            # If normalization fails, leave as-is and let downstream logic handle it
            pass

        if self.verbose:
            try:
                self.logger.info(f"LLM raw output length: {len(output)} chars")
            except Exception:
                self.logger.info("LLM raw output length: (unknown)")
            self.logger.debug(f"LLM full output: {output}")
        
        yield "📋 Parsing response..."
        
        thought, response, action = parse_output(output)
        
        if self.verbose:
            self.logger.info(f"Parsed - Response: {response[:100] if response != 'None' else 'None'}..., Action: {action[:100]}...")

        # If response is "None" (the string), it means no structured output was found
        # In that case, treat the entire output as the response
        if response == "None" and not output.startswith("{"):
            yield output
            return

        if output.startswith("{") and output.endswith("}"):
            action = output
            response = ""

        if stack == 0:
            self.executed = []

        try:    
            action = json.loads(action)
            
            if self.verbose:
                self.logger.info(f"Action parsed: {action.get('name')}")
            
            if action["name"] == "end":
                if response:
                    yield response
                else:
                    yield "Task completed."
                return
            
            if action["name"] == "ask":
                # Return response and let the main loop handle the next question
                if response:
                    yield response
                return
            
            if action["name"] == "shell":
                command = action["parameters"]["value"]
                
                if self.verbose:
                    self.logger.info(f"Shell action - command: {command[:100]}...")

                # If the model attempts to run help automatically, skip it in the
                # general/automatic case to avoid clutter. However, if the *user*
                # explicitly asked for help (for example: "what can X do?",
                # "show me help", or the query contains the word 'help' or a
                # trailing question mark) then allow the help command to run so
                # we can show usage to the user.
                try:
                    token_check = shlex.split(command)
                    if any(t in ('-h', '--help') for t in token_check):
                        # Detect whether the original user input asked for help.
                        # If so, allow running the help command. Typical user
                        # phrasings include: 'help', 'what can', 'show', 'list',
                        # or a trailing '?'. Otherwise, assume the model is
                        # attempting an automatic help run and skip it.
                        user_q = (input or "").lower()
                        wants_help = False
                        if 'help' in user_q:
                            wants_help = True
                        elif any(w in user_q for w in ('what can', 'what does', 'show', 'list')):
                            wants_help = True
                        elif user_q.strip().endswith('?'):
                            wants_help = True

                        if not wants_help:
                            if self.verbose:
                                self.logger.info("Skipping automatic execution of help flag (-h/--help).")
                            return
                except Exception:
                    # If tokenization fails, continue to normal handling
                    pass

                if stack > 0 and command in self.executed:
                    self.logger.error(f"Command already executed: {command}")
                    yield response
                    yield f"$ {command}"
                    yield "! This command has already been executed."
                    
                    for item in self.query("user", f"""Your previous action ({command}) was rejected because it has already been executed.
                    Your task is to answer the question: {input}""", stack + 1):
                        yield item
                    return
                # Show what we're about to execute
                # Before announcing execution, ensure required params are present
                try:
                    tokens = shlex.split(command)
                    key, missing = _missing_required_flags(tokens)
                    if missing:
                        missing_list = ', '.join(missing)
                        # Prompt user to provide missing parameters instead of executing
                        yield (f"Tried Command: {command}\n\n"
                               "⚠️ Missing required parameters\n"
                               f"Missing: {missing_list}\n\n"
                               "Please provide the missing flags and try again.\n"
                               "I'll show the command help below to assist you.")

                        # Run the command's help (-h) to show usage, but do NOT run the full command
                        try:
                            command = tokens[0] + " " + tokens[1] + " " + tokens[2]
                            help_cmd =  command + " -h"
                            if self.verbose:
                                self.logger.info(f"Running help for command: {help_cmd}")
                            help_exec = self.executor.run(help_cmd)
                            help_resp = self.interface.standardify(help_exec)

                            if help_resp.get("success"):
                                help_output = help_resp.get("output", "")
                                if help_output:
                                    yield f"$ {help_cmd}"
                                    yield help_output
                            else:
                                yield "(Could not retrieve help for this command.)"
                        except Exception:
                            # Never raise on help retrieval; just continue
                            yield "(Failed to run help for this command.)"

                        return
                    # If all required flags were provided, verify any file/dir values exist in the workspace
                    try:
                        required = REQUIRED_PARAMS.get(key, []) if key else []
                        if required:
                            from pathlib import Path
                            bad = []
                            i = 0
                            while i < len(tokens):
                                t = tokens[i]
                                for flag in required:
                                    # flag as separate token: --flag value
                                    if t == flag and i + 1 < len(tokens) and not tokens[i+1].startswith('--'):
                                        val = tokens[i+1]
                                    # flag as --flag=value
                                    elif t.startswith(flag + "="):
                                        val = t.split('=', 1)[1]
                                    else:
                                        val = None

                                    if val:
                                        p = Path(val)
                                        # Resolve relative paths against executor workspace
                                        try:
                                            ws = Path(self.executor.workspace)
                                        except Exception:
                                            ws = Path('.')
                                        if not p.is_absolute():
                                            p = (ws / p).resolve()

                                        # If the flag explicitly references a directory name, require directory
                                        if 'dir' in flag or 'db' in flag:
                                            if not p.exists() or not p.is_dir():
                                                bad.append((flag, val))
                                        else:
                                            # Only treat the value as a file path if it has a filename extension.
                                            # Many flags accept identifiers or names (no extension) which shouldn't be checked.
                                            import os as _os
                                            _, ext = _os.path.splitext(val)
                                            if ext:
                                                if not p.exists():
                                                    bad.append((flag, val))
                                            else:
                                                # No extension -> assume non-file argument (skip existence check)
                                                pass
                                i += 1

                            if bad:
                                # Inform the user which required paths are missing and show help
                                missing_lines = '\n'.join([f"{f}: {v}" for f, v in bad])
                                yield (f"Tried Command: {command}\n\n"
                                       "⚠️ Required files/directories not found in workspace:\n"
                                       f"{missing_lines}\n"
                                       "Please provide correct paths and try again.")
                                return
                    except Exception:
                        # If existence checks fail for any reason, fall back to normal execution path
                        pass
                except Exception:
                    # If parsing fails, fall back to the normal execution path
                    pass

                # Announce execution for top-level user requests or when verbose
                # logging is enabled. This shows the "⚡ Executing" line to the
                # user for normal interactions while still avoiding duplicate
                # announcements during recursive LLM-driven analysis (stack>0).
                if self.verbose or stack == 0:
                    yield f"⚡ Executing: {command}"
                    self.logger.info(f"Executing: {command}")
                success, cmd_output, apology = self.execute(command, stack)
                command_failed = not success

                # Show the result: first any agent response
                if response:
                    yield response

                # If there is an apology text, show it as normal text (not in terminal)
                if apology:
                    yield apology

                # Then show terminal-style output: the frontend recognizes the line starting
                # with "$ <command>" and will render following yields as the command output box.
                yield f"$ {command}"
                yield cmd_output

                # If the command failed, stop here and do not automatically invoke
                # further LLM-driven actions (like running -h). Let the user decide
                # how to proceed. This prevents the agent from auto-running help
                # commands when the user likely wanted to see the error and fix it.
                if command_failed:
                    return

                # Only continue the loop if we haven't hit max iterations
                # Skip recursion for:
                # 1. Simple read-only commands (ls, cat, etc.)
                # 2. Help commands (-h, --help)
                # 3. Complete workflow commands and standalone operations that show full output (ONLY IF SUCCESSFUL)
                skip_recursion = any(cmd in command.lower() for cmd in [
                    'ls', 'cat', 'echo', 'pwd', 'tree', 'head', 'tail',
                    ' -h', ' --help', 'help',
                ])
                
                # For commands that produce complete output, skip recursion if successful
                if not command_failed and any(cmd in command.lower() for cmd in [
                    'workflow',      # pathway_profiler workflow shows complete output
                    'complete',      # pangenomic_analyzer complete shows complete output
                    'extract-ec',    # extract-ec shows all EC numbers found
                    'get-profiles',  # get-profiles shows HMM extraction
                    'search',        # search shows HMM search results
                    'analyze',       # analyze shows analysis results
                    'visualize',     # visualize generates visualization
                    'kegg',          # compatibility_predictor kegg queries
                    'bacdive',       # compatibility_predictor bacdive queries
                    'match',         # compatibility_predictor match
                ]):
                    skip_recursion = True
                
                if stack < 3 and not skip_recursion:  # Limit recursion depth
                    yield "🔄 Analyzing results..."
                    
                    # Give better context to LLM when there's an error
                    if command_failed:
                        context_msg = f"""Your previous command failed:
Command: {command}
Error: {output}

Please analyze the error and try again with the correct parameters. You may need to:
1. Run the command with -h to check the correct parameter names
2. Check if files exist with ls
3. Fix any typos in parameter names

Original task: {input}"""
                    else:
                        context_msg = f"""Here is the result of your previous action ({command}):
{output}

Your task is to answer the question: {input}"""
                    
                    for item in self.query("user", context_msg, stack + 1):
                        yield item
                return
                
        except json.JSONDecodeError:
            pass
        
        if response:
            yield response

    def execute(self, input_str: str, stack = 0) -> str:
        """Execute a command in the workspace."""

        input = self.interface.parse(input_str)

        if not input["success"]:
            self.logger.error(f"Parsing error: {input['error']}")
            return "Parsing error: the format of the action is incorrect."
        
        command = input.get("command", "")
        is_valid, command = self.validator.validate(command)

        if not is_valid:
            self.logger.error(f"Validation error: {command}")
            return f"Validation error: {command} is not allowed."
        
        execution = self.executor.run(command)
        self.executed.append(command)
        response = self.interface.standardify(execution)

        if not response["success"]:
            error_msg = response.get('error', 'Execution failed')
            self.logger.error(f"Execution error: {error_msg}")
            # Include the command output (which may contain stderr) for context
            stdout_output = response.get('output', '') or ''

            if stdout_output:
                self.logger.debug(f"Command output (hidden): {stdout_output}")

            # Build terminal output: prefer stdout+stderr (output), but also append the
            # standardized error message which often includes return code or traceback.
            terminal_output_parts = []
            if stdout_output:
                terminal_output_parts.append(stdout_output)
            if error_msg:
                terminal_output_parts.append(f"ERROR: {error_msg}")
            terminal_output = "\n\n".join(terminal_output_parts) if terminal_output_parts else "(no output)"

            # Apology shown as normal text (not in terminal block)
            apology = (
                "Apologies — I couldn't run that command right now. I'm still a little bot in development!\n"
                "But you can try executing it manually. Please refer to our documentation at: https://gitlab.igem.org/2025/software-tools/evry-paris-saclay\n\n"
                "The encountered error message is displayed below.\n"
            )

            # Return structured tuple: failure, terminal output (without the leading $ line), apology
            return (False, terminal_output, apology)

        return (True, response.get('output', ''), None)


def main_entrypoint(config_path: str = "config/config.json"):
    """Interactive AI agent entrypoint - chat with the LLM to run commands."""
    process = Main(config_path)
    
    print("BIOMERA AI Agent ready. Type your questions in natural language.")
    print("The agent will interpret and execute Solaris commands for you.")
    print("Press Ctrl+C to exit.\n")

    try:
        while True:
            try:
                # Get user input
                user_input = input("Ask Agent > ").strip()
                
                if not user_input:
                    continue
                
                # Query the agent with the user's question
                # print("Processing your request...")
                try:
                    responses = process.query("user", user_input)
                    
                    if not responses or len(responses) == 0:
                        print("(No response generated)")
                        continue
                    
                    # Print all responses
                    for response in responses:
                        if response:
                            print(response)
                except Exception as query_error:
                    print(f"ERROR in query: {query_error}")
                    import traceback
                    traceback.print_exc()
                        
            except EOFError:
                break
                
    except KeyboardInterrupt:
        print("\nExiting.")
    except Exception as e:
        process.logger.error(e)
        print(f"Error: {e}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='BIOMERA AI Agent')
    parser.add_argument('-c', '--config', default='config/config.json',
                       help='Path to config file (default: config/config.json)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose debug output')
    
    args = parser.parse_args()
    
    # Set verbose flag globally or pass it to Main
    os.environ['BIOMERA_VERBOSE'] = '1' if args.verbose else '0'
    
    main_entrypoint(args.config)