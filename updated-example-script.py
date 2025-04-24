"""
Example script demonstrating the mutation-guided test generator on a simple calculator module.
"""

import os
import shutil
import tempfile
import logging

from mutation_guided_test_generator import MutationGuidedTestGenerator

def setup_example_project():
    """Set up an example project with a calculator module and basic tests."""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    src_dir = os.path.join(temp_dir, "src")
    tests_dir = os.path.join(temp_dir, "tests")
    
    # Create directories
    os.makedirs(src_dir)
    os.makedirs(tests_dir)
    
    # Create calculator.py
    calc_content = """# calculator.py

def add(a, b):
    """Add two numbers and return the result."""
    return a + b

def subtract(a, b):
    """Subtract b from a and return the result."""
    return a - b

def multiply(a, b):
    """Multiply two numbers and return the result."""
    return a * b

def divide(a, b):
    """Divide a by b and return the result."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def calculate_discount(price, discount_percent):
    """Calculate the final price after applying a discount."""
    if not (0 <= discount_percent <= 100):
        raise ValueError("Discount percentage must be between 0 and 100")
    discount = price * (discount_percent / 100)
    return price - discount

def is_prime(n):
    """Check if a number is prime."""
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True
"""
    
    # Create test_calculator.py
    test_content = """# test_calculator.py
import unittest
import sys
import os

# Add the src directory to the path so we can import calculator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import calculator

class TestCalculator(unittest.TestCase):
    def test_add(self):
        self.assertEqual(calculator.add(2, 3), 5)
        self.assertEqual(calculator.add(-1, 1), 0)
    
    def test_subtract(self):
        self.assertEqual(calculator.subtract(5, 3), 2)
        self.assertEqual(calculator.subtract(10, 10), 0)
    
    def test_multiply(self):
        self.assertEqual(calculator.multiply(3, 4), 12)
        self.assertEqual(calculator.multiply(0, 5), 0)
    
    def test_divide(self):
        self.assertEqual(calculator.divide(10, 2), 5)
        self.assertEqual(calculator.divide(7, 2), 3.5)
        with self.assertRaises(ValueError):
            calculator.divide(5, 0)
    
    def test_calculate_discount(self):
        self.assertEqual(calculator.calculate_discount(100, 20), 80)

if __name__ == "__main__":
    unittest.main()
"""
    
    # Write the files
    with open(os.path.join(src_dir, "calculator.py"), 'w') as f:
        f.write(calc_content)
    
    with open(os.path.join(tests_dir, "test_calculator.py"), 'w') as f:
        f.write(test_content)
    
    return temp_dir, src_dir, tests_dir

def run_test_generator(src_dir, tests_dir):
    """Run the mutation-guided test generator on the example project."""
    # Create the generator
    generator = MutationGuidedTestGenerator(
        source_dir=src_dir,
        test_dir=tests_dir
    )
    
    # Run the generator
    result = generator.run()
    print(result)
    
    # Print the updated test file
    with open(os.path.join(tests_dir, "test_calculator.py"), 'r') as f:
        print("\nUpdated test file:")
        print(f.read())

def cleanup(temp_dir):
    """Clean up the temporary directory."""
    shutil.rmtree(temp_dir)

def main():
    """Main function to demonstrate the test generator."""
    temp_dir, src_dir, tests_dir = setup_example_project()
    
    try:
        print(f"Created example project in {temp_dir}")
        print(f"Source directory: {src_dir}")
        print(f"Test directory: {tests_dir}")
        
        print("\nRunning mutation-guided test generator...")
        run_test_generator(src_dir, tests_dir)
        
    finally:
        # Uncomment to clean up the temporary directory
        # cleanup(temp_dir)
        print(f"\nExample project files are in {temp_dir}")
        print("You can inspect them and then delete the directory manually.")

if __name__ == "__main__":
    main()
