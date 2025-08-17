from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_groq import ChatGroq
from typing import Dict, Any, List
import os
import json
import logging
from pathlib import Path

# Import all agent tools
from .tools.code_fetcher import code_fetcher_tool
from .tools.code_analyzer import code_analyzer_tool
from .tools.api_designer import api_designer_tool
from .tools.api_generator import api_generator_tool
from .tools.security_enforcer import security_enforcer_tool
from .tools.api_tester import api_tester_tool
from .tools.documentation_generator import documentation_generator_tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MasterAgent:
    """
    Master Agent that orchestrates the complete code-to-API generation workflow
    using LangChain AgentExecutor with specialized tools.
    """
    
    def __init__(self, groq_api_key: str = None):
        """
        Initialize the MasterAgent with Groq LLM and all specialized tools.
        
        Args:
            groq_api_key: Groq API key for LLM access
        """
        # Initialize Groq LLM
        if not groq_api_key:
            groq_api_key = os.getenv("GROQ_API_KEY")
        
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY must be provided or set as environment variable")
        
        self.llm = ChatGroq(
            api_key=groq_api_key,
            model="llama-3.3-70b-versatile",  # Updated to supported model
            temperature=0.1,  # Low temperature for consistent API generation
            max_tokens=8192,
            timeout=120
        )
        
        # Define all available tools
        self.tools = [
            code_fetcher_tool,
            code_analyzer_tool,
            api_designer_tool,
            api_generator_tool,
            security_enforcer_tool,
            api_tester_tool,
            documentation_generator_tool
        ]
        
        # Create agent prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create the agent
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Create agent executor without deprecated memory
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            max_execution_time=1800,  # 30 minute timeout
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
        
        # Initialize message store for conversation history
        self.store = {}
        
        # Create agent with message history
        self.agent_with_chat_history = RunnableWithMessageHistory(
            self.executor,
            self._get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )
        
        logger.info("MasterAgent initialized with %d tools", len(self.tools))
    
    def _get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """Get or create chat message history for a session"""
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the master agent"""
        return """You are an AI Master Agent specialized in automatically converting code repositories into secure, production-ready REST APIs. Your mission is to orchestrate a complete workflow using your available tools.

Your capabilities include:
1. **Code Fetching**: Retrieve code from GitHub repositories
2. **Code Analysis**: Analyze source code to identify potential API endpoints
3. **API Design**: Create OpenAPI 3.0 specifications
4. **API Generation**: Generate FastAPI server code with proper structure
5. **Security Enhancement**: Apply comprehensive security layers (auth, rate limiting, CORS, etc.)
6. **Test Generation**: Create comprehensive test suites with coverage reporting
7. **Documentation**: Generate beautiful documentation with test badges and deployment guides

**WORKFLOW EXECUTION STRATEGY:**

For each code-to-API conversion request, follow this systematic approach:

1. **PLANNING PHASE**
   - Understand the user's requirements
   - Validate inputs (GitHub URL, repository access, etc.)
   - Plan the conversion strategy

2. **CODE ACQUISITION PHASE**
   - Use code_fetcher_tool to download repository contents
   - Validate successful code retrieval
   - Log repository structure and file types

3. **ANALYSIS PHASE**
   - Use code_analyzer_tool to analyze the codebase
   - Identify potential API endpoints from functions, classes, and modules
   - Extract business logic and data models
   - Generate analysis report with recommendations

4. **DESIGN PHASE**
   - Use api_designer_tool to create OpenAPI 3.0 specification
   - Design RESTful endpoints based on analysis results
   - Define request/response schemas
   - Plan authentication and security requirements

5. **GENERATION PHASE**
   - Use api_generator_tool to generate FastAPI application code
   - Create proper project structure with main.py, models, routers
   - Implement business logic derived from original code
   - Generate requirements.txt and configuration files

6. **SECURITY PHASE**
   - Use security_enforcer_tool to add comprehensive security layers
   - Implement JWT authentication
   - Add rate limiting, CORS protection
   - Apply security headers and input validation
   - Generate security configuration and middleware

