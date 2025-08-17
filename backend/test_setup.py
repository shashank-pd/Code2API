"""
Test the MasterAgent initialization and basic functionality
"""

import pytest
import asyncio
import os
from unittest.mock import patch, MagicMock

from app.agents.master_agent import MasterAgent


class TestMasterAgent:
    """Test the MasterAgent class"""
    
    @pytest.fixture
    def mock_groq_key(self):
        """Mock Groq API key"""
        with patch.dict(os.environ, {"GROQ_API_KEY": "test_key"}):
            yield "test_key"
    
    def test_master_agent_creation(self, mock_groq_key):
        """Test MasterAgent can be created"""
        agent = MasterAgent()
        assert agent is not None
        assert agent.groq_api_key == "test_key"
    
    @pytest.mark.asyncio
    async def test_master_agent_initialization(self, mock_groq_key):
        """Test MasterAgent initialization"""
        with patch('app.agents.master_agent.ChatGroq') as mock_groq:
            with patch('app.agents.master_agent.create_openai_tools_agent') as mock_agent:
                with patch('app.agents.master_agent.AgentExecutor') as mock_executor:
                    
                    # Setup mocks
                    mock_groq.return_value = MagicMock()
                    mock_agent.return_value = MagicMock()
                    mock_executor.return_value = MagicMock()
                    
                    agent = MasterAgent()
                    await agent.initialize()
                    
                    # Verify initialization
                    assert agent.llm is not None
                    assert agent.agent_executor is not None
                    assert len(agent.tools) == 7  # Should have 7 tools
    
    def test_master_agent_no_groq_key(self):
        """Test MasterAgent fails without Groq API key"""
        with patch.dict(os.environ, {}, clear=True):
            agent = MasterAgent()
            
            with pytest.raises(ValueError, match="GROQ_API_KEY"):
                asyncio.run(agent.initialize())
    
    @pytest.mark.asyncio
    async def test_check_groq_connection(self, mock_groq_key):
        """Test Groq connection check"""
        agent = MasterAgent()
        
        # Test without initialization
        status = await agent.check_groq_connection()
        assert status == "not_initialized"
        
        # Test with initialization
        with patch('app.agents.master_agent.ChatGroq') as mock_groq:
            mock_llm = MagicMock()
            mock_groq.return_value = mock_llm
            
            await agent.initialize()
            
            # Mock successful API call
            mock_llm.ainvoke = MagicMock(return_value="test response")
            status = await agent.check_groq_connection()
            assert status == "connected"
    
    @pytest.mark.asyncio 
    async def test_check_github_connection(self, mock_groq_key):
        """Test GitHub connection check"""
        agent = MasterAgent()
        
        # Test without GitHub token
        status = await agent.check_github_connection()
        assert status == "public_access_only"
        
        # Test with GitHub token
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
            agent = MasterAgent()
            status = await agent.check_github_connection()
            assert status == "configured"
    
    def test_get_workflow_status(self, mock_groq_key):
        """Test workflow status reporting"""
        agent = MasterAgent()
        status = agent.get_workflow_status()
        
        assert isinstance(status, dict)
        assert "initialized" in status
        assert "tools_available" in status
        assert "current_workflow" in status
        assert "groq_configured" in status
        assert "github_configured" in status
        
        # Before initialization
        assert status["initialized"] is False
        assert status["tools_available"] == 0
        assert status["groq_configured"] is True  # Mock key is set


@pytest.mark.asyncio
async def test_import_all_tools():
    """Test that all required tools can be imported"""
    try:
        from app.tools.code_fetcher import code_fetcher_tool
        from app.tools.code_analyzer import code_analyzer_tool
        from app.tools.api_designer import api_designer_tool
        from app.tools.api_generator import api_generator_tool
        from app.tools.security_enforcer import security_enforcer_tool
        from app.tools.api_tester import api_tester_tool
        from app.tools.documentation_generator import documentation_generator_tool
        
        # Verify tools have required attributes
        tools = [
            code_fetcher_tool,
            code_analyzer_tool,
            api_designer_tool,
            api_generator_tool,
            security_enforcer_tool,
            api_tester_tool,
            documentation_generator_tool
        ]
        
        for tool in tools:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert callable(tool)
        
        print("✅ All tools imported successfully")
        
    except ImportError as e:
        pytest.fail(f"Failed to import tools: {e}")


if __name__ == "__main__":
    # Run a simple test
    import sys
    import os
    
    # Add the backend directory to Python path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Set a mock Groq API key for testing
    os.environ["GROQ_API_KEY"] = "test_key"
    
    try:
        # Test imports
        asyncio.run(test_import_all_tools())
        
        # Test MasterAgent creation
        agent = MasterAgent()
        print(f"✅ MasterAgent created successfully")
        print(f"✅ Groq API key configured: {agent.groq_api_key is not None}")
        print(f"✅ Tools available: {len(agent.tools)}")
        
        # Test workflow status
        status = agent.get_workflow_status()
        print(f"✅ Workflow status: {status}")
        
        print("\n🎉 Backend setup test completed successfully!")
        
    except Exception as e:
        print(f"❌ Backend setup test failed: {e}")
        sys.exit(1)
