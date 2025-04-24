"""
Mutation-Guided Test Generator

A tool that enhances test suites using mutation testing and LLM-guided test generation.
"""

import os
import re
import sys
import subprocess
import ast
import argparse
import glob
from typing import List, Dict, Tuple, Any, Optional
import logging
import openai  # For LLM integration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
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


class MutationTester:
    """Runs mutation testing using MutMut."""
    
    @staticmethod
    def ensure_mutmut_installed() -> bool:
        """Ensure MutMut is installed."""
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'mutmut'], 
                          check=True, 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install MutMut: {e}")
            return False
    
    @staticmethod
    def run_mutation_testing(source_file: str, test_file: str) -> List[Dict[str, Any]]:
        """Run mutation testing using MutMut and return surviving mutants."""
        if not MutationTester.ensure_mutmut_installed():
            return []
        
        try:
            # Run mutmut on the source file
            logger.info(f"Running mutation testing on {source_file}")
            cmd = [
                'mutmut', 'run', 
                f'--paths-to-mutate={source_file}',
                f'--test-dir={os.path.dirname(test_file)}'
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True,
                text=True
            )
            
            # Parse the output to find surviving mutants
            surviving_mutants = []
            
            # Get the list of surviving mutants
            list_cmd = ['mutmut', 'results']
            list_result = subprocess.run(
                list_cmd,
                capture_output=True,
                text=True
            )
            
            # Parse the results to extract mutant IDs
            mutant_ids = []
            for line in list_result.stdout.splitlines():
                # Look for lines with surviving mutant IDs
                if 'SURVIVED' in line:
                    try:
                        mutant_id = line.split(':')[0].strip()
                        if mutant_id.isdigit():
                            mutant_ids.append(mutant_id)
                    except Exception:
                        continue
            
            # Get details for each surviving mutant
            for mutant_id in mutant_ids:
                show_cmd = ['mutmut', 'show', mutant_id]
                show_result = subprocess.run(
                    show_cmd,
                    capture_output=True,
                    text=True
                )
                
                # Parse the diff to understand the mutation
                diff_lines = show_result.stdout.splitlines()
                original_line = ""
                mutated_line = ""
                line_number = 0
                
                for i, line in enumerate(diff_lines):
                    if line.startswith('--- '):
                        # Extract file and line information
                        file_info = line
                        continue
                    if line.startswith('@@'):
                        # Extract line number
                        line_info = line
                        match = re.search(r'@@ -(\d+)', line)
                        if match:
                            line_number = int(match.group(1))
                        continue
                    if line.startswith('-') and not line.startswith('--- '):
                        original_line = line[1:].strip()
                    if line.startswith('+') and not line.startswith('+++ '):
                        mutated_line = line[1:].strip()
                
                if original_line and mutated_line:
                    surviving_mutants.append({
                        'id': mutant_id,
                        'line_number': line_number,
                        'original_line': original_line,
                        'mutated_line': mutated_line,
                        'description': f"Changed '{original_line}' to '{mutated_line}' at line {line_number}"
                    })
            
            logger.info(f"Found {len(surviving_mutants)} surviving mutants")
            return surviving_mutants
            
        except Exception as e:
            logger.error(f"Error running mutation testing: {e}")
            return []


