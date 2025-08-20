import React from 'react';
import { motion } from 'framer-motion';

const NeuralBackground = () => {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden bg-gradient-to-br from-slate-950 via-purple-950/30 to-slate-900">
      
      {/* Neural Network Nodes - AI Brain Effect */}
      {Array.from({ length: 15 }).map((_, i) => (
        <motion.div
          key={`neural-node-${i}`}
          className="absolute w-3 h-3 rounded-full"
          style={{
            left: `${10 + (i * 6)}%`,
            top: `${15 + Math.sin(i * 0.8) * 40}%`,
            background: `radial-gradient(circle, rgba(34, 197, 94, 0.9) 0%, rgba(34, 197, 94, 0.1) 100%)`,
            boxShadow: '0 0 15px rgba(34, 197, 94, 0.7), 0 0 30px rgba(34, 197, 94, 0.3)',
          }}
          animate={{
            scale: [1, 2, 1],
            opacity: [0.7, 1, 0.7],
            boxShadow: [
              '0 0 15px rgba(34, 197, 94, 0.7)',
              '0 0 30px rgba(34, 197, 94, 1), 0 0 50px rgba(34, 197, 94, 0.5)',
              '0 0 15px rgba(34, 197, 94, 0.7)'
            ],
          }}
          transition={{
            duration: 1.5 + Math.random() * 1,
            repeat: Infinity,
            ease: "easeInOut",
            delay: i * 0.2,
          }}
        />
      ))}

      {/* Plasma Energy Waves - Rotating Plasma */}
      {Array.from({ length: 5 }).map((_, i) => (
        <motion.div
          key={`plasma-${i}`}
          className="absolute rounded-full"
          style={{
            width: `${200 + i * 100}px`,
            height: `${200 + i * 100}px`,
            left: `${20 + i * 10}%`,
            top: `${15 + i * 8}%`,
            background: `conic-gradient(from ${i * 72}deg, 
              rgba(168, 85, 247, 0.4) 0deg, 
              rgba(59, 130, 246, 0.3) 72deg, 
              rgba(34, 197, 94, 0.3) 144deg, 
              rgba(245, 101, 101, 0.3) 216deg,
              rgba(251, 191, 36, 0.3) 288deg,
              rgba(168, 85, 247, 0.4) 360deg)`,
            filter: 'blur(60px)',
            opacity: 0.3,
          }}
          animate={{
            rotate: [0, 360],
            scale: [1, 1.5, 1],
            opacity: [0.2, 0.5, 0.2],
          }}
          transition={{
            duration: 15 + i * 5,
            repeat: Infinity,
            ease: "linear",
          }}
        />
      ))}

      {/* Digital Rain Effect - Matrix Style */}
      {Array.from({ length: 12 }).map((_, i) => (
        <motion.div
          key={`rain-${i}`}
          className="absolute w-1 opacity-60"
          style={{
            left: `${5 + i * 8}%`,
            top: '-20%',
            height: '200px',
            background: `linear-gradient(to bottom, 
              transparent 0%, 
              rgba(34, 197, 94, 0.8) 20%, 
              rgba(34, 197, 94, 0.4) 50%, 
              rgba(34, 197, 94, 0.1) 80%, 
              transparent 100%)`,
            filter: 'blur(1px)',
            boxShadow: '0 0 10px rgba(34, 197, 94, 0.5)',
          }}
          animate={{
            y: ['0vh', '120vh'],
            opacity: [0, 1, 0],
            scaleY: [0.5, 2, 0.5],
          }}
          transition={{
            duration: 3 + Math.random() * 2,
            repeat: Infinity,
            ease: "linear",
            delay: i * 0.5,
          }}
        />
      ))}

      {/* Quantum Field Visualization */}
      <motion.div 
        className="absolute inset-0 opacity-10"
        style={{
          backgroundImage: `
            radial-gradient(circle at 25% 25%, rgba(34, 197, 94, 0.3) 0%, transparent 50%),
            radial-gradient(circle at 75% 75%, rgba(59, 130, 246, 0.3) 0%, transparent 50%),
            radial-gradient(circle at 75% 25%, rgba(168, 85, 247, 0.3) 0%, transparent 50%),
            radial-gradient(circle at 25% 75%, rgba(245, 101, 101, 0.3) 0%, transparent 50%)
          `,
        }}
        animate={{
          opacity: [0.05, 0.2, 0.05],
          scale: [1, 1.1, 1],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

    </div>
  );
};

export default NeuralBackground;
