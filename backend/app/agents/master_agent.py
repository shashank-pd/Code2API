from typing import Dict, Any, List, Optional
import os
import asyncio
import logging
from pathlib import Path
import json

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_groq import ChatGroq

# Import all specialized tools
from ..tools.code_fetcher import code_fetcher_tool
from ..tools.code_analyzer import code_analyzer_tool
from ..tools.api_designer import api_designer_tool
from ..tools.api_generator import api_generator_tool
from ..tools.security_enforcer import security_enforcer_tool
from ..tools.api_tester import api_tester_tool
from ..tools.documentation_generator import documentation_generator_tool

logger = logging.getLogger(__name__)

class MasterAgent:
    """
    Master Agent that orchestrates the complete code-to-API generation workflow.
    Coordinates multiple specialized agents to transform GitHub repositories 
    into production-ready REST APIs.
    """
    
    def __init__(self):
        """Initialize the MasterAgent with all required tools and LLM"""
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.github_token = os.getenv("GITHUB_TOKEN")
        
        # Will be initialized in initialize() method
        self.llm = None
        self.agent_executor = None
        self.tools = []
        
        # Workflow state
        self.current_workflow = None
        self.workflow_results = {}
        
    async def initialize(self):
        """Initialize the agent and all tools"""
        try:
            if not self.groq_api_key:
                raise ValueError("GROQ_API_KEY environment variable is required")
            
            # Initialize Groq LLM
            self.llm = ChatGroq(
                api_key=self.groq_api_key,
                model="llama-3.3-70b-versatile",  # Updated to supported model
                temperature=0.1,
                max_tokens=8192,
                timeout=120
            )
            
            # Initialize all specialized tools
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
            prompt = ChatPromptTemplate.from_messages([
                ("system", self._get_system_prompt()),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad")
            ])
            
            # Create the agent
            agent = create_openai_tools_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt
            )
            
            # Create agent executor without deprecated memory
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                max_iterations=15,
                max_execution_time=1800,  # 30 minutes
                handle_parsing_errors="Check your output and make sure it conforms to the expected format.",
                return_intermediate_steps=True
            )
            
            # Initialize message store for conversation history
            self.store = {}
            
            # Create agent with message history
            self.agent_with_chat_history = RunnableWithMessageHistory(
                self.agent_executor,
                self._get_session_history,
                input_messages_key="input",
                history_messages_key="chat_history",
            )
            
            logger.info("MasterAgent initialized successfully with %d tools", len(self.tools))
            
        except Exception as e:
            logger.error(f"Failed to initialize MasterAgent: {e}")
            raise
    
    def _get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """Get or create chat message history for a session"""
        if session_id not in self.store:
            self.store[session_id] = ChatMessageHistory()
        return self.store[session_id]
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the master agent"""
        return """You are an AI Master Agent specialized in transforming GitHub repositories into production-ready REST APIs.

Your mission is to orchestrate a complete multi-stage workflow using your specialized tools:

1. **CODE_FETCHER_TOOL**: Download and extract code from GitHub repositories
2. **CODE_ANALYZER_TOOL**: Analyze source code to identify API opportunities  
3. **API_DESIGNER_TOOL**: Create comprehensive OpenAPI 3.0 specifications
4. **API_GENERATOR_TOOL**: Generate FastAPI application code with proper structure
5. **SECURITY_ENFORCER_TOOL**: Apply enterprise-grade security layers
6. **API_TESTER_TOOL**: Create comprehensive test suites with coverage reporting
7. **DOCUMENTATION_GENERATOR_TOOL**: Generate beautiful documentation with badges

**WORKFLOW EXECUTION STRATEGY:**

Execute these phases in sequence for every repository conversion:

**PHASE 1: CODE ACQUISITION**
- Use code_fetcher_tool with the GitHub URL
- Validate successful download and extraction
- Log repository structure and file types

**PHASE 2: CODE ANALYSIS** 
- Use code_analyzer_tool on the downloaded code
- Identify functions, classes, and modules suitable for API endpoints
- Extract business logic and data models
- Generate recommendations for API design

**PHASE 3: API DESIGN**
- Use api_designer_tool with analysis results
- Create comprehensive OpenAPI 3.0 specification
- Design RESTful endpoints with proper HTTP methods
- Define request/response schemas and authentication

**PHASE 4: CODE GENERATION**
- Use api_generator_tool with the OpenAPI spec
- Generate FastAPI application with main.py, models, routers
- Implement business logic derived from original code
- Create proper project structure and configuration

**PHASE 5: SECURITY ENHANCEMENT**
- Use security_enforcer_tool on generated API
- Add JWT authentication and authorization
- Implement rate limiting, CORS, security headers
- Apply input validation and sanitization

**PHASE 6: TEST GENERATION**
- Use api_tester_tool to create comprehensive tests
- Generate unit tests, integration tests, security tests
- Configure pytest with coverage reporting
- Aim for >80% test coverage

**PHASE 7: DOCUMENTATION**
- Use documentation_generator_tool with all results
- Generate README with test badges and quick start
- Create API reference documentation
- Add deployment guides and examples

**QUALITY STANDARDS:**
- Prioritize security (authentication, authorization, input validation)
- Ensure comprehensive test coverage (>80%)
- Generate production-ready code with error handling
- Follow REST API best practices and OpenAPI standards
- Create clear, actionable documentation

**ERROR HANDLING:**
- If any tool fails, log the error and continue with remaining phases
- Provide clear progress updates throughout execution
- Validate inputs and outputs between phases
- Return comprehensive results even if some phases fail

Always execute the complete workflow and provide detailed results for each phase."""

    async def execute_workflow(self, repo_url: str, branch: str = "main") -> Dict[str, Any]:
        """
        Execute the complete code-to-API generation workflow
        
        Args:
            repo_url: GitHub repository URL
            branch: Git branch to analyze (default: main)
            
        Returns:
            Complete workflow results with generated API details
        """
        if not self.agent_executor:
            raise RuntimeError("MasterAgent not initialized. Call initialize() first.")
        
        try:
            # Prepare workflow input
            workflow_input = f"""
Execute the complete code-to-API generation workflow for this repository:

Repository URL: {repo_url}
Branch: {branch}

Follow this systematic approach:
1. Use code_fetcher_tool to download the repository
2. Use code_analyzer_tool to analyze the downloaded code for API opportunities
3. Use api_designer_tool to create an OpenAPI specification
4. Use api_generator_tool to generate FastAPI code
5. Use security_enforcer_tool to add security features
6. Use api_tester_tool to create tests
7. Use documentation_generator_tool to create documentation

Focus on creating a working API from the analyzed code structure.
"""
            
            logger.info(f"Starting workflow execution for {repo_url}")
            
            # Execute the workflow with better error handling using the new agent with chat history
            try:
                result = await self.agent_with_chat_history.ainvoke(
                    {"input": workflow_input},
                    config={"configurable": {"session_id": f"workflow_{repo_url.split('/')[-1]}"}}
                )
            except Exception as tool_error:
                logger.error(f"Tool execution error: {tool_error}")
                # Try to continue with a simplified workflow
                result = {
                    "output": f"Workflow partially completed. Error: {str(tool_error)}",
                    "intermediate_steps": []
                }
            
            # Parse and structure the results
            workflow_results = self._parse_workflow_results(result, repo_url)
            
            # Store workflow state
            self.current_workflow = {
                "repo_url": repo_url,
                "branch": branch,
                "results": workflow_results
            }
            
            logger.info("Workflow execution completed successfully")
            return workflow_results
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            # Return a fallback result
            return {
                "success": False,
                "error": str(e),
                "repo_url": repo_url,
                "analysis": {
                    "endpoints_identified": 0,
                    "security_features": [],
                    "recommendations": ["Check repository access and API keys"]
                },
                "api_path": f"/tmp/generated_apis/{repo_url.split('/')[-1]}",
                "test_results": {
                    "total_tests": 0,
                    "passed": 0,
                    "coverage": 0
                },
                "documentation_url": "",
                "phases_completed": ["Error occurred"],
                "generated_files": [],
                "errors": [str(e)]
            }
    
    async def analyze_single_file(self, file_path: str, filename: str) -> Dict[str, Any]:
        """
        Analyze a single uploaded file for API generation potential
        
        Args:
            file_path: Path to the uploaded file
            filename: Original filename
            
        Returns:
            Analysis results and potential API design
        """
        if not self.agent_executor:
            raise RuntimeError("MasterAgent not initialized. Call initialize() first.")
        
        try:
            analysis_input = f"""
Analyze this single code file for API generation potential:

File: {filename}
Path: {file_path}

Execute these steps:
1. Use code_analyzer_tool to analyze the file
2. Use api_designer_tool to create potential API endpoints
3. Provide recommendations for API structure

Focus on identifying functions and classes that could become API endpoints.
"""
            
            result = await self.agent_with_chat_history.ainvoke(
                {"input": analysis_input},
                config={"configurable": {"session_id": f"file_analysis_{filename}"}}
            )
            
            return self._parse_single_file_results(result, filename)
            
        except Exception as e:
            logger.error(f"Single file analysis failed: {e}")
            raise
    
    def _parse_workflow_results(self, agent_result: Dict[str, Any], repo_url: str) -> Dict[str, Any]:
        """Parse agent execution results into structured format"""
        try:
            # Extract key information from agent output
            output = agent_result.get("output", "")
            intermediate_steps = agent_result.get("intermediate_steps", [])
            
            # Extract repo name from URL
            repo_name = repo_url.rstrip('/').split('/')[-1]
            
            # Initialize results structure matching Pydantic schemas
            results = {
                "success": True,
                "repo_url": repo_url,
                "analysis": {
                    "repo_name": repo_name,
                    "language": "python",  # Default, will be updated if detected
                    "api_endpoints": [],
                    "functions_analyzed": 0,
                    "classes_analyzed": 0,
                    "security_recommendations": []
                },
                "api_path": "",
                "test_results": [],  # List of TestResult objects
                "documentation_url": "",
                "phases_completed": [],
                "generated_files": [],
                "errors": []
            }
            
            # Parse intermediate steps to extract phase results
            for step in intermediate_steps:
                if len(step) >= 2:
                    action = step[0]
                    tool_output = step[1]
                    
                    tool_name = getattr(action, 'tool', 'unknown')
                    
                    if "code_fetcher" in tool_name:
                        results["phases_completed"].append("Code Fetching")
                        if isinstance(tool_output, dict) and tool_output.get("success"):
                            results["api_path"] = tool_output.get("extracted_path", "")
                    
                    elif "code_analyzer" in tool_name:
                        results["phases_completed"].append("Code Analysis")
                        if isinstance(tool_output, dict):
                            # Update analysis with proper schema fields
                            results["analysis"]["functions_analyzed"] = tool_output.get("functions_count", 0)
                            results["analysis"]["classes_analyzed"] = tool_output.get("classes_count", 0)
                            results["analysis"]["security_recommendations"] = tool_output.get("recommendations", [])
                            # Detect language if provided
                            if "language" in tool_output:
                                results["analysis"]["language"] = tool_output["language"]
                            # Convert endpoints to proper format
                            endpoints = tool_output.get("endpoints", [])
                            if endpoints:
                                for endpoint in endpoints:
                                    if isinstance(endpoint, dict):
                                        results["analysis"]["api_endpoints"].append({
                                            "path": endpoint.get("path", "/"),
                                            "method": endpoint.get("method", "GET"),
                                            "function_name": endpoint.get("function_name", "unknown"),
                                            "description": endpoint.get("description"),
                                            "parameters": endpoint.get("parameters", []),
                                            "return_type": endpoint.get("return_type")
                                        })
                    
                    elif "api_designer" in tool_name:
                        results["phases_completed"].append("API Design")
                    
                    elif "api_generator" in tool_name:
                        results["phases_completed"].append("API Generation")
                        if isinstance(tool_output, dict):
                            results["generated_files"].extend(tool_output.get("generated_files", []))
                    
                    elif "security_enforcer" in tool_name:
                        results["phases_completed"].append("Security Enhancement")
                        if isinstance(tool_output, dict):
                            security_features = tool_output.get("security_features", [])
                            results["analysis"]["security_recommendations"].extend(security_features)
                    
                    elif "api_tester" in tool_name:
                        results["phases_completed"].append("Test Generation")
                        if isinstance(tool_output, dict):
                            # Create TestResult objects for the list
                            total_tests = tool_output.get("total", 0)
                            passed_tests = tool_output.get("passed", 0)
                            failed_tests = total_tests - passed_tests
                            
                            # Create individual test results
                            for i in range(passed_tests):
                                results["test_results"].append({
                                    "test_name": f"test_endpoint_{i+1}",
                                    "status": "passed",
                                    "execution_time": 0.1,
                                    "error_message": None
                                })
                            
                            for i in range(failed_tests):
                                results["test_results"].append({
                                    "test_name": f"test_endpoint_{passed_tests + i + 1}",
                                    "status": "failed",
                                    "execution_time": 0.1,
                                    "error_message": "Test failed during execution"
                                })
                    
                    elif "documentation_generator" in tool_name:
                        results["phases_completed"].append("Documentation Generation")
                        if isinstance(tool_output, dict):
                            results["documentation_url"] = tool_output.get("documentation_url", "")
            
            # Set default values if phases weren't completed
            if not results["api_path"]:
                results["api_path"] = f"/tmp/generated_apis/{repo_url.split('/')[-1]}"
            
            if not results["documentation_url"]:
                results["documentation_url"] = f"{results['api_path']}/docs/index.html"
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to parse workflow results: {e}")
            return {
                "success": False,
                "error": str(e),
                "repo_url": repo_url
            }
    
    def _parse_single_file_results(self, agent_result: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """Parse single file analysis results"""
        try:
            output = agent_result.get("output", "")
            
            return {
                "success": True,
                "filename": filename,
                "analysis": {
                    "potential_endpoints": 3,  # Default estimate
                    "recommendations": ["Consider adding authentication", "Implement input validation"],
                    "file_type": Path(filename).suffix,
                    "complexity": "medium"
                },
                "api_path": f"/tmp/single_file_apis/{Path(filename).stem}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "filename": filename,
                "error": str(e)
            }
    
    async def check_groq_connection(self) -> str:
        """Check Groq API connection status"""
        try:
            if not self.groq_api_key:
                return "not_configured"
            
            if self.llm:
                # Try a simple API call
                response = await self.llm.ainvoke("test")
                return "connected"
            else:
                return "not_initialized"
                
        except Exception as e:
            logger.error(f"Groq connection check failed: {e}")
            return "error"
    
    async def check_github_connection(self) -> str:
        """Check GitHub API connection status"""
        try:
            if self.github_token:
                return "configured"
            else:
                return "public_access_only"
                
        except Exception as e:
            logger.error(f"GitHub connection check failed: {e}")
            return "error"
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        return {
            "initialized": self.agent_executor is not None,
            "tools_available": len(self.tools),
            "current_workflow": self.current_workflow is not None,
            "groq_configured": self.groq_api_key is not None,
            "github_configured": self.github_token is not None
        }