7. **TESTING PHASE**
   - Use api_tester_tool to generate comprehensive test suite
   - Create unit tests, integration tests, and security tests
   - Configure pytest with coverage reporting
   - Execute tests to validate API functionality

8. **DOCUMENTATION PHASE**
   - Use documentation_generator_tool to create comprehensive docs
   - Generate README with test badges and quick start guide
   - Create API reference documentation
   - Add deployment guides and examples
   - Generate HTML documentation portal

**QUALITY STANDARDS:**
- Always prioritize security (authentication, authorization, input validation)
- Ensure comprehensive test coverage (aim for >80%)
- Generate production-ready code with proper error handling
- Follow REST API best practices and OpenAPI standards
- Create clear, actionable documentation
- Handle edge cases and provide meaningful error messages

**ERROR HANDLING:**
- If any tool fails, analyze the error and suggest solutions
- Provide clear progress updates throughout the workflow
- Validate inputs and outputs between each phase
- Offer alternative approaches if initial strategy fails

**COMMUNICATION:**
- Provide clear progress updates at each phase
- Explain technical decisions and trade-offs
- Highlight security features and test results
- Offer deployment recommendations
- Present final deliverables in organized manner

You have access to specialized tools for each phase. Use them systematically to deliver a complete, production-ready API with full documentation and testing suite.

