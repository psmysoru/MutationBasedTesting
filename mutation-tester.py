"""
MutationTester module for running mutation testing using MutMut.
"""

import os
import re
import sys
import subprocess
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

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
