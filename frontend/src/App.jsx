import React, { useState, useRef, useMemo } from "react";
import axios from "axios";
import MonacoEditor from "@monaco-editor/react";
import SwaggerUI from "swagger-ui-react";
import "swagger-ui-react/swagger-ui.css";
import { cn } from "./lib/utils";

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
    if (inputMode === "code") {
      if (!code.trim()) {
        setError("Please enter some code to analyze");
        return;
      }
    } else {
      if (!repoUrl.trim()) {
        setError("Please enter a GitHub repository URL");
        return;
      }
    }

    setLoading(true);
    setError(null);

    try {
      let response;

      if (inputMode === "code") {
        response = await axios.post("/api/analyze", {
          code,
          language,
          filename,
        });
      } else {
        response = await axios.post("/api/analyze-repo", {
          repo_url: repoUrl,
          branch: branch || "main",
          max_files: 50,
        });
      }

      setAnalysis(response.data);
      setActiveTab("results");
    } catch (err) {
      setError(err.response?.data?.detail || "Error analyzing code");
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
      formData.append("files", files[i]);
    }

    try {
      const response = await axios.post("/api/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      // Show results for the first successful analysis
      const firstSuccess = response.data.results.find((r) => r.success);
      if (firstSuccess) {
        setAnalysis({
          success: true,
          analysis: firstSuccess.analysis,
          generated_api_path: firstSuccess.api_path,
          message: `Analyzed ${response.data.results.length} files`,
        });
        setActiveTab("results");
      } else {
        setError("No files could be analyzed successfully");
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Error uploading files");
    } finally {
      setLoading(false);
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
    <div className="min-h-screen bg-gradient-to-br from-primary-600 via-purple-600 to-secondary-600 text-white">
      <header className="bg-black/10 p-8 text-center">
        <h1 className="text-5xl font-bold mb-2 drop-shadow-lg">🚀 Code2API</h1>
        <p className="text-xl opacity-90">
          AI-powered system that converts source code into APIs
        </p>
      </header>

      <div className="max-w-7xl mx-auto p-8">
        <div className="flex mb-8 bg-white/10 rounded-lg overflow-hidden shadow-lg">
          <button
            className={cn(
              "flex-1 py-4 px-6 text-lg font-medium transition-all duration-300",
              activeTab === "editor"
                ? "bg-white/20 text-white"
                : "hover:bg-white/10 text-white/80"
            )}
            onClick={() => setActiveTab("editor")}
          >
            Code Editor
          </button>
          <button
            className={cn(
              "flex-1 py-4 px-6 text-lg font-medium transition-all duration-300",
              activeTab === "results"
                ? "bg-white/20 text-white"
                : "hover:bg-white/10 text-white/80",
              !analysis && "opacity-50 cursor-not-allowed"
            )}
            onClick={() => setActiveTab("results")}
            disabled={!analysis}
          >
            Analysis Results
          </button>
          <button
            className={cn(
              "flex-1 py-4 px-6 text-lg font-medium transition-all duration-300",
              activeTab === "swagger"
                ? "bg-white/20 text-white"
                : "hover:bg-white/10 text-white/80",
              !analysis?.analysis?.api_endpoints &&
                "opacity-50 cursor-not-allowed"
            )}
            onClick={() => setActiveTab("swagger")}
            disabled={!analysis?.analysis?.api_endpoints}
          >
            API Documentation
          </button>
        </div>

        {activeTab === "editor" && (
          <div className="space-y-6">
            <div className="flex gap-4 bg-white/10 rounded-lg p-4">
              <button
                className={cn(
                  "flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all duration-300",
                  inputMode === "code"
                    ? "bg-white text-primary-600 shadow-lg"
                    : "bg-white/20 text-white hover:bg-white/30"
                )}
                onClick={() => setInputMode("code")}
              >
                📝 Code Editor
              </button>
              <button
                className={cn(
                  "flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all duration-300",
                  inputMode === "repo"
                    ? "bg-white text-primary-600 shadow-lg"
                    : "bg-white/20 text-white hover:bg-white/30"
                )}
                onClick={() => setInputMode("repo")}
              >
                📦 GitHub Repository
              </button>
            </div>

            {inputMode === "code" ? (
              <>
                <div className="bg-white/10 rounded-lg p-6 space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Language:
                      </label>
                      <select
                        value={language}
                        onChange={(e) => setLanguage(e.target.value)}
                        className="w-full p-3 rounded-lg bg-white/20 border border-white/30 text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-white/50"
                      >
                        {Object.entries(SUPPORTED_LANGUAGES).map(
                          ([key, lang]) => (
                            <option
                              key={key}
                              value={key}
                              className="text-gray-900"
                            >
                              {lang.label}
                            </option>
                          )
                        )}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Filename:
                      </label>
                      <input
                        type="text"
                        value={filename}
                        onChange={(e) => setFilename(e.target.value)}
                        className="w-full p-3 rounded-lg bg-white/20 border border-white/30 text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-white/50"
                      />
                    </div>

                    <div className="flex flex-col justify-end">
                      <input
                        type="file"
                        ref={fileInputRef}
                        multiple
                        accept=".py,.js,.jsx,.ts,.tsx,.java"
                        onChange={uploadFiles}
                        className="hidden"
                      />
                      <button
                        onClick={() => fileInputRef.current?.click()}
                        className="px-6 py-3 bg-white/20 hover:bg-white/30 text-white rounded-lg font-medium transition-all duration-300 border border-white/30"
                      >
                        Upload Files
                      </button>
                    </div>
                  </div>

                  <button
                    onClick={analyzeCode}
                    disabled={loading}
                    className={cn(
                      "w-full py-4 px-6 rounded-lg font-bold text-lg transition-all duration-300",
                      loading
                        ? "bg-gray-500 cursor-not-allowed"
                        : "bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600 transform hover:scale-105 shadow-lg"
                    )}
                  >
                    {loading ? "Analyzing..." : "Analyze Code"}
                  </button>
                </div>

                <div className="bg-white/10 rounded-lg p-4">
                  <MonacoEditor
                    height="500px"
                    language={SUPPORTED_LANGUAGES[language].mode}
                    value={code}
                    onChange={setCode}
                    theme="vs-dark"
                    options={{
                      minimap: { enabled: false },
                      fontSize: 14,
                      lineNumbers: "on",
                      roundedSelection: false,
                      scrollBeyondLastLine: false,
                      automaticLayout: true,
                    }}
                  />
                </div>
              </>
            ) : (
              <>
                <div className="bg-white/10 rounded-lg p-6 space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        GitHub Repository URL:
                      </label>
                      <input
                        type="text"
                        value={repoUrl}
                        onChange={(e) => setRepoUrl(e.target.value)}
                        placeholder="https://github.com/owner/repo or owner/repo"
                        className="w-full p-3 rounded-lg bg-white/20 border border-white/30 text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-white/50"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Branch:
                      </label>
                      <input
                        type="text"
                        value={branch}
                        onChange={(e) => setBranch(e.target.value)}
                        placeholder="main"
                        className="w-full p-3 rounded-lg bg-white/20 border border-white/30 text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-white/50"
                      />
                    </div>
                  </div>

                  <button
                    onClick={analyzeCode}
                    disabled={loading}
                    className={cn(
                      "w-full py-4 px-6 rounded-lg font-bold text-lg transition-all duration-300",
                      loading
                        ? "bg-gray-500 cursor-not-allowed"
                        : "bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600 transform hover:scale-105 shadow-lg"
                    )}
                  >
                    {loading ? "Analyzing Repository..." : "Analyze Repository"}
                  </button>
                </div>

                <div className="bg-white/10 rounded-lg p-6">
                  <h3 className="text-xl font-bold mb-4">
                    Try these example repositories:
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {[
                      { name: "🚀 fastapi/fastapi", url: "fastapi/fastapi" },
                      { name: "🌶️ pallets/flask", url: "pallets/flask" },
                      { name: "💻 microsoft/vscode", url: "microsoft/vscode" },
                      { name: "⚛️ facebook/react", url: "facebook/react" },
                    ].map((repo) => (
                      <button
                        key={repo.url}
                        className="p-4 bg-white/20 hover:bg-white/30 rounded-lg font-medium transition-all duration-300 border border-white/30"
                        onClick={() => setRepoUrl(repo.url)}
                      >
                        {repo.name}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}

            {error && (
              <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <span className="text-red-300 font-bold">⚠️ Error:</span>
                  <span className="text-red-100">{error}</span>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "results" && analysis && (
          <div className="space-y-6">
            <div className="flex justify-between items-center bg-white/10 rounded-lg p-6">
              <h2 className="text-3xl font-bold">Analysis Results</h2>
              {analysis.generated_api_path && (
                <button
                  onClick={downloadAPI}
                  className="px-6 py-3 bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600 text-white rounded-lg font-medium transition-all duration-300 shadow-lg transform hover:scale-105"
                >
                  Download Generated API
                </button>
              )}
            </div>

            {analysis.analysis?.repository_info && (
              <div className="bg-white/10 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  📦 Repository Information
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div className="bg-white/5 rounded-lg p-4">
                    <div className="text-sm text-white/70">Name</div>
                    <div className="font-bold">
                      {analysis.analysis.repository_info.name}
                    </div>
                  </div>
                  <div className="bg-white/5 rounded-lg p-4">
                    <div className="text-sm text-white/70">Language</div>
                    <div className="font-bold">
                      {analysis.analysis.repository_info.language || "Multiple"}
                    </div>
                  </div>
                  <div className="bg-white/5 rounded-lg p-4">
                    <div className="text-sm text-white/70">Stars</div>
                    <div className="font-bold">
                      ⭐ {analysis.analysis.repository_info.stars || 0}
                    </div>
                  </div>
                  <div className="bg-white/5 rounded-lg p-4">
                    <div className="text-sm text-white/70">Forks</div>
                    <div className="font-bold">
                      🍴 {analysis.analysis.repository_info.forks || 0}
                    </div>
                  </div>
                  <div className="bg-white/5 rounded-lg p-4">
                    <div className="text-sm text-white/70">Files Analyzed</div>
                    <div className="font-bold">
                      📄 {analysis.analysis.files_analyzed || 0}
                    </div>
                  </div>
                  <div className="bg-white/5 rounded-lg p-4 md:col-span-2 lg:col-span-1">
                    <div className="text-sm text-white/70">Description</div>
                    <div className="font-bold truncate">
                      {analysis.analysis.repository_info.description ||
                        "No description"}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {analysis.analysis?.statistics && (
              <div className="bg-white/10 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  📊 Code Statistics
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <div className="text-center bg-white/10 rounded-lg p-4">
                    <div className="text-3xl font-bold text-blue-300">
                      {analysis.analysis.statistics.total_files}
                    </div>
                    <div className="text-sm text-white/70">Total Files</div>
                  </div>
                  <div className="text-center bg-white/10 rounded-lg p-4">
                    <div className="text-3xl font-bold text-green-300">
                      {analysis.analysis.statistics.total_lines?.toLocaleString()}
                    </div>
                    <div className="text-sm text-white/70">Total Lines</div>
                  </div>
                  <div className="text-center bg-white/10 rounded-lg p-4">
                    <div className="text-3xl font-bold text-purple-300">
                      {
                        Object.keys(
                          analysis.analysis.statistics.languages || {}
                        ).length
                      }
                    </div>
                    <div className="text-sm text-white/70">Languages</div>
                  </div>
                  <div className="text-center bg-white/10 rounded-lg p-4">
                    <div className="text-3xl font-bold text-yellow-300">
                      {analysis.analysis.api_endpoints?.length || 0}
                    </div>
                    <div className="text-sm text-white/70">API Endpoints</div>
                  </div>
                </div>

                {analysis.analysis.statistics.languages && (
                  <div>
                    <h4 className="font-bold mb-3">Language Breakdown:</h4>
                    <div className="space-y-2">
                      {Object.entries(
                        analysis.analysis.statistics.languages
                      ).map(([lang, count]) => (
                        <div
                          key={lang}
                          className="flex justify-between items-center bg-white/5 rounded p-3"
                        >
                          <span className="font-medium">{lang}</span>
                          <span className="text-white/70">{count} files</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="bg-white/10 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4">API Endpoints</h3>
                <div className="space-y-3">
                  {analysis.analysis.api_endpoints?.map((endpoint, index) => (
                    <div
                      key={index}
                      className="bg-white/5 rounded-lg p-4 space-y-2"
                    >
                      <div className="flex items-center gap-3">
                        <span
                          className={cn(
                            "px-3 py-1 text-xs font-bold rounded-full",
                            endpoint.http_method.toLowerCase() === "get" &&
                              "bg-green-500",
                            endpoint.http_method.toLowerCase() === "post" &&
                              "bg-blue-500",
                            endpoint.http_method.toLowerCase() === "put" &&
                              "bg-yellow-500",
                            endpoint.http_method.toLowerCase() === "delete" &&
                              "bg-red-500"
                          )}
                        >
                          {endpoint.http_method}
                        </span>
                        <code className="text-sm font-mono text-blue-300">
                          {endpoint.endpoint_path}
                        </code>
                      </div>
                      <p className="text-sm text-white/80">
                        {endpoint.description}
                      </p>
                      <div className="flex gap-2">
                        {endpoint.needs_auth && (
                          <span className="px-2 py-1 text-xs bg-red-500/20 text-red-300 rounded">
                            🔒 Auth Required
                          </span>
                        )}
                        {endpoint.class_name && (
                          <span className="px-2 py-1 text-xs bg-purple-500/20 text-purple-300 rounded">
                            📦 {endpoint.class_name}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                  {!analysis.analysis.api_endpoints?.length && (
                    <div className="text-center text-white/60 py-8">
                      No API endpoints generated
                    </div>
                  )}
                </div>
              </div>

              <div className="bg-white/10 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4">
                  Security Recommendations
                </h3>
                <ul className="space-y-2">
                  {analysis.analysis.security_recommendations?.map(
                    (rec, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <span className="text-red-400 mt-1">•</span>
                        <span className="text-sm">{rec}</span>
                      </li>
                    )
                  )}
                  {!analysis.analysis.security_recommendations?.length && (
                    <li className="text-center text-white/60 py-8">
                      No security issues detected
                    </li>
                  )}
                </ul>
              </div>

              <div className="bg-white/10 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4">
                  Optimization Suggestions
                </h3>
                <ul className="space-y-2">
                  {analysis.analysis.optimization_suggestions?.map(
                    (sug, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">•</span>
                        <span className="text-sm">{sug}</span>
                      </li>
                    )
                  )}
                  {!analysis.analysis.optimization_suggestions?.length && (
                    <li className="text-center text-white/60 py-8">
                      No optimization suggestions
                    </li>
                  )}
                </ul>
              </div>
            </div>
          </div>
        )}

        {activeTab === "swagger" && analysis?.analysis?.api_endpoints && (
          <div className="bg-white rounded-lg">
            <SwaggerUI spec={generateSwaggerSpec()} />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
