import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const isDev = mode === 'development';
  const apiTarget = process.env.VITE_API_URL || "http://localhost:8000";
  
  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      port: 3000,
      host: true, // Allow external connections
      proxy: {
        "/api": {
          target: apiTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ""),
          configure: (proxy, options) => {
            proxy.on('error', (err, req, res) => {
              console.log('Proxy error:', err);
            });
            proxy.on('proxyReq', (proxyReq, req, res) => {
              console.log('Proxying request:', req.method, req.url, '→', options.target + req.url);
            });
          },
        },
        "/download": {
          target: apiTarget,
          changeOrigin: true,
        },
      },
    },
  build: {
    outDir: "dist",
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom"],
          monaco: ["monaco-editor", "@monaco-editor/react"],
          swagger: ["swagger-ui-react"],
          utils: ["axios", "clsx", "tailwind-merge"],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
  };
});
