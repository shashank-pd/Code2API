import React, { useState, useRef, useMemo } from "react";
import axios from "axios";
import SwaggerUI from "swagger-ui-react";
import "swagger-ui-react/swagger-ui.css";
import Sidebar from "./components/layout/Sidebar";
import Topbar from "./components/layout/Topbar";
import EditorPanel from "./components/panels/EditorPanel";
import RepoPanel from "./components/panels/RepoPanel";
import ResultsPanel from "./components/panels/ResultsPanel";
import Alert from "./components/ui/Alert";
import ProgressBar from "./components/ui/ProgressBar";
import LoadingSpinner from "./components/ui/LoadingSpinner";
import StatsCard from "./components/ui/StatsCard";

const SUPPORTED_LANGUAGES = {
  python: { label: "Python", extension: ".py", mode: "python" },
  javascript: { label: "JavaScript", extension: ".js", mode: "javascript" },
  java: { label: "Java", extension: ".java", mode: "java" },
};

function App() {
  const [code, setCode] = useState("");
  const [language, setLanguage] = useState("python");
  const [filename, setFilename] = useState("example.py");
  const [repoUrl, setRepoUrl] = useState("");
  const [branch, setBranch] = useState("main");
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("editor");
  const [inputMode, setInputMode] = useState("code"); // 'code' or 'repo'
  const [progress, setProgress] = useState(0);
  const [analysisStats, setAnalysisStats] = useState(null);
  const fileInputRef = useRef(null);

  const sampleCode = useMemo(
    () => ({
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
}`,
    }),
    []
  );

  React.useEffect(() => {
    setCode(sampleCode[language]);
    setFilename(`example${SUPPORTED_LANGUAGES[language].extension}`);
  }, [language, sampleCode]);

  const analyzeCode = async () => {
    // Input validation
    if (inputMode === "code") {
      if (!code.trim()) {
        setError("Please enter some code to analyze");
        return;
      }
      if (code.length > 100000) {
        setError("Code is too long. Maximum 100,000 characters allowed.");
        return;
      }
    } else {
      if (!repoUrl.trim()) {
        setError("Please enter a GitHub repository URL");
        return;
      }
      
      // Basic URL validation
      const urlPattern = /^https:\/\/github\.com\/[\w\-\.]+\/[\w\-\.]+/;
      if (!urlPattern.test(repoUrl) && !repoUrl.includes('/')) {
        setError("Please enter a valid GitHub repository URL (e.g., https://github.com/owner/repo)");
        return;
      }
    }

    setLoading(true);
    setError(null);
    setProgress(0);
    setAnalysisStats(null);

    // Simulate progress for better UX
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev < 90) return prev + Math.random() * 10;
        return prev;
      });
    }, 500);

    try {
      let response;
      const startTime = Date.now();

      if (inputMode === "code") {
        setProgress(20);
        response = await axios.post("/api/analyze", {
          code,
          language,
          filename,
        });
      } else {
        setProgress(20);
        response = await axios.post("/api/analyze-repo", {
          repo_url: repoUrl,
          branch: branch || "main",
          max_files: 50,
        });
      }

      const endTime = Date.now();
      setProgress(100);
      
      // Set analysis stats
      const stats = {
        processingTime: (endTime - startTime) / 1000,
        endpointCount: response.data.analysis?.api_endpoints?.length || 0,
        securityIssues: response.data.analysis?.security_recommendations?.length || 0,
        optimizations: response.data.analysis?.optimization_suggestions?.length || 0,
      };
      setAnalysisStats(stats);

      setAnalysis(response.data);
      setActiveTab("results");
      
      // Show success notification
      setTimeout(() => {
        setProgress(0);
      }, 2000);
      
    } catch (err) {
      console.error("Analysis error:", err);
      
      // Enhanced error handling
      if (err.response) {
        const { status, data } = err.response;
        
        switch (status) {
          case 400:
            setError(data.detail || "Invalid request. Please check your input.");
            break;
          case 401:
            setError("Authentication failed. Please check your API keys.");
            break;
          case 422:
            if (data.errors && Array.isArray(data.errors)) {
              const errorMessages = data.errors.map(e => e.msg).join(", ");
              setError(`Validation error: ${errorMessages}`);
            } else {
              setError(data.detail || "Invalid input data.");
            }
            break;
          case 429:
            setError("Rate limit exceeded. Please wait a moment before trying again.");
            break;
          case 500:
            setError("Server error. Please try again later or contact support.");
            break;
          default:
            setError(data.detail || `Error ${status}: Analysis failed`);
        }
      } else if (err.request) {
        setError("Network error. Please check your connection and try again.");
      } else {
        setError("An unexpected error occurred. Please try again.");
      }
    } finally {
      clearInterval(progressInterval);
      setLoading(false);
      setProgress(0);
    }
  };

  const uploadFiles = async (event) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    // Validate files before upload
    const maxFiles = 10;
    const maxSize = 1024 * 1024; // 1MB
    const allowedExtensions = ['.py', '.js', '.jsx', '.ts', '.tsx', '.java'];

    if (files.length > maxFiles) {
      setError(`Too many files. Maximum ${maxFiles} files allowed.`);
      return;
    }

    // Validate each file
    for (let file of files) {
      if (file.size > maxSize) {
        setError(`File "${file.name}" is too large. Maximum 1MB per file.`);
        return;
      }

      const ext = '.' + file.name.split('.').pop().toLowerCase();
      if (!allowedExtensions.includes(ext)) {
        setError(`File "${file.name}" has unsupported extension. Allowed: ${allowedExtensions.join(', ')}`);
        return;
      }
    }

    setLoading(true);
    setError(null);
    setProgress(0);

    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev < 80) return prev + Math.random() * 10;
        return prev;
      });
    }, 300);

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }

    try {
      const startTime = Date.now();
      
      const response = await axios.post("/api/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        onUploadProgress: (progressEvent) => {
          const uploadProgress = Math.round((progressEvent.loaded * 80) / progressEvent.total);
          setProgress(uploadProgress);
        },
      });

      const endTime = Date.now();
      setProgress(100);

      const { results, successful_analyses, total_files } = response.data;
      
      // Set analysis stats
      const totalEndpoints = results.reduce((sum, r) => sum + (r.endpoints_count || 0), 0);
      const stats = {
        processingTime: (endTime - startTime) / 1000,
        endpointCount: totalEndpoints,
        filesProcessed: total_files,
        successfulFiles: successful_analyses,
      };
      setAnalysisStats(stats);

      // Show results for the first successful analysis
      const firstSuccess = results.find((r) => r.success);
      if (firstSuccess) {
        setAnalysis({
          success: true,
          analysis: firstSuccess.analysis,
          generated_api_path: firstSuccess.api_path,
          message: `Analyzed ${successful_analyses}/${total_files} files successfully`,
          uploadResults: results, // Store all results for detailed view
        });
        setActiveTab("results");
      } else {
        // Show detailed error messages
        const errors = results.filter(r => !r.success).map(r => `${r.filename}: ${r.error}`);
        setError(`No files could be analyzed successfully:\n${errors.join('\n')}`);
      }

      // Clear file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }

    } catch (err) {
      console.error("Upload error:", err);
      
      if (err.response?.status === 413) {
        setError("Files too large. Please reduce file sizes and try again.");
      } else if (err.response?.status === 400) {
        setError(err.response.data.detail || "Invalid files. Please check file types and sizes.");
      } else {
        setError(err.response?.data?.detail || "Error uploading files. Please try again.");
      }
    } finally {
      clearInterval(progressInterval);
      setLoading(false);
      setTimeout(() => setProgress(0), 2000);
    }
  };

  const downloadAPI = async () => {
    if (!analysis?.generated_api_path) return;

    try {
      const projectName = analysis.generated_api_path.split("/").pop();
      const response = await axios.get(`/download/${projectName}`, {
        responseType: "blob",
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `${projectName}.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError("Error downloading API");
    }
  };

  const generateSwaggerSpec = () => {
    if (!analysis?.analysis?.api_endpoints) return null;

    const spec = {
      openapi: "3.0.0",
      info: {
        title: "Generated API",
        version: "1.0.0",
        description: "Auto-generated API from source code analysis",
      },
      paths: {},
    };

    analysis.analysis.api_endpoints.forEach((endpoint) => {
      const path = endpoint.endpoint_path;
      const method = endpoint.http_method.toLowerCase();

      if (!spec.paths[path]) {
        spec.paths[path] = {};
      }

      spec.paths[path][method] = {
        summary: endpoint.description,
        parameters:
          endpoint.parameters?.map((param) => ({
            name: param.name,
            in: "query",
            required: !param.default,
            schema: {
              type: param.type || "string",
            },
          })) || [],
        responses: {
          200: {
            description: "Success",
            content: {
              "application/json": {
                schema: {
                  type: "object",
                },
              },
            },
          },
        },
      };

      if (endpoint.needs_auth) {
        spec.paths[path][method].security = [{ bearerAuth: [] }];
      }
    });

    if (analysis.analysis.api_endpoints.some((ep) => ep.needs_auth)) {
      spec.components = {
        securitySchemes: {
          bearerAuth: {
            type: "http",
            scheme: "bearer",
            bearerFormat: "JWT",
          },
        },
      };
    }

    return spec;
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="flex">
        <Sidebar active={activeTab} onChange={setActiveTab} />
        <div className="flex min-h-screen flex-1 flex-col">
          <Topbar
            onUploadClick={() => fileInputRef.current?.click()}
            onAnalyze={analyzeCode}
            analyzing={loading}
            inputMode={inputMode}
            setInputMode={setInputMode}
          />
          <main className="mx-auto w-full max-w-7xl flex-1 p-4 md:p-6">
            <div className="mb-4 rounded-lg border bg-card p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-2xl font-bold tracking-tight">
                    Code2API
                  </h1>
                  <p className="text-sm text-muted-foreground">
                    AI-powered system that converts source code into APIs
                  </p>
                </div>
              </div>
            </div>

            {activeTab === "editor" && (
              <div className="space-y-4">
                {/* Progress Bar */}
                {loading && progress > 0 && (
                  <div className="rounded-lg border bg-card p-4">
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-sm font-medium">
                        {inputMode === "code" ? "Analyzing Code..." : "Analyzing Repository..."}
                      </span>
                      <span className="text-sm text-gray-500">{Math.round(progress)}%</span>
                    </div>
                    <ProgressBar value={progress} variant="default" />
                  </div>
                )}

                {/* Analysis Stats */}
                {analysisStats && !loading && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <StatsCard
                      title="Processing Time"
                      value={`${analysisStats.processingTime.toFixed(1)}s`}
                      icon="⏱️"
                      variant="info"
                    />
                    <StatsCard
                      title="API Endpoints"
                      value={analysisStats.endpointCount}
                      icon="🔗"
                      variant="success"
                    />
                    <StatsCard
                      title="Security Issues"
                      value={analysisStats.securityIssues}
                      icon="🔒"
                      variant={analysisStats.securityIssues > 0 ? "warning" : "success"}
                    />
                    <StatsCard
                      title="Optimizations"
                      value={analysisStats.optimizations}
                      icon="⚡"
                      variant="info"
                    />
                  </div>
                )}

                {inputMode === "code" ? (
                  <EditorPanel
                    language={language}
                    setLanguage={setLanguage}
                    filename={filename}
                    setFilename={setFilename}
                    fileInputRef={fileInputRef}
                    uploadFiles={uploadFiles}
                    analyzing={loading}
                    code={code}
                    setCode={setCode}
                    onAnalyze={analyzeCode}
                  />
                ) : (
                  <RepoPanel
                    repoUrl={repoUrl}
                    setRepoUrl={setRepoUrl}
                    branch={branch}
                    setBranch={setBranch}
                    analyzing={loading}
                    onAnalyze={analyzeCode}
                  />
                )}

                {/* Enhanced Error Display */}
                {error && (
                  <Alert 
                    variant="error" 
                    title="Analysis Error"
                    onClose={() => setError(null)}
                  >
                    <div className="whitespace-pre-line">{error}</div>
                    <div className="mt-2 text-xs opacity-75">
                      If this error persists, please check your input or try again later.
                    </div>
                  </Alert>
                )}

                {/* Loading Overlay */}
                {loading && (
                  <div className="rounded-lg border bg-card p-8">
                    <LoadingSpinner 
                      size="lg" 
                      text={inputMode === "code" ? "Analyzing your code..." : "Analyzing repository..."}
                    />
                  </div>
                )}
              </div>
            )}

            {activeTab === "results" && analysis && (
              <ResultsPanel analysis={analysis} onDownload={downloadAPI} />
            )}

            {activeTab === "swagger" && analysis?.analysis?.api_endpoints && (
              <div className="rounded-lg border bg-card p-2">
                <SwaggerUI spec={generateSwaggerSpec()} />
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}

export default App;
