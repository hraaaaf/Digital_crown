import React from 'react';
import { Sparkles } from 'lucide-react';

interface CrownGuideProps {
  message: string;
}

export const CrownGuide: React.FC<CrownGuideProps> = React.memo(({ message }) => {
  return (
    <div
      data-testid="crown-guide"
      className="hidden xl:flex fixed bottom-8 right-8 z-[200] flex-col items-end gap-3 pointer-events-none"
    >
      <div className="bg-white/80 backdrop-blur-xl border border-primary/20 p-4 rounded-3xl rounded-br-none shadow-2xl max-w-[280px] animate-in slide-in-from-bottom-4 duration-500 pointer-events-auto">
        <p className="text-[11px] font-bold text-slate-700 leading-relaxed">
          {message}
        </p>
      </div>
      <div className="w-16 h-16 bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center shadow-2xl shadow-primary/40 animate-pulse pointer-events-auto cursor-help">
        <div className="absolute inset-0 rounded-full border-4 border-white/20 animate-ping duration-[3000ms]" />
        <Sparkles className="text-white" size={24} />
      </div>
    </div>
  );
});

CrownGuide.displayName = 'CrownGuide';
