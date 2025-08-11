import pytest
import tempfile
import os
from pathlib import Path

from src.parsers.code_parser import CodeParser
from src.ai.analyzer import AIAnalyzer
from src.generators.api_generator import APIGenerator

class TestCodeParser:
    """Test the code parser functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.parser = CodeParser()
    
    def test_python_parsing(self):
        """Test parsing Python code"""
        python_code = '''
def hello_world(name):
    """Say hello to someone"""
    return f"Hello, {name}!"

class TestClass:
    def test_method(self, value):
        return value * 2
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_code)
            temp_path = f.name
        
        try:
            parsed = self.parser.parse_file(temp_path)
            
            assert parsed.language == "python"
            assert len(parsed.functions) >= 1
            assert len(parsed.classes) >= 1
            assert parsed.functions[0].name == "hello_world"
            assert parsed.classes[0].name == "TestClass"
        finally:
            os.unlink(temp_path)
    
    def test_javascript_parsing(self):
        """Test parsing JavaScript code"""
        js_code = '''
function calculateSum(a, b) {
    return a + b;
}

const multiply = (x, y) => x * y;
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(js_code)
            temp_path = f.name
        
        try:
            parsed = self.parser.parse_file(temp_path)
            
            assert parsed.language == "javascript"
            assert len(parsed.functions) >= 2
            function_names = [f.name for f in parsed.functions]
            assert "calculateSum" in function_names
            assert "multiply" in function_names
        finally:
            os.unlink(temp_path)

class TestAIAnalyzer:
    """Test the AI analyzer functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.analyzer = AIAnalyzer()
    
    def test_security_analysis(self):
        """Test security analysis functionality"""
        # Mock parsed code with security-sensitive function
        from src.parsers.code_parser import ParsedCode, Function
        
        security_func = Function(
            name="authenticate_user",
            parameters=[{"name": "username"}, {"name": "password"}],
            return_type="bool",
            docstring="Authenticate user",
            line_number=1
        )
        
        parsed_code = ParsedCode(
            functions=[security_func],
            classes=[],
            imports=[],
            language="python",
            file_path="test.py"
        )
        
        recommendations = self.analyzer._analyze_security(parsed_code)
        assert len(recommendations) > 0
        assert any("auth" in rec.lower() for rec in recommendations)

class TestAPIGenerator:
    """Test the API generator functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.generator = APIGenerator()
    
    def test_api_generation(self):
        """Test API generation"""
        # Mock analysis data
        analysis = {
            "api_endpoints": [
                {
                    "function_name": "test_function",
                    "http_method": "GET",
                    "endpoint_path": "/test",
                    "description": "Test endpoint",
                    "needs_auth": False,
                    "parameters": [],
                    "is_async": False
                }
            ],
            "security_recommendations": [],
            "optimization_suggestions": []
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate API
            api_path = self.generator.generate_api(analysis, "test_api")
            
            # Check that files were created
            api_dir = Path(api_path)
            assert api_dir.exists()
            assert (api_dir / "main.py").exists()
            assert (api_dir / "models.py").exists()
            assert (api_dir / "auth.py").exists()
            assert (api_dir / "requirements.txt").exists()
            assert (api_dir / "README.md").exists()
            
            # Check main.py content
            main_content = (api_dir / "main.py").read_text()
            assert "test_function" in main_content
            assert "/test" in main_content

class TestIntegration:
    """Integration tests"""
    
    def test_full_pipeline(self):
        """Test the complete pipeline from parsing to API generation"""
        python_code = '''
def get_user_data(user_id):
    """Get user data by ID"""
    return {"id": user_id, "name": f"User {user_id}"}

def create_user(username, email):
    """Create a new user"""
    return {"message": "User created", "username": username}
'''
        
        parser = CodeParser()
        analyzer = AIAnalyzer()
        generator = APIGenerator()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_code)
            temp_path = f.name
        
        try:
            # Parse
            parsed_code = parser.parse_file(temp_path)
            assert len(parsed_code.functions) == 2
            
            # Analyze (skip AI analysis for testing)
            analysis = {
                "api_endpoints": [
                    {
                        "function_name": func.name,
                        "http_method": "GET" if "get" in func.name.lower() else "POST",
                        "endpoint_path": f"/{func.name}",
                        "description": func.docstring or "",
                        "needs_auth": False,
                        "parameters": func.parameters,
                        "is_async": func.is_async
                    }
                    for func in parsed_code.functions
                ],
                "security_recommendations": [],
                "optimization_suggestions": []
            }
            
            # Generate API
            with tempfile.TemporaryDirectory() as temp_dir:
                api_path = generator.generate_api(analysis, "integration_test")
                
                # Verify API was generated
                api_dir = Path(api_path)
                assert api_dir.exists()
                assert (api_dir / "main.py").exists()
                
                # Check that both functions are in the API
                main_content = (api_dir / "main.py").read_text()
                assert "get_user_data" in main_content
                assert "create_user" in main_content
        
        finally:
            os.unlink(temp_path)

if __name__ == "__main__":
    pytest.main([__file__])
