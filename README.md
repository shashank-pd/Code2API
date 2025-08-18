# Code2API - Enhanced AI-Powered Code-to-API Generator

An intelligent system that ingests GitHub repositories, analyzes their source code, and automatically produces secure, tested, and documented REST APIs with **actual business logic implementation**.

## 🚀 What's New - Enhanced Version

### Major Improvements
- **🧠 Deep Code Analysis**: Advanced AST parsing with business logic extraction
- **🎯 Repository Purpose Detection**: LLM-powered semantic analysis to understand what repositories actually do
- **🔧 Domain-Specific API Generation**: Creates APIs tailored to repository purpose (ML, data analysis, file processing, etc.)
- **💡 Real Business Logic**: Implements actual functionality from original repositories, not just boilerplate
- **🔄 Enhanced Agent Coordination**: Improved LangChain workflow with robust parameter passing
- **📊 Comprehensive Analytics**: Better insights into generated APIs and their capabilities

## 🏗️ Architecture Overview

### Core Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   GitHub Repo   │ => │  Enhanced Agent  │ => │ Domain-Specific │
│   Analysis      │    │   Orchestrator   │    │  FastAPI Code   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                        │                        │
        ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Business Logic  │    │ LLM-Powered      │    │ Actual Function │
│   Extraction    │    │ Purpose Detection│    │ Implementation  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Technology Stack
- **🤖 AI/LLM**: Groq Cloud API with LLaMA 3.3 70B
- **🔗 Orchestration**: LangChain Agents & AgentExecutor
- **🔍 Code Analysis**: Tree-sitter AST parsing + semantic analysis
- **🌐 API Framework**: FastAPI + Uvicorn
- **🔒 Security**: OAuth 2.0, JWT, python-jose
- **✅ Testing**: pytest + httpx with comprehensive coverage
- **📚 Documentation**: OpenAPI 3.0 + Swagger UI

## 🎯 Repository Purpose Detection

The enhanced system automatically detects repository purpose and generates appropriate APIs:

| Repository Type | Generated API Features | Example Endpoints |
|----------------|----------------------|------------------|
| **Data Analysis** | Statistical analysis, visualizations, reporting | `/analyze`, `/visualize`, `/report` |
| **Machine Learning** | Model training, prediction, evaluation | `/predict`, `/train`, `/evaluate` |
| **File Processing** | Upload, conversion, format transformation | `/upload`, `/process`, `/convert` |
| **Web Scraping** | URL scraping, content extraction | `/scrape`, `/extract`, `/batch-scrape` |
| **Database** | CRUD operations, data management | `/{model}s`, `/{model}s/{id}` |
| **Security** | Encryption, hashing, authentication | `/encrypt`, `/decrypt`, `/hash` |
| **Automation** | Task scheduling, workflow management | `/tasks/schedule`, `/execute` |

## 🛠️ Enhanced Workflow

### Phase 1: Intelligent Code Acquisition
- GitHub repository download and extraction
- Language detection and file structure analysis
- Repository metadata collection

### Phase 2: Deep Code Analysis
- **AST Parsing**: Extract functions, classes, and business logic
- **Semantic Analysis**: LLM-powered understanding of repository purpose
- **Business Logic Mapping**: Identify core functionality and data flows
- **Domain Classification**: Categorize repository type for specialized handling

### Phase 3: Domain-Specific API Design
- **Purpose-Driven Design**: Create APIs tailored to repository type
- **Business Logic Integration**: Design endpoints that preserve original functionality
- **OpenAPI 3.0 Specification**: Comprehensive API documentation
- **Security Planning**: Domain-appropriate security measures

### Phase 4: Real Implementation Generation
- **FastAPI Application**: Production-ready server code
- **Business Logic Modules**: Actual implementation of repository functionality
- **Domain-Specific Classes**: ML predictors, data analyzers, file processors, etc.
- **Database Models**: Data structures extracted from original code

### Phase 5: Security Enhancement
- **Authentication**: JWT-based security with proper token handling
- **Authorization**: Role-based access control
- **Input Validation**: Comprehensive request validation
- **Security Headers**: CORS, rate limiting, security headers

### Phase 6: Comprehensive Testing
- **Unit Tests**: Test individual business logic components
- **Integration Tests**: End-to-end API testing
- **Business Logic Tests**: Validate actual functionality implementation
- **Security Tests**: Authentication and authorization testing

### Phase 7: Enhanced Documentation
- **Interactive Docs**: Swagger UI with business logic explanations
- **README Generation**: Comprehensive setup and usage guides
- **API Reference**: Detailed endpoint documentation
- **Business Logic Mapping**: Explanation of how original code translates to API

## 🚀 Quick Start

### Prerequisites
```bash
# Required environment variables
export GROQ_API_KEY="your_groq_api_key"
export GITHUB_TOKEN="your_github_token"  # Optional, for private repos
```

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/Code2API.git
cd Code2API

# Install dependencies
pip install -r requirements.txt

# Start the enhanced system
python main.py
```

### Usage Examples

#### Example 1: Data Analysis Repository
```bash
# Input: Repository with pandas/numpy data analysis code
curl -X POST "http://localhost:8000/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/user/data-analysis-repo"}'

# Output: API with endpoints like:
# POST /analyze - Perform data analysis using original algorithms
# POST /visualize - Generate charts using repository's visualization code
# POST /report - Create reports with actual analysis logic
```

#### Example 2: Machine Learning Repository
```bash
# Input: Repository with ML models and training code
curl -X POST "http://localhost:8000/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/user/ml-model-repo"}'

