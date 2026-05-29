import React from 'react';

import { motion, AnimatePresence } from 'framer-motion';

import { Lightbulb, ArrowUpRight } from 'lucide-react';
import { Link } from 'react-router-dom';

interface ClinicalTipBubbleProps {
  show: boolean;
  tip: string;
  onClose?: () => void;
  autoHideMs?: number;
  className?: string;
}

export const ClinicalTipBubble = ({ 
  show, 
  tip, 
  onClose,
  autoHideMs = 2000,
  className = "fixed left-6 top-6 w-64 z-[10001] pointer-events-none" 
}: ClinicalTipBubbleProps) => {
  const isEnabled = localStorage.getItem('clinical_tips_enabled') !== 'false';
  React.useEffect(() => {
    if (show && onClose && autoHideMs > 0) {
      const timer = setTimeout(() => {
        onClose();
      }, autoHideMs);
      return () => clearTimeout(timer);
    }
  }, [show, onClose, autoHideMs]);

  if (!isEnabled) return null;

  return (
    <div className={className}>
      <AnimatePresence>
        {show && (
          <motion.div
            initial={{ opacity: 0, x: -100, scale: 0.3, rotate: -20, skewX: -10 }}
            animate={{ opacity: 1, x: 0, scale: 1, rotate: 0, skewX: 0 }}
            exit={{ opacity: 0, x: 40, scale: 0.8, filter: 'blur(8px)', rotate: 5 }}
            transition={{ 
              type: "spring",
              stiffness: 450,
              damping: 20,
              mass: 0.8,
              velocity: 20
            }}
            className="pointer-events-auto"
          >
            <Link to="/science-hub" className="block group">
              {/* Glassmorphism Bubble */}
              <div 
                className="bg-white/80 backdrop-blur-2xl border border-white/50 p-4 rounded-2xl shadow-[0_20px_40px_rgba(0,0,0,0.1)] overflow-hidden transition-all duration-300 group-hover:bg-white group-hover:shadow-[0_30px_60px_rgba(0,0,0,0.15)] group-hover:border-primary/20"
                style={{ 
                  borderLeft: '4px solid var(--primary)',
                }}
              >
                {/* Subtle background glow */}
                <div className="absolute -top-10 -right-10 w-24 h-24 bg-primary/10 rounded-full blur-3xl" />
                
                <div className="flex items-start gap-3 relative z-10">
                  <div className="mt-0.5 p-1.5 rounded-lg bg-primary/10 text-primary shrink-0">
                    <Lightbulb size={14} className="animate-pulse" />
                  </div>
                  
                  <div className="space-y-1 font-outfit">
                    <div className="flex items-center justify-between">
                      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-primary/70">
                        Elite Clinical Tip
                      </p>
                      <ArrowUpRight size={12} className="text-primary opacity-0 group-hover:opacity-100 transition-all translate-y-1 group-hover:translate-y-0" />
                    </div>
                    <p className="text-[11.5px] leading-relaxed font-semibold text-slate-800">
                      {tip}
                    </p>
                    <div className="pt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                       <span className="text-[9px] font-black uppercase tracking-widest text-primary">Savoir Plus →</span>
                    </div>
                  </div>
                </div>

                {/* Decorative Element */}
                <div className="absolute top-0 right-0 p-1 opacity-10">
                  <Lightbulb size={40} />
                </div>
              </div>

              {/* Decorative side element (Tail) removed for fixed top-left placement */}
            </Link>
          </motion.div>

        )}
      </AnimatePresence>
    </div>
  );
};
