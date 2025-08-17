# Code2API - Usage Examples

This document provides practical examples of using Code2API to convert source code into APIs.

## Quick Start Examples

### Example 1: Simple Python Function

**Input Code:**
```python
def calculate_discount(price, discount_percent):
    """Calculate discounted price"""
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount must be between 0 and 100")
    
    discount_amount = price * (discount_percent / 100)
    return price - discount_amount

def get_tax_rate(state):
    """Get tax rate for a state"""
    tax_rates = {
        "CA": 0.08,
        "NY": 0.07,
        "TX": 0.06
    }
    return tax_rates.get(state, 0.05)
```

**API Request:**
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def calculate_discount(price, discount_percent):\n    \"\"\"Calculate discounted price\"\"\"\n    if discount_percent < 0 or discount_percent > 100:\n        raise ValueError(\"Discount must be between 0 and 100\")\n    \n    discount_amount = price * (discount_percent / 100)\n    return price - discount_amount\n\ndef get_tax_rate(state):\n    \"\"\"Get tax rate for a state\"\"\"\n    tax_rates = {\n        \"CA\": 0.08,\n        \"NY\": 0.07,\n        \"TX\": 0.06\n    }\n    return tax_rates.get(state, 0.05)",
    "language": "python",
    "filename": "pricing.py"
  }'
```

**Generated API Endpoints:**
- `POST /calculate-discount` - Calculate discounted price
- `GET /get-tax-rate` - Get tax rate for a state

---

### Example 2: JavaScript Class

**Input Code:**
```javascript
class UserManager {
    constructor() {
        this.users = [];
    }

    /**
     * Create a new user
     */
    async createUser(username, email, password) {
        const user = {
            id: Date.now(),
            username,
            email,
            password: await this.hashPassword(password),
            createdAt: new Date()
        };
        this.users.push(user);
        return user;
    }

    /**
     * Get user by ID
     */
    getUserById(id) {
        return this.users.find(user => user.id === parseInt(id));
    }

    /**
     * Update user information
     */
    updateUser(id, updates) {
        const userIndex = this.users.findIndex(user => user.id === parseInt(id));
        if (userIndex === -1) {
            throw new Error('User not found');
        }
        
        this.users[userIndex] = { ...this.users[userIndex], ...updates };
        return this.users[userIndex];
    }

    async hashPassword(password) {
        // Simulate password hashing
        return btoa(password);
    }
}
```

**Generated API Endpoints:**
- `POST /users` - Create a new user
- `GET /users/{id}` - Get user by ID
- `PUT /users/{id}` - Update user information

---

## Repository Analysis Examples

### Example 3: Analyzing a GitHub Repository

**Request:**
```bash
curl -X POST "http://localhost:8000/analyze-repo" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/thakare-om03/Basic-Task-Manager",
    "branch": "main",
    "max_files": 30,
    "include_patterns": [".py", ".js", ".jsx"]
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "analysis": {
    "api_endpoints": [
      {
        "function_name": "create_task",
        "http_method": "POST",
        "endpoint_path": "/tasks",
        "description": "Create a new task",
        "needs_auth": true,
        "parameters": [
          {"name": "title", "type": "str"},
          {"name": "description", "type": "str"},
          {"name": "priority", "type": "str", "default": "medium"}
        ]
      },
      {
        "function_name": "get_tasks",
        "http_method": "GET",
        "endpoint_path": "/tasks",
        "description": "Get all tasks",
        "needs_auth": true,
        "parameters": [
          {"name": "status", "type": "str", "default": "all"},
          {"name": "limit", "type": "int", "default": "50"}
        ]
      }
    ],
    "repository_info": {
      "name": "Basic-Task-Manager",
      "description": "A simple task management system",
      "language": "Python",
      "stars": 15,
      "forks": 3
    },
    "security_recommendations": [
      "Implement proper authentication",
      "Validate user input",
      "Use HTTPS for all endpoints"
    ],
    "optimization_suggestions": [
      "Add database connection pooling",
      "Implement caching for task queries",
      "Add pagination for large result sets"
    ]
  },
  "generated_api_path": "/generated/thakare_om03_Basic_Task_Manager",
  "message": "Successfully analyzed 8 files from thakare-om03/Basic-Task-Manager"
}
```

---

### Example 4: File Upload Analysis

**Upload Multiple Files:**
```bash
# Create sample files
echo 'def add(a, b): return a + b' > math_utils.py
echo 'def subtract(a, b): return a - b' >> math_utils.py