# Output: API with endpoints like:
# POST /predict - Make predictions using trained models
# POST /train - Train models with repository's training logic
# GET /models - List available models with metadata
```

#### Example 3: File Processing Repository
```bash
# Input: Repository with file manipulation utilities
curl -X POST "http://localhost:8000/api/generate" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/user/file-processor"}'

# Output: API with endpoints like:
# POST /upload - Upload files for processing
# POST /convert - Convert files using original conversion logic
# GET /download/{file_id} - Download processed files
```

## 🧪 Example Generated APIs

### Data Analysis API Structure
```
generated_api/
├── main.py                     # FastAPI application
├── business_logic/
│   └── data_analyzer.py       # Actual analysis implementation
├── models.py                  # Pydantic models
├── routers/
│   ├── analysis.py           # Analysis endpoints
│   └── visualization.py      # Visualization endpoints
├── auth.py                   # Authentication
└── tests/
    ├── test_analysis.py      # Business logic tests
    └── test_api.py          # API integration tests
```

### Machine Learning API Structure
```
generated_api/
├── main.py                     # FastAPI application
├── business_logic/
│   └── ml_predictor.py        # ML model implementation
├── models.py                  # Request/response models
├── routers/
│   ├── prediction.py         # Prediction endpoints
│   └── training.py           # Training endpoints
└── tests/
    ├── test_ml_logic.py      # ML logic tests
    └── test_models.py        # Model validation tests
```

## 🔧 Configuration

### Enhanced Settings
```python
# config/settings.py
REPOSITORY_ANALYSIS = {
    "deep_ast_parsing": True,
    "semantic_analysis": True,
    "business_logic_extraction": True,
    "llm_purpose_detection": True
}

API_GENERATION = {
    "domain_specific_endpoints": True,
    "business_logic_implementation": True,
    "comprehensive_security": True,
    "enhanced_documentation": True
}

GROQ_SETTINGS = {
    "model": "llama-3.3-70b-versatile",
    "temperature": 0.1,
    "max_tokens": 8192,
    "timeout": 120
}
```

## 📊 Enhanced Features

### Repository Analysis Capabilities
- **Purpose Detection**: Automatically identifies repository type and use case
- **Business Logic Extraction**: Extracts and preserves actual functionality
- **Data Model Discovery**: Identifies data structures and relationships
- **Dependency Analysis**: Understands library usage and patterns
- **Complexity Assessment**: Evaluates code complexity and API potential

### API Generation Improvements
- **Domain-Specific Templates**: Different API structures for different repository types
- **Business Logic Integration**: Actual implementation instead of placeholder code
- **Intelligent Endpoint Design**: Endpoints that make sense for the specific use case
- **Comprehensive Error Handling**: Robust error management throughout
- **Performance Optimization**: Efficient code generation and execution

### Security Enhancements
- **Purpose-Aware Security**: Security measures appropriate for repository type
- **Multi-Layer Authentication**: JWT + API Keys + OAuth 2.0 options
- **Input Sanitization**: Comprehensive validation for all endpoints
- **Rate Limiting**: Configurable rate limits based on endpoint criticality
- **Audit Logging**: Complete audit trail for security-sensitive operations

## 🧠 LLM Integration

### Groq Cloud API Integration
- **Model**: LLaMA 3.3 70B for advanced reasoning
- **Purpose**: Repository analysis and code understanding
- **Context**: Maintains conversation history for complex analysis
- **Fallback**: Graceful degradation when LLM is unavailable

### LangChain Agent Workflow
```python
# Enhanced agent workflow
workflow_phases = [
    "code_acquisition",      # Download and extract
    "semantic_analysis",     # LLM-powered understanding
    "business_extraction",   # Extract actual functionality
    "domain_classification", # Identify repository type
    "api_design",           # Create domain-specific design
    "implementation",       # Generate real business logic
    "security_enhancement", # Apply appropriate security
    "testing",             # Comprehensive test generation
    "documentation"        # Enhanced docs with business context
]
```

## 🔍 Monitoring and Analytics

### Generated API Analytics
- **Endpoint Usage**: Track which endpoints are called most frequently
- **Performance Metrics**: Response times and throughput analysis
- **Error Tracking**: Comprehensive error logging and analysis
- **Business Logic Execution**: Track how well original functionality is preserved

### Repository Analysis Insights
- **Purpose Detection Accuracy**: Measure how well repository types are identified
- **Business Logic Coverage**: Percentage of original functionality captured
- **Code Complexity Metrics**: Analyze repository complexity and API generation success
- **User Satisfaction**: Track API quality and usability metrics

## 🤝 Contributing

We welcome contributions to enhance the Code2API system!

### Areas for Contribution
- **New Repository Types**: Add support for additional domain-specific patterns
- **Enhanced Analysis**: Improve code analysis and business logic extraction
- **Security Features**: Strengthen security implementations
- **Performance**: Optimize API generation and execution
- **Documentation**: Improve docs and examples

### Development Setup
```bash
# Clone and setup development environment
git clone https://github.com/yourusername/Code2API.git
cd Code2API

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v --cov=backend

# Run the enhanced system in development mode
python main.py --debug
```

## 📄 License

MIT License - Feel free to use and modify as needed.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/Code2API/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/Code2API/discussions)
- **Documentation**: [Full Documentation](https://code2api.readthedocs.io)

## 🎯 Roadmap

### Upcoming Features
- **Multi-Language Support**: Support for Java, JavaScript, Go, Rust
- **Advanced ML Integration**: Better ML model handling and inference
- **Cloud Deployment**: One-click deployment to major cloud providers
- **API Marketplace**: Share and discover generated APIs
- **Visual Workflow Editor**: GUI for customizing API generation workflows

---

**Code2API v2.0 - Transform any repository into a production-ready API with actual business logic implementation.**