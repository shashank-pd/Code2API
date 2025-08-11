# Code2API Setup Guide

## Quick Start

### 1. Get OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign up or log in to your account
3. Create a new API key
4. Copy the API key (starts with `sk-...`)

### 2. Set Up Environment

**Option A: Using .env file (Recommended)**
1. Open the `.env` file in the project root
2. Replace `your_openai_api_key_here` with your actual API key:
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

**Option B: Using Environment Variable**
- Windows PowerShell:
  ```powershell
  $env:OPENAI_API_KEY="sk-your-actual-api-key-here"
  ```
- Windows Command Prompt:
  ```cmd
  set OPENAI_API_KEY=sk-your-actual-api-key-here
  ```
- Linux/Mac:
  ```bash
  export OPENAI_API_KEY=sk-your-actual-api-key-here
  ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Test the Setup

```bash
# Test with CLI
python cli.py analyze example.py

# Test with web interface
python -m uvicorn src.api.main:app --reload
```

## Usage Examples

### CLI Usage

```bash
# Analyze a local file
python cli.py analyze src/example.py

# Analyze a GitHub repository
python cli.py analyze-repo https://github.com/user/repo.git

# Get help
python cli.py --help
```

### Web Interface

1. Start the backend:
   ```bash
   python -m uvicorn src.api.main:app --reload
   ```

2. Start the frontend:
   ```bash
   cd frontend
   npm install
   npm start
   ```

3. Open http://localhost:3000

## API Costs

The system uses OpenAI's GPT-4 API. Typical costs:
- Small file analysis: ~$0.01-$0.05
- Medium repository: ~$0.10-$0.50
- Large repository: ~$0.50-$2.00

Monitor your usage at [OpenAI Usage Dashboard](https://platform.openai.com/usage).

## Troubleshooting

### "API key not found" Error
- Double-check your API key in the `.env` file
- Ensure no extra spaces or quotes around the key
- Try setting the environment variable directly

### "Rate limit exceeded" Error
- You've hit OpenAI's rate limits
- Wait a few minutes and try again
- Consider upgrading your OpenAI plan

### "Invalid API key" Error
- Check that your API key is correct
- Ensure your OpenAI account has credits available
- Regenerate a new API key if needed

## Features

✅ Multi-language support (Python, JavaScript, Java)
✅ GitHub repository analysis  
✅ AI-powered endpoint generation
✅ Automatic documentation
✅ Security recommendations
✅ Web interface with Monaco Editor
✅ CLI for automation
✅ Docker deployment ready

## Support

- Check the [README.md](README.md) for detailed documentation
- Review example files in the `examples/` directory
- Open an issue for bugs or feature requests