echo 'class Calculator {
  multiply(a, b) { return a * b; }
  divide(a, b) { return a / b; }
}' > calculator.js

# Upload both files
curl -X POST "http://localhost:8000/upload" \
  -F "files=@math_utils.py" \
  -F "files=@calculator.js"
```

**Response:**
```json
{
  "results": [
    {
      "filename": "math_utils.py",
      "success": true,
      "analysis": {
        "api_endpoints": [
          {
            "function_name": "add",
            "http_method": "POST",
            "endpoint_path": "/add",
            "description": "Add two numbers"
          },
          {
            "function_name": "subtract",
            "http_method": "POST",
            "endpoint_path": "/subtract",
            "description": "Subtract two numbers"
          }
        ]
      },
      "api_path": "/generated/math_utils_py",
      "endpoints_count": 2
    },
    {
      "filename": "calculator.js",
      "success": true,
      "analysis": {
        "api_endpoints": [
          {
            "function_name": "Calculator_multiply",
            "http_method": "POST",
            "endpoint_path": "/multiply",
            "description": "Multiply two numbers"
          }
        ]
      },
      "api_path": "/generated/calculator_js",
      "endpoints_count": 1
    }
  ],
  "total_files": 2,
  "successful_analyses": 2
}
```

---

## Advanced Usage Examples

### Example 5: E-commerce API Generation

**Input Code - Order Management System:**
```python
from datetime import datetime
from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderManager:
    def __init__(self):
        self.orders = {}
        self.next_id = 1

    def create_order(self, customer_id, items, shipping_address):
        """Create a new order"""
        order = {
            "id": self.next_id,
            "customer_id": customer_id,
            "items": items,
            "shipping_address": shipping_address,
            "status": OrderStatus.PENDING.value,
            "created_at": datetime.now().isoformat(),
            "total_amount": self._calculate_total(items)
        }
        
        self.orders[self.next_id] = order
        self.next_id += 1
        return order

    def get_order(self, order_id):
        """Get order by ID"""
        return self.orders.get(order_id)

    def update_order_status(self, order_id, status):
        """Update order status"""
        if order_id in self.orders:
            self.orders[order_id]["status"] = status
            self.orders[order_id]["updated_at"] = datetime.now().isoformat()
            return self.orders[order_id]
        return None

    def get_customer_orders(self, customer_id):
        """Get all orders for a customer"""
        return [order for order in self.orders.values() 
                if order["customer_id"] == customer_id]

    def cancel_order(self, order_id):
        """Cancel an order"""
        if order_id in self.orders:
            order = self.orders[order_id]
            if order["status"] in [OrderStatus.PENDING.value, OrderStatus.CONFIRMED.value]:
                order["status"] = OrderStatus.CANCELLED.value
                order["cancelled_at"] = datetime.now().isoformat()
                return order
        return None

    def _calculate_total(self, items):
        """Calculate total order amount"""
        return sum(item.get("price", 0) * item.get("quantity", 1) for item in items)

def get_shipping_cost(weight, distance):
    """Calculate shipping cost"""
    base_rate = 5.00
    weight_rate = 0.50 * weight
    distance_rate = 0.10 * distance
    return base_rate + weight_rate + distance_rate

def apply_discount(amount, discount_code):
    """Apply discount code to amount"""
    discounts = {
        "SAVE10": 0.10,
        "SAVE20": 0.20,
        "NEWUSER": 0.15
    }
    
    discount_rate = discounts.get(discount_code, 0)
    return amount * (1 - discount_rate)
