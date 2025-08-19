/**
 * API Health Status Component
 * Shows the connection status with the backend API
 */

import React, { useState, useEffect } from "react";
import apiService from "../services/api";

const APIHealthStatus = () => {
  const [status, setStatus] = useState({
    backend: "unknown",
    groq: "unknown",
    lastChecked: null,
  });
  const [loading, setLoading] = useState(false);

  const checkHealth = async () => {
    setLoading(true);
    try {
      // Check main backend health
      const healthResponse = await apiService.healthCheck();
      const backendStatus =
        healthResponse.status === 200 ? "online" : "offline";

      // Check Groq service health
      let groqStatus = "unknown";
      try {
        const groqResponse = await apiService.groqHealthCheck();
        groqStatus = groqResponse.data.success ? "online" : "offline";
      } catch (groqError) {
        groqStatus = "offline";
      }

      setStatus({
        backend: backendStatus,
        groq: groqStatus,
        lastChecked: new Date().toLocaleTimeString(),
      });
    } catch (error) {
      setStatus({
        backend: "offline",
        groq: "unknown",
        lastChecked: new Date().toLocaleTimeString(),
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Only check health once on component mount
    checkHealth();
    // Remove the interval to stop continuous checking
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case "online":
        return "text-green-600";
      case "offline":
        return "text-red-600";
      default:
        return "text-gray-500";
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "online":
        return "●";
      case "offline":
        return "●";
      default:
        return "○";
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border p-4 mb-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">API Status</h3>
        <button
          onClick={checkHealth}
          disabled={loading}
          className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Checking..." : "Refresh"}
        </button>
      </div>

      <div className="mt-3 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Backend API</span>
          <span
            className={`text-sm font-medium ${getStatusColor(status.backend)}`}
          >
            {getStatusIcon(status.backend)} {status.backend}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Groq AI Service</span>
          <span
            className={`text-sm font-medium ${getStatusColor(status.groq)}`}
          >
            {getStatusIcon(status.groq)} {status.groq}
          </span>
        </div>

        {status.lastChecked && (
          <div className="text-xs text-gray-500 pt-2 border-t">
            Last checked: {status.lastChecked}
          </div>
        )}
      </div>
    </div>
  );
};

export default APIHealthStatus;
