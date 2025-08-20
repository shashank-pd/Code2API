import React from 'react';
import { motion } from 'framer-motion';

const CodeFlowBackground = () => {
  // Code snippets for different languages
  const codeSnippets = [
    'def generate_api():', 'function createAPI() {', 'public class API {',
    '@app.route("/api")', 'const express = require', 'import requests',
    'POST /api/generate', 'GET /api/docs', 'PUT /api/update',
    'Content-Type: application/json', '{"status": "success"}', 'HTTP/1.1 200 OK',
    'class CodeGenerator:', 'async function parse()', 'try { ... } catch',
    'npm install express', 'pip install fastapi', 'mvn clean install',
    '<endpoint>', '</response>', '{ "data": [...] }',
    'localhost:3000', 'swagger.json', 'API_KEY=secret'
  ];

  // API method badges
  const apiMethods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'];
  const statusCodes = ['200', '201', '400', '404', '500'];

  return (
    <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
      {/* Base gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-gray-900 to-slate-950" />
      
      {/* Animated code grid pattern */}
      <motion.div 
        className="absolute inset-0 opacity-5"
        style={{
          backgroundImage: `
            linear-gradient(rgba(34, 197, 94, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(34, 197, 94, 0.1) 1px, transparent 1px)
          `,
          backgroundSize: '50px 50px'
        }}
        animate={{
          backgroundPosition: ['0% 0%', '100% 100%']
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "linear"
        }}
      />

      {/* Floating code snippets */}
      {Array.from({ length: 25 }).map((_, i) => (
        <motion.div
          key={`code-${i}`}
          className="absolute text-xs font-mono text-green-400/70 whitespace-nowrap"
          style={{
            left: i < 12 ? `${Math.random() * 30}%` : `${70 + Math.random() * 30}%`, // Left 30% or Right 30%
            top: `${Math.random() * 100}%`,
            fontSize: `${0.6 + Math.random() * 0.4}rem`,
          }}
          initial={{
            opacity: 0,
            y: 100,
          }}
          animate={{
            opacity: [0, 0.8, 0],
            y: [100, -100],
            x: [0, Math.random() * 200 - 100],
          }}
          transition={{
            duration: 8 + Math.random() * 4,
            repeat: Infinity,
            delay: Math.random() * 5,
            ease: "linear"
          }}
        >
          {codeSnippets[Math.floor(Math.random() * codeSnippets.length)]}
        </motion.div>
      ))}

      {/* API Method badges floating */}
      {Array.from({ length: 15 }).map((_, i) => (
        <motion.div
          key={`method-${i}`}
          className="absolute text-xs font-bold px-2 py-1 rounded border"
          style={{
            left: i % 2 === 0 ? `${Math.random() * 25}%` : `${75 + Math.random() * 25}%`, // Left side (0-25%) or Right side (75-100%)
            top: `${Math.random() * 90}%`,
            backgroundColor: 
              apiMethods[i % apiMethods.length] === 'GET' ? 'rgba(34, 197, 94, 0.3)' :
              apiMethods[i % apiMethods.length] === 'POST' ? 'rgba(59, 130, 246, 0.3)' :
              apiMethods[i % apiMethods.length] === 'PUT' ? 'rgba(251, 191, 36, 0.3)' :
              apiMethods[i % apiMethods.length] === 'DELETE' ? 'rgba(239, 68, 68, 0.3)' :
              'rgba(168, 85, 247, 0.3)',
            borderColor:
              apiMethods[i % apiMethods.length] === 'GET' ? 'rgba(34, 197, 94, 0.6)' :
              apiMethods[i % apiMethods.length] === 'POST' ? 'rgba(59, 130, 246, 0.6)' :
              apiMethods[i % apiMethods.length] === 'PUT' ? 'rgba(251, 191, 36, 0.6)' :
              apiMethods[i % apiMethods.length] === 'DELETE' ? 'rgba(239, 68, 68, 0.6)' :
              'rgba(168, 85, 247, 0.6)',
            color:
              apiMethods[i % apiMethods.length] === 'GET' ? 'rgba(34, 197, 94, 0.9)' :
              apiMethods[i % apiMethods.length] === 'POST' ? 'rgba(59, 130, 246, 0.9)' :
              apiMethods[i % apiMethods.length] === 'PUT' ? 'rgba(251, 191, 36, 0.9)' :
              apiMethods[i % apiMethods.length] === 'DELETE' ? 'rgba(239, 68, 68, 0.9)' :
              'rgba(168, 85, 247, 0.9)',
          }}
          animate={{
            y: [0, -300],
            opacity: [0, 1, 0],
            rotate: [0, 360],
            scale: [0.8, 1.2, 0.8],
          }}
          transition={{
            duration: 6 + Math.random() * 3,
            repeat: Infinity,
            delay: Math.random() * 3,
            ease: "easeOut"
          }}
        >
          {apiMethods[i % apiMethods.length]}
        </motion.div>
      ))}

      {/* Status code indicators */}
      {Array.from({ length: 10 }).map((_, i) => (
        <motion.div
          key={`status-${i}`}
          className="absolute text-sm font-mono opacity-60"
          style={{
            left: i % 2 === 0 ? `${Math.random() * 25}%` : `${75 + Math.random() * 25}%`, // Sides only
            top: `${Math.random() * 95}%`,
            color: 
              statusCodes[i % statusCodes.length].startsWith('2') ? '#22c55e' :
              statusCodes[i % statusCodes.length].startsWith('4') ? '#f59e0b' :
              statusCodes[i % statusCodes.length].startsWith('5') ? '#ef4444' : '#6b7280',
          }}
          animate={{
            opacity: [0.3, 0.8, 0.3],
            scale: [1, 1.5, 1],
          }}
          transition={{
            duration: 3 + Math.random() * 2,
            repeat: Infinity,
            delay: Math.random() * 2,
          }}
        >
          {statusCodes[i % statusCodes.length]}
        </motion.div>
      ))}

      {/* Data flow streams */}
      {Array.from({ length: 8 }).map((_, i) => (
        <motion.div
          key={`stream-${i}`}
          className="absolute w-px h-20 bg-gradient-to-b from-transparent via-green-400/30 to-transparent"
          style={{
            left: `${10 + i * 11}%`,
            top: '0%',
          }}
          animate={{
            y: ['0vh', '120vh'],
            opacity: [0, 1, 0],
          }}
          transition={{
            duration: 3 + Math.random() * 2,
            repeat: Infinity,
            delay: i * 0.5,
            ease: "linear"
          }}
        />
      ))}

      <motion.div
        className="absolute bottom-10 left-10 text-green-400 font-mono text-sm opacity-60"
        animate={{
          opacity: [0.6, 0.6, 0, 0],
        }}
        transition={{
          duration: 1,
          repeat: Infinity,
        }}
      >
        $ generating-api |
      </motion.div>

      <motion.div
        className="absolute top-20 right-20 text-xs font-mono text-blue-400/20 whitespace-pre"
        animate={{
          opacity: [0.1, 0.3, 0.1],
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
        }}
      >
        {`{
  "api": {
    "version": "1.0",
    "endpoints": [...]
  }
}`}
      </motion.div>

      {/* Glowing accent lines */}
      <motion.div
        className="absolute top-1/3 left-0 w-full h-px bg-gradient-to-r from-transparent via-green-400/20 to-transparent"
        animate={{
          scaleX: [0, 1, 0],
          opacity: [0, 0.5, 0],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      
      <motion.div
        className="absolute bottom-1/3 left-0 w-full h-px bg-gradient-to-r from-transparent via-blue-400/20 to-transparent"
        animate={{
          scaleX: [0, 1, 0],
          opacity: [0, 0.5, 0],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          delay: 4,
          ease: "easeInOut"
        }}
      />

    </div>
  );
};

export default CodeFlowBackground;
