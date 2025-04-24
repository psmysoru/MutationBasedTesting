"""
CodeAnalyzer module for analyzing code structure and relationships.
"""

import os
import ast
import re
from typing import List, Dict, Any

class CodeAnalyzer:
    """Analyzes code structure and relationships."""
    
    @staticmethod
    def map_test_to_source_files(source_files: List[str], test_files: List[str]) -> Dict[str, str]:
        """Map test files to their corresponding source files."""
        mapping = {}
        
        source_base_names = {os.path.splitext(os.path.basename(f))[0]: f for f in source_files}
        
        for test_file in test_files:
            test_name = os.path.splitext(os.path.basename(test_file))[0]
            
            # Handle common naming patterns
            if test_name.startswith('test_'):
                source_name = test_name[5:]  # Remove 'test_'
                if source_name in source_base_names:
                    mapping[source_base_names[source_name]] = test_file
            elif test_name.endswith('_test'):
                source_name = test_name[:-5]  # Remove '_test'
                if source_name in source_base_names:
                    mapping[source_base_names[source_name]] = test_file
            
            # If no match found by naming convention, try to infer from content
            if test_file not in mapping.values():
                # This would require more sophisticated analysis in a production tool
                pass
        
        return mapping
    
    @staticmethod
    def create_prompt_for_mutant(source_file: str, test_file: str, mutant: Dict[str, Any]) -> str:
        """Create a prompt for the LLM to generate a test for the given mutant."""
        # Read the source file to extract the relevant function
        with open(source_file, 'r', encoding='utf-8') as f:
            source_content = f.read()
        
        # Read the test file to extract existing tests
        with open(test_file, 'r', encoding='utf-8') as f:
            test_content = f.read()
        
        # Parse the source file to find the function containing the mutation
        tree = ast.parse(source_content)
        function_name = None
        function_code = None
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                    if node.lineno <= mutant['line_number'] <= node.end_lineno:
                        function_name = node.name
                        function_code = source_content.splitlines()[node.lineno-1:node.end_lineno]
                        function_code = '\n'.join(function_code)
                        break
        
        if not function_name or not function_code:
            # If we couldn't find the function, use a more generic approach
            # Extract a few lines around the mutation
            lines = source_content.splitlines()
            start_line = max(0, mutant['line_number'] - 5)
            end_line = min(len(lines), mutant['line_number'] + 5)
            context_code = '\n'.join(lines[start_line:end_line])
            
            # Try to extract the function name from the context
            match = re.search(r'def\s+(\w+)\s*\(', context_code)
            if match:
                function_name = match.group(1)
            else:
                function_name = "unknown_function"
        
        # Extract existing tests for this function
        existing_tests = ""
        test_tree = ast.parse(test_content)
        for node in ast.walk(test_tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith('test_') and function_name.lower() in node.name.lower():
                    test_code = test_content.splitlines()[node.lineno-1:node.end_lineno]
                    existing_tests += '\n'.join(test_code) + '\n\n'
        
        # Create the prompt
        module_name = os.path.splitext(os.path.basename(source_file))[0]
        
        prompt = f"""
I have a function in module '{module_name}':

{function_code}

My current test(s) for this function:

{existing_tests}

I found a bug where changing '{mutant['original_line']}' to '{mutant['mutated_line']}' at line {mutant['line_number']} isn't caught by my test suite.

Please generate a new test method that would detect this change. The test should pass on the original code but fail if the mutation is applied.

Return only the Python code for the test method, properly indented and with docstrings explaining what it tests.
"""
        
        return prompt
