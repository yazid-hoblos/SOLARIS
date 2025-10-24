import requests
import os
import json
from typing import Dict, List, Any

class Agent:

    def __init__(self, config: Dict):
        self.config = config
        self.provider = config.get("provider", "fireworks").lower()
        
        # Support multiple providers
        if self.provider == "groq":
            self.api_key = os.environ.get("GROQ_API_KEY", "")
            self.api_base = "https://api.groq.com/openai/v1"
            self.model_name = config.get("online_model", "llama-3.1-70b-versatile")
            env_var_name = "GROQ_API_KEY"
        else:  # fireworks
            self.api_key = os.environ.get("FIREWORKS_API_KEY", "")
            self.api_base = "https://api.fireworks.ai/inference/v1"
            self.model_name = config.get("online_model", "accounts/fireworks/models/mixtral-8x7b-instruct")
            env_var_name = "FIREWORKS_API_KEY"
        
        if not self.api_key:
            print(f"\nWARNING: {env_var_name} environment variable not set!")
            print(f"Set it with: export {env_var_name}=your_api_key_here\n")

        config_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(config_dir, "prompt.txt")
        if os.path.exists(config["prompt"]):
            with open(config["prompt"], "r") as f:
                self.messages = [
                    {
                        "role": "system",
                        "content": f.read()
                    }
                ]
        
    def ask(self, role: str, query: str) -> str:
        if not self.api_key:
            return "Please set the FIREWORKS_API_KEY environment variable."
            
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            self.messages.append({"role": role, "content": query})

            payload = {
                "model": self.model_name,
                "messages": self.messages,
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "shell",
                            "description": "Execute a shell command in the workspace.",
                            "parameters": {
                                "type": "string",
                                "description": "the shell command and its arguments to execute",
                            }
                        }
                    }
                ],
                "tool_choice": "auto",
                "temperature": 0.5,
                "max_tokens": 1024,
            }

            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                error_msg = f"Error: API returned status code {response.status_code}"
                try:
                    error_detail = response.json()
                    if "error" in error_detail:
                        error_msg += f", {error_detail['error']['message']}"
                except:
                    error_msg += f", {response.text}"
                return error_msg

            response_data = response.json()
            return response_data["choices"][0]["message"]["content"]

        except Exception as e:
            return f"Error processing request: {str(e)}"