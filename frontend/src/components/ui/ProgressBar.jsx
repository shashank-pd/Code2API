import React from 'react';
import { cn } from '../../lib/utils';

const ProgressBar = ({ 
  value = 0, 
  max = 100, 
  className,
  showPercentage = true,
  size = 'md',
  variant = 'default'
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  
  const sizeClasses = {
    sm: 'h-2',
    md: 'h-3',
    lg: 'h-4'
  };
  
  const variantClasses = {
    default: 'bg-blue-600',
    success: 'bg-green-600',
    warning: 'bg-yellow-600',
    error: 'bg-red-600'
  };

  return (
    <div className={cn("w-full", className)}>
      <div className={cn(
        "w-full bg-gray-200 rounded-full overflow-hidden dark:bg-gray-700",
        sizeClasses[size]
      )}>
        <div
          className={cn(
            "h-full transition-all duration-300 ease-out rounded-full",
            variantClasses[variant]
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showPercentage && (
        <div className="text-sm text-gray-600 mt-1 text-center">
          {Math.round(percentage)}%
        </div>
      )}
    </div>
  );
};

export default ProgressBar;