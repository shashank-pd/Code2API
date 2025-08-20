import React from "react";
import { motion } from "framer-motion";
import { cn } from "../../lib/utils";

export function Particles({ 
  className,
  quantity = 50,
  staticity = 50,
  ease = 50,
  refresh = false,
}) {
  const [particles, setParticles] = React.useState([]);

  React.useEffect(() => {
    const generateParticles = () => {
      const newParticles = [];
      for (let i = 0; i < quantity; i++) {
        newParticles.push({
          id: i,
          x: Math.random() * 100,
          y: Math.random() * 100,
          size: Math.random() * 3 + 1,
          opacity: Math.random() * 0.5 + 0.1,
          duration: Math.random() * 10 + 10,
          delay: Math.random() * 5,
        });
      }
      setParticles(newParticles);
    };

    generateParticles();
  }, [quantity, refresh]);

  return (
    <div className={cn("absolute inset-0 overflow-hidden", className)}>
      {particles.map((particle) => (
        <motion.div
          key={particle.id}
          className="absolute rounded-full blur-[1px]"
          style={{
            left: `${particle.x}%`,
            top: `${particle.y}%`,
            width: `${particle.size * 2}px`,
            height: `${particle.size * 2}px`,
            background: `radial-gradient(circle, rgba(59, 130, 246, 0.6), rgba(168, 85, 247, 0.4), rgba(16, 185, 129, 0.3), transparent)`,
            opacity: particle.opacity,
          }}
          animate={{
            y: [0, -80, 20, 0],
            x: [0, Math.random() * 60 - 30, Math.random() * 40 - 20, 0],
            scale: [0.5, 1.8, 1.2, 0.5],
            opacity: [particle.opacity, particle.opacity * 1.2, particle.opacity * 0.4, particle.opacity],
          }}
          transition={{
            duration: particle.duration * 0.6,
            delay: particle.delay * 0.5,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  );
}
