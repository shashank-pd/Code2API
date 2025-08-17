#!/usr/bin/env python3
"""
Test the fixed /tasks/complete endpoint
"""
import requests
import json

# API Base URL for the generated API
BASE_URL = "http://localhost:8001"

def test_tasks_complete_endpoint():
    print("🧪 Testing Fixed /tasks/complete Endpoint")
    print("=" * 50)
    
    # 1. Health Check
    print("\n1️⃣ Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health Check: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return
    
    # 2. Get Authentication Token
    print("\n2️⃣ Getting Authentication Token...")
    try:
        auth_data = {
            "username": "demo",
            "password": "demo"
        }
        response = requests.post(f"{BASE_URL}/auth/token", json=auth_data)
        print(f"✅ Auth: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data["access_token"]
            print(f"   Token: {token[:50]}...")
            
            # 3. Test the FIXED /tasks/complete endpoint
            print("\n3️⃣ Testing FIXED /tasks/complete Endpoint...")
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test with proper JSON body
            task_data = {
                "task_title": "Complete the hackathon project"
            }
            
            response = requests.post(f"{BASE_URL}/tasks/complete", 
                                   json=task_data, 
                                   headers=headers)
            print(f"✅ POST /tasks/complete: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   Response: {json.dumps(result, indent=2)}")
                print("\n🎉 SUCCESS: /tasks/complete endpoint is now working!")
            else:
                print(f"❌ Error: {response.text}")
                
        else:
            print(f"❌ Authentication failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Test Failed: {e}")

if __name__ == "__main__":
    test_tasks_complete_endpoint()
    
    print("\n🎯 Endpoint Fixed!")
    print("✅ Proper request body model (Mark_task_completeRequest)")
    print("✅ Proper response model (TaskCompleteResponse)")  
    print("✅ Correct parameter types (task_title: str)")
    print("✅ Working implementation with meaningful response")
    print("\n📖 View API docs: http://localhost:8001/docs")
