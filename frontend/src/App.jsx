import React, { useState, useRef, useMemo } from "react";
import axios from "axios";
import SwaggerUI from "swagger-ui-react";
import "swagger-ui-react/swagger-ui.css";
import Sidebar from "./components/layout/Sidebar";
import Topbar from "./components/layout/Topbar";
import EditorPanel from "./components/panels/EditorPanel";
import RepoPanel from "./components/panels/RepoPanel";
import ResultsPanel from "./components/panels/ResultsPanel";

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
                {error && (
                  <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-300">
                    {error}
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
