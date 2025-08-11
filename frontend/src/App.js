import React, { useState, useRef } from 'react';
import axios from 'axios';
import MonacoEditor from '@monaco-editor/react';
import SwaggerUI from 'swagger-ui-react';
import 'swagger-ui-react/swagger-ui.css';
import './App.css';

const SUPPORTED_LANGUAGES = {
  python: { label: 'Python', extension: '.py', mode: 'python' },
  javascript: { label: 'JavaScript', extension: '.js', mode: 'javascript' },
  java: { label: 'Java', extension: '.java', mode: 'java' }
};

function App() {
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [filename, setFilename] = useState('example.py');
  const [repoUrl, setRepoUrl] = useState('');
  const [branch, setBranch] = useState('main');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('editor');
  const [inputMode, setInputMode] = useState('code'); // 'code' or 'repo'
  const fileInputRef = useRef(null);

  const sampleCode = {
    python: `def calculate_user_score(user_id, scores):
    """Calculate the average score for a user"""
    if not scores:
        return 0
    return sum(scores) / len(scores)

def get_user_profile(user_id):
    """Get user profile information"""
    # This would typically fetch from a database
    return {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com"
    }

class UserManager:
    def create_user(self, username, email, password):
        """Create a new user account"""
        # Hash password and save to database
        return {"message": "User created successfully"}
    
    def authenticate_user(self, username, password):
        """Authenticate user credentials"""
        # Check credentials against database
        return {"authenticated": True, "token": "jwt_token_here"}`,
    
    javascript: `function calculateUserScore(userId, scores) {
    /**
     * Calculate the average score for a user
     */
    if (!scores || scores.length === 0) {
        return 0;
    }
    return scores.reduce((a, b) => a + b, 0) / scores.length;
}

async function getUserProfile(userId) {
    /**
     * Get user profile information
     */
    return {
        id: userId,
        name: \`User \${userId}\`,
        email: \`user\${userId}@example.com\`
    };
}

class UserManager {
    async createUser(username, email, password) {
        /**
         * Create a new user account
         */
        return { message: "User created successfully" };
    }
    
    async authenticateUser(username, password) {
        /**
         * Authenticate user credentials
         */
        return { authenticated: true, token: "jwt_token_here" };
    }
}`,
    
    java: `public class UserManager {
    
    public double calculateUserScore(int userId, double[] scores) {
        /**
         * Calculate the average score for a user
         */
        if (scores == null || scores.length == 0) {
            return 0;
        }
        double sum = 0;
        for (double score : scores) {
            sum += score;
        }
        return sum / scores.length;
    }
    
    public UserProfile getUserProfile(int userId) {
        /**
         * Get user profile information
         */
        return new UserProfile(userId, "User " + userId, "user" + userId + "@example.com");
    }
    
    public String createUser(String username, String email, String password) {
        /**
         * Create a new user account
         */
        return "User created successfully";
    }
}`
  };

  React.useEffect(() => {
    setCode(sampleCode[language]);
    setFilename(`example${SUPPORTED_LANGUAGES[language].extension}`);
  }, [language]);

  const analyzeCode = async () => {
    if (inputMode === 'code') {
      if (!code.trim()) {
        setError('Please enter some code to analyze');
        return;
      }
    } else {
      if (!repoUrl.trim()) {
        setError('Please enter a GitHub repository URL');
        return;
      }
    }

    setLoading(true);
    setError(null);

    try {
      let response;
      
      if (inputMode === 'code') {
        response = await axios.post('/analyze', {
          code,
          language,
          filename
        });
      } else {
        response = await axios.post('/analyze-repo', {
          repo_url: repoUrl,
          branch: branch || 'main',
          max_files: 50
        });
      }

      setAnalysis(response.data);
      setActiveTab('results');
    } catch (err) {
      setError(err.response?.data?.detail || 'Error analyzing code');
    } finally {
      setLoading(false);
    }
  };

  const uploadFiles = async (event) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setLoading(true);
    setError(null);

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    try {
      const response = await axios.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      // Show results for the first successful analysis
      const firstSuccess = response.data.results.find(r => r.success);
      if (firstSuccess) {
        setAnalysis({
          success: true,
          analysis: firstSuccess.analysis,
          generated_api_path: firstSuccess.api_path,
          message: `Analyzed ${response.data.results.length} files`
        });
        setActiveTab('results');
      } else {
        setError('No files could be analyzed successfully');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Error uploading files');
    } finally {
      setLoading(false);
    }
  };

  const downloadAPI = async () => {
    if (!analysis?.generated_api_path) return;

    try {
      const projectName = analysis.generated_api_path.split('/').pop();
      const response = await axios.get(`/download/${projectName}`, {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${projectName}.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Error downloading API');
    }
  };

  const generateSwaggerSpec = () => {
    if (!analysis?.analysis?.api_endpoints) return null;

    const spec = {
      openapi: '3.0.0',
      info: {
        title: 'Generated API',
        version: '1.0.0',
        description: 'Auto-generated API from source code analysis'
      },
      paths: {}
    };

    analysis.analysis.api_endpoints.forEach(endpoint => {
      const path = endpoint.endpoint_path;
      const method = endpoint.http_method.toLowerCase();

      if (!spec.paths[path]) {
        spec.paths[path] = {};
      }

      spec.paths[path][method] = {
        summary: endpoint.description,
        parameters: endpoint.parameters?.map(param => ({
          name: param.name,
          in: 'query',
          required: !param.default,
          schema: {
            type: param.type || 'string'
          }
        })) || [],
        responses: {
          '200': {
            description: 'Success',
            content: {
              'application/json': {
                schema: {
                  type: 'object'
                }
              }
            }
          }
        }
      };

      if (endpoint.needs_auth) {
        spec.paths[path][method].security = [{ bearerAuth: [] }];
      }
    });

    if (analysis.analysis.api_endpoints.some(ep => ep.needs_auth)) {
      spec.components = {
        securitySchemes: {
          bearerAuth: {
            type: 'http',
            scheme: 'bearer',
            bearerFormat: 'JWT'
          }
        }
      };
    }

    return spec;
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>🚀 Code2API</h1>
        <p>AI-powered system that converts source code into APIs</p>
      </header>

      <div className="app-content">
        <div className="tabs">
          <button 
            className={activeTab === 'editor' ? 'tab active' : 'tab'}
            onClick={() => setActiveTab('editor')}
          >
            Code Editor
          </button>
          <button 
            className={activeTab === 'results' ? 'tab active' : 'tab'}
            onClick={() => setActiveTab('results')}
            disabled={!analysis}
          >
            Analysis Results
          </button>
          <button 
            className={activeTab === 'swagger' ? 'tab active' : 'tab'}
            onClick={() => setActiveTab('swagger')}
            disabled={!analysis?.analysis?.api_endpoints}
          >
            API Documentation
          </button>
        </div>

        {activeTab === 'editor' && (
          <div className="editor-tab">
            <div className="input-mode-selector">
              <button 
                className={inputMode === 'code' ? 'mode-btn active' : 'mode-btn'}
                onClick={() => setInputMode('code')}
              >
                📝 Code Editor
              </button>
              <button 
                className={inputMode === 'repo' ? 'mode-btn active' : 'mode-btn'}
                onClick={() => setInputMode('repo')}
              >
                📦 GitHub Repository
              </button>
            </div>

            {inputMode === 'code' ? (
              <>
                <div className="controls">
                  <div className="control-group">
                    <label>Language:</label>
                    <select 
                      value={language} 
                      onChange={(e) => setLanguage(e.target.value)}
                    >
                      {Object.entries(SUPPORTED_LANGUAGES).map(([key, lang]) => (
                        <option key={key} value={key}>{lang.label}</option>
                      ))}
                    </select>
                  </div>

                  <div className="control-group">
                    <label>Filename:</label>
                    <input 
                      type="text" 
                      value={filename}
                      onChange={(e) => setFilename(e.target.value)}
                    />
                  </div>

                  <div className="control-group">
                    <input
                      type="file"
                      ref={fileInputRef}
                      multiple
                      accept=".py,.js,.jsx,.ts,.tsx,.java"
                      onChange={uploadFiles}
                      style={{ display: 'none' }}
                    />
                    <button onClick={() => fileInputRef.current?.click()}>
                      Upload Files
                    </button>
                  </div>

                  <button 
                    onClick={analyzeCode} 
                    disabled={loading}
                    className="analyze-btn"
                  >
                    {loading ? 'Analyzing...' : 'Analyze Code'}
                  </button>
                </div>

                <div className="editor-container">
                  <MonacoEditor
                    height="500px"
                    language={SUPPORTED_LANGUAGES[language].mode}
                    value={code}
                    onChange={setCode}
                    theme="vs-dark"
                    options={{
                      minimap: { enabled: false },
                      fontSize: 14,
                      lineNumbers: 'on',
                      roundedSelection: false,
                      scrollBeyondLastLine: false,
                      automaticLayout: true
                    }}
                  />
                </div>
              </>
            ) : (
              <>
                <div className="repo-controls">
                  <div className="control-group repo-url-group">
                    <label>GitHub Repository URL:</label>
                    <input 
                      type="text" 
                      value={repoUrl}
                      onChange={(e) => setRepoUrl(e.target.value)}
                      placeholder="https://github.com/owner/repo or owner/repo"
                      className="repo-url-input"
                    />
                  </div>

                  <div className="control-group">
                    <label>Branch:</label>
                    <input 
                      type="text" 
                      value={branch}
                      onChange={(e) => setBranch(e.target.value)}
                      placeholder="main"
                    />
                  </div>

                  <button 
                    onClick={analyzeCode} 
                    disabled={loading}
                    className="analyze-btn"
                  >
                    {loading ? 'Analyzing Repository...' : 'Analyze Repository'}
                  </button>
                </div>

                <div className="repo-examples">
                  <h3>Try these example repositories:</h3>
                  <div className="example-repos">
                    <button 
                      className="example-repo-btn"
                      onClick={() => setRepoUrl('fastapi/fastapi')}
                    >
                      🚀 fastapi/fastapi
                    </button>
                    <button 
                      className="example-repo-btn"
                      onClick={() => setRepoUrl('pallets/flask')}
                    >
                      🌶️ pallets/flask
                    </button>
                    <button 
                      className="example-repo-btn"
                      onClick={() => setRepoUrl('microsoft/vscode')}
                    >
                      💻 microsoft/vscode
                    </button>
                    <button 
                      className="example-repo-btn"
                      onClick={() => setRepoUrl('facebook/react')}
                    >
                      ⚛️ facebook/react
                    </button>
                  </div>
                </div>
              </>
            )}

            {error && (
              <div className="error">
                <strong>Error:</strong> {error}
              </div>
            )}
          </div>
        )}

        {activeTab === 'results' && analysis && (
          <div className="results-tab">
            <div className="results-header">
              <h2>Analysis Results</h2>
              {analysis.generated_api_path && (
                <button onClick={downloadAPI} className="download-btn">
                  Download Generated API
                </button>
              )}
            </div>

            {analysis.analysis?.repository_info && (
              <div className="repo-info-card">
                <h3>📦 Repository Information</h3>
                <div className="repo-details">
                  <div className="repo-detail">
                    <strong>Name:</strong> {analysis.analysis.repository_info.name}
                  </div>
                  <div className="repo-detail">
                    <strong>Description:</strong> {analysis.analysis.repository_info.description || 'No description'}
                  </div>
                  <div className="repo-detail">
                    <strong>Language:</strong> {analysis.analysis.repository_info.language || 'Multiple'}
                  </div>
                  <div className="repo-detail">
                    <strong>Stars:</strong> ⭐ {analysis.analysis.repository_info.stars || 0}
                  </div>
                  <div className="repo-detail">
                    <strong>Forks:</strong> 🍴 {analysis.analysis.repository_info.forks || 0}
                  </div>
                  <div className="repo-detail">
                    <strong>Files Analyzed:</strong> 📄 {analysis.analysis.files_analyzed || 0}
                  </div>
                </div>
              </div>
            )}

            {analysis.analysis?.statistics && (
              <div className="stats-card">
                <h3>📊 Code Statistics</h3>
                <div className="stats-grid">
                  <div className="stat-item">
                    <div className="stat-number">{analysis.analysis.statistics.total_files}</div>
                    <div className="stat-label">Total Files</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-number">{analysis.analysis.statistics.total_lines?.toLocaleString()}</div>
                    <div className="stat-label">Total Lines</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-number">{Object.keys(analysis.analysis.statistics.languages || {}).length}</div>
                    <div className="stat-label">Languages</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-number">{analysis.analysis.api_endpoints?.length || 0}</div>
                    <div className="stat-label">API Endpoints</div>
                  </div>
                </div>
                
                {analysis.analysis.statistics.languages && (
                  <div className="language-breakdown">
                    <h4>Language Breakdown:</h4>
                    {Object.entries(analysis.analysis.statistics.languages).map(([lang, count]) => (
                      <div key={lang} className="language-item">
                        <span className="language-name">{lang}</span>
                        <span className="language-count">{count} files</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            <div className="results-grid">
              <div className="result-card">
                <h3>API Endpoints</h3>
                <div className="endpoint-list">
                  {analysis.analysis.api_endpoints?.map((endpoint, index) => (
                    <div key={index} className="endpoint-item">
                      <span className={`method ${endpoint.http_method.toLowerCase()}`}>
                        {endpoint.http_method}
                      </span>
                      <span className="path">{endpoint.endpoint_path}</span>
                      <span className="description">{endpoint.description}</span>
                      {endpoint.needs_auth && <span className="auth-badge">🔒 Auth Required</span>}
                      {endpoint.class_name && <span className="class-badge">📦 {endpoint.class_name}</span>}
                    </div>
                  ))}
                  {!analysis.analysis.api_endpoints?.length && (
                    <div className="no-results">No API endpoints generated</div>
                  )}
                </div>
              </div>

              <div className="result-card">
                <h3>Security Recommendations</h3>
                <ul>
                  {analysis.analysis.security_recommendations?.map((rec, index) => (
                    <li key={index}>{rec}</li>
                  ))}
                  {!analysis.analysis.security_recommendations?.length && (
                    <li>No security issues detected</li>
                  )}
                </ul>
              </div>

              <div className="result-card">
                <h3>Optimization Suggestions</h3>
                <ul>
                  {analysis.analysis.optimization_suggestions?.map((sug, index) => (
                    <li key={index}>{sug}</li>
                  ))}
                  {!analysis.analysis.optimization_suggestions?.length && (
                    <li>No optimization suggestions</li>
                  )}
                </ul>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'swagger' && analysis?.analysis?.api_endpoints && (
          <div className="swagger-tab">
            <SwaggerUI spec={generateSwaggerSpec()} />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
