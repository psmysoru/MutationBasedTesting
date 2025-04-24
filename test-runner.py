"""
TestRunner module for running tests and verifying their effectiveness.
"""

import os
import sys
import subprocess
import logging

logger = logging.getLogger(__name__)

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
