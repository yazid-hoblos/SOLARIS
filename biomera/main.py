import sys, importlib, json, os
from typing import List
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

    def ask(self, question = None) -> List[str]:
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
        
    def query(self, role: str, input: str, stack = 0) -> List[str]:

        if stack > 5:
            self.logger.error("Stack overflow detected.")
            return [f"! The model is not able to iterate more than {self.config['llm']['max_iterations']} times."]

        output = self.agent.ask(role, input)
        
        if self.verbose:
            self.logger.info(f"LLM raw output length: {len(output)} chars")
            self.logger.debug(f"LLM full output: {output}")
        
        thought, response, action = parse_output(output)
        
        if self.verbose:
            self.logger.info(f"Parsed - Response: {response[:100] if response != 'None' else 'None'}..., Action: {action[:100]}...")

        # If response is "None" (the string), it means no structured output was found
        # In that case, treat the entire output as the response
        if response == "None" and not output.startswith("{"):
            return [output]

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
                return [response] if response else ["Task completed."]
            
            if action["name"] == "ask":
                # Return response and let the main loop handle the next question
                return [response] if response else []
            
            if action["name"] == "shell":
                command = action["parameters"]["value"]
                
                if self.verbose:
                    self.logger.info(f"Shell action - command: {command[:100]}...")

                if stack > 0 and command in self.executed:
                    self.logger.error(f"Command already executed: {command}")
                    next = self.query("user", f"""Your previous action ({command}) was rejected because it has already been executed.
                    Your task is to answer the question: {input}""", stack + 1)

                    return [response, f"$ {command}", "! This command has already been executed."] + next
                
                # Execute the command
                if self.verbose:
                    self.logger.info(f"Executing: {command}")
                output = self.execute(command, stack)
                
                # Show the command and its output immediately
                result_lines = [response, f"\n$ {command}", output]
                
                # Only continue the loop if we haven't hit max iterations
                # Skip recursion for simple read-only commands and help commands
                skip_recursion = any(cmd in command.lower() for cmd in ['ls', 'cat', 'echo', 'pwd', 'tree', 'head', 'tail', ' -h', ' --help', 'help'])
                
                if stack < 3 and not skip_recursion:  # Limit recursion depth
                    next = self.query("user", f"""Here is the result of your previous action ({command}):
                        {output}.\n Your task is to answer the question: {input}""", stack + 1)
                    return result_lines + next
                else:
                    return result_lines
                
        except json.JSONDecodeError:
            pass
        
        return [response] + self.ask()

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
            error_msg = response['error']
            self.logger.error(f"Execution error: {error_msg}")
            return f"Execution error: {error_msg}"
        
        return response['output']


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