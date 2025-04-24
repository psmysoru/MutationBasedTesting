"""
Mutation-Guided Test Generator

A tool that enhances test suites using mutation testing and GitHub Copilot-guided test generation.
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

# Import our GitHub Copilot test generator
from github_copilot_test_generator import GithubCopilotTestGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Re-use the FileSystem, MutationTester, TestRunner, and CodeAnalyzer classes from your original code
# [These classes would be included here, but I'm omitting them for brevity]

class MutationGuidedTestGenerator:
    """Main class that orchestrates the mutation-guided test generation process."""
    
    def __init__(self, source_dir: str, test_dir: str, vscode_path: Optional[str] = None):
        """Initialize with source and test directories."""
        self.source_dir = source_dir
        self.test_dir = test_dir
        self.copilot_generator = GithubCopilotTestGenerator(vscode_path)
        
        if not os.path.exists(source_dir):
            raise ValueError(f"Source directory does not exist: {source_dir}")
        if not os.path.exists(test_dir):
            raise ValueError(f"Test directory does not exist: {test_dir}")
    
    def run(self) -> str:
        """Run the mutation-guided test generation process."""
        logger.info(f"Starting mutation-guided test generation with GitHub Copilot")
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
            
            # Step 3 & 4: Generate Copilot prompts and new tests
            new_tests = []
            for mutant in mutants:
                logger.info(f"Processing mutant: {mutant['description']}")
                
                # Create prompt based on the mutant
                prompt = CodeAnalyzer.create_prompt_for_mutant(
                    source_file, test_file, mutant
                )
                
                # Generate new test using GitHub Copilot
                test_code = self.copilot_generator.generate_test(prompt)
                if test_code:
                    new_tests.append(test_code)
                    logger.info("Generated new test for mutant using GitHub Copilot")
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
        
        The test files have been updated with GitHub Copilot-generated tests that target
        previously undetected mutations in your code.
        """
        
        logger.info("Test generation process completed")
        return result


def main():
    """Main function to run the tool from command line."""
    parser = argparse.ArgumentParser(
        description='Mutation-guided test generator that enhances test coverage using GitHub Copilot'
    )
    parser.add_argument('--source_dir', required=True, help='Directory containing source code files')
    parser.add_argument('--test_dir', required=True, help='Directory containing test files')
    parser.add_argument('--vscode_path', help='Path to VS Code executable (optional)')
    
    args = parser.parse_args()
    
    try:
        generator = MutationGuidedTestGenerator(
            source_dir=args.source_dir,
            test_dir=args.test_dir,
            vscode_path=args.vscode_path
        )
        result = generator.run()
        print(result)
    except Exception as e:
        logger.error(f"Error running test generator: {e}")
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
