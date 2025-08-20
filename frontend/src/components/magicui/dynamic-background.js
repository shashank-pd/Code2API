import React from 'react';
import { motion } from 'framer-motion';

export const DynamicBackground = () => {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none">
      {/* Base Dark Layer */}
      <div className="absolute inset-0 bg-gradient-to-br from-gray-900 via-slate-900 to-black" />

      {/* Animated Gradient Mesh */}
      <motion.div 
        className="absolute inset-0 opacity-70"
        animate={{
          background: [
            'radial-gradient(800px circle at 20% 30%, rgba(120, 119, 198, 0.15), transparent 50%), radial-gradient(600px circle at 80% 20%, rgba(168, 85, 247, 0.1), transparent 50%), radial-gradient(400px circle at 40% 80%, rgba(59, 130, 246, 0.12), transparent 50%)',
            'radial-gradient(800px circle at 80% 70%, rgba(120, 119, 198, 0.15), transparent 50%), radial-gradient(600px circle at 20% 80%, rgba(168, 85, 247, 0.1), transparent 50%), radial-gradient(400px circle at 60% 20%, rgba(59, 130, 246, 0.12), transparent 50%)',
            'radial-gradient(800px circle at 50% 20%, rgba(120, 119, 198, 0.15), transparent 50%), radial-gradient(600px circle at 30% 70%, rgba(168, 85, 247, 0.1), transparent 50%), radial-gradient(400px circle at 80% 60%, rgba(59, 130, 246, 0.12), transparent 50%)',
            'radial-gradient(800px circle at 20% 30%, rgba(120, 119, 198, 0.15), transparent 50%), radial-gradient(600px circle at 80% 20%, rgba(168, 85, 247, 0.1), transparent 50%), radial-gradient(400px circle at 40% 80%, rgba(59, 130, 246, 0.12), transparent 50%)'
          ]
        }}
        transition={{
          duration: 25,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />

      {/* Floating Orbs with better performance */}
      {Array.from({ length: 6 }).map((_, i) => (
        <motion.div
          key={`orb-${i}`}
          className="absolute rounded-full blur-xl"
          style={{
            width: 150 + i * 50,
            height: 150 + i * 50,
            background: `radial-gradient(circle, ${
              ['rgba(99, 102, 241, 0.08)', 'rgba(168, 85, 247, 0.06)', 'rgba(59, 130, 246, 0.07)', 'rgba(16, 185, 129, 0.05)', 'rgba(245, 101, 101, 0.06)', 'rgba(251, 191, 36, 0.05)'][i]
            }, transparent 70%)`,
            left: `${10 + i * 15}%`,
            top: `${15 + i * 10}%`,
          }}
          animate={{
            x: [0, 100, -50, 0],
            y: [0, -80, 60, 0],
            scale: [1, 1.3, 0.8, 1],
            opacity: [0.4, 0.8, 0.3, 0.4]
          }}
          transition={{
            duration: 20 + i * 5,
            repeat: Infinity,
            ease: "easeInOut",
            delay: i * 3
          }}
        />
      ))}

      {/* Animated Grid Pattern */}
      <motion.div 
        className="absolute inset-0 opacity-5"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.3) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.3) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px'
        }}
        animate={{
          x: [0, 60, 0],
          y: [0, 60, 0]
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "linear"
        }}
      />

      {/* Geometric Floating Shapes */}
      {Array.from({ length: 8 }).map((_, i) => (
        <motion.div
          key={`shape-${i}`}
          className="absolute border border-white/10 backdrop-blur-[1px]"
          style={{
            width: 60 + i * 15,
            height: 60 + i * 15,
            borderRadius: i % 3 === 0 ? '50%' : i % 3 === 1 ? '15%' : '0%',
            left: `${Math.random() * 80}%`,
            top: `${Math.random() * 80}%`,
          }}
          animate={{
            x: [0, (i % 2 === 0 ? 100 : -100), 0],
            y: [0, (i % 2 === 0 ? -80 : 80), 0],
            rotate: [0, 180, 360],
            scale: [1, 1.2, 1],
            opacity: [0.1, 0.3, 0.1]
          }}
          transition={{
            duration: 15 + i * 3,
            repeat: Infinity,
            ease: "easeInOut",
            delay: i * 2
          }}
        />
      ))}

      {/* Concentric Pulsing Rings */}
      <div className="absolute inset-0 flex items-center justify-center">
        {Array.from({ length: 5 }).map((_, i) => (
          <motion.div
            key={`ring-${i}`}
            className="absolute border border-blue-500/5 rounded-full"
            style={{
              width: (i + 1) * 200,
              height: (i + 1) * 200,
            }}
            animate={{
              scale: [1, 1.3, 1],
              opacity: [0.05, 0.2, 0.05],
              rotate: i % 2 === 0 ? [0, 360] : [360, 0]
            }}
            transition={{
              duration: 12 + i * 2,
              repeat: Infinity,
              ease: "easeInOut",
              delay: i * 1.5
            }}
          />
        ))}
      </div>

      {/* Floating Energy Bubbles */}
      {Array.from({ length: 12 }).map((_, i) => (
        <motion.div
          key={`bubble-${i}`}
          className="absolute rounded-full border-2 backdrop-blur-sm"
          style={{
            width: 30 + i * 12,
            height: 30 + i * 12,
            background: `radial-gradient(circle, ${
              ['rgba(59, 130, 246, 0.2)', 'rgba(168, 85, 247, 0.15)', 'rgba(16, 185, 129, 0.18)', 'rgba(99, 102, 241, 0.2)'][i % 4]
            }, transparent 60%)`,
            borderColor: ['rgba(59, 130, 246, 0.4)', 'rgba(168, 85, 247, 0.3)', 'rgba(16, 185, 129, 0.35)', 'rgba(99, 102, 241, 0.4)'][i % 4],
            boxShadow: `0 0 20px ${['rgba(59, 130, 246, 0.3)', 'rgba(168, 85, 247, 0.2)', 'rgba(16, 185, 129, 0.25)', 'rgba(99, 102, 241, 0.3)'][i % 4]}`,
            left: `${5 + (i * 8)}%`,
            top: `${10 + (i * 6)}%`,
          }}
          animate={{
            y: [0, -150, -80, 0],
            x: [0, 60, -40, 0],
            scale: [1, 1.6, 0.7, 1],
            opacity: [0.6, 1, 0.4, 0.6],
            rotate: [0, 180, 360]
          }}
          transition={{
            duration: 4 + i * 0.5,
            repeat: Infinity,
            ease: "easeInOut",
            delay: i * 0.3
          }}
        />
      ))}

      {/* Flowing Light Streams */}
      {Array.from({ length: 6 }).map((_, i) => (
        <motion.div
          key={`stream-${i}`}
          className="absolute opacity-80"
          style={{
            width: '3px',
            height: '120px',
            background: `linear-gradient(to bottom, transparent, ${
              ['#60a5fa', '#a855f7', '#10b981', '#6366f1', '#f59e0b', '#ef4444'][i]
            }, transparent)`,
            boxShadow: `0 0 15px ${['#60a5fa', '#a855f7', '#10b981', '#6366f1', '#f59e0b', '#ef4444'][i]}`,
            left: `${15 + i * 14}%`,
            top: `${5 + i * 10}%`,
          }}
          animate={{
            y: [0, 500, 0],
            opacity: [0, 1, 0.7, 0],
            scaleY: [0.3, 2.5, 1.5, 0.3],
            scaleX: [1, 1.5, 1]
          }}
          transition={{
            duration: 3 + i * 0.5,
            repeat: Infinity,
            ease: "easeInOut",
            delay: i * 0.8
          }}
        />
      ))}

      {/* Holographic Grid Lines */}
      <div className="absolute inset-0 opacity-10">
        {Array.from({ length: 3 }).map((_, i) => (
          <motion.div
            key={`line-${i}`}
            className="absolute h-px bg-gradient-to-r from-transparent via-cyan-400 to-transparent"
            style={{
              width: '100%',
              top: `${30 + i * 20}%`,
            }}
            animate={{
              x: ['-100%', '100%'],
              opacity: [0, 1, 0]
            }}
            transition={{
              duration: 8,
              repeat: Infinity,
              ease: "linear",
              delay: i * 3
            }}
          />
        ))}
      </div>

      {/* Top Gradient Overlay for depth */}
      <div className="absolute inset-0 bg-gradient-to-b from-gray-900/50 via-transparent to-gray-900/30 pointer-events-none" />
    </div>
  );
};
