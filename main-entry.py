"""
Main entry point for the mutation-guided test generator.
"""

import sys
import argparse
import logging

from mutation_guided_test_generator import MutationGuidedTestGenerator

logger = logging.getLogger(__name__)

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