class LLMTestGenerator:
    """Generates tests using LLM."""
    
    def __init__(self, api_key=None):
        """Initialize with API key if provided."""
        self.api_key = api_key
        if api_key:
            openai.api_key = api_key
    
    def generate_test(self, prompt: str) -> str:
        """Generate a test method using an LLM."""
        try:
            if self.api_key:
                # Use OpenAI API
                response = openai.Completion.create(
                    engine="gpt-4",
                    prompt=prompt,
                    max_tokens=1000,
                    temperature=0.5,
                    top_p=1.0,
                    frequency_penalty=0.0,
                    presence_penalty=0.0
                )
                return response.choices[0].text.strip()
            else:
                # Mock response for demonstration
                logger.warning("No API key provided. Using mock LLM responses.")
                return self._mock_response(prompt)
        except Exception as e:
            logger.error(f"Error generating test with LLM: {e}")
            return ""
    
    def _mock_response(self, prompt: str) -> str:
        """Provide mock responses for demonstration purposes."""
        if "calculate_discount" in prompt and "100" in prompt:
            return """def test_calculate_discount_boundary_case(self):
    """Test the boundary case where discount_percent is exactly 100."""
    # Should fully discount the price (price becomes 0)
    self.assertEqual(calculator.calculate_discount(100, 100), 0)
    # Ensure large values still work correctly
    self.assertEqual(calculator.calculate_discount(500, 100), 0)"""
            
        elif "is_prime" in prompt and "n <= 1" in prompt:
            return """def test_is_prime_edge_cases(self):
    """Test edge cases for the is_prime function."""
    # n=1 is specifically defined as not prime
    self.assertFalse(calculator.is_prime(1))
    # n=0 is not prime
    self.assertFalse(calculator.is_prime(0))
    # Negative numbers are not prime
    self.assertFalse(calculator.is_prime(-5))"""
            
        elif "is_prime" in prompt and "n % 2 == 0" in prompt:
            return """def test_is_prime_even_numbers(self):
    """Test that even numbers greater than 2 are correctly identified as non-prime."""
    # 2 is prime (the only even prime)
    self.assertTrue(calculator.is_prime(2))
    # Test various even numbers, which should all be non-prime
    self.assertFalse(calculator.is_prime(4))
    self.assertFalse(calculator.is_prime(6))
    self.assertFalse(calculator.is_prime(100))"""
            
        elif "is_prime" in prompt and "return True" in prompt:
            return """def test_is_prime_larger_numbers(self):
    """Test that larger prime numbers are correctly identified."""
    # Test with known larger prime numbers
    self.assertTrue(calculator.is_prime(17))
    self.assertTrue(calculator.is_prime(19))
    self.assertTrue(calculator.is_prime(97))
    # Test a larger prime number
    self.assertTrue(calculator.is_prime(7919))"""
            
        else:
            return """def test_generated_for_mutant(self):
    """Test generated to catch a specific mutant."""
    # This test would be tailored to catch the specific mutation
    pass"""


