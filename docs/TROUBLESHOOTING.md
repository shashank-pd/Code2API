# Code2API - Troubleshooting Guide

This guide helps you resolve common issues when using Code2API.

## Common Issues and Solutions

### 1. API Key Configuration Issues

#### Problem: "No AI API key configured" Error

**Error Message:**
```
HTTPException: AI API key not found. Please set up your Groq or OpenAI API key.
```

**Solution:**
1. **Get a Groq API Key (Recommended - Free):**
   - Visit https://console.groq.com/keys
   - Create an account and generate an API key
   - Add to your `.env` file:
     ```
     GROQ_API_KEY=your_groq_api_key_here
     ```

2. **Alternative - OpenAI API Key:**
   - Visit https://platform.openai.com/api-keys
   - Generate an API key
   - Add to your `.env` file:
     ```
     OPENAI_API_KEY=your_openai_api_key_here
     ```

3. **Environment Variable Method:**
   ```bash
   # Linux/Mac
   export GROQ_API_KEY=your_key_here
   
   # Windows
   set GROQ_API_KEY=your_key_here
   ```

4. **Verify Configuration:**
   ```bash
   python cli.py analyze-file test.py
   ```

---

### 2. Installation and Dependency Issues

#### Problem: Import Errors

**Error Message:**
```
ImportError: No module named 'groq'
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Update pip and setuptools:**
   ```bash
   pip install --upgrade pip setuptools wheel
   ```

3. **Use Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

4. **Check Python Version:**
   ```bash
   python --version  # Should be 3.8+
   ```

#### Problem: Frontend Dependencies

**Error Message:**
```
npm ERR! peer dep missing
```

**Solution:**
1. **Update Node.js:**
   - Ensure Node.js 16+ is installed
   
2. **Clean Install:**
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **Use Specific Node Version:**
   ```bash
   nvm use 18  # if using nvm
   npm install
   ```

---

### 3. API Server Issues

#### Problem: Port Already in Use

**Error Message:**
```
OSError: [Errno 48] Address already in use
```

**Solution:**
1. **Change Port:**
   ```bash
   # In .env file
   API_PORT=8001
   
   # Or command line
   python -m uvicorn src.api.main:app --port 8001
   ```

2. **Kill Existing Process:**
   ```bash
   # Find process using port 8000
   lsof -i :8000
   kill -9 <PID>
   ```

3. **Use Docker:**
   ```bash
   docker-compose up --build
   ```

#### Problem: CORS Errors in Frontend

**Error Message:**
```
Access to XMLHttpRequest blocked by CORS policy
```

**Solution:**
1. **Check CORS Configuration:**
   - Ensure frontend URL is in allowed origins
   - Verify API is running on correct port

2. **Development Mode:**
   ```bash
   # Set API_DEBUG=True in .env
   API_DEBUG=True
   ```

3. **Proxy Configuration:**
   ```bash
   # Frontend should proxy to backend
   cd frontend
   npm run dev
   ```

---

### 4. Code Analysis Issues

#### Problem: "No endpoints found" Result

**Possible Causes:**
- Functions are private (start with `_`)
- No suitable functions for API conversion
- AI model couldn't parse the code

**Solutions:**
1. **Check Function Names:**
   ```python
   # Good - will be analyzed
   def get_users():
       return []
   
   # Bad - will be skipped
   def _private_function():
       return []
   ```

2. **Add Docstrings:**
   ```python
   def calculate_tax(amount, rate):
       """Calculate tax amount for given rate"""
       return amount * rate
   ```

3. **Use Descriptive Names:**
   ```python
   # Better for API generation
   def create_user_account():
       pass
   
   # Less clear purpose
   def process():
       pass
   ```

#### Problem: Code Parsing Errors

**Error Message:**
```
SyntaxError: invalid syntax
```

**Solution:**
1. **Validate Syntax:**
   ```bash
   python -m py_compile your_file.py
   ```

2. **Check Encoding:**
   - Ensure files are UTF-8 encoded
   - Remove non-ASCII characters

3. **Simplify Code:**
   - Remove complex decorators temporarily
   - Break down large classes

---

### 5. Repository Analysis Issues

#### Problem: GitHub Repository Access

**Error Message:**
```
Repository owner/repo not found
```

**Solutions:**
1. **Check URL Format:**
   ```bash
   # Correct formats
   https://github.com/owner/repo
   owner/repo
   ```

2. **Public Repository:**
   - Ensure repository is public
   - Or provide GitHub token for private repos

3. **Branch Exists:**
   ```bash
   # Check if branch exists
   git ls-remote --heads https://github.com/owner/repo
   ```

4. **Set GitHub Token:**
   ```bash
   # In .env file for private repos
   GITHUB_TOKEN=your_github_token
   ```

#### Problem: Too Many Files

**Error Message:**
```
Found 500 files, limiting to 50
```

**Solution:**
1. **Increase Limit:**
   ```json
   {
     "repo_url": "https://github.com/owner/repo",
     "max_files": 100
   }
   ```

2. **Filter File Types:**
   ```json
   {
     "repo_url": "https://github.com/owner/repo",
     "include_patterns": [".py", ".js"]
   }
   ```

---

### 6. Generated API Issues

#### Problem: Generated API Won't Start

**Error in Generated API:**
```
ImportError: cannot import name 'FastAPI'
```

**Solution:**
1. **Install Requirements:**
   ```bash
   cd generated_project
   pip install -r requirements.txt
   ```

2. **Check Python Path:**
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   python main.py
   ```

