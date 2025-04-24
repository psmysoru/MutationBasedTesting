"""
FileSystem module for handling file system operations.
"""

import os
import glob
import ast
import logging
from typing import List

logger = logging.getLogger(__name__)

class FileSystem:
    """Handles file system operations."""
    
    @staticmethod
    def list_python_files(directory: str) -> List[str]:
        """List all Python files in a directory recursively."""
        if not os.path.exists(directory):
            return []
        
        return glob.glob(os.path.join(directory, "**/*.py"), recursive=True)
    
    @staticmethod
    def read_file(file_path: str) -> str:
        """Read the contents of a file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def write_file(file_path: str, content: str) -> bool:
        """Write content to a file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Error writing to file {file_path}: {e}")
            return False
    
    @staticmethod
    def update_test_file(test_file: str, new_tests: List[str]) -> bool:
        """Update a test file with new test methods."""
        try:
            content = FileSystem.read_file(test_file)
            
            # Parse the test file to find the test class
            tree = ast.parse(content)
            
            # Find the last line of the last test class
            last_class_line = 0
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name.startswith('Test'):
                    if hasattr(node, 'end_lineno'):
                        last_class_line = max(last_class_line, node.end_lineno)
            
            if last_class_line == 0:
                # No test class found, can't update
                logger.error(f"No test class found in {test_file}")
                return False
            
            # Split the content into lines
            lines = content.split('\n')
            
            # Find the line to insert new tests
            insert_line = last_class_line
            for i in range(last_class_line - 1, 0, -1):
                if i >= len(lines):
                    continue
                if lines[i].strip() == '' or 'if __name__' in lines[i]:
                    insert_line = i
                    break
            
            # Insert the new tests
            indent = '    '  # Assuming 4-space indentation
            new_content = '\n'.join(lines[:insert_line])
            
            for test in new_tests:
                # Make sure the test is properly indented
                indented_test = '\n'.join([indent + line for line in test.strip().split('\n')])
                new_content += f"\n\n{indented_test}"
            
            if insert_line < len(lines):
                new_content += '\n\n' + '\n'.join(lines[insert_line:])
            
            # Write the updated content back
            return FileSystem.write_file(test_file, new_content)
            
        except Exception as e:
            logger.error(f"Error updating test file: {e}")
            return False