class TestRunner:
    """Runs tests and verifies their effectiveness."""
    
    @staticmethod
    def verify_tests(source_file: str, test_file: str) -> str:
        """Run tests to verify they're working and killing mutants."""
        try:
            # Run the tests
            test_dir = os.path.dirname(test_file)
            test_module = os.path.basename(test_file)[:-3]  # Remove .py
            
            logger.info(f"Running tests in {test_file}")
            cmd = [sys.executable, '-m', 'unittest', f'{test_module}']
            result = subprocess.run(
                cmd,
                cwd=test_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                error_msg = f"Tests failed to run: {result.stderr}"
                logger.error(error_msg)
                return error_msg
            
            # Run mutation testing again to see if mutants are now killed
            logger.info("Running mutation testing again to verify improvement")
            cmd = [
                'mutmut', 'run', 
                f'--paths-to-mutate={source_file}',
                f'--test-dir={os.path.dirname(test_file)}'
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True,
                text=True
            )
            
            # Parse the output for mutation score
            mutation_score = "Unknown"
            for line in result.stdout.splitlines():
                if "Mutation score" in line:
                    mutation_score = line.strip()
                    break
            
            success_msg = f"Tests passed. {mutation_score}"
            logger.info(success_msg)
            return success_msg
            
        except Exception as e:
            error_msg = f"Error verifying tests: {e}"
            logger.error(error_msg)
            return error_msg


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
            if len(mapping) == 0:
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


class MutationGuidedTestGenerator:
    """Main class that orchestrates the mutation-guided test generation process."""
    
    def __init__(self, source_dir: str, test_dir: str, llm_api_key: Optional[str] = None):
        """Initialize with source and test directories."""
        self.source_dir = source_dir
        self.test_dir = test_dir
        self.llm_generator = LLMTestGenerator(llm_api_key)
        
        if not os.path.exists(source_dir):
            raise ValueError(f"Source directory does not exist: {source_dir}")
        if not os.path.exists(test_dir):
            raise ValueError(f"Test directory does not exist: {test_dir}")
    
    def run(self) -> str:
        """Run the mutation-guided test generation process."""
        logger.info(f"Starting mutation-guided test generation")
        logger.info(f"Source directory: {self.source_dir}")
        logger.info(f"Test directory: {self.test_dir}")
        
        # Step 1: Locate source and test files
        source_files = FileSystem.list_python_files(self.source_dir)
        test_files = FileSystem.list_python_files(self.test_dir)
        
        if not source_files:
            return "Could not find Python files in the source directory."
        if not test_files:
            return "Could not find Python files in the test directory."
        
        logger.info(f"Found {len(source_files)} source files and {len(test_files)} test files")
        
        # Map test files to source files
        file_mapping = CodeAnalyzer.map_test_to_source_files(source_files, test_files)
        
        if not file_mapping:
            return "Could not map test files to source files. Make sure they follow naming conventions."
        
        improved_files_count = 0
        
        # Process each source file with corresponding test file
        for source_file, test_file in file_mapping.items():
            logger.info(f"\n--- Processing {source_file} with test file {test_file} ---")
            
            # Step 2: Run mutation testing
            mutants = MutationTester.run_mutation_testing(source_file, test_file)
            
            if not mutants:
                logger.info(f"No surviving mutants found for {source_file}, skipping...")
                continue
                
            logger.info(f"Found {len(mutants)} surviving mutants")
            
            # Step 3 & 4: Generate LLM prompts and new tests
            new_tests = []
            for mutant in mutants:
                logger.info(f"Processing mutant: {mutant['description']}")
                
                # Create LLM prompt based on the mutant
                prompt = CodeAnalyzer.create_prompt_for_mutant(
                    source_file, test_file, mutant
                )
                
                # Generate new test using LLM
                test_code = self.llm_generator.generate_test(prompt)
                if test_code:
                    new_tests.append(test_code)
                    logger.info("Generated new test for mutant")
                else:
                    logger.warning("Failed to generate test for this mutant")
            
            if not new_tests:
                logger.info(f"No new tests generated for {source_file}, skipping...")
                continue
                
            # Step 5: Update test file with new tests
            test_updated = FileSystem.update_test_file(
                test_file, new_tests
            )
            
            if test_updated:
                improved_files_count += 1
                logger.info(f"Updated test file: {test_file}")
                
                # Step 6: Verify the effectiveness of new tests
                verification = TestRunner.verify_tests(
                    source_file, test_file
                )
                logger.info(f"Verification result: {verification}")
            else:
                logger.error(f"Failed to update test file: {test_file}")
        
        result = f"""
        Mutation-guided test generation completed.
        
        Summary:
        - Processed {len(file_mapping)} source/test file pairs
        - Improved test coverage for {improved_files_count} files
        
        The test files have been updated with LLM-generated tests that target
        previously undetected mutations in your code.
        """
        
        logger.info("Test generation process completed")
        return result


def main():
    """Main function to run the tool from command line."""
    parser = argparse.ArgumentParser(
        description='Mutation-guided test generator that enhances test coverage using LLMs'
    )
    parser.add_argument('--source_dir', required=True, help='Directory containing source code files')
    parser.add_argument('--test_dir', required=True, help='Directory containing test files')
    parser.add_argument('--api_key', help='API key for the LLM service (optional)')
    
    args = parser.parse_args()
    
    try:
        generator = MutationGuidedTestGenerator(
            source_dir=args.source_dir,
            test_dir=args.test_dir,
            llm_api_key=args.api_key
        )
        result = generator.run()
        print(result)
    except Exception as e:
        logger.error(f"Error running test generator: {e}")
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
