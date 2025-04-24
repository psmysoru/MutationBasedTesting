# Mutation-Guided Test Generator

A tool that enhances test suites using mutation testing and LLM-guided test generation.

## Overview

This tool helps improve test coverage by:
1. Identifying code mutations that aren't caught by existing tests
2. Using LLMs to generate new test cases that specifically target these mutations
3. Adding these generated tests to the test suite

## Project Structure

The codebase has been refactored to follow SOLID principles:

- `file_system.py`: Handles file system operations
- `mutation_tester.py`: Runs mutation testing using MutMut
- `llm_test_generator.py`: Generates tests using an LLM
- `test_runner.py`: Runs tests and verifies their effectiveness
- `code_analyzer.py`: Analyzes code structure and relationships
- `mutation_guided_test_generator.py`: Main orchestrator class
- `main.py`: Command-line entry point
- `example_script.py`: Example script demonstrating usage

## SOLID Principles Applied

1. **Single Responsibility Principle**: Each class has one specific responsibility
2. **Open/Closed Principle**: Classes are open for extension but closed for modification
3. **Liskov Substitution Principle**: Each component can be replaced with another implementation
4. **Interface Segregation Principle**: Separated interfaces for different responsibilities
5. **Dependency Inversion Principle**: High-level modules depend on abstractions

## Usage

```python
from mutation_guided_test_generator import MutationGuidedTestGenerator

# Initialize the generator
generator = MutationGuidedTestGenerator(
    source_dir="path/to/source",
    test_dir="path/to/tests",
    llm_api_key="your_api_key"  # Optional
)

# Run the generator
result = generator.run()
print(result)
```

You can also run it from the command line:

```bash
python main.py --source_dir path/to/source --test_dir path/to/tests --api_key your_api_key
```

## Example

See `example_script.py` for a complete working example with a simple calculator module.
