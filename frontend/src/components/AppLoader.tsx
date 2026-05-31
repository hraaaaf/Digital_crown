import React from 'react';
import { motion } from 'framer-motion';
import Logo from '../assets/digital-crown-logo.svg';

interface AppLoaderProps {
  text?: string;
  minHeight?: string;
  className?: string;
}

export const AppLoader: React.FC<AppLoaderProps> = ({ 
  text, 
  minHeight = "h-screen",
  className = "bg-slate-50"
}) => {
  return (
    <div className={`flex items-center justify-center ${minHeight} ${className} dark:bg-slate-900 overflow-hidden`}>
      <div className="flex flex-col items-center gap-6">
        <div className="relative w-32 h-32 flex items-center justify-center">
          
          {/* Medical Pulse Rings */}
          <motion.div
            className="absolute inset-0 rounded-full border border-blue-500/20"
            animate={{ 
              scale: [1, 1.5, 2], 
              opacity: [0.8, 0.4, 0],
              borderWidth: ["2px", "1px", "0px"]
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeOut"
            }}
          />
          <motion.div
            className="absolute inset-2 rounded-full border border-amber-500/20"
            animate={{ 
              scale: [1, 1.5, 2], 
              opacity: [0.8, 0.4, 0],
              borderWidth: ["2px", "1px", "0px"]
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeOut",
              delay: 0.5
            }}
          />
          <motion.div
            className="absolute inset-4 rounded-full border border-blue-400/30"
            animate={{ 
              scale: [1, 1.5, 2], 
              opacity: [0.8, 0.4, 0],
              borderWidth: ["2px", "1px", "0px"]
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeOut",
              delay: 1
            }}
          />

          {/* Central Logo Beating */}
          <motion.div 
            className="relative z-10 w-16 h-16 bg-white dark:bg-slate-800 rounded-full shadow-[0_0_30px_rgba(59,130,246,0.15)] flex items-center justify-center border border-slate-100 dark:border-slate-700"
            animate={{
              scale: [1, 1.1, 1]
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          >
            <img 
              src={Logo} 
              alt="Digital Crown Loading" 
              className="w-10 h-10 object-contain drop-shadow-sm"
            />
          </motion.div>
        </div>

        {text && (
          <motion.div 
            className="flex flex-col items-center gap-1"
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          >
            <p className="font-semibold text-blue-600/80 dark:text-blue-400/80 tracking-[0.15em] uppercase text-xs">
              {text}
            </p>
            <div className="flex gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400/60 animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400/60 animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400/60 animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};