3. **Use Uvicorn Directly:**
   ```bash
   uvicorn main:app --reload
   ```

#### Problem: Authentication Not Working

**Generated API Auth Issues:**

**Solution:**
1. **Get Token First:**
   ```bash
   curl -X POST "http://localhost:8000/auth/token" \
     -H "Content-Type: application/json" \
     -d '{"username": "demo", "password": "demo"}'
   ```

2. **Use Token in Requests:**
   ```bash
   curl -X GET "http://localhost:8000/protected-endpoint" \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

3. **Check Token Expiry:**
   - Tokens expire after 30 minutes by default
   - Get a new token if needed

---

### 7. Performance Issues

#### Problem: Slow Analysis

**Symptoms:**
- Long response times
- Timeouts

**Solutions:**
1. **Enable Caching:**
   ```bash
   # Check cache stats
   curl -X GET "http://localhost:8000/cache/stats"
   ```

2. **Reduce Code Size:**
   - Split large files
   - Remove unnecessary code

3. **Use Groq Instead of OpenAI:**
   ```bash
   # Groq is generally faster
   GROQ_API_KEY=your_key_here
   ```

4. **Batch Processing:**
   ```bash
   # Upload multiple files at once
   curl -X POST "http://localhost:8000/upload" \
     -F "files=@file1.py" \
     -F "files=@file2.py"
   ```

#### Problem: Memory Issues

**Error Message:**
```
MemoryError: Unable to allocate array
```

**Solutions:**
1. **Reduce File Size:**
   - Split large files
   - Use max_files parameter

2. **Clear Cache:**
   ```bash
   curl -X POST "http://localhost:8000/cache/clear"
   ```

3. **Restart Service:**
   ```bash
   docker-compose restart
   ```

---

### 8. Docker Issues

#### Problem: Docker Build Failures

**Error Message:**
```
ERROR: failed to solve: process "/bin/sh -c pip install -r requirements.txt" did not complete successfully
```

**Solutions:**
1. **Update Docker:**
   ```bash
   docker --version  # Should be recent
   ```

2. **Clear Docker Cache:**
   ```bash
   docker system prune -a
   ```

3. **Build with No Cache:**
   ```bash
   docker-compose build --no-cache
   ```

4. **Check Requirements:**
   ```bash
   # Verify requirements.txt exists and is valid
   cat requirements.txt
   ```

#### Problem: Container Communication

**Frontend can't reach backend:**

**Solutions:**
1. **Check Network:**
   ```bash
   docker network ls
   docker network inspect code2api_network
   ```

2. **Use Service Names:**
   ```bash
   # In docker-compose, use service names
   REACT_APP_API_URL=http://api:8000
   ```

3. **Port Mapping:**
   ```yaml
   # Ensure ports are mapped correctly
   ports:
     - "8000:8000"
   ```

---

### 9. Security Issues

#### Problem: File Upload Rejected

**Error Message:**
```
File size exceeds 1MB limit
Invalid character in filename
```

**Solutions:**
1. **Check File Size:**
   ```bash
   ls -lh your_file.py  # Should be < 1MB
   ```

2. **Sanitize Filename:**
   ```bash
   # Remove special characters
   mv "file with spaces.py" "file_with_spaces.py"
   ```

3. **Validate Content:**
   ```bash
   file your_file.py  # Should be text file
   ```

#### Problem: Rate Limiting

**Error Message:**
```
Rate limit exceeded: Maximum 100 requests per 60 seconds
```

**Solutions:**
1. **Wait and Retry:**
   ```bash
   sleep 60
   # Then retry request
   ```

2. **Batch Requests:**
   ```bash
   # Instead of multiple single requests
   # Use upload endpoint for multiple files
   ```

3. **Contact Admin:**
   - For higher rate limits in production

---

### 10. Development and Testing Issues

#### Problem: Tests Failing

**Error Message:**
```
ModuleNotFoundError in tests
```

**Solutions:**
1. **Install Test Dependencies:**
   ```bash
   pip install pytest httpx
   ```

2. **Run Tests Correctly:**
   ```bash
   # From project root
   python -m pytest tests/ -v
   ```

3. **Set Environment:**
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   python -m pytest
   ```

