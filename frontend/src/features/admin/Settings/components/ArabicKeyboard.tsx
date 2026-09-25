import React from 'react';

interface ArabicKeyboardProps {
  onInput: (char: string) => void;
}

export const ArabicKeyboard: React.FC<ArabicKeyboardProps> = ({ onInput }) => {
  const letters = [
    'ض', 'ص', 'ث', 'ق', 'ف', 'غ', 'ع', 'ه', 'خ', 'ح', 'ج', 'د',
    'ش', 'س', 'ي', 'ب', 'ل', 'ا', 'ت', 'ن', 'م', 'ك', 'ط',
    'ئ', 'ء', 'ؤ', 'ر', 'لا', 'ى', 'ة', 'و', 'ز', 'ظ'
  ];

  return (
    <div 
      className="relative z-[60] grid w-[264px] grid-cols-7 gap-1 p-2 bg-slate-900 rounded-xl shadow-2xl border border-slate-700 animate-in fade-in zoom-in-95 duration-200 sm:w-[408px] sm:grid-cols-11 max-w-[calc(100vw-2rem)]"
      onMouseDown={(e) => e.preventDefault()}
      onClick={(e) => e.stopPropagation()}
    >
      {letters.map(l => (
        <button
          key={l}
          type="button"
          onClick={() => onInput(l)}
          className="w-8 h-8 flex items-center justify-center bg-slate-800 text-white rounded-md hover:bg-primary active:scale-95 transition-colors text-sm font-arabic"
        >
          {l}
        </button>
      ))}
      <button 
        type="button"
        onClick={() => onInput(' ')} 
        className="col-span-3 h-8 bg-slate-700 text-white rounded-md hover:bg-primary hover:scale-[1.02] active:scale-95 transition-all text-[10px] font-black uppercase tracking-widest"
      >
        Espace
      </button>
    </div>
  );
};
