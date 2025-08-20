import React, { useState, useRef } from 'react';
import axios from 'axios';
import MonacoEditor from '@monaco-editor/react';
import SwaggerUI from 'swagger-ui-react';
import 'swagger-ui-react/swagger-ui.css';
import { motion } from 'framer-motion';
import { 
  Code2, 
  Upload, 
  Download, 
  Github, 
  Sparkles, 
  Zap, 
  Shield, 
  TrendingUp,
  FileText,
  Globe,
  Star,
  GitFork,
  Lock,
  Package
} from 'lucide-react';

// UI Components
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Input } from './components/ui/input';

// Magic UI Components
import { BorderBeam } from './components/magicui/border-beam';
import { ShimmerButton } from './components/magicui/shimmer-button';
import { MagicCard } from './components/magicui/magic-card';
import { BlurFade } from './components/magicui/blur-fade';
import { Meteors } from './components/magicui/meteors';

import { cn } from './lib/utils';

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
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900">
      {/* Background Effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <Meteors number={20} />
      </div>
      
      {/* Header */}
      <BlurFade delay={0.2}>
        <header className="relative z-10 text-center py-16 px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="max-w-4xl mx-auto"
          >
            <div className="inline-flex items-center gap-3 mb-6 px-6 py-3 rounded-full bg-white/10 backdrop-blur-sm border border-white/20">
              <Zap className="w-5 h-5 text-yellow-400" />
              <span className="text-sm font-medium text-gray-200">AI-Powered Code Analysis</span>
              <Sparkles className="w-5 h-5 text-purple-400" />
            </div>
            
            <h1 className="text-6xl md:text-7xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent mb-6">
              Code2API
            </h1>
            
            <p className="text-xl md:text-2xl text-gray-300 max-w-2xl mx-auto leading-relaxed">
              Transform your source code into production-ready APIs with AI-powered analysis and generation
            </p>
          </motion.div>
        </header>
      </BlurFade>

      {/* Main Content */}
      <div className="relative z-10 max-w-7xl mx-auto px-6 pb-16">
        {/* Tab Navigation */}
        <BlurFade delay={0.4}>
          <div className="flex flex-wrap justify-center gap-2 mb-8">
            {[
              { id: 'editor', label: 'Code Editor', icon: Code2 },
              { id: 'results', label: 'Analysis Results', icon: TrendingUp, disabled: !analysis },
              { id: 'swagger', label: 'API Documentation', icon: FileText, disabled: !analysis?.analysis?.api_endpoints }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                disabled={tab.disabled}
                className={cn(
                  "flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all duration-200",
                  activeTab === tab.id
                    ? "bg-blue-600 text-white shadow-lg shadow-blue-600/25"
                    : tab.disabled
                    ? "bg-gray-800 text-gray-500 cursor-not-allowed"
                    : "bg-gray-800/50 text-gray-300 hover:bg-gray-700/50 hover:text-white"
                )}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </BlurFade>

        {/* Editor Tab */}
        {activeTab === 'editor' && (
          <BlurFade delay={0.6}>
            <div className="space-y-8">
              {/* Input Mode Selector */}
              <MagicCard className="p-6">
                <div className="flex flex-wrap gap-4 justify-center mb-6">
                  <button
                    onClick={() => setInputMode('code')}
                    className={cn(
                      "flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all duration-200",
                      inputMode === 'code'
                        ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg"
                        : "bg-gray-700/50 text-gray-300 hover:bg-gray-600/50"
                    )}
                  >
                    <Code2 className="w-4 h-4" />
                    Code Editor
                  </button>
                  <button
                    onClick={() => setInputMode('repo')}
                    className={cn(
                      "flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all duration-200",
                      inputMode === 'repo'
                        ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg"
                        : "bg-gray-700/50 text-gray-300 hover:bg-gray-600/50"
                    )}
                  >
                    <Github className="w-4 h-4" />
                    GitHub Repository
                  </button>
                </div>

                {inputMode === 'code' ? (
                  <div className="space-y-6">
                    {/* Controls */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Language
                        </label>
                        <select
                          value={language}
                          onChange={(e) => setLanguage(e.target.value)}
                          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                          {Object.entries(SUPPORTED_LANGUAGES).map(([key, lang]) => (
                            <option key={key} value={key}>{lang.label}</option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Filename
                        </label>
                        <Input
                          value={filename}
                          onChange={(e) => setFilename(e.target.value)}
                          className="bg-gray-700 border-gray-600 text-white"
                        />
                      </div>

                      <div className="flex items-end">
                        <input
                          type="file"
                          ref={fileInputRef}
                          multiple
                          accept=".py,.js,.jsx,.ts,.tsx,.java"
                          onChange={uploadFiles}
                          className="hidden"
                        />
                        <Button
                          onClick={() => fileInputRef.current?.click()}
                          variant="outline"
                          className="w-full"
                        >
                          <Upload className="w-4 h-4 mr-2" />
                          Upload Files
                        </Button>
                      </div>
                    </div>

                    {/* Code Editor */}
                    <div className="relative overflow-hidden rounded-lg">
                      <BorderBeam />
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
                          automaticLayout: true,
                          padding: { top: 20 }
                        }}
                      />
                    </div>

                    {/* Analyze Button */}
                    <div className="flex justify-center">
                      <ShimmerButton
                        onClick={analyzeCode}
                        disabled={loading}
                        className="px-8 py-4 text-lg"
                      >
                        {loading ? (
                          <>
                            <motion.div
                              animate={{ rotate: 360 }}
                              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                              className="w-5 h-5 border-2 border-white border-t-transparent rounded-full mr-2"
                            />
                            Analyzing...
                          </>
                        ) : (
                          <>
                            <Zap className="w-5 h-5 mr-2" />
                            Analyze Code
                          </>
                        )}
                      </ShimmerButton>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {/* Repository Controls */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          GitHub Repository URL
                        </label>
                        <Input
                          value={repoUrl}
                          onChange={(e) => setRepoUrl(e.target.value)}
                          placeholder="https://github.com/owner/repo or owner/repo"
                          className="bg-gray-700 border-gray-600 text-white"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Branch
                        </label>
                        <Input
                          value={branch}
                          onChange={(e) => setBranch(e.target.value)}
                          placeholder="main"
                          className="bg-gray-700 border-gray-600 text-white"
                        />
                      </div>

                      <div className="flex items-end">
                        <ShimmerButton
                          onClick={analyzeCode}
                          disabled={loading}
                          className="w-full"
                        >
                          {loading ? (
                            <>
                              <motion.div
                                animate={{ rotate: 360 }}
                                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                                className="w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2"
                              />
                              Analyzing...
                            </>
                          ) : (
                            <>
                              <Github className="w-4 h-4 mr-2" />
                              Analyze Repo
                            </>
                          )}
                        </ShimmerButton>
                      </div>
                    </div>

                    {/* Example Repositories */}
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-4">Try these example repositories:</h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        {[
                          { repo: 'fastapi/fastapi', label: '🚀 FastAPI', desc: 'Modern Python API framework' },
                          { repo: 'pallets/flask', label: '🌶️ Flask', desc: 'Lightweight Python web framework' },
                          { repo: 'microsoft/vscode', label: '💻 VS Code', desc: 'Popular code editor' },
                          { repo: 'facebook/react', label: '⚛️ React', desc: 'JavaScript UI library' }
                        ].map((example) => (
                          <button
                            key={example.repo}
                            onClick={() => setRepoUrl(example.repo)}
                            className="p-4 text-left bg-gray-800/50 border border-gray-700 rounded-lg hover:bg-gray-700/50 hover:border-gray-600 transition-all group"
                          >
                            <div className="font-medium text-white group-hover:text-blue-400 transition-colors">
                              {example.label}
                            </div>
                            <div className="text-sm text-gray-400 mt-1">
                              {example.desc}
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Error Display */}
                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-4 bg-red-900/50 border border-red-700 rounded-lg text-red-200"
                  >
                    <strong>Error:</strong> {error}
                  </motion.div>
                )}
              </MagicCard>
            </div>
          </BlurFade>
        )}

        {/* Results Tab */}
        {activeTab === 'results' && analysis && (
          <BlurFade delay={0.6}>
            <div className="space-y-8">
              {/* Results Header */}
              <div className="flex flex-wrap items-center justify-between gap-4">
                <h2 className="text-3xl font-bold text-white">Analysis Results</h2>
                {analysis.generated_api_path && (
                  <Button
                    onClick={downloadAPI}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Download API
                  </Button>
                )}
              </div>

              {/* Repository Info */}
              {analysis.analysis?.repository_info && (
                <MagicCard className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <Globe className="w-6 h-6 text-blue-400" />
                    <h3 className="text-xl font-semibold text-white">Repository Information</h3>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <div className="text-sm text-gray-400">Name</div>
                      <div className="text-white font-medium">{analysis.analysis.repository_info.name}</div>
                    </div>
                    <div className="space-y-2">
                      <div className="text-sm text-gray-400">Language</div>
                      <div className="text-white font-medium">{analysis.analysis.repository_info.language || 'Multiple'}</div>
                    </div>
                    <div className="space-y-2">
                      <div className="text-sm text-gray-400">Files Analyzed</div>
                      <div className="text-white font-medium">{analysis.analysis.files_analyzed || 0}</div>
                    </div>
                    <div className="space-y-2">
                      <div className="text-sm text-gray-400">Stars</div>
                      <div className="flex items-center text-white font-medium">
                        <Star className="w-4 h-4 text-yellow-400 mr-1" />
                        {analysis.analysis.repository_info.stars || 0}
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="text-sm text-gray-400">Forks</div>
                      <div className="flex items-center text-white font-medium">
                        <GitFork className="w-4 h-4 text-gray-400 mr-1" />
                        {analysis.analysis.repository_info.forks || 0}
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="text-sm text-gray-400">Description</div>
                      <div className="text-gray-300 text-sm">{analysis.analysis.repository_info.description || 'No description'}</div>
                    </div>
                  </div>
                </MagicCard>
              )}

              {/* Statistics */}
              {analysis.analysis?.statistics && (
                <MagicCard className="p-6">
                  <div className="flex items-center gap-3 mb-6">
                    <TrendingUp className="w-6 h-6 text-green-400" />
                    <h3 className="text-xl font-semibold text-white">Code Statistics</h3>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-blue-400">{analysis.analysis.statistics.total_files}</div>
                      <div className="text-sm text-gray-400">Total Files</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-green-400">{analysis.analysis.statistics.total_lines?.toLocaleString()}</div>
                      <div className="text-sm text-gray-400">Total Lines</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-purple-400">{Object.keys(analysis.analysis.statistics.languages || {}).length}</div>
                      <div className="text-sm text-gray-400">Languages</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-yellow-400">{analysis.analysis.api_endpoints?.length || 0}</div>
                      <div className="text-sm text-gray-400">API Endpoints</div>
                    </div>
                  </div>

                  {analysis.analysis.statistics.languages && (
                    <div>
                      <h4 className="text-lg font-medium text-white mb-3">Language Breakdown</h4>
                      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                        {Object.entries(analysis.analysis.statistics.languages).map(([lang, count]) => (
                          <div key={lang} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                            <span className="text-white font-medium">{lang}</span>
                            <span className="text-gray-400 text-sm">{count} files</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </MagicCard>
              )}

              {/* Results Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* API Endpoints */}
                <MagicCard className="lg:col-span-2">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-white">
                      <Package className="w-5 h-5 text-blue-400" />
                      API Endpoints
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {analysis.analysis.api_endpoints?.map((endpoint, index) => (
                        <motion.div
                          key={index}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.1 }}
                          className="p-4 bg-gray-800/50 rounded-lg border border-gray-700"
                        >
                          <div className="flex flex-wrap items-center gap-2 mb-2">
                            <span className={cn(
                              "px-2 py-1 rounded text-xs font-medium uppercase",
                              endpoint.http_method.toLowerCase() === 'get' && "bg-blue-600 text-white",
                              endpoint.http_method.toLowerCase() === 'post' && "bg-green-600 text-white",
                              endpoint.http_method.toLowerCase() === 'put' && "bg-yellow-600 text-white",
                              endpoint.http_method.toLowerCase() === 'delete' && "bg-red-600 text-white"
                            )}>
                              {endpoint.http_method}
                            </span>
                            <code className="text-gray-300 bg-gray-800 px-2 py-1 rounded text-sm">
                              {endpoint.endpoint_path}
                            </code>
                            {endpoint.needs_auth && (
                              <span className="flex items-center gap-1 px-2 py-1 bg-amber-600/20 text-amber-400 rounded text-xs">
                                <Lock className="w-3 h-3" />
                                Auth Required
                              </span>
                            )}
                            {endpoint.class_name && (
                              <span className="px-2 py-1 bg-purple-600/20 text-purple-400 rounded text-xs">
                                {endpoint.class_name}
                              </span>
                            )}
                          </div>
                          <p className="text-gray-300 text-sm">{endpoint.description}</p>
                        </motion.div>
                      ))}
                      {!analysis.analysis.api_endpoints?.length && (
                        <div className="text-center py-8 text-gray-400">
                          No API endpoints generated
                        </div>
                      )}
                    </div>
                  </CardContent>
                </MagicCard>

                {/* Security & Optimization */}
                <div className="space-y-6">
                  <MagicCard>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-white">
                        <Shield className="w-5 h-5 text-red-400" />
                        Security
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-2">
                        {analysis.analysis.security_recommendations?.map((rec, index) => (
                          <li key={index} className="text-sm text-gray-300 flex items-start gap-2">
                            <div className="w-1.5 h-1.5 bg-red-400 rounded-full mt-2 flex-shrink-0" />
                            {rec}
                          </li>
                        ))}
                        {!analysis.analysis.security_recommendations?.length && (
                          <li className="text-sm text-gray-400">No security issues detected</li>
                        )}
                      </ul>
                    </CardContent>
                  </MagicCard>

                  <MagicCard>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-white">
                        <Zap className="w-5 h-5 text-green-400" />
                        Optimization
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-2">
                        {analysis.analysis.optimization_suggestions?.map((sug, index) => (
                          <li key={index} className="text-sm text-gray-300 flex items-start gap-2">
                            <div className="w-1.5 h-1.5 bg-green-400 rounded-full mt-2 flex-shrink-0" />
                            {sug}
                          </li>
                        ))}
                        {!analysis.analysis.optimization_suggestions?.length && (
                          <li className="text-sm text-gray-400">No optimization suggestions</li>
                        )}
                      </ul>
                    </CardContent>
                  </MagicCard>
                </div>
              </div>
            </div>
          </BlurFade>
        )}

        {/* Swagger Tab */}
        {activeTab === 'swagger' && analysis?.analysis?.api_endpoints && (
          <BlurFade delay={0.6}>
            <MagicCard className="overflow-hidden">
              <div className="p-6 border-b border-gray-700">
                <h2 className="text-2xl font-bold text-white">API Documentation</h2>
                <p className="text-gray-400 mt-1">Interactive API documentation generated from your code</p>
              </div>
              <div className="swagger-container">
                <SwaggerUI spec={generateSwaggerSpec()} />
              </div>
            </MagicCard>
          </BlurFade>
        )}
      </div>
    </div>
  );
}

export default App;
