"""
LLMTestGenerator module for generating tests using LLMs.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

class LLMTestGenerator:
    """Generates tests using LLM."""
    
    def __init__(self, api_key=None):
        """Initialize with API key if provided."""
        self.api_key = api_key
        if api_key:
            try:
                import openai
                openai.api_key = api_key
                self.openai = openai
            except ImportError:
                logger.warning("OpenAI package is not installed. Using mock responses instead.")
                self.openai = None
        else:
            self.openai = None
    
    def generate_test(self, prompt: str) -> str:
        """Generate a test method using an LLM."""
        try:
            if self.api_key and self.openai:
                # Use OpenAI API
                response = self.openai.Completion.create(
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
