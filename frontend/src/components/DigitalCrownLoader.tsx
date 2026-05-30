import React from 'react';
import Logo from '../assets/logo.png';

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
        <div className="relative w-16 h-16">
          <div className="absolute inset-0 border-4 border-slate-200 rounded-full"></div>
          <div className={`absolute inset-0 border-4 ${spinnerColor} rounded-full border-t-transparent animate-spin`}></div>
          <img 
            src={Logo} 
            alt="Loading..." 
            className="absolute inset-0 m-auto object-contain w-8 h-8"
            style={{ filter: document.body?.dataset?.theme === 'dark' ? 'brightness(0) invert(1)' : 'none' }}
          />
        </div>
        {text && <p className={`font-black ${textColor} tracking-widest uppercase text-sm`}>{text}</p>}
      </div>
    </div>
  );
};
