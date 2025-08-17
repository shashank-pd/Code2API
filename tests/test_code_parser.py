"""
Tests for the code parser module
"""
import pytest
import tempfile
import os
from pathlib import Path

from src.parsers.code_parser import CodeParser, ParsedCode, Function, Class


class TestCodeParser:
    """Test code parser functionality"""
    
    def setup_method(self):
        """Setup test parser"""
        self.parser = CodeParser()
    
    def test_detect_python_language(self):
        """Test Python language detection"""
        result = self.parser._detect_language(Path("test.py"))
        assert result == "python"
    
    def test_detect_javascript_language(self):
        """Test JavaScript language detection"""
        assert self.parser._detect_language(Path("test.js")) == "javascript"
        assert self.parser._detect_language(Path("test.jsx")) == "javascript"
        assert self.parser._detect_language(Path("test.ts")) == "javascript"
        assert self.parser._detect_language(Path("test.tsx")) == "javascript"
    
    def test_detect_java_language(self):
        """Test Java language detection"""
        result = self.parser._detect_language(Path("test.java"))
        assert result == "java"
    
    def test_unsupported_language(self):
        """Test unsupported language detection"""
        with pytest.raises(ValueError, match="Unsupported file extension"):
            self.parser._detect_language(Path("test.cpp"))
    
    def test_parse_python_simple_function(self):
        """Test parsing simple Python function"""
        python_code = '''
def hello_world():
    """Simple hello world function"""
    return "Hello, World!"
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_code)
            temp_file = f.name
        
        try:
            result = self.parser.parse_file(temp_file)
            assert isinstance(result, ParsedCode)
            assert result.language == "python"
            assert len(result.functions) == 1
            assert result.functions[0].name == "hello_world"
            assert "Simple hello world function" in result.functions[0].docstring
            assert len(result.classes) == 0
        finally:
            os.unlink(temp_file)
    
    def test_parse_python_class(self):
        """Test parsing Python class"""
        python_code = '''
class TestClass:
    """A test class"""
    
    def __init__(self):
        self.value = 0
    
    def get_value(self):
        """Get the value"""
        return self.value
    
    def set_value(self, new_value):
        """Set the value"""
        self.value = new_value
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_code)
            temp_file = f.name
        
        try:
            result = self.parser.parse_file(temp_file)
            assert len(result.classes) == 1
            assert result.classes[0].name == "TestClass"
            assert len(result.classes[0].methods) >= 2  # get_value and set_value (excluding __init__)
            assert "A test class" in result.classes[0].docstring
        finally:
            os.unlink(temp_file)
    
    def test_parse_python_async_function(self):
        """Test parsing async Python function"""
        python_code = '''
async def async_hello():
    """Async hello function"""
    return "Hello Async!"
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_code)
            temp_file = f.name
        
        try:
            result = self.parser.parse_file(temp_file)
            assert len(result.functions) == 1
            assert result.functions[0].is_async is True
            assert result.functions[0].name == "async_hello"
        finally:
            os.unlink(temp_file)
    
    def test_parse_python_with_imports(self):
        """Test parsing Python file with imports"""
        python_code = '''
import os
from pathlib import Path
import json as js

def use_imports():
    return os.getcwd()
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_code)
            temp_file = f.name
        
        try:
            result = self.parser.parse_file(temp_file)
            assert len(result.imports) >= 2  # Should capture imports
            assert any("os" in imp for imp in result.imports)
            assert any("pathlib" in imp for imp in result.imports)
        finally:
            os.unlink(temp_file)
    
    def test_parse_javascript_simple(self):
        """Test parsing simple JavaScript function"""
        js_code = '''
function helloWorld() {
    /**
     * Simple hello world function
     */
    return "Hello, World!";
}

const arrowFunction = () => {
    return "Arrow function";
};
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(js_code)
            temp_file = f.name
        
        try:
            result = self.parser.parse_file(temp_file)
            assert result.language == "javascript"
            # JavaScript parsing is more basic in the current implementation
            # Should at least parse without errors
            assert isinstance(result, ParsedCode)
        finally:
            os.unlink(temp_file)
    
    def test_parse_java_simple(self):
        """Test parsing simple Java class"""
        java_code = '''
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
    
    public String greet(String name) {
        return "Hello, " + name + "!";
    }
}
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
            f.write(java_code)
            temp_file = f.name
        
        try:
            result = self.parser.parse_file(temp_file)
            assert result.language == "java"
            # Java parsing is more basic in the current implementation
            assert isinstance(result, ParsedCode)
        finally:
            os.unlink(temp_file)
    
    def test_parse_empty_file(self):
        """Test parsing empty file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("")
            temp_file = f.name
        
        try:
            result = self.parser.parse_file(temp_file)
            assert len(result.functions) == 0
            assert len(result.classes) == 0
        finally:
            os.unlink(temp_file)
    
    def test_parse_syntax_error(self):
        """Test parsing file with syntax errors"""
        broken_code = '''
def broken_function(
    # Missing closing parenthesis
print("This is broken")
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(broken_code)
            temp_file = f.name
        
        try:
            # Should handle syntax errors gracefully
            with pytest.raises(Exception):  # Could be SyntaxError or other parsing error
                self.parser.parse_file(temp_file)
        finally:
            os.unlink(temp_file)
    
    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file"""
        with pytest.raises(FileNotFoundError):
            self.parser.parse_file("/path/that/does/not/exist.py")


class TestParsedCodeDataClasses:
    """Test the data classes used for parsed code"""
    
    def test_function_dataclass(self):
        """Test Function dataclass"""
        func = Function(
            name="test_func",
            parameters=[{"name": "arg1", "type": "str"}],
            return_type="str",
            docstring="Test function",
            line_number=10,
            is_async=False
        )
        
        assert func.name == "test_func"
        assert func.is_async is False
        assert func.line_number == 10
        assert len(func.parameters) == 1
    
    def test_class_dataclass(self):
        """Test Class dataclass"""
        method = Function(
            name="method1",
            parameters=[],
            return_type="None",
            docstring="Test method",
            line_number=5
        )
        
        cls = Class(
            name="TestClass",
            methods=[method],
            attributes=["attr1", "attr2"],
            docstring="Test class",
            line_number=1
        )
        
        assert cls.name == "TestClass"
        assert len(cls.methods) == 1
        assert len(cls.attributes) == 2
        assert cls.methods[0].name == "method1"
    
    def test_parsed_code_dataclass(self):
        """Test ParsedCode dataclass"""
        func = Function(
            name="test_func",
            parameters=[],
            return_type="None",
            docstring="Test",
            line_number=1
        )
        
        parsed = ParsedCode(
            functions=[func],
            classes=[],
            imports=["import os"],
            language="python",
            file_path="/test/file.py"
        )
        
        assert len(parsed.functions) == 1
        assert len(parsed.classes) == 0
        assert parsed.language == "python"
        assert parsed.file_path == "/test/file.py"