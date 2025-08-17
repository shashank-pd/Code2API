import React from 'react';
import { cn } from '../../lib/utils';

const Alert = ({ 
  children, 
  variant = 'default', 
  className,
  onClose,
  title
}) => {
  const variantClasses = {
    default: 'bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-900/20 dark:border-blue-900/50 dark:text-blue-300',
    success: 'bg-green-50 border-green-200 text-green-800 dark:bg-green-900/20 dark:border-green-900/50 dark:text-green-300',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800 dark:bg-yellow-900/20 dark:border-yellow-900/50 dark:text-yellow-300',
    error: 'bg-red-50 border-red-200 text-red-800 dark:bg-red-900/20 dark:border-red-900/50 dark:text-red-300'
  };

  const iconClasses = {
    default: '🔵',
    success: '✅',
    warning: '⚠️',
    error: '❌'
  };

  return (
    <div className={cn(
      "relative rounded-lg border p-4",
      variantClasses[variant],
      className
    )}>
      {onClose && (
        <button
          onClick={onClose}
          className="absolute top-2 right-2 text-gray-400 hover:text-gray-600 focus:outline-none"
          aria-label="Close alert"
        >
          ✕
        </button>
      )}
      
      <div className="flex items-start space-x-3">
        <span className="text-lg flex-shrink-0 mt-0.5">
          {iconClasses[variant]}
        </span>
        <div className="flex-1">
          {title && (
            <h3 className="font-medium mb-1">
              {title}
            </h3>
          )}
          <div className="text-sm">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Alert;