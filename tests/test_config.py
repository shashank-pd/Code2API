"""
Tests for the configuration module
"""
import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.config import Config


class TestConfig:
    """Test configuration functionality"""
    
    def test_default_values(self):
        """Test default configuration values"""
        config = Config()
        assert config.API_HOST == "localhost"
        assert config.API_PORT == 8000
        assert config.API_VERSION == "v1"
        assert config.JWT_ALGORITHM == "HS256"
        assert config.ACCESS_TOKEN_EXPIRE_MINUTES == 30
    
    def test_supported_languages(self):
        """Test supported languages configuration"""
        config = Config()
        assert "python" in config.SUPPORTED_LANGUAGES
        assert "javascript" in config.SUPPORTED_LANGUAGES
        assert "java" in config.SUPPORTED_LANGUAGES
        
        # Check language structure
        python_config = config.SUPPORTED_LANGUAGES["python"]
        assert ".py" in python_config["extensions"]
        assert python_config["tree_sitter"] == "python"
        assert python_config["comment_style"] == "#"
    
    def test_ai_analysis_settings(self):
        """Test AI analysis configuration"""
        config = Config()
        assert config.MAX_TOKENS == 2000
        assert config.TEMPERATURE == 0.3
        assert config.GROQ_MODEL == "openai/gpt-oss-20b"
    
    def test_ensure_directories(self):
        """Test directory creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a temporary config with custom paths
            temp_path = Path(temp_dir)
            
            # Mock the Config class paths
            with patch.object(Config, 'GENERATED_DIR', temp_path / "generated"), \
                 patch.object(Config, 'TEMPLATES_DIR', temp_path / "templates"), \
                 patch.object(Config, 'EXAMPLES_DIR', temp_path / "examples"):
                
                Config.ensure_directories()
                
                assert (temp_path / "generated").exists()
                assert (temp_path / "templates").exists()
                assert (temp_path / "examples").exists()
    
    def test_validate_config_no_api_keys(self):
        """Test config validation with no API keys"""
        with patch.object(Config, 'GROQ_API_KEY', None), \
             patch.object(Config, 'OPENAI_API_KEY', None):
            
            result = Config.validate_config()
            assert result["valid"] is False
            assert any("No AI API key configured" in issue for issue in result["issues"])
    
    def test_validate_config_with_groq_key(self):
        """Test config validation with Groq API key"""
        with patch.object(Config, 'GROQ_API_KEY', "test_groq_key"), \
             patch.object(Config, 'OPENAI_API_KEY', None), \
             patch.object(Config, 'SECRET_KEY', "a_very_long_secret_key_that_is_secure_enough"):
            
            result = Config.validate_config()
            # May have warnings but should be valid
            assert result["valid"] is True or len(result["issues"]) == 0
    
    def test_validate_config_default_secret_key(self):
        """Test config validation with default secret key"""
        with patch.object(Config, 'GROQ_API_KEY', "test_key"), \
             patch.object(Config, 'SECRET_KEY', "your-secret-key-change-in-production"):
            
            result = Config.validate_config()
            assert any("Using default SECRET_KEY" in warning for warning in result["warnings"])
    
    def test_validate_config_short_secret_key(self):
        """Test config validation with short secret key"""
        with patch.object(Config, 'GROQ_API_KEY', "test_key"), \
             patch.object(Config, 'SECRET_KEY', "short"):
            
            result = Config.validate_config()
            assert any("SECRET_KEY should be at least 32 characters" in warning for warning in result["warnings"])
    
    def test_validate_config_invalid_port(self):
        """Test config validation with invalid port"""
        with patch.object(Config, 'GROQ_API_KEY', "test_key"), \
             patch.object(Config, 'API_PORT', 999999):
            
            result = Config.validate_config()
            assert result["valid"] is False
            assert any("Invalid API_PORT" in issue for issue in result["issues"])
    
    def test_get_ai_provider_groq(self):
        """Test AI provider detection - Groq"""
        with patch.object(Config, 'GROQ_API_KEY', "test_groq_key"), \
             patch.object(Config, 'OPENAI_API_KEY', None):
            
            result = Config.get_ai_provider()
            assert result == "groq"
    
    def test_get_ai_provider_openai(self):
        """Test AI provider detection - OpenAI"""
        with patch.object(Config, 'GROQ_API_KEY', None), \
             patch.object(Config, 'OPENAI_API_KEY', "test_openai_key"):
            
            result = Config.get_ai_provider()
            assert result == "openai"
    
    def test_get_ai_provider_none(self):
        """Test AI provider detection - None"""
        with patch.object(Config, 'GROQ_API_KEY', None), \
             patch.object(Config, 'OPENAI_API_KEY', None):
            
            result = Config.get_ai_provider()
            assert result == "none"
    
    def test_get_ai_provider_prefers_groq(self):
        """Test AI provider detection prefers Groq when both are available"""
        with patch.object(Config, 'GROQ_API_KEY', "test_groq_key"), \
             patch.object(Config, 'OPENAI_API_KEY', "test_openai_key"):
            
            result = Config.get_ai_provider()
            assert result == "groq"
    
    @patch.dict(os.environ, {
        'API_HOST': 'test.example.com',
        'API_PORT': '9000',
        'API_DEBUG': 'true',
        'GROQ_API_KEY': 'test_groq_key_from_env',
        'SECRET_KEY': 'test_secret_key_from_environment'
    })
    def test_environment_variable_loading(self):
        """Test loading configuration from environment variables"""
        # Create a new config instance to pick up env vars
        config = Config()
        
        assert config.API_HOST == 'test.example.com'
        assert config.API_PORT == 9000
        assert config.API_DEBUG is True
        assert config.GROQ_API_KEY == 'test_groq_key_from_env'
        assert config.SECRET_KEY == 'test_secret_key_from_environment'
    
    def test_path_configuration(self):
        """Test path configuration"""
        config = Config()
        
        # ROOT_DIR should be the parent of the src directory
        assert config.ROOT_DIR.name == "Code2API"
        assert config.TEMPLATES_DIR == config.ROOT_DIR / "templates"
        assert config.GENERATED_DIR == config.ROOT_DIR / "generated"
        assert config.EXAMPLES_DIR == config.ROOT_DIR / "examples"
    
    def test_language_extensions(self):
        """Test language extension mappings"""
        config = Config()
        
        python_exts = config.SUPPORTED_LANGUAGES["python"]["extensions"]
        assert ".py" in python_exts
        
        js_exts = config.SUPPORTED_LANGUAGES["javascript"]["extensions"]
        assert ".js" in js_exts
        assert ".jsx" in js_exts
        assert ".ts" in js_exts
        assert ".tsx" in js_exts
        
        java_exts = config.SUPPORTED_LANGUAGES["java"]["extensions"]
        assert ".java" in java_exts


class TestConfigIntegration:
    """Integration tests for configuration"""
    
    def test_config_singleton_behavior(self):
        """Test that config behaves consistently"""
        from src.config import config
        
        # The config should be importable and usable
        assert hasattr(config, 'API_HOST')
        assert hasattr(config, 'SUPPORTED_LANGUAGES')
        assert hasattr(config, 'ensure_directories')
        assert hasattr(config, 'validate_config')
    
    def test_validation_with_real_config(self):
        """Test validation with the actual config instance"""
        from src.config import config
        
        result = config.validate_config()
        
        # Should return a properly structured result
        assert "valid" in result
        assert "issues" in result
        assert "warnings" in result
        assert isinstance(result["valid"], bool)
        assert isinstance(result["issues"], list)
        assert isinstance(result["warnings"], list)
    
    def test_ai_provider_with_real_config(self):
        """Test AI provider detection with real config"""
        from src.config import config
        
        provider = config.get_ai_provider()
        assert provider in ["groq", "openai", "none"]