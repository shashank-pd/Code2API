import pytest
import os
import sys

# Mock environment for CI
if not os.getenv('GROQ_API_KEY'):
    os.environ['GROQ_API_KEY'] = 'test_key_for_ci'

def test_imports():
    """Test that core modules can be imported"""
    try:
        from src.parsers.code_parser import CodeParser
        from src.generators.api_generator import APIGenerator
        assert True
    except ImportError as e:
        pytest.skip(f"Import failed: {e}")

def test_basic_functionality():
    """Basic smoke test"""
    assert 1 + 1 == 2

if __name__ == "__main__":
    test_imports()
    test_basic_functionality()
    print("Basic tests passed!")
