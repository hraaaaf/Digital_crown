import React from 'react';
import { Delete, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface ArabicKeyboardProps {
  value: string;
  onChange: (val: string) => void;
  onClose: () => void;
  show: boolean;
}

const ARABIC_CHARS = [
  ["ض", "ص", "ث", "ق", "ف", "غ", "ع", "ه", "خ", "ح", "ج", "د"],
  ["ش", "س", "ي", "ب", "ل", "ا", "ت", "ن", "م", "ك", "ط"],
  ["ئ", "ء", "ؤ", "ر", "لا", "ى", "ة", "و", "ز", "ظ"]
];

const DIACRITICS = ["َ", "ِ", "ُ", "ْ", "ّ", "ً", "ٍ", "ٌ"];

export const ArabicKeyboard: React.FC<ArabicKeyboardProps> = ({ value, onChange, onClose, show }) => {
  if (!show) return null;

  return (
    <AnimatePresence>
      <motion.div 
        drag
        dragConstraints={{ left: -500, right: 500, top: -500, bottom: 50 }}
        dragMomentum={false}
        initial={{ opacity: 0, y: 20, x: "-50%" }}
        animate={{ opacity: 1, y: 0, x: "-50%" }}
        exit={{ opacity: 0, y: 20, x: "-50%" }}
        className="fixed bottom-8 left-1/2 z-[100] w-full max-w-2xl bg-slate-900/95 backdrop-blur-xl p-6 pt-3 rounded-[2.5rem] border border-white/10 shadow-2xl ring-1 ring-white/20 cursor-grab active:cursor-grabbing"
      >
        <div className="w-12 h-1 bg-white/20 rounded-full mx-auto mb-4" />
        
        <div className="flex justify-between items-center mb-4 px-2">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Clavier Arabe Intelligent</span>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-full transition-colors text-slate-400 hover:text-white"
          >
            <X size={18} />
          </button>
        </div>

        <div className="space-y-2">
          {ARABIC_CHARS.map((row, i) => (
            <div key={i} className="flex justify-center gap-1.5">
              {row.map(char => (
                <button
                  key={char}
                  onClick={() => onChange(value + char)}
                  className="w-12 h-12 flex items-center justify-center bg-white/5 hover:bg-primary hover:text-white border border-white/5 rounded-xl text-lg font-arabic transition-all shadow-sm active:scale-90 text-slate-200"
                >
                  {char}
                </button>
              ))}
              {i === 2 && (
                <button
                  onClick={() => onChange(value.slice(0, -1))}
                  className="px-6 h-12 flex items-center justify-center bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 hover:bg-red-500 hover:text-white transition-all active:scale-95"
                >
                  <Delete size={20} />
                </button>
              )}
            </div>
          ))}
          
          <div className="flex justify-center gap-1.5 pt-2 border-t border-white/5">
            {DIACRITICS.map(char => (
              <button
                key={char}
                onClick={() => onChange(value + char)}
                className="w-10 h-10 flex items-center justify-center bg-emerald-500/5 hover:bg-emerald-500 hover:text-white border border-emerald-500/10 rounded-lg text-lg font-arabic transition-all active:scale-90 text-emerald-400"
              >
                {char}
              </button>
            ))}
            <button
              onClick={() => onChange(value + ' ')}
              className="px-16 h-10 flex items-center justify-center bg-white/5 hover:bg-white/10 border border-white/5 rounded-lg text-xs font-black uppercase tracking-widest text-slate-400 transition-all active:scale-95"
            >
              Espace
            </button>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};
