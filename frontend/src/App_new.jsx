import React, { useState } from "react";
import apiService from "./services/api";

function App() {
  const [repoUrl, setRepoUrl] = useState("");
  const [branch, setBranch] = useState("main");
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [generatedApiPath, setGeneratedApiPath] = useState(null);
  const [apiRunning, setApiRunning] = useState(false);

  const handleAnalyzeRepo = async () => {
    if (!repoUrl.trim()) {
      setError("Please enter a repository URL");
      return;
    }

    setLoading(true);
    setError(null);
    setAnalysis(null);

    try {
      const result = await apiService.analyzeRepository(repoUrl, branch);
      setAnalysis(result);
      
      // Auto-generate API after successful analysis
      if (result?.functions_analyzed > 0) {
        const projectName = `${repoUrl.split('/').pop()}_api_${new Date().toISOString().slice(0,10).replace(/-/g,'')}`;
        const generatedApi = await apiService.generateAPI(result, projectName);
        setGeneratedApiPath(generatedApi.api_path);
      }
    } catch (err) {
      setError(err.message || "Failed to analyze repository");
    } finally {
      setLoading(false);
    }
  };

  const handleRunGeneratedAPI = async () => {
    if (!generatedApiPath) return;
    
    try {
      setApiRunning(true);
      // Start the generated API server
      await apiService.startGeneratedAPI(generatedApiPath);
      
      // Open the API docs in a new tab
      window.open('http://localhost:8001/docs', '_blank');
    } catch (err) {
      setError("Failed to start generated API");
    } finally {
      setApiRunning(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Code2API</h1>
              <p className="text-gray-600 mt-1">Transform any repository into a REST API instantly</p>
            </div>
            <div className="text-sm text-gray-500">
              AI-Powered Code Analysis
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Repository Input Section */}
        <div className="bg-white rounded-lg shadow-sm border p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Analyze Repository
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Repository URL
              </label>
              <input
                type="url"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/username/repository"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loading}
              />
            </div>
            
            <div className="flex items-center gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Branch
                </label>
                <input
                  type="text"
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  placeholder="main"
                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={loading}
                />
              </div>
              
              <div className="flex-1 flex justify-end items-end">
                <button
                  onClick={handleAnalyzeRepo}
                  disabled={loading || !repoUrl.trim()}
                  className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                      Analyzing...
                    </>
                  ) : (
                    'Analyze & Generate API'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">{error}</div>
              </div>
            </div>
          </div>
        )}

        {/* Loading Indicator */}
        {loading && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent mr-4"></div>
              <div>
                <h3 className="text-lg font-medium text-blue-900">Analyzing Repository</h3>
                <p className="text-blue-700">Please wait while we analyze your code and generate the API...</p>
              </div>
            </div>
          </div>
        )}

        {/* Results Section */}
        {analysis && (
          <div className="space-y-6">
            {/* Analysis Summary */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Analysis Results
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-green-50 rounded-lg p-4">
                  <h3 className="text-lg font-medium text-green-900">Functions Found</h3>
                  <p className="text-2xl font-bold text-green-600">{analysis.functions_analyzed || 0}</p>
                </div>
                
                <div className="bg-blue-50 rounded-lg p-4">
                  <h3 className="text-lg font-medium text-blue-900">API Endpoints</h3>
                  <p className="text-2xl font-bold text-blue-600">{analysis.api_endpoints?.length || 0}</p>
                </div>
                
                <div className="bg-purple-50 rounded-lg p-4">
                  <h3 className="text-lg font-medium text-purple-900">Language</h3>
                  <p className="text-lg font-semibold text-purple-600">{analysis.language || 'Unknown'}</p>
                </div>
              </div>

              {/* Generated API Actions */}
              {generatedApiPath && (
                <div className="border-t pt-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">Generated API Ready!</h3>
                      <p className="text-gray-600">Your API has been generated and is ready to run.</p>
                    </div>
                    <button
                      onClick={handleRunGeneratedAPI}
                      disabled={apiRunning}
                      className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
                    >
                      {apiRunning ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                          Starting...
                        </>
                      ) : (
                        'View API Documentation'
                      )}
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* API Endpoints */}
            {analysis.api_endpoints && analysis.api_endpoints.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Generated API Endpoints
                </h2>
                
                <div className="space-y-4">
                  {analysis.api_endpoints.map((endpoint, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <span className={`px-2 py-1 text-xs font-semibold rounded ${{
                            'GET': 'bg-green-100 text-green-800',
                            'POST': 'bg-blue-100 text-blue-800',
                            'PUT': 'bg-yellow-100 text-yellow-800',
                            'DELETE': 'bg-red-100 text-red-800'
                          }[endpoint.http_method] || 'bg-gray-100 text-gray-800'}`}>
                            {endpoint.http_method}
                          </span>
                          <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                            {endpoint.endpoint_path}
                          </code>
                        </div>
                        <span className="text-sm text-gray-500">
                          {endpoint.function_name}
                        </span>
                      </div>
                      
                      <p className="text-gray-700 text-sm mb-2">
                        {endpoint.description}
                      </p>
                      
                      {endpoint.parameters && endpoint.parameters.length > 0 && (
                        <div className="text-xs text-gray-500">
                          Parameters: {endpoint.parameters.map(p => p.name).join(', ')}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Security & Optimization Notes */}
            {(analysis.security_recommendations?.length > 0 || analysis.optimization_suggestions?.length > 0) && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {analysis.security_recommendations?.length > 0 && (
                  <div className="bg-white rounded-lg shadow-sm border p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">
                      Security Recommendations
                    </h3>
                    <ul className="space-y-2 text-sm text-gray-700">
                      {analysis.security_recommendations.map((rec, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <span className="text-yellow-500 mt-0.5">⚠️</span>
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {analysis.optimization_suggestions?.length > 0 && (
                  <div className="bg-white rounded-lg shadow-sm border p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">
                      Optimization Suggestions
                    </h3>
                    <ul className="space-y-2 text-sm text-gray-700">
                      {analysis.optimization_suggestions.map((suggestion, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <span className="text-blue-500 mt-0.5">💡</span>
                          {suggestion}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
