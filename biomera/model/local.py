from langchain_ollama import ChatOllama
import ollama
from typing import Dict
import os
import logging

class Agent:

    def __init__(self, config: Dict, tools):
        self.config = config
        self.tools = tools
        self.model_name = self.config["model"]
        self.model = ChatOllama(model=self.model_name, verbose=False)
        self.logger = logging.getLogger(__name__)
        self.verbose = os.getenv('BIOMERA_VERBOSE', '0') == '1'

        # Load system prompt from file if specified, otherwise use default
        system_prompt = self._load_system_prompt()
        
        self.messages = {
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                }
            ]
        }
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from config file(s) or use default."""
        prompt_config = self.config.get("prompt")
        
        # Support both single file (string) and multiple files (list)
        if isinstance(prompt_config, str):
            prompt_files = [prompt_config]
        elif isinstance(prompt_config, list):
            prompt_files = prompt_config
        else:
            prompt_files = []
        
        # Load and combine all prompt files
        combined_prompt = []
        for prompt_file in prompt_files:
            if os.path.exists(prompt_file):
                try:
                    with open(prompt_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        combined_prompt.append(content)
                        if self.verbose:
                            self.logger.info(f"Loaded prompt file: {prompt_file}")
                except Exception as e:
                    if self.verbose:
                        self.logger.warning(f"Could not load prompt file {prompt_file}: {e}")
            else:
                if self.verbose:
                    self.logger.warning(f"Prompt file not found: {prompt_file}")
        
        if combined_prompt:
            return "\n\n".join(combined_prompt)
        
        # Default prompt if no files loaded
        return (
            "You are a bioproduction assistant specialized in molecular biology and "
            "biotechnology. Your tasks include:\n"
            "- Searching and retrieving DNA and protein sequences from trusted databases "
            "like NCBI and UniProt.\n"
            "- Explaining protocols and biological pathways.\n"
            "- Suggesting bioinformatics commands and pipelines.\n"
            "- Using available tools like shell commands or APIs when needed.\n"
            "- Provide concise, factual answers.\n"
            "Be collaborative and ask clarifying questions when unsure."
        )

    def ask(self, role: str, query: str) -> str:
        try:
            system_message = self.messages["messages"][0]["content"]
            
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": role, "content": query}
                ],
                options={
                    "num_predict": 512,   # Reduced for faster responses
                    "temperature": 0.5,   # Lower for more focused/deterministic commands
                    "top_p": 0.9,
                    "num_ctx": 2048      # Smaller context window for speed
                }
            )
            
            answer = response["message"]["content"]
            return answer
            
        except Exception as e:
            return f"Error: {str(e)}"