#### Problem: Mock API Keys in Tests

**Solution:**
```python
# In test files
@patch.dict(os.environ, {'GROQ_API_KEY': 'test-key'})
def test_with_mock_key():
    # Your test code
    pass
```

---

## Diagnostic Commands

### Health Check Sequence

1. **Check API Server:**
   ```bash
   curl -X GET "http://localhost:8000/health"
   ```

2. **Check Configuration:**
   ```bash
   python -c "from src.config import config; print(config.validate_config())"
   ```

3. **Check Dependencies:**
   ```bash
   pip check
   ```

4. **Check Logs:**
   ```bash
   docker-compose logs api
   # or
   tail -f app.log
   ```

### Performance Diagnostics

1. **Cache Statistics:**
   ```bash
   curl -X GET "http://localhost:8000/cache/stats"
   ```

2. **Generated APIs List:**
   ```bash
   curl -X GET "http://localhost:8000/generated"
   ```

3. **System Resources:**
   ```bash
   docker stats
   # or
   htop
   ```

---

## Getting Help

### Log Files
- Backend logs: Check console output or log files
- Frontend logs: Check browser developer console
- Docker logs: `docker-compose logs`

### Debug Mode
Enable debug mode for more verbose output:
```bash
# In .env
API_DEBUG=True
```

### Support Channels
1. **GitHub Issues**: Report bugs and feature requests
2. **Documentation**: Check API_REFERENCE.md and EXAMPLES.md
3. **Community**: Share solutions and get help

### Reporting Issues
When reporting issues, include:
1. Error message (full stack trace)
2. Operating system and Python version
3. Code2API version
4. Steps to reproduce
5. Configuration (without API keys)

### Emergency Recovery
If the system is completely broken:
```bash
# Reset everything
docker-compose down -v
docker system prune -a
git clean -fdx
pip install -r requirements.txt
cd frontend && npm install
docker-compose up --build
```