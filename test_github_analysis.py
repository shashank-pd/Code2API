#!/usr/bin/env python3
"""
Test script to verify GitHub repository analysis functionality
"""
import requests
import json
import sys

def test_analyze_repo():
    """Test the analyze-repo endpoint with fallback mechanisms"""
    
    # API endpoint
    url = "http://localhost:8000/analyze-repo"
    
    # Test data
    test_repo = {
        "repo_url": "https://github.com/inforkgodara/python-calculator",
        "branch": "main",
        "include_patterns": [".py"],
        "max_files": 10
    }
    
    print("🔍 Testing GitHub repository analysis...")
    print(f"Repository: {test_repo['repo_url']}")
    print(f"Branch: {test_repo['branch']}")
    print("-" * 50)
    
    try:
        # Make request
        response = requests.post(url, json=test_repo, timeout=60)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS! Repository analyzed successfully")
            print(f"📊 Analysis Summary:")
            
            analysis = result.get('analysis', {})
            
            # Repository info
            if 'repository_info' in analysis:
                repo_info = analysis['repository_info']
                print(f"  - Repository: {repo_info.get('name', 'Unknown')}")
                print(f"  - Owner: {repo_info.get('owner', {}).get('login', 'Unknown')}")
                print(f"  - Language: {repo_info.get('language', 'Unknown')}")
            
            # Statistics
            if 'statistics' in analysis:
                stats = analysis['statistics']
                print(f"  - Files analyzed: {stats.get('total_files', 0)}")
                print(f"  - Total lines: {stats.get('total_lines', 0):,}")
                print(f"  - Languages: {list(stats.get('languages', {}).keys())}")
            
            # API endpoints
            endpoints = analysis.get('api_endpoints', [])
            print(f"  - API endpoints generated: {len(endpoints)}")
            
            for i, endpoint in enumerate(endpoints[:3], 1):  # Show first 3
                print(f"    {i}. {endpoint.get('http_method', 'POST')} {endpoint.get('endpoint_path', 'Unknown')}")
                print(f"       Description: {endpoint.get('description', 'No description')[:80]}...")
            
            # Generated API path
            if 'generated_api_path' in result:
                print(f"  - Generated API path: {result['generated_api_path']}")
            
            print(f"\n🎉 Analysis completed successfully!")
            
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

if __name__ == "__main__":
    test_analyze_repo()