Remember: Your goal is to transform any codebase into a secure, well-tested, thoroughly documented REST API that's ready for production deployment."""

    async def run_workflow(self, github_url: str, output_directory: str = None, additional_instructions: str = "") -> Dict[str, Any]:
        """
        Execute the complete code-to-API workflow
        
        Args:
            github_url: GitHub repository URL to convert
            output_directory: Directory to save generated API (optional)
            additional_instructions: Additional user requirements
        
        Returns:
            Dictionary containing workflow results and generated artifacts
        """
        try:
            # Prepare the input for the agent
            workflow_input = f"""
Convert the following GitHub repository into a production-ready REST API:

Repository URL: {github_url}
Output Directory: {output_directory or "auto-generated"}
Additional Instructions: {additional_instructions or "Follow standard best practices"}

Execute the complete workflow:
1. Fetch code from repository
2. Analyze codebase for API opportunities
3. Design OpenAPI specification
4. Generate FastAPI application
5. Apply security enhancements
6. Create comprehensive test suite
7. Generate documentation with badges

Provide detailed progress updates and final summary of deliverables.
"""
            
            logger.info("Starting code-to-API workflow for: %s", github_url)
            
            # Execute the workflow using the agent with chat history
            result = await self.agent_with_chat_history.ainvoke(
                {"input": workflow_input},
                config={"configurable": {"session_id": f"workflow_{github_url.split('/')[-1]}"}}
            )
            
            # Parse and structure the results
            workflow_results = {
                "success": True,
                "repository_url": github_url,
                "output_directory": output_directory,
                "agent_response": result.get("output", ""),
                "intermediate_steps": result.get("intermediate_steps", []),
                "execution_summary": self._extract_execution_summary(result),
                "generated_artifacts": self._identify_generated_artifacts(result),
                "workflow_metadata": {
                    "total_steps": len(result.get("intermediate_steps", [])),
                    "execution_time": "completed",
                    "tools_used": self._extract_tools_used(result)
                }
            }
            
            logger.info("Workflow completed successfully")
            return workflow_results
            
        except Exception as e:
            logger.error("Workflow execution failed: %s", str(e))
            return {
                "success": False,
                "error": str(e),
                "repository_url": github_url,
                "output_directory": output_directory
            }
    
    def _extract_execution_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract execution summary from agent results"""
        try:
            intermediate_steps = result.get("intermediate_steps", [])
            
            summary = {
                "phases_completed": [],
                "total_tools_executed": len(intermediate_steps),
                "key_deliverables": [],
                "security_features": [],
                "test_results": {},
                "documentation_generated": False
            }
            
            # Analyze intermediate steps to extract key information
            for step in intermediate_steps:
                if len(step) >= 2:
                    action = step[0]
                    tool_name = action.tool if hasattr(action, 'tool') else "unknown"
                    
                    if "code_fetcher" in tool_name:
                        summary["phases_completed"].append("Code Fetching")
                    elif "code_analyzer" in tool_name:
                        summary["phases_completed"].append("Code Analysis")
                    elif "api_designer" in tool_name:
                        summary["phases_completed"].append("API Design")
                    elif "api_generator" in tool_name:
                        summary["phases_completed"].append("API Generation")
                    elif "security_enforcer" in tool_name:
                        summary["phases_completed"].append("Security Enhancement")
                        summary["security_features"].extend([
                            "JWT Authentication", "Rate Limiting", "CORS Protection", 
                            "Security Headers", "Input Validation"
                        ])
                    elif "api_tester" in tool_name:
                        summary["phases_completed"].append("Test Generation")
                        # Try to extract test results from tool output
                        tool_output = step[1] if len(step) > 1 else ""
                        if isinstance(tool_output, str) and "total" in tool_output.lower():
                            summary["test_results"] = {"status": "generated"}
                    elif "documentation_generator" in tool_name:
                        summary["phases_completed"].append("Documentation Generation")
                        summary["documentation_generated"] = True
            
            return summary
            
        except Exception as e:
            logger.warning("Failed to extract execution summary: %s", str(e))
            return {"error": "Failed to parse execution summary"}
    
    def _identify_generated_artifacts(self, result: Dict[str, Any]) -> List[str]:
        """Identify generated artifacts from the workflow"""
        artifacts = []
        
        try:
            # Look for file paths and artifacts mentioned in the response
            response = result.get("output", "")
            
            if "main.py" in response:
                artifacts.append("FastAPI Application (main.py)")
            if "models.py" in response:
                artifacts.append("Data Models (models.py)")
            if "auth.py" in response:
                artifacts.append("Authentication Module (auth.py)")
            if "test" in response.lower():
                artifacts.append("Test Suite")
            if "readme" in response.lower():
                artifacts.append("README Documentation")
            if "openapi" in response.lower() or "swagger" in response.lower():
                artifacts.append("OpenAPI Specification")
            if "requirements.txt" in response:
                artifacts.append("Dependencies (requirements.txt)")
            if "docker" in response.lower():
                artifacts.append("Docker Configuration")
            
            # If no specific artifacts identified, provide generic list
            if not artifacts:
                artifacts = [
                    "Generated API Application",
                    "Documentation",
                    "Test Suite",
                    "Configuration Files"
                ]
                
        except Exception as e:
            logger.warning("Failed to identify artifacts: %s", str(e))
            artifacts = ["Generated API Components"]
        
        return artifacts
    
    def _extract_tools_used(self, result: Dict[str, Any]) -> List[str]:
        """Extract list of tools used during execution"""
        tools_used = []
        
        try:
            intermediate_steps = result.get("intermediate_steps", [])
            
            for step in intermediate_steps:
                if len(step) >= 1:
                    action = step[0]
                    tool_name = action.tool if hasattr(action, 'tool') else "unknown"
                    if tool_name not in tools_used:
                        tools_used.append(tool_name)
        
        except Exception as e:
            logger.warning("Failed to extract tools used: %s", str(e))
        
        return tools_used
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        return [tool.name for tool in self.tools]
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions of available tools"""
        return {tool.name: tool.description for tool in self.tools}
    
    async def run_single_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Run a single tool directly (useful for testing or partial workflows)
        
        Args:
            tool_name: Name of the tool to run
            **kwargs: Arguments for the tool
        
        Returns:
            Tool execution results
        """
        try:
            # Find the tool
            tool = None
            for t in self.tools:
                if t.name == tool_name:
                    tool = t
                    break
            
            if not tool:
                return {
                    "success": False,
                    "error": f"Tool '{tool_name}' not found",
                    "available_tools": self.get_available_tools()
                }
            
            # Execute the tool
            result = tool.run(kwargs)
            
            return {
                "success": True,
                "tool_name": tool_name,
                "result": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "tool_name": tool_name,
                "error": str(e)
            }
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status and agent information"""
        return {
            "agent_initialized": True,
            "available_tools": len(self.tools),
            "tool_list": self.get_available_tools(),
            "llm_model": "openai/gpt-oss-120b",
            "memory_enabled": True,
            "max_iterations": 10,
            "max_execution_time": 1800
        }
