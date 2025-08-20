import React from "react";
import { cn } from "../../lib/utils";

export function Meteors({
  number = 20,
  className,
}) {
  const meteors = new Array(number || 20).fill(true);
  
  return (
    <>
      {meteors.map((el, idx) => {
        // Randomly choose direction: 0 = left-to-right, 1 = right-to-left, 2 = top-to-bottom
        const direction = Math.floor(Math.random() * 3);
        const isLeftToRight = direction === 0;
        const isRightToLeft = direction === 1;
        const isTopToBottom = direction === 2;
        
        let rotationClass, startPosition, animationName;
        
        if (isLeftToRight) {
          rotationClass = "rotate-[215deg]";
          startPosition = {
            top: Math.floor(Math.random() * 100) + "%",
            left: "-50px",
          };
          animationName = "meteor-left";
        } else if (isRightToLeft) {
          rotationClass = "rotate-[35deg]";
          startPosition = {
            top: Math.floor(Math.random() * 100) + "%",
            right: "-50px",
          };
          animationName = "meteor-right";
        } else {
          rotationClass = "rotate-[180deg]";
          startPosition = {
            top: "-50px",
            left: Math.floor(Math.random() * 100) + "%",
          };
          animationName = "meteor-top";
        }
        
        return (
          <span
            key={"meteor" + idx}
            className={cn(
              `animate-${animationName} absolute h-0.5 w-0.5 rounded-[9999px] shadow-[0_0_0_1px_#ffffff10] ${rotationClass}`,
              "before:content-[''] before:absolute before:top-1/2 before:transform before:-translate-y-[50%] before:w-[50px] before:h-[1px]",
              isLeftToRight && "bg-blue-400 before:bg-gradient-to-r before:from-[#60a5fa] before:to-transparent",
              isRightToLeft && "bg-purple-400 before:bg-gradient-to-r before:from-[#a855f7] before:to-transparent", 
              isTopToBottom && "bg-cyan-400 before:bg-gradient-to-r before:from-[#22d3ee] before:to-transparent",
              className
            )}
            style={{
              ...startPosition,
              animationDelay: Math.random() * (2 - 0.2) + 0.2 + "s",
              animationDuration: Math.floor(Math.random() * (8 - 3) + 3) + "s",
            }}
          />
        );
      })}
    </>
  );
}
