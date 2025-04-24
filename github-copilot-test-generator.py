"""
GitHub Copilot Test Generator module for generating tests using GitHub Copilot.
"""

import os
import subprocess
import tempfile
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class GithubCopilotTestGenerator:
    """Generates tests using GitHub Copilot."""
    
    def __init__(self, vscode_executable_path=None):
        """
        Initialize with VS Code executable path if provided.
        
        Args:
            vscode_executable_path: Path to the VS Code executable 
                                   (defaults to common locations if not provided)
        """
        self.vscode_executable_path = vscode_executable_path or self._find_vscode_executable()
        
    def _find_vscode_executable(self) -> str:
        """Find VS Code executable based on platform."""
        import platform
        system = platform.system()
        
        if system == "Windows":
            # Look in common Windows locations
            paths = [
                os.path.expandvars("%LOCALAPPDATA%\\Programs\\Microsoft VS Code\\Code.exe"),
                os.path.expandvars("%ProgramFiles%\\Microsoft VS Code\\Code.exe"),
                os.path.expandvars("%ProgramFiles(x86)%\\Microsoft VS Code\\Code.exe")
            ]
        elif system == "Darwin":  # macOS
            paths = [
                "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
            ]
        else:  # Linux and others
            paths = [
                "/usr/bin/code",
                "/usr/local/bin/code",
                os.path.expanduser("~/.local/bin/code")
            ]
            
        for path in paths:
            if os.path.isfile(path):
                return path
                
        logger.warning("VS Code executable not found. Please specify path manually.")
        return "code"  # Default command, may work if VS Code is in PATH
    
    def generate_test(self, prompt: str) -> str:
        """
        Generate a test method using GitHub Copilot.
        
        Args:
            prompt: The prompt for generating a test
            
        Returns:
            Generated test code as string
        """
        try:
            # Create a temporary Python file with the prompt as a comment
            with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as temp_file:
                # Format prompt as Python comments
                formatted_prompt = '\n'.join([f"# {line}" for line in prompt.strip().split('\n')])
                
                # Add a marker where we want Copilot to start generating
                content = f"{formatted_prompt}\n\n# Copilot, please generate the test below:\n\ndef "
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            # Use VS Code command line to open file and invoke Copilot
            try:
                # Open VS Code with the temp file
                logger.info(f"Opening temporary file in VS Code: {temp_file_path}")
                
                # Command to open VS Code and wait for it
                cmd = [
                    self.vscode_executable_path,
                    "--wait",  # Wait for the window to close before returning
                    temp_file_path
                ]
                
                # Start VS Code
                logger.info("Starting VS Code...")
                subprocess.run(cmd, check=True)
                
                # Read the content after VS Code closes (user should have accepted Copilot's suggestion)
                with open(temp_file_path, 'r') as f:
                    content = f.read()
                
                # Extract the generated test
                # This assumes the user accepted the Copilot suggestion and saved the file
                test_code = content.split("def ", 1)[1] if "def " in content else ""
                if test_code:
                    test_code = "def " + test_code.strip()
                    logger.info("Successfully retrieved test code from Copilot")
                    return test_code
                else:
                    logger.warning("No test code was generated or accepted.")
                    return ""
                    
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file: {e}")
        
        except Exception as e:
            logger.error(f"Error generating test with GitHub Copilot: {e}")
            return ""
    
    def generate_test_with_cli(self, prompt: str) -> str:
        """
        Alternative implementation using the GitHub Copilot CLI if available.
        This requires the GitHub Copilot CLI to be installed.
        
        Args:
            prompt: The prompt for generating a test
            
        Returns:
            Generated test code as string
        """
        try:
            # Create a temporary file to store the output
            with tempfile.NamedTemporaryFile(suffix='.txt', mode='w', delete=False) as output_file:
                output_file_path = output_file.name
            
            # Build the command for GitHub Copilot CLI
            cmd = [
                "github-copilot",
                "suggest",
                "--output-file", output_file_path,
                prompt
            ]
            
            # Run the command
            logger.info("Running GitHub Copilot CLI...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"GitHub Copilot CLI failed: {result.stderr}")
                return ""
            
            # Read the generated test from the output file
            with open(output_file_path, 'r') as f:
                test_code = f.read().strip()
            
            # Clean up
            os.unlink(output_file_path)
            
            return test_code
            
        except Exception as e:
            logger.error(f"Error using GitHub Copilot CLI: {e}")
            return ""
            
    def generate_test_headless(self, prompt: str) -> str:
        """
        Headless implementation using VS Code's built-in API capabilities.
        This requires VS Code to be installed with the Copilot extension.
        
        Args:
            prompt: The prompt for generating a test
            
        Returns:
            Generated test code as string
        """
        try:
            # Create a temporary file with the prompt
            with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as temp_file:
                # Format prompt as Python comments
                formatted_prompt = '\n'.join([f"# {line}" for line in prompt.strip().split('\n')])
                content = f"{formatted_prompt}\n\n# Copilot, please generate the test below:\n\ndef "
                temp_file.write(content)
                temp_file_path = temp_file.name
                
            # Create a script to automate VS Code
            with tempfile.NamedTemporaryFile(suffix='.js', mode='w', delete=False) as script_file:
                script = f"""
                const vscode = require('vscode');

                async function activateCopilot() {{
                    try {{
                        // Open the file
                        const document = await vscode.workspace.openTextDocument('{temp_file_path.replace('\\', '\\\\')}');
                        const editor = await vscode.window.showTextDocument(document);
                        
                        // Move cursor to end of file
                        const lastLine = document.lineCount - 1;
                        const lastChar = document.lineAt(lastLine).text.length;
                        editor.selection = new vscode.Selection(lastLine, lastChar, lastLine, lastChar);
                        
                        // Trigger Copilot inline suggestion
                        await vscode.commands.executeCommand('github.copilot.generate');
                        
                        // Wait for suggestions
                        await new Promise(resolve => setTimeout(resolve, 3000));
                        
                        // Accept suggestion
                        await vscode.commands.executeCommand('github.copilot.acceptCurrent');
                        
                        // Save the file
                        await document.save();
                        
                        // Exit VS Code
                        await vscode.commands.executeCommand('workbench.action.closeActiveEditor');
                        setTimeout(() => vscode.commands.executeCommand('workbench.action.quit'), 500);
                    }} catch (error) {{
                        console.error('Error:', error);
                        vscode.window.showErrorMessage('Error: ' + error.message);
                        setTimeout(() => vscode.commands.executeCommand('workbench.action.quit'), 1000);
                    }}
                }}

                activateCopilot();
                """
                script_file.write(script)
                script_file_path = script_file.name
                
            # Run VS Code with the extension script
            cmd = [
                self.vscode_executable_path,
                "--extensions-dir", os.path.expanduser("~/.vscode/extensions"),
                "--user-data-dir", os.path.expanduser("~/.vscode-copilot-automation"),
                "--disable-workspace-trust",
                "--extensionDevelopmentPath", os.path.dirname(script_file_path)
            ]
            
            logger.info("Running VS Code in headless mode...")
            subprocess.run(cmd, check=True, timeout=20)
            
            # Read the result
            with open(temp_file_path, 'r') as f:
                content = f.read()
            
            # Extract the test code
            test_code = content.split("def ", 1)[1] if "def " in content else ""
            if test_code:
                test_code = "def " + test_code.strip()
                
            # Clean up
            os.unlink(temp_file_path)
            os.unlink(script_file_path)
            
            return test_code
            
        except Exception as e:
            logger.error(f"Error in headless mode: {e}")
            return ""
