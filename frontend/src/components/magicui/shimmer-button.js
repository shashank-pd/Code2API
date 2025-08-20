import React from "react";
import { motion } from "framer-motion";
import { cn } from "../../lib/utils";

export function ShimmerButton({
  shimmerColor = "#ffffff",
  shimmerSize = "0.05em",
  shimmerDuration = "3s",
  borderRadius = "100px",
  background = "radial-gradient(ellipse 80% 50% at 50% 120%, #120078, #000000)",
  className,
  children,
  ...props
}) {
  return (
    <button
      style={{
        "--shimmer-color": shimmerColor,
        "--shimmer-size": shimmerSize,
        "--shimmer-duration": shimmerDuration,
        "--border-radius": borderRadius,
        background,
      }}
      className={cn(
        "group relative z-0 flex cursor-pointer items-center justify-center overflow-hidden whitespace-nowrap border border-white/10 px-6 py-3 text-white [border-radius:var(--border-radius)] transition-all duration-300 hover:scale-105 hover:shadow-xl hover:shadow-white/10 min-h-[48px]",
        "before:absolute before:inset-0 before:rounded-[inherit] before:bg-[linear-gradient(45deg,transparent_25%,var(--shimmer-color)_50%,transparent_75%,transparent_100%)] before:opacity-0 before:[background-size:var(--shimmer-size)_var(--shimmer-size)] before:animate-shimmer before:[transition:opacity_0.5s_ease-out] hover:before:opacity-100",
        className
      )}
      {...props}
    >
      <span className="relative z-10">{children}</span>
    </button>
  );
}