```

**Generated API Structure:**
```
POST /orders                    # Create new order
GET /orders/{order_id}          # Get order by ID
PUT /orders/{order_id}/status   # Update order status
GET /customers/{customer_id}/orders  # Get customer orders
DELETE /orders/{order_id}       # Cancel order
POST /shipping/calculate        # Calculate shipping cost
POST /discounts/apply          # Apply discount code
```

---

### Example 6: Microservice Pattern

**Input Code - User Service:**
```python
import asyncio
from typing import List, Optional

class UserService:
    def __init__(self, db_connection):
        self.db = db_connection

    async def create_user(self, username: str, email: str, password: str) -> dict:
        """Create a new user account"""
        # Hash password
        hashed_password = await self._hash_password(password)
        
        # Create user record
        user = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "is_active": True,
            "created_at": datetime.now()
        }
        
        # Save to database
        user_id = await self.db.insert("users", user)
        user["id"] = user_id
        
        # Remove password from response
        del user["password"]
        return user

    async def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """Authenticate user credentials"""
        user = await self.db.find_one("users", {"username": username})
        
        if user and await self._verify_password(password, user["password"]):
            del user["password"]
            return user
        
        return None

    async def get_user_profile(self, user_id: int) -> Optional[dict]:
        """Get user profile information"""
        user = await self.db.find_one("users", {"id": user_id})
        
        if user:
            del user["password"]
            return user
        
        return None

    async def update_user_profile(self, user_id: int, updates: dict) -> Optional[dict]:
        """Update user profile"""
        # Don't allow password updates through this method
        updates.pop("password", None)
        
        await self.db.update("users", {"id": user_id}, updates)
        return await self.get_user_profile(user_id)

    async def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user account"""
        result = await self.db.update("users", {"id": user_id}, {"is_active": False})
        return result.modified_count > 0

    async def _hash_password(self, password: str) -> str:
        """Hash password securely"""
        # Implementation would use bcrypt or similar
        return f"hashed_{password}"

    async def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return f"hashed_{password}" == hashed
```

**Generated Async API:**
```python
# Generated main.py will include:

@app.post("/users")
async def create_user(username: str, email: str, password: str):
    # Async endpoint implementation
    
@app.post("/auth/login")
async def authenticate_user(username: str, password: str):
    # Async authentication endpoint
    
@app.get("/users/{user_id}")
async def get_user_profile(user_id: int):
    # Async profile retrieval
```

---

## Testing Generated APIs

### Example 7: Testing the Generated API

After generating an API, you can test it:

**1. Download and Setup:**
```bash
# Download generated API
curl -X GET "http://localhost:8000/download/my_project" -o my_project.zip

# Extract and setup
unzip my_project.zip
cd my_project
pip install -r requirements.txt
```

**2. Start the API:**
```bash
python main.py
# or
uvicorn main:app --reload
```

**3. Test Endpoints:**
```bash
# Health check
curl http://localhost:8000/health

# Get authentication token
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo"}'

# Test your generated endpoints
curl -X GET "http://localhost:8000/your-endpoint"

# Test with authentication
curl -X POST "http://localhost:8000/protected-endpoint" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"param1": "value1"}'
```

---

## Error Handling Examples

### Example 8: Handling Common Errors

**Invalid Input:**
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "",
    "language": "invalid",
    "filename": ""
  }'
```

**Response:**
```json
{
  "error": "Validation Error",
  "detail": "Invalid input data",
  "errors": [
    {
      "loc": ["body", "code"],
      "msg": "Code cannot be empty",
      "type": "value_error"
    },
    {
      "loc": ["body", "language"],
      "msg": "Unsupported language: invalid. Supported: ['python', 'javascript', 'java', 'typescript']",
      "type": "value_error"
    }
  ],
  "timestamp": "2024-01-20 15:30:45"
}
```

**Rate Limiting:**
```bash
# After too many requests
curl -X POST "http://localhost:8000/analyze" -d '{...}'
```

**Response:**
```json
{
  "error": "Rate limit exceeded",
  "detail": "Maximum 100 requests per 60 seconds",
  "timestamp": "2024-01-20 15:31:00"
}
```

---

## Integration Examples

### Example 9: Python Client Integration

```python
import requests
import json

class Code2APIClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def analyze_code(self, code, language, filename):
        """Analyze source code"""
        response = self.session.post(
            f"{self.base_url}/analyze",
            json={
                "code": code,
                "language": language,
                "filename": filename
            }
        )
        response.raise_for_status()
        return response.json()

    def analyze_repository(self, repo_url, branch="main", max_files=50):
        """Analyze GitHub repository"""
        response = self.session.post(
            f"{self.base_url}/analyze-repo",
            json={
                "repo_url": repo_url,
                "branch": branch,
                "max_files": max_files
            }
        )
        response.raise_for_status()
        return response.json()

    def download_api(self, project_name, output_path):
        """Download generated API"""
        response = self.session.get(f"{self.base_url}/download/{project_name}")
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)

# Usage example
client = Code2APIClient()

# Analyze code
result = client.analyze_code(
    code="def hello(): return 'world'",
    language="python",
    filename="test.py"
)

print(f"Generated {len(result['analysis']['api_endpoints'])} endpoints")

# Download the generated API
project_name = result['generated_api_path'].split('/')[-1]
client.download_api(project_name, f"{project_name}.zip")
```

### Example 10: JavaScript/Node.js Integration

```javascript
const axios = require('axios');
const fs = require('fs');

class Code2APIClient {
    constructor(baseURL = 'http://localhost:8000') {
        this.client = axios.create({ baseURL });
    }

    async analyzeCode(code, language, filename) {
        try {
            const response = await this.client.post('/analyze', {
                code,
                language,
                filename
            });
            return response.data;
        } catch (error) {
            throw new Error(`Analysis failed: ${error.response?.data?.detail || error.message}`);
        }
    }

    async analyzeRepository(repoUrl, branch = 'main', maxFiles = 50) {
        try {
            const response = await this.client.post('/analyze-repo', {
                repo_url: repoUrl,
                branch,
                max_files: maxFiles
            });
            return response.data;
        } catch (error) {
            throw new Error(`Repository analysis failed: ${error.response?.data?.detail || error.message}`);
        }
    }

    async downloadAPI(projectName, outputPath) {
        try {
            const response = await this.client.get(`/download/${projectName}`, {
                responseType: 'stream'
            });
            
            const writer = fs.createWriteStream(outputPath);
            response.data.pipe(writer);
            
            return new Promise((resolve, reject) => {
                writer.on('finish', resolve);
                writer.on('error', reject);
            });
        } catch (error) {
            throw new Error(`Download failed: ${error.response?.data?.detail || error.message}`);
        }
    }
}

// Usage example
(async () => {
    const client = new Code2APIClient();
    
    try {
        const result = await client.analyzeCode(
            'function greet(name) { return `Hello, ${name}!`; }',
            'javascript',
            'greet.js'
        );
        
        console.log(`Generated ${result.analysis.api_endpoints.length} endpoints`);
        
        // Download the API
        const projectName = result.generated_api_path.split('/').pop();
        await client.downloadAPI(projectName, `${projectName}.zip`);
        console.log('API downloaded successfully');
        
    } catch (error) {
        console.error('Error:', error.message);
    }
})();
```

---

## Performance Optimization Examples

### Example 11: Using Cache for Better Performance

**Check Cache Statistics:**
```bash
curl -X GET "http://localhost:8000/cache/stats"
```

**Clear Cache When Needed:**
```bash
curl -X POST "http://localhost:8000/cache/clear"
```

**Batch Operations:**
```bash
# Instead of multiple single-file requests, use upload for multiple files
curl -X POST "http://localhost:8000/upload" \
  -F "files=@file1.py" \
  -F "files=@file2.py" \
  -F "files=@file3.py"
```

These examples demonstrate the full capabilities of Code2API and how to integrate it into your development workflow effectively.