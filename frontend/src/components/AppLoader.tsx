import React from 'react';
import { motion } from 'framer-motion';
import Logo from '../assets/logo.png';

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
    <div className={`flex items-center justify-center ${minHeight} ${className} overflow-hidden`}>
      <div className="flex flex-col items-center gap-10">

        <div className="relative flex items-center justify-center">
          {/* Outer ring pulse */}
          <motion.div
            className="absolute w-52 h-52 rounded-full border border-blue-200/60"
            animate={{ scale: [1, 1.18, 1], opacity: [0.6, 0, 0.6] }}
            transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
          />
          {/* Inner ring pulse (offset phase) */}
          <motion.div
            className="absolute w-40 h-40 rounded-full border border-blue-300/40"
            animate={{ scale: [1, 1.22, 1], opacity: [0.4, 0, 0.4] }}
            transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut", delay: 0.6 }}
          />
          {/* Glow blob */}
          <motion.div
            className="absolute w-36 h-36 rounded-full bg-blue-500/10 blur-2xl"
            animate={{ scale: [0.9, 1.15, 0.9], opacity: [0.4, 0.8, 0.4] }}
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
          />

          {/* Logo */}
          <motion.img
            src={Logo}
            alt="Digital Crown"
            className="w-44 h-auto object-contain relative z-10"
            initial={{ opacity: 0, scale: 0.85 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, ease: [0.34, 1.56, 0.64, 1] }}
          />
        </div>

        {text && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.5 }}
            className="flex items-center gap-4"
          >
            <div className="w-10 h-[1px] bg-gradient-to-r from-transparent to-slate-300" />
            <span className="text-slate-400 font-semibold tracking-[0.2em] text-[11px] uppercase">
              {text}
            </span>
            <div className="w-10 h-[1px] bg-gradient-to-l from-transparent to-slate-300" />
          </motion.div>
        )}

        {/* Dot loader */}
        <div className="flex gap-2">
          {[0, 1, 2].map(i => (
            <motion.div
              key={i}
              className="w-1.5 h-1.5 rounded-full bg-blue-400"
              animate={{ y: [0, -6, 0], opacity: [0.4, 1, 0.4] }}
              transition={{ duration: 0.8, repeat: Infinity, ease: "easeInOut", delay: i * 0.18 }}
            />
          ))}
        </div>
      </div>
    </div>
  );
};
