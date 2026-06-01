import React from 'react';
import { motion } from 'framer-motion';

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
  // SVG sub-paths traced directly from the Digital Crown app logo
  const appLogoPaths = [
    "M43.4 33.8 L40.2 36.8 L39.7 37.7 L40.5 41.9 L44.2 44.6 L41.8 48.0 L43.6 52.3 L45.3 54.7 L46.8 54.8 L47.7 53.6 L48.3 51.7 L49.9 49.6 L51.6 51.7 L52.4 54.4 L53.0 54.8 L54.5 54.7 L56.3 52.3 L58.1 48.2 L55.7 44.6 L57.8 43.1 L57.3 45.6 L58.2 46.8 L59.2 43.6 L60.0 37.2 L56.1 33.7 L53.6 34.1 L51.0 35.2 L51.0 35.9 L52.4 36.0 L55.7 35.0 L58.6 37.8 L58.2 41.1 L54.7 43.7 L53.6 42.2 L54.9 41.4 L56.1 41.4 L56.7 40.6 L56.6 39.3 L55.1 38.8 L54.4 39.4 L54.2 40.2 L52.3 41.7 L51.1 40.6 L53.6 38.8 L53.8 38.1 L48.7 35.0 L45.8 34.0 Z",
    "M64.7 57.8 L64.7 58.3 L65.1 59.5 L65.0 60.0 L65.3 60.0 L66.0 62.2 L67.2 62.0 L67.5 61.4 L67.5 60.7 L68.1 59.7 L68.2 60.3 L68.5 60.6 L68.7 61.4 L69.1 62.2 L70.2 62.0 L70.5 60.9 L70.9 60.1 L70.8 59.7 L71.0 59.4 L71.3 58.2 L71.8 58.2 L71.9 62.2 L72.8 62.2 L73.1 61.9 L72.8 61.0 L73.0 60.1 L73.3 60.1 L75.0 62.2 L75.8 62.2 L75.9 61.0 L75.8 57.6 L74.9 57.8 L74.9 59.4 L74.6 59.8 L74.2 59.4 L74.3 59.2 L73.6 58.6 L72.8 57.6 L71.8 57.8 L70.5 57.6 L70.5 57.9 L70.0 58.3 L70.2 58.9 L69.7 60.0 L69.4 60.3 L68.7 57.9 L68.4 57.6 L67.5 57.8 L67.5 58.1 L67.2 58.3 L67.2 58.8 L66.9 58.9 L67.1 59.4 L66.8 60.0 L66.0 59.2 L66.0 58.5 L65.7 58.2 L65.7 57.8 L65.4 57.6 Z",
    "M61.0 57.6 L60.7 58.1 L60.0 58.6 L60.0 58.9 L59.7 59.2 L59.7 60.4 L60.1 61.3 L60.6 61.7 L61.3 62.2 L62.9 62.2 L63.5 61.9 L63.8 61.6 L64.0 61.6 L64.1 61.4 L64.1 61.3 L64.4 61.0 L64.5 60.7 L64.5 59.1 L64.3 58.6 L63.5 57.9 L63.2 57.8 L62.8 57.6 L61.3 57.8 Z",
    "M23.9 57.6 L23.8 58.1 L24.1 58.3 L23.9 61.9 L24.1 62.2 L26.4 62.2 L27.0 61.9 L27.5 61.9 L27.8 61.7 L27.9 61.3 L28.2 61.0 L28.4 60.6 L28.4 59.2 L28.1 58.8 L27.9 58.3 L27.3 57.9 L26.6 57.6 Z",
    "M40.3 61.7 L40.5 62.2 L41.5 62.0 L41.7 61.7 L41.7 61.4 L41.9 61.2 L43.9 61.3 L44.2 62.0 L45.5 61.9 L48.9 62.2 L48.9 61.3 L46.7 61.2 L46.5 57.6 L45.6 57.8 L45.5 61.9 L45.2 61.7 L44.9 61.3 L44.9 60.9 L44.5 60.3 L44.2 59.2 L43.9 58.9 L43.4 58.1 L43.4 57.6 L42.4 57.6 L42.1 57.9 L41.7 58.9 L41.7 59.4 L41.2 60.3 L40.9 60.6 L40.8 60.9 L40.8 61.2 Z",
    "M55.4 57.8 L55.5 62.2 L56.6 62.0 L56.6 61.3 L56.7 61.0 L57.3 60.9 L57.9 61.4 L58.2 62.0 L59.4 61.9 L58.6 60.7 L59.2 60.0 L59.4 59.2 L59.2 58.5 L58.6 57.9 L58.3 57.8 L57.6 57.6 L55.7 57.6 Z",
    "M35.5 57.8 L35.6 62.2 L36.5 62.2 L36.6 61.9 L36.6 60.0 L36.5 58.8 L36.9 58.1 L37.1 58.5 L38.0 58.5 L38.3 58.6 L38.6 62.2 L39.4 62.0 L39.4 59.1 L39.9 58.5 L40.8 58.5 L40.9 58.2 L40.9 57.8 L40.6 57.6 L37.1 57.6 L36.6 57.9 L36.3 57.6 Z",
    "M31.3 58.1 L30.9 58.5 L30.6 58.9 L30.7 59.7 L30.6 59.8 L30.6 60.4 L30.7 61.0 L31.0 61.3 L31.0 61.4 L31.5 61.9 L32.2 62.2 L33.8 62.2 L34.7 61.7 L34.9 61.4 L34.7 60.3 L34.9 59.8 L34.6 59.7 L33.8 59.8 L33.7 60.3 L33.7 61.0 L33.4 61.3 L32.9 61.3 L32.5 61.2 L32.1 60.9 L31.8 60.6 L31.6 60.3 L31.6 59.5 L31.8 59.2 L32.3 58.6 L32.6 58.5 L32.9 58.5 L33.5 58.6 L34.0 58.9 L34.9 58.8 L34.7 58.5 L34.9 58.3 L34.7 58.1 L34.4 58.1 L34.3 57.8 L33.8 57.8 L33.7 57.6 L32.3 57.6 Z",
    "M61.9 65.7 L62.0 66.3 L62.3 66.2 L62.5 66.0 L62.5 65.9 L63.7 65.9 L63.7 66.0 L64.0 66.3 L64.4 66.0 L65.0 66.2 L65.1 65.6 L65.4 65.6 L66.0 66.2 L66.5 66.0 L66.2 65.4 L66.5 65.0 L66.6 64.3 L66.9 65.3 L66.9 66.2 L67.4 66.3 L68.5 65.7 L67.5 65.3 L68.5 65.1 L68.4 64.8 L67.5 64.4 L68.5 64.3 L68.5 64.0 L66.2 64.1 L64.5 64.0 L64.4 66.0 L64.1 65.7 L64.0 65.4 L64.3 65.3 L63.7 64.8 L63.7 64.4 L63.5 64.1 L62.6 64.0 L62.6 64.4 L62.0 65.3 Z",
    "M52.0 57.8 L51.7 57.9 L51.4 58.3 L51.3 58.3 L50.8 58.8 L50.7 59.4 L50.7 60.4 L51.0 61.2 L51.7 61.9 L52.3 62.2 L53.9 62.2 L54.5 61.9 L54.8 61.2 L54.8 60.7 L54.1 60.9 L53.8 61.2 L53.2 61.3 L52.7 61.3 L52.0 60.7 L51.7 60.1 L51.7 59.7 L52.1 58.9 L52.6 58.6 L53.6 58.6 L54.4 59.1 L54.8 58.8 L54.8 58.2 L54.5 57.9 L53.8 57.6 L52.6 57.6 Z",
    "M54.5 64.3 L54.8 64.5 L55.2 66.0 L55.2 65.7 L55.5 65.4 L56.3 65.4 L56.3 65.0 L55.4 64.8 L55.5 64.4 L57.2 64.5 L57.3 66.2 L57.8 66.0 L57.9 64.4 L58.6 64.5 L58.8 64.8 L58.9 65.6 L59.2 66.0 L59.8 66.0 L60.3 65.1 L60.6 66.0 L61.3 66.0 L61.4 65.7 L61.7 64.4 L62.0 64.1 L61.4 64.0 L61.0 64.4 L61.2 64.5 L60.9 64.8 L60.6 64.1 L60.0 64.0 L59.7 64.4 L59.5 65.0 L59.2 64.5 L59.2 64.3 L59.1 64.0 L54.8 64.0 Z",
    "M50.1 64.0 L50.1 64.8 L50.4 65.6 L50.1 66.0 L50.5 66.2 L51.3 66.2 L51.4 66.0 L51.7 65.9 L52.0 65.4 L52.1 65.7 L52.4 66.0 L52.9 66.2 L53.5 66.2 L54.2 65.9 L54.5 65.3 L54.5 65.0 L54.2 64.3 L54.1 64.1 L53.8 64.0 L53.2 63.8 L52.0 64.0 L52.3 64.1 L52.1 64.5 L51.8 65.1 L51.3 64.7 L51.6 64.5 L51.6 64.0 L51.1 63.8 L50.8 63.8 Z",
    "M35.6 64.3 L35.9 64.4 L36.0 66.2 L37.1 66.2 L37.7 66.0 L38.1 65.6 L38.3 65.1 L38.6 66.2 L40.3 66.2 L40.2 65.7 L39.1 65.3 L40.0 65.3 L40.0 64.8 L39.0 64.7 L39.3 64.4 L40.2 64.4 L40.2 64.0 L38.4 64.1 L38.3 65.0 L38.0 64.3 L37.8 64.1 L37.5 64.0 L35.9 64.0 Z",
    "M40.6 66.2 L40.9 66.3 L41.2 65.1 L41.9 66.0 L42.2 66.2 L42.7 66.0 L42.8 64.4 L43.6 64.5 L43.7 66.3 L44.0 66.2 L44.0 64.7 L44.3 64.4 L44.9 64.4 L44.9 64.0 L41.9 64.0 L41.8 64.5 L41.5 64.4 L41.4 64.1 L41.1 64.0 L40.6 64.0 Z",
    "M44.6 65.6 L44.8 66.2 L45.1 66.2 L45.6 65.7 L46.2 65.7 L46.4 66.0 L46.7 66.2 L47.0 66.2 L47.3 66.0 L49.0 66.0 L49.0 65.7 L47.9 65.6 L47.9 64.0 L47.3 64.0 L47.1 65.9 L47.0 65.3 L46.5 64.8 L46.4 64.5 L46.4 64.3 L46.2 64.0 L45.5 64.0 L45.2 64.5 L44.9 65.6 Z",
    "M29.8 57.6 L29.0 57.8 L28.8 58.1 L29.0 62.2 L30.0 62.2 Z",
    "M40.8 43.0 L40.6 43.6 L40.8 43.7 L40.8 44.5 L40.9 45.2 L41.2 45.5 L41.2 46.2 L41.5 46.8 L42.2 46.2 L42.5 45.8 L42.5 45.2 L42.2 44.5 L42.4 44.0 L41.9 43.9 L41.5 43.6 L41.1 43.1 Z",
    "M32.1 64.1 L31.8 64.7 L31.3 65.7 L31.5 66.3 L31.9 66.0 L32.1 65.7 L32.8 65.7 L33.2 66.2 L33.7 66.2 L33.7 65.7 L33.4 64.8 L32.9 64.0 Z"
  ];

  return (
    <div className={`flex items-center justify-center ${minHeight} ${className} dark:bg-slate-900 overflow-hidden`}>
      <div className="flex flex-col items-center gap-10">
        
        {/* Premium App Logo Animation */}
        <div className="relative w-72 h-40 flex items-center justify-center">
          {/* Subtle glow behind the logo */}
          <motion.div
            className="absolute inset-0 rounded-full bg-amber-500/10 dark:bg-amber-400/10 blur-2xl"
            animate={{ 
              scale: [1, 1.2, 1],
              opacity: [0.3, 0.6, 0.3]
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
          
          <svg 
            viewBox="0 0 100 100" 
            className="w-full h-full relative z-10 drop-shadow-lg"
            style={{ overflow: 'visible' }}
          >
            <defs>
              <linearGradient id="premiumGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#f59e0b" /> {/* amber-500 */}
                <stop offset="50%" stopColor="#d97706" /> {/* amber-600 */}
                <stop offset="100%" stopColor="#fbbf24" /> {/* amber-400 */}
              </linearGradient>
              <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="1" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* Render all subpaths simultaneously */}
            {appLogoPaths.map((path, idx) => (
              <React.Fragment key={idx}>
                {/* Background faint path */}
                <path
                  d={path}
                  fill="none"
                  stroke="#e2e8f0"
                  strokeWidth="0.3"
                  className="dark:stroke-slate-700/50"
                />

                {/* Animated glowing drawing path */}
                <motion.path
                  d={path}
                  fill="none"
                  stroke="url(#premiumGrad)"
                  strokeWidth="0.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  filter="url(#glow)"
                  initial={{ pathLength: 0, opacity: 0 }}
                  animate={{ 
                    pathLength: [0, 1, 1, 0],
                    opacity: [0, 1, 1, 0]
                  }}
                  transition={{
                    duration: 4, 
                    repeat: Infinity, 
                    ease: "easeInOut",
                    times: [0, 0.4, 0.6, 1],
                    delay: idx * 0.05 // Slight stagger for each letter/icon part
                  }}
                />
              </React.Fragment>
            ))}
          </svg>
        </div>

        {text && (
          <motion.div 
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-slate-500 dark:text-slate-400 font-medium tracking-widest text-sm uppercase flex items-center gap-4"
          >
            <div className="w-12 h-[1px] bg-gradient-to-r from-transparent to-slate-300 dark:to-slate-600" />
            <span className="bg-gradient-to-r from-slate-600 to-slate-400 dark:from-slate-300 dark:to-slate-500 bg-clip-text text-transparent">
              {text}
            </span>
            <div className="w-12 h-[1px] bg-gradient-to-l from-transparent to-slate-300 dark:to-slate-600" />
          </motion.div>
        )}
      </div>
    </div>
  );
};

