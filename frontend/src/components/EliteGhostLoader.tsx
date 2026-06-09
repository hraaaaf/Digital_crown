import React from 'react';
import { AppLoader } from './AppLoader';

interface EliteGhostLoaderProps {
  text?: string;
  fullScreen?: boolean;
  size?: 'small' | 'medium' | 'large';
}

export const EliteGhostLoader: React.FC<EliteGhostLoaderProps> = ({ 
  text = "Initialisation de votre cabinet...", 
  fullScreen = true,
  size = 'large'
}) => {
  const containerClass = fullScreen 
    ? "fixed inset-0 z-50 bg-slate-50/80 dark:bg-slate-950/80 backdrop-blur-2xl" 
    : "absolute inset-0 z-10 rounded-3xl bg-slate-50/80 dark:bg-slate-950/80 backdrop-blur-md";
    
  // Size could be passed down later if AppLoader supports size adjustments,
  // For now, AppLoader uses a standard elegant size.

  return <AppLoader text={text} className={containerClass} minHeight={fullScreen ? "h-screen" : "h-full"} />;
};
