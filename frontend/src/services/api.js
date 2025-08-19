/**
 * API Configuration and Service
 * Centralized API calls for the Code2API frontend
 */

import axios from "axios";

// API Configuration
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const API_TIMEOUT = 30000; // 30 seconds

// Create axios instance with default configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor for adding auth tokens if needed
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("authToken");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for handling common errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("authToken");
      // Could redirect to login here
    }
    return Promise.reject(error);
  }
);

// API Service functions
export const apiService = {
  // Health check
  healthCheck: () => apiClient.get("/health"),

  // Repository analysis workflow
  runWorkflow: (repoUrl, branch = "main") =>
    apiClient.post("/api/run-workflow", { repo_url: repoUrl, branch }),

  // Repository analysis - simplified for new flow
  analyzeRepository: async (repoUrl, branch = "main") => {
    const response = await apiClient.post("/api/run-workflow", {
      repo_url: repoUrl,
      branch,
    });
    return response.data;
  },

  // Generate API from analysis results
  generateAPI: async (analysisResults, projectName) => {
    const response = await apiClient.post("/api/generate-api", {
      analysis_data: analysisResults,
      project_name: projectName,
      include_auth: true,
      include_tests: true,
      include_docs: true,
    });
    return response.data;
  },

  // Start generated API server
  startGeneratedAPI: async (apiPath) => {
    const response = await apiClient.post("/api/start-generated-api", {
      api_path: apiPath,
    });
    return response.data;
  },

  // Code analysis using Groq
  analyzeCode: (code, language = "python") =>
    apiClient.post("/api/groq/analyze-code", { code, language }),

  // Generate documentation
  generateDocumentation: (endpoints) =>
    apiClient.post("/api/groq/generate-documentation", { endpoints }),

  // Generate test cases
  generateTests: (endpointInfo) =>
    apiClient.post("/api/groq/generate-tests", { endpoint_info: endpointInfo }),

  // Get Groq models
  getGroqModels: () => apiClient.get("/api/groq/models"),

  // Groq health check
  groqHealthCheck: () => apiClient.get("/api/groq/health"),

  // Get usage examples
  getUsageExamples: () => apiClient.get("/api/groq/usage-examples"),

  // File upload (if needed)
  uploadFiles: (formData) =>
    apiClient.post("/api/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),

  // Get workflow status
  getWorkflowStatus: (workflowId) =>
    apiClient.get(`/api/workflow/${workflowId}/status`),

  // Download generated API
  downloadGeneratedAPI: (workflowId) =>
    apiClient.get(`/api/workflow/${workflowId}/download`, {
      responseType: "blob",
    }),
};

// Export the configured axios instance for custom calls
export { apiClient };

// Export API base URL for reference
export { API_BASE_URL };

export default apiService;
