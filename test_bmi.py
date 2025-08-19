#!/usr/bin/env python3
"""
Test script to verify BMI Calculator repository analysis functionality
"""
import requests
import json
import sys

def test_analyze_bmi_repo():
    """Test the analyze-repo endpoint with BMI Calculator repository"""
    
    # API endpoint
    url = "http://localhost:8000/analyze-repo"
    
    # Test data for BMI Calculator repository
    test_repo = {
        "repo_url": "https://github.com/Raveesh1505/BMI-Calculator",
        "branch": "main",
        "include_patterns": [".py"],
        "max_files": 15
    }
    
    print("🔍 Testing BMI Calculator repository analysis...")
    print(f"Repository: {test_repo['repo_url']}")
    print(f"Branch: {test_repo['branch']}")
    print("-" * 50)
    
    try:
        # Make request
        response = requests.post(url, json=test_repo, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS! BMI Calculator repository analyzed successfully")
            print(f"📊 Analysis Summary:")
            
            analysis = result.get('analysis', {})
            
            # Repository info
            if 'repository_info' in analysis:
                repo_info = analysis['repository_info']
                print(f"  - Repository: {repo_info.get('name', 'Unknown')}")
                print(f"  - Owner: {repo_info.get('owner', {}).get('login', 'Unknown')}")
                print(f"  - Language: {repo_info.get('language', 'Unknown')}")
                print(f"  - Description: {repo_info.get('description', 'No description')}")
            
            # Statistics
            if 'statistics' in analysis:
                stats = analysis['statistics']
                print(f"  - Files analyzed: {stats.get('total_files', 0)}")
                print(f"  - Total lines: {stats.get('total_lines', 0):,}")
                print(f"  - Languages: {list(stats.get('languages', {}).keys())}")
            
            # API endpoints
            endpoints = analysis.get('api_endpoints', [])
            print(f"  - API endpoints generated: {len(endpoints)}")
            
            # Show BMI-specific endpoints
            bmi_endpoints = [ep for ep in endpoints if 'bmi' in ep.get('function_name', '').lower()]
            if bmi_endpoints:
                print(f"  - BMI-specific endpoints: {len(bmi_endpoints)}")
                for i, endpoint in enumerate(bmi_endpoints, 1):
                    print(f"    {i}. {endpoint.get('http_method', 'POST')} {endpoint.get('endpoint_path', 'Unknown')}")
                    print(f"       Function: {endpoint.get('function_name', 'Unknown')}")
                    print(f"       Description: {endpoint.get('description', 'No description')[:80]}...")
                    
                    # Show parameters for BMI endpoints
                    params = endpoint.get('input_validation', {}).get('required_params', [])
                    if params:
                        param_names = [p.get('name') for p in params]
                        print(f"       Parameters: {', '.join(param_names)}")
            
            # Show all endpoints
            print(f"\n  📋 All Generated Endpoints:")
            for i, endpoint in enumerate(endpoints, 1):
                print(f"    {i}. {endpoint.get('http_method', 'POST')} {endpoint.get('endpoint_path', 'Unknown')}")
                print(f"       {endpoint.get('description', 'No description')[:100]}...")
            
            # Generated API path
            if 'generated_api_path' in result:
                api_path = result['generated_api_path']
                print(f"\n  - Generated API path: {api_path}")
                
                # Test if the generated API can run
                print(f"\n🧪 Testing generated BMI API...")
                test_generated_bmi_api(api_path)
            
            print(f"\n🎉 BMI Calculator analysis completed successfully!")
            
        else:
            print(f"❌ ERROR: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Details: {error_detail.get('detail', 'Unknown error')}")
            except:
                print(f"Response: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to backend server")
        print("Make sure the backend is running on http://localhost:8000")
        
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out")
        print("Repository analysis took too long (>60 seconds)")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

def test_generated_bmi_api(api_path):
    """Test the generated BMI API endpoints"""
    import os
    import subprocess
    import time
    
    try:
        # Change to the generated API directory
        main_py_path = os.path.join(api_path, "main.py")
        
        if os.path.exists(main_py_path):
            print(f"  ✅ Generated main.py exists at: {main_py_path}")
            
            # Check if models.py exists
            models_py_path = os.path.join(api_path, "models.py")
            if os.path.exists(models_py_path):
                print(f"  ✅ Generated models.py exists")
                
                # Try to import and check syntax
                print(f"  🔍 Checking Python syntax...")
                result = subprocess.run([
                    "python", "-m", "py_compile", main_py_path
                ], capture_output=True, text=True, cwd=api_path)
                
                if result.returncode == 0:
                    print(f"  ✅ Generated API has valid Python syntax")
                    
                    # Check models file too
                    result = subprocess.run([
                        "python", "-m", "py_compile", models_py_path
                    ], capture_output=True, text=True, cwd=api_path)
                    
                    if result.returncode == 0:
                        print(f"  ✅ Generated models have valid Python syntax")
                        print(f"  🎯 BMI API is ready to run!")
                        print(f"  📝 To test manually:")
                        print(f"     cd \"{api_path}\"")
                        print(f"     python main.py")
                    else:
                        print(f"  ❌ Models syntax error: {result.stderr}")
                else:
                    print(f"  ❌ Main file syntax error: {result.stderr}")
            else:
                print(f"  ❌ models.py not found")
        else:
            print(f"  ❌ main.py not found at expected location")
            
    except Exception as e:
        print(f"  ❌ Error testing generated API: {str(e)}")

if __name__ == "__main__":
    test_analyze_bmi_repo()
