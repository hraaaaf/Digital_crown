import { motion, AnimatePresence } from 'framer-motion';
import { X, Brain } from 'lucide-react';
import type { ClinicalProtocol } from './types';
import { cn } from '../../utils/cn';
import { ClinicalRefContent } from './ClinicalRefContent';

interface SidebarProps {
  protocol: ClinicalProtocol;
  onClose: () => void;
  isOpen: boolean;
}

export const ClinicalRefSidebar: React.FC<SidebarProps> = ({ protocol, onClose, isOpen }) => {
  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div 
        initial={{ x: 340, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        exit={{ x: 340, opacity: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        className="fixed top-24 right-6 w-[340px] bg-white/80 backdrop-blur-2xl border border-slate-200/60 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.15)] rounded-[2.5rem] p-6 z-50 overflow-hidden flex flex-col max-h-[calc(100vh-120px)]"
      >
        {/* HEADER */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary/5 rounded-2xl flex items-center justify-center text-primary" style={{ color: 'var(--primary)' }}>
              <Brain size={20} />
            </div>
            <div>
              <h3 className="text-sm font-black text-slate-800 leading-tight uppercase tracking-tight">{protocol.act_names[0]}</h3>
              <div className="flex items-center gap-2 mt-0.5">
                <span className={cn(
                  "text-[8px] font-black px-1.5 py-0.5 rounded-md uppercase tracking-widest",
                  protocol.difficulty === 'complex' ? "bg-orange-50 text-orange-600" : 
                  protocol.difficulty === 'specialist' ? "bg-red-50 text-red-600" : "bg-emerald-50 text-emerald-600"
                )}>
                  {protocol.difficulty}
                </span>
                <span className="text-[8px] font-bold text-slate-400 uppercase">~{protocol.duration_min} MIN</span>
              </div>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-slate-100 rounded-xl transition-all text-slate-400">
            <X size={18} />
          </button>
        </div>

        <ClinicalRefContent protocol={protocol} />

        <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
          <span className="text-[9px] font-black text-slate-300 uppercase tracking-widest">Digital Crown Elite Ref</span>
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
        </div>
      </motion.div>
    </AnimatePresence>
  );
};
