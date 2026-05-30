import React from 'react';
import { motion } from 'framer-motion';
import logoUrl from '../assets/tooth.png';

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
  const [particles] = React.useState(() => {
    return [...Array(5)].map(() => ({
      initialX: (Math.random() - 0.5) * 100,
      initialY: (Math.random() - 0.5) * 100,
      animateY: -100 - Math.random() * 50,
      animateScale: [0, Math.random() * 2 + 1, 0],
      duration: 2 + Math.random() * 2,
      delay: Math.random() * 2,
    }));
  });

  const containerClass = fullScreen 
    ? "fixed inset-0 z-50" 
    : "absolute inset-0 z-10 rounded-3xl";
    
  const logoClass = size === 'small' ? 'w-24 md:w-32' : size === 'medium' ? 'w-40 md:w-56' : 'w-56 md:w-72';
  const glowClass = size === 'small' ? 'w-32 h-32 blur-[40px]' : size === 'medium' ? 'w-48 h-48 blur-[60px]' : 'w-72 h-72 blur-[80px]';
  return (
    <div className={`${containerClass} flex flex-col items-center justify-center bg-slate-50/80 dark:bg-slate-950/80 backdrop-blur-2xl`}>
      <div className="relative flex flex-col items-center justify-center">
        
        {/* Lueur d'arrière-plan (Ethereal Glow) */}
        <motion.div
          className={`absolute ${glowClass} bg-primary/20 rounded-full`}
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1.2 }}
          transition={{ duration: 2, repeat: Infinity, repeatType: "mirror", ease: "easeInOut" }}
        />

        {/* Le Logo avec Blur-in initial */}
        <motion.div
          className="relative overflow-hidden rounded-xl"
          initial={{ opacity: 0, filter: 'blur(20px)', scale: 0.8 }}
          animate={{ opacity: 1, filter: 'blur(0px)', scale: 1 }}
          transition={{ duration: 1.5, ease: "easeOut" }}
        >
          {/* Logo plein */}
          <img src={logoUrl} alt="Digital Crown Elite" className={`${logoClass} h-auto drop-shadow-2xl relative z-0`} />

          {/* Faisceau Hologram Scanner (Glassmorphism) qui monte et descend */}
          <motion.div
            className="absolute left-0 w-full h-1/3 bg-gradient-to-b from-transparent via-primary/30 to-transparent backdrop-blur-[2px] border-y border-primary/20 z-10 shadow-[0_0_15px_rgba(var(--primary-rgb),0.5)]"
            initial={{ top: '-40%' }}
            animate={{ top: '120%' }}
            transition={{ 
              duration: 2.5, 
              repeat: Infinity, 
              repeatType: 'mirror',
              ease: "easeInOut" 
            }}
          />
        </motion.div>

        {/* Particules flottantes */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          {particles.map((p, i) => (
            <motion.div
              key={i}
              className="absolute w-1 h-1 rounded-full bg-primary/50 blur-[1px]"
              initial={{ 
                x: p.initialX, 
                y: p.initialY,
                opacity: 0,
                scale: 0
              }}
              animate={{ 
                y: p.animateY,
                opacity: [0, 1, 0],
                scale: p.animateScale
              }}
              transition={{
                duration: p.duration,
                repeat: Infinity,
                delay: p.delay,
              }}
            />
          ))}
        </div>

      </div>

      {/* Texte de chargement */}
      <motion.div 
        className="mt-12 flex flex-col items-center gap-2"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5, duration: 1 }}
      >
        <p className="text-primary font-black uppercase tracking-[0.2em] text-sm font-outfit drop-shadow-sm">
          {text}
        </p>
        <div className="flex gap-1.5 mt-2">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="w-1.5 h-1.5 rounded-full bg-primary/60"
              animate={{ opacity: [0.3, 1, 0.3], scale: [0.8, 1.2, 0.8] }}
              transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
            />
          ))}
        </div>
      </motion.div>

    </div>
  );
};
