#!/usr/bin/env python3
"""
Test script for the generated Basic Task Manager API
"""
import requests
import json

# API Base URL
BASE_URL = "http://localhost:8000"

def test_api():
    print("🧪 Testing Generated Basic Task Manager API")
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
            
            # 3. Test the API endpoint
            print("\n3️⃣ Testing API Endpoint...")
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(f"{BASE_URL}/tasks", headers=headers)
            print(f"✅ GET /tasks: {response.status_code}")
            print(f"   Response: {json.dumps(response.json(), indent=2)}")
            
        else:
            print(f"❌ Authentication failed: {response.text}")
            
    except Exception as e:
        print(f"❌ API Test Failed: {e}")

def show_api_documentation():
    print("\n📚 API Documentation")
    print("=" * 50)
    print("🌐 Swagger UI: http://localhost:8000/docs")
    print("📖 ReDoc: http://localhost:8000/redoc")
    print("🔧 OpenAPI JSON: http://localhost:8000/openapi.json")

if __name__ == "__main__":
    test_api()
    show_api_documentation()
    
    print("\n🎯 Next Steps:")
    print("1. Start the API server: cd generated/thakare_om03_Basic_Task_Manager && python main.py")
    print("2. Open Swagger UI: http://localhost:8000/docs")
    print("3. Use the authentication endpoint to get a token")
    print("4. Test the /tasks endpoint with the token")
