import React from 'react';
import Logo from '../assets/digital-crown-logo.svg';

interface DigitalCrownLoaderProps {
  text?: string;
  minHeight?: string;
  textColor?: string;
  spinnerColor?: string;
  className?: string;
}

export const DigitalCrownLoader: React.FC<DigitalCrownLoaderProps> = ({ 
  text, 
  minHeight = "h-screen",
  textColor = "text-slate-600",
  spinnerColor = "border-blue-600",
  className = "bg-slate-50"
}) => {
  return (
    <div className={`flex items-center justify-center ${minHeight} ${className}`}>
      <div className="flex flex-col items-center gap-4">
        <div className="relative w-24 h-24 flex items-center justify-center">
          {/* Subtle outer glow */}
          <div className="absolute inset-0 bg-yellow-400/20 blur-xl rounded-full animate-pulse"></div>
          
          {/* Spinners */}
          <div className="absolute inset-0 border-[3px] border-slate-200/50 dark:border-slate-800 rounded-full"></div>
          <div className={`absolute inset-0 border-[3px] ${spinnerColor} rounded-full border-t-transparent animate-spin`} style={{ animationDuration: '1.5s' }}></div>
          
          {/* Inner Logo */}
          <img 
            src={Logo} 
            alt="Loading..." 
            className="absolute inset-0 m-auto object-contain w-12 h-12 drop-shadow-md"
          />
        </div>
        {text && (
          <p className={`font-medium ${textColor} tracking-[0.2em] uppercase text-xs mt-2 opacity-80 animate-pulse`}>
            {text}
          </p>
        )}
      </div>
    </div>
  );
};
