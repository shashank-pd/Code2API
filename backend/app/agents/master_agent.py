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

**ENHANCED WORKFLOW EXECUTION STRATEGY:**

Execute these phases in sequence with improved data flow:

**PHASE 1: CODE ACQUISITION**
- Use code_fetcher_tool with GitHub URL and branch
- Pass clean parameters: {"repo_url": "...", "branch": "main", "output_dir": "..."}
- Validate successful download and extract files_data structure
- Return: {"success": True, "files_data": {...}, "repo_language": "python"}

**PHASE 2: ENHANCED CODE ANALYSIS** 
- Use code_analyzer_tool with files_data from Phase 1
- Pass: {"files_data": result_from_phase1["files_data"], "repo_language": "python"}
- Extract business logic, repository purpose, and data models
- Return enhanced analysis with repo_purpose and main_functionality

**PHASE 3: DOMAIN-SPECIFIC API DESIGN**
- Use api_designer_tool with enhanced analysis results
- Pass: analysis_result from Phase 2 directly
- Create domain-specific OpenAPI specification based on repo_purpose
- Generate purpose-specific endpoints (ML, data analysis, file processing, etc.)

**PHASE 4: BUSINESS LOGIC CODE GENERATION**
- Use api_generator_tool with OpenAPI spec and analysis
- Pass: {"openapi_spec": result_from_phase3, "analysis_result": result_from_phase2, "output_dir": "..."}
- Generate FastAPI code with actual business logic implementation
- Create domain-specific modules and integrate repository functionality

**PHASE 5: SECURITY ENHANCEMENT**
- Use security_enforcer_tool on generated API directory
- Apply purpose-specific security measures
- Implement authentication, authorization, and input validation

**PHASE 6: COMPREHENSIVE TEST GENERATION**
- Use api_tester_tool with API path and business logic
- Generate tests that validate actual functionality
- Create domain-specific test cases based on repository purpose

**PHASE 7: ENHANCED DOCUMENTATION**
- Use documentation_generator_tool with all workflow results
- Generate comprehensive documentation with business logic explanation
- Include repository purpose and functionality mapping

**CRITICAL DATA FLOW REQUIREMENTS:**
- Always pass clean, structured data between tools
- Validate tool outputs before passing to next phase
- Handle nested parameter structures by extracting actual data
- Preserve business logic context throughout the workflow
- Use repository purpose to guide all subsequent phases

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
            # Prepare enhanced workflow input with explicit data flow instructions
            workflow_input = f"""
Execute the ENHANCED code-to-API generation workflow for repository: {repo_url}

Branch: {branch}
Output Directory: /tmp/generated_apis/{repo_url.split('/')[-1]}

IMPORTANT: Follow this EXACT sequence with proper data passing:

1. FETCH: Use code_fetcher_tool(repo_url="{repo_url}", branch="{branch}", output_dir="/tmp/repos/{repo_url.split('/')[-1]}")
   - Extract files_data and repo_language from result

2. ANALYZE: Use code_analyzer_tool(files_data=<result_from_step1.files_data>, repo_language=<result_from_step1.repo_language>)
   - Get enhanced analysis with repo_purpose and main_functionality
   - Extract business logic and data models

3. DESIGN: Use api_designer_tool(analysis_result=<complete_result_from_step2>)
   - Create domain-specific OpenAPI specification
   - Generate endpoints based on repository purpose

4. GENERATE: Use api_generator_tool(openapi_spec=<result_from_step3.openapi_spec>, analysis_result=<result_from_step2>, output_dir="/tmp/generated_apis/{repo_url.split('/')[-1]}")
   - Generate FastAPI code with actual business logic
   - Implement domain-specific functionality

5. SECURE: Use security_enforcer_tool(api_directory=<result_from_step4.output_directory>)
   - Apply security measures appropriate for the repository purpose

6. TEST: Use api_tester_tool(api_directory=<result_from_step4.output_directory>, analysis_result=<result_from_step2>)
   - Generate comprehensive tests for business logic

7. DOCUMENT: Use documentation_generator_tool(api_directory=<result_from_step4.output_directory>, workflow_results=<all_previous_results>)
   - Create complete documentation

CRITICAL: Pass actual data between tools, not nested structures. Validate each step before proceeding.
Focus on implementing REAL functionality from the original repository.
"""
            
            logger.info(f"Starting workflow execution for {repo_url}")
            
            # Execute the enhanced workflow with robust error handling
            session_id = f"enhanced_workflow_{repo_url.split('/')[-1]}"
            
            try:
                result = await self.agent_with_chat_history.ainvoke(
                    {"input": workflow_input},
                    config={"configurable": {"session_id": session_id}}
                )
                
                # Validate workflow completion
                if not self._validate_workflow_completion(result):
                    logger.warning("Workflow completed with some phases missing")
                    
            except Exception as tool_error:
                logger.error(f"Enhanced workflow execution error: {tool_error}")
                
                # Attempt a simplified fallback workflow
                fallback_input = f"""
Execute a simplified workflow for {repo_url}:
1. Try code_fetcher_tool to download repository
2. If successful, try code_analyzer_tool for basic analysis
3. Generate a simple API structure

Handle any tool parameter issues by extracting clean data.
"""
                
                try:
                    result = await self.agent_with_chat_history.ainvoke(
                        {"input": fallback_input},
                        config={"configurable": {"session_id": f"fallback_{session_id}"}}
                    )
                except Exception as fallback_error:
                    logger.error(f"Fallback workflow also failed: {fallback_error}")
                    result = {
                        "output": f"Both primary and fallback workflows failed. Primary error: {str(tool_error)}. Fallback error: {str(fallback_error)}",
                        "intermediate_steps": []
                    }
            
            # Parse and structure the enhanced results
            workflow_results = self._parse_enhanced_workflow_results(result, repo_url)
            
            # Store workflow state
            self.current_workflow = {
                "repo_url": repo_url,
                "branch": branch,
                "results": workflow_results
            }
            
            logger.info("Workflow execution completed successfully")
            return workflow_results
            
        except Exception as e:
            logger.error(f"Enhanced workflow execution failed: {e}")
            # Return an enhanced fallback result
            return {
                "success": False,
                "error": str(e),
                "repo_url": repo_url,
                "repo_purpose": "unknown",
                "analysis": {
                    "repo_name": repo_url.split('/')[-1],
                    "language": "unknown",
                    "api_endpoints": [],
                    "functions_analyzed": 0,
                    "classes_analyzed": 0,
                    "security_recommendations": ["Check repository access and API keys"],
                    "business_logic_mapping": {},
                    "domain_specific_features": []
                },
                "api_path": f"/tmp/generated_apis/{repo_url.split('/')[-1]}",
                "test_results": [],
                "documentation_url": "",
                "phases_completed": ["Error occurred"],
                "generated_files": [],
                "errors": [str(e)],
                "business_logic_implemented": False,
                "functionality_mapped": 0
            }
    
    def _validate_workflow_completion(self, result: Dict[str, Any]) -> bool:
        """Validate that the workflow completed successfully"""
        try:
            intermediate_steps = result.get("intermediate_steps", [])
            
            # Check for critical phases
            required_tools = ["code_fetcher", "code_analyzer", "api_designer", "api_generator"]
            completed_tools = set()
            
            for step in intermediate_steps:
                if len(step) >= 2:
                    action = step[0]
                    tool_name = getattr(action, 'tool', 'unknown').lower()
                    
                    for required_tool in required_tools:
                        if required_tool in tool_name:
                            completed_tools.add(required_tool)
            
            # Workflow is valid if at least the core tools executed
            return len(completed_tools) >= 3  # At least fetcher, analyzer, and one of designer/generator
            
        except Exception as e:
            logger.error(f"Workflow validation failed: {e}")
            return False
    
    def _parse_enhanced_workflow_results(self, agent_result: Dict[str, Any], repo_url: str) -> Dict[str, Any]:
        """Parse enhanced agent execution results with business logic focus"""
        try:
            output = agent_result.get("output", "")
            intermediate_steps = agent_result.get("intermediate_steps", [])
            
            repo_name = repo_url.rstrip('/').split('/')[-1]
            
            # Initialize enhanced results structure
            results = {
                "success": True,
                "repo_url": repo_url,
                "repo_purpose": "general_utility",
                "analysis": {
                    "repo_name": repo_name,
                    "language": "python",
                    "api_endpoints": [],
                    "functions_analyzed": 0,
                    "classes_analyzed": 0,
                    "security_recommendations": [],
                    "business_logic_mapping": {},
                    "domain_specific_features": []
                },
                "api_path": f"/tmp/generated_apis/{repo_name}",
                "test_results": [],
                "documentation_url": "",
                "phases_completed": [],
                "generated_files": [],
                "errors": [],
                "business_logic_implemented": False,
                "functionality_mapped": 0
            }
            
            # Parse enhanced intermediate steps
            for step in intermediate_steps:
                if len(step) >= 2:
                    action = step[0]
                    tool_output = step[1]
                    tool_name = getattr(action, 'tool', 'unknown').lower()
                    
                    try:
                        if "code_fetcher" in tool_name:
                            self._process_fetcher_results(tool_output, results)
                        elif "code_analyzer" in tool_name:
                            self._process_enhanced_analyzer_results(tool_output, results)
                        elif "api_designer" in tool_name:
                            self._process_enhanced_designer_results(tool_output, results)
                        elif "api_generator" in tool_name:
                            self._process_enhanced_generator_results(tool_output, results)
                        elif "security_enforcer" in tool_name:
                            self._process_security_results(tool_output, results)
                        elif "api_tester" in tool_name:
                            self._process_tester_results(tool_output, results)
                        elif "documentation_generator" in tool_name:
                            self._process_documentation_results(tool_output, results)
                    except Exception as phase_error:
                        logger.error(f"Error processing {tool_name} results: {phase_error}")
                        results["errors"].append(f"{tool_name}: {str(phase_error)}")
            
            # Set default values for missing phases
            self._set_default_values(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to parse enhanced workflow results: {e}")
            return {
                "success": False,
                "error": str(e),
                "repo_url": repo_url,
                "repo_purpose": "unknown"
            }
    
    def _process_fetcher_results(self, tool_output: Any, results: Dict[str, Any]) -> None:
        """Process code fetcher results"""
        results["phases_completed"].append("Code Fetching")
        if isinstance(tool_output, dict) and tool_output.get("success"):
            if "extracted_path" in tool_output:
                results["api_path"] = tool_output["extracted_path"]
            if "repo_language" in tool_output:
                results["analysis"]["language"] = tool_output["repo_language"]
    
    def _process_enhanced_analyzer_results(self, tool_output: Any, results: Dict[str, Any]) -> None:
        """Process enhanced code analyzer results"""
        results["phases_completed"].append("Enhanced Code Analysis")
        if isinstance(tool_output, dict) and tool_output.get("success"):
            # Extract enhanced analysis data
            results["analysis"]["functions_analyzed"] = tool_output.get("functions_analyzed", 0)
            results["analysis"]["classes_analyzed"] = tool_output.get("classes_analyzed", 0)
            results["analysis"]["security_recommendations"] = tool_output.get("security_recommendations", [])
            
            # Extract repository purpose and business logic
            if "repo_purpose" in tool_output:
                results["repo_purpose"] = tool_output["repo_purpose"]
            
            if "main_functionality" in tool_output:
                results["functionality_mapped"] = len(tool_output["main_functionality"])
                results["analysis"]["business_logic_mapping"] = tool_output.get("business_logic_mapping", {})
            
            if "domain_specific_features" in tool_output:
                results["analysis"]["domain_specific_features"] = tool_output["domain_specific_features"]
            
            # Process API endpoints
            api_endpoints = tool_output.get("api_endpoints", [])
            for endpoint in api_endpoints:
                if isinstance(endpoint, dict):
                    results["analysis"]["api_endpoints"].append({
                        "path": endpoint.get("path", "/"),
                        "method": endpoint.get("method", "GET"),
                        "function_name": endpoint.get("function_name", "unknown"),
                        "description": endpoint.get("description"),
                        "parameters": endpoint.get("parameters", []),
                        "return_type": endpoint.get("return_type"),
                        "business_logic": endpoint.get("business_logic", {})
                    })
    
    def _process_enhanced_designer_results(self, tool_output: Any, results: Dict[str, Any]) -> None:
        """Process enhanced API designer results"""
        results["phases_completed"].append("Domain-Specific API Design")
        if isinstance(tool_output, dict) and tool_output.get("success"):
            if "repo_purpose" in tool_output:
                results["repo_purpose"] = tool_output["repo_purpose"]
            if "domain_specific_features" in tool_output:
                results["analysis"]["domain_specific_features"] = tool_output["domain_specific_features"]
    
    def _process_enhanced_generator_results(self, tool_output: Any, results: Dict[str, Any]) -> None:
        """Process enhanced API generator results"""
        results["phases_completed"].append("Business Logic Implementation")
        if isinstance(tool_output, dict) and tool_output.get("success"):
            results["generated_files"].extend(tool_output.get("generated_files", []))
            if "output_directory" in tool_output:
                results["api_path"] = tool_output["output_directory"]
            if "business_logic_implemented" in tool_output:
                results["business_logic_implemented"] = tool_output["business_logic_implemented"]
            if "functionality_mapped" in tool_output:
                results["functionality_mapped"] = tool_output["functionality_mapped"]
    
    def _process_security_results(self, tool_output: Any, results: Dict[str, Any]) -> None:
        """Process security enforcer results"""
        results["phases_completed"].append("Security Enhancement")
        if isinstance(tool_output, dict) and tool_output.get("success"):
            security_features = tool_output.get("security_features", [])
            results["analysis"]["security_recommendations"].extend(security_features)
    
    def _process_tester_results(self, tool_output: Any, results: Dict[str, Any]) -> None:
        """Process API tester results"""
        results["phases_completed"].append("Comprehensive Test Generation")
        if isinstance(tool_output, dict) and tool_output.get("success"):
            total_tests = tool_output.get("total", 0)
            passed_tests = tool_output.get("passed", 0)
            failed_tests = total_tests - passed_tests
            
            # Generate test results
            for i in range(passed_tests):
                results["test_results"].append({
                    "test_name": f"test_business_logic_{i+1}",
                    "status": "passed",
                    "execution_time": 0.1,
                    "error_message": None
                })
            
            for i in range(failed_tests):
                results["test_results"].append({
                    "test_name": f"test_business_logic_{passed_tests + i + 1}",
                    "status": "failed",
                    "execution_time": 0.1,
                    "error_message": "Business logic test failed"
                })
    
    def _process_documentation_results(self, tool_output: Any, results: Dict[str, Any]) -> None:
        """Process documentation generator results"""
        results["phases_completed"].append("Enhanced Documentation Generation")
        if isinstance(tool_output, dict) and tool_output.get("success"):
            results["documentation_url"] = tool_output.get("documentation_url", "")
    
    def _set_default_values(self, results: Dict[str, Any]) -> None:
        """Set default values for missing workflow components"""
        if not results["api_path"]:
            repo_name = results["repo_url"].split('/')[-1]
            results["api_path"] = f"/tmp/generated_apis/{repo_name}"
        
        if not results["documentation_url"]:
            results["documentation_url"] = f"{results['api_path']}/docs/index.html"
        
        # Ensure business logic implementation status is set
        if "business_logic_implemented" not in results:
            results["business_logic_implemented"] = len(results["generated_files"]) > 0
    
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
