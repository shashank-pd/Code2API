/**
 * Groq API Usage Statistics Component
 * Shows rate limits, usage, and performance metrics
 */

import React, { useState, useEffect } from "react";
import { apiService } from "../services/api";

const GroqUsageStats = () => {
  const [stats, setStats] = useState({
    rateLimit: null,
    usage: null,
    performance: null,
    lastUpdated: null,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchUsageStats = async () => {
    setLoading(true);
    setError(null);

    try {
      // Make a test request to get rate limit headers
      const response = await apiService.groqHealthCheck();

      // Extract rate limit information from headers
      const headers = response.headers;
      const rateLimit = {
        requestsPerDay: headers["x-ratelimit-limit-requests"] || "Unknown",
        tokensPerMinute: headers["x-ratelimit-limit-tokens"] || "Unknown",
        remainingRequests:
          headers["x-ratelimit-remaining-requests"] || "Unknown",
        remainingTokens: headers["x-ratelimit-remaining-tokens"] || "Unknown",
        resetRequests: headers["x-ratelimit-reset-requests"] || "Unknown",
        resetTokens: headers["x-ratelimit-reset-tokens"] || "Unknown",
      };

      // Performance metrics from response
      const performance = {
        responseTime: response.config?.timeout || "N/A",
        statusCode: response.status,
        timestamp: new Date().toISOString(),
      };

      setStats({
        rateLimit,
        performance,
        lastUpdated: new Date().toLocaleTimeString(),
      });
    } catch (err) {
      setError(`Failed to fetch usage stats: ${err.message}`);
      console.error("Error fetching Groq usage stats:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsageStats();
  }, []);

  const formatNumber = (value) => {
    if (!value || value === "Unknown") return "N/A";
    return parseInt(value).toLocaleString();
  };

  const getUsagePercentage = (remaining, limit) => {
    if (
      !remaining ||
      !limit ||
      remaining === "Unknown" ||
      limit === "Unknown"
    ) {
      return 0;
    }
    const used = parseInt(limit) - parseInt(remaining);
    return Math.round((used / parseInt(limit)) * 100);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border p-4 mb-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Groq API Usage & Limits
        </h3>
        <button
          onClick={fetchUsageStats}
          disabled={loading}
          className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Updating..." : "Refresh"}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}

      {stats.rateLimit && (
        <div className="space-y-4">
          {/* Daily Requests */}
          <div className="border rounded-md p-3">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">
                Daily Requests
              </span>
              <span className="text-sm text-gray-500">
                {formatNumber(stats.rateLimit.remainingRequests)} /{" "}
                {formatNumber(stats.rateLimit.requestsPerDay)} remaining
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{
                  width: `${getUsagePercentage(
                    stats.rateLimit.remainingRequests,
                    stats.rateLimit.requestsPerDay
                  )}%`,
                }}
              ></div>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Resets in: {stats.rateLimit.resetRequests}
            </div>
          </div>

          {/* Tokens Per Minute */}
          <div className="border rounded-md p-3">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">
                Tokens Per Minute
              </span>
              <span className="text-sm text-gray-500">
                {formatNumber(stats.rateLimit.remainingTokens)} /{" "}
                {formatNumber(stats.rateLimit.tokensPerMinute)} remaining
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-600 h-2 rounded-full transition-all duration-300"
                style={{
                  width: `${getUsagePercentage(
                    stats.rateLimit.remainingTokens,
                    stats.rateLimit.tokensPerMinute
                  )}%`,
                }}
              ></div>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Resets in: {stats.rateLimit.resetTokens}
            </div>
          </div>

          {/* Performance Metrics */}
          {stats.performance && (
            <div className="border rounded-md p-3">
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                Performance
              </h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Status:</span>
                  <span
                    className={`ml-2 font-medium ${
                      stats.performance.statusCode === 200
                        ? "text-green-600"
                        : "text-red-600"
                    }`}
                  >
                    {stats.performance.statusCode === 200 ? "Healthy" : "Error"}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Model:</span>
                  <span className="ml-2 font-medium text-gray-900">
                    openai/gpt-oss-120b
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Tips */}
          <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
            <h4 className="text-sm font-medium text-blue-800 mb-1">
              Rate Limit Tips
            </h4>
            <ul className="text-xs text-blue-700 space-y-1">
              <li>• Free tier: 30 RPM, 6K TPM</li>
              <li>• Batching reduces request count</li>
              <li>• Structured outputs ensure reliable parsing</li>
              <li>• Lower temperature (0.1) improves consistency</li>
            </ul>
          </div>

          {stats.lastUpdated && (
            <div className="text-xs text-gray-500 pt-2 border-t">
              Last updated: {stats.lastUpdated}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default GroqUsageStats;
