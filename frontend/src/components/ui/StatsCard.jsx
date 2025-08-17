import React from 'react';
import { cn } from '../../lib/utils';

const StatsCard = ({ 
  title, 
  value, 
  icon,
  description,
  variant = 'default',
  className 
}) => {
  const variantClasses = {
    default: 'bg-white border-gray-200 dark:bg-gray-800 dark:border-gray-700',
    success: 'bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-900/50',
    warning: 'bg-yellow-50 border-yellow-200 dark:bg-yellow-900/20 dark:border-yellow-900/50',
    info: 'bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-900/50'
  };

  return (
    <div className={cn(
      "rounded-lg border p-4 shadow-sm",
      variantClasses[variant],
      className
    )}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-300">
            {title}
          </p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {value}
          </p>
          {description && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {description}
            </p>
          )}
        </div>
        {icon && (
          <div className="text-2xl opacity-60">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
};

export default StatsCard;