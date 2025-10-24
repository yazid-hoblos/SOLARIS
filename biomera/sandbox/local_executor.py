import os, subprocess, shutil
from typing import Dict, List, Union
from pathlib import Path

class LocalExecutor:
    """
    Local executor that runs commands in a local workspace directory.
    This is a development/testing alternative to DockerExecutor.
    WARNING: Less secure than Docker - commands run with current user permissions.
    """
    
    def __init__(self, config: Dict):
        self.workspace = Path(config.get("workspace", "./workspace")).resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        
        # Copy initial files if specified
        for file_path in config.get("copied_files", []):
            src = Path(file_path)
            if src.exists():
                dst = self.workspace / src.name
                if src.is_file():
                    shutil.copy2(src, dst)
                else:
                    shutil.copytree(src, dst, dirs_exist_ok=True)
    
    def run(self, command: Union[str, List[str]]) -> Dict:
        """Execute a command in the workspace directory."""
        try:
            if isinstance(command, list):
                command = " ".join(command)
            
            # Run command in workspace directory
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes for SOLARIS commands (KEGG/UniProt queries can be slow)
            )
            
            # Combine stdout and stderr for output
            output = result.stdout
            if result.stderr:
                output += "\n" + result.stderr
            
            # If command failed, include the error details
            if result.returncode != 0:
                # Build comprehensive error message
                error_msg = f"Command exited with code {result.returncode}"
                
                # Add stderr details to error message
                if result.stderr and result.stderr.strip():
                    error_msg += f"\n\nError details:\n{result.stderr.strip()}"
                
                # Also include stdout if it has useful info
                if result.stdout and result.stdout.strip():
                    error_msg += f"\n\nCommand output:\n{result.stdout.strip()}"
                
                return {
                    "success": False,
                    "output": output.strip() if output else "",
                    "error": error_msg
                }
            
            return {
                "success": True,
                "output": output.strip() if output else "",
                "error": None
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": None,
                "error": "Command timed out after 5 minutes"
            }
        except Exception as e:
            return {
                "success": False,
                "output": None,
                "error": str(e)
            }
    
    def start(self):
        """No-op for compatibility with DockerExecutor interface."""
        pass
    
    def list_files(self) -> List[Dict]:
        """List all files in the workspace."""
        tree = {}
        
        for root, dirs, files in os.walk(self.workspace):
            rel_root = Path(root).relative_to(self.workspace)
            parts = list(rel_root.parts) if str(rel_root) != '.' else []
            
            for file in files:
                file_parts = parts + [file]
                cursor = tree
                for part in file_parts[:-1]:
                    cursor = cursor.setdefault(part, {})
                cursor[file_parts[-1]] = {}
        
        def to_tree(d):
            return [
                {
                    "name": key,
                    "children": to_tree(value) if value else None
                } for key, value in d.items()
            ]
        
        return to_tree(tree)
    
    def upload(self, src_path: str, dst_path: str):
        """Copy a file or directory to the workspace."""
        src = Path(src_path)
        dst = self.workspace / dst_path / src.name
        
        if not src.exists():
            return {"error": f"Source path does not exist: {src_path}"}
        
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_file():
                shutil.copy2(src, dst)
            else:
                shutil.copytree(src, dst, dirs_exist_ok=True)
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}
