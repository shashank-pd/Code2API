/**
 * Loading Component with Progress Indication
 * Shows different stages of the analysis process
 */

import React from "react";

const LoadingProgress = ({ loading, inputMode, repoUrl }) => {
  if (!loading) return null;

  const getLoadingMessage = () => {
    if (inputMode === "code") {
      return {
        title: "🔍 Analyzing Code",
        steps: [
          "Parsing source code...",
          "Extracting functions...",
          "AI-powered analysis...",
          "Generating API endpoints...",
        ],
      };
    } else {
      return {
        title: "📦 Analyzing Repository",
        steps: [
          `Cloning repository: ${repoUrl}`,
          "Scanning source files...",
          "Extracting functions and classes...",
          "AI-powered code analysis...",
          "Generating API endpoints...",
          "Creating documentation...",
          "Building project structure...",
        ],
      };
    }
  };

  const { title, steps } = getLoadingMessage();

  return (
    <div className="loading-overlay">
      <div className="loading-container">
        <div className="loading-header">
          <div className="spinner"></div>
          <h3>{title}</h3>
        </div>

        <div className="loading-steps">
          {steps.map((step, index) => (
            <div key={index} className="loading-step">
              <div className="step-icon">{index < 2 ? "✅" : "⏳"}</div>
              <span className={index < 2 ? "completed" : "pending"}>
                {step}
              </span>
            </div>
          ))}
        </div>

        <div className="loading-progress-bar">
          <div className="progress-fill"></div>
        </div>

        <p className="loading-note">
          {inputMode === "repo"
            ? "This may take a few minutes for large repositories..."
            : "Analyzing your code..."}
        </p>
      </div>
    </div>
  );
};

export default LoadingProgress;
