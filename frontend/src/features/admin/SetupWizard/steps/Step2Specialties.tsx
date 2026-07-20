import React from 'react';
import { Check, Plus, X, Type } from 'lucide-react';
import { cn } from '../../../../utils/cn';
import { SPECIALTIES_DICT } from '../../constants';
import type { ContactType } from '../../types';

interface Props {
  selectedSpecialties: string[];
  setSelectedSpecialties: React.Dispatch<React.SetStateAction<string[]>>;
  customSpecialty: { fr: string; ar: string };
  setCustomSpecialty: React.Dispatch<React.SetStateAction<{ fr: string; ar: string }>>;
  showCustomModal: boolean;
  setShowCustomModal: React.Dispatch<React.SetStateAction<boolean>>;
  errors: Record<string, string>;
  setShowArKeyboard: React.Dispatch<React.SetStateAction<{ show: boolean; target: 'identity' | 'custom_spec' }>>;
}

// Suppress unused import warning — ContactType may be needed by parent
void (null as unknown as ContactType);

export const Step2Specialties: React.FC<Props> = ({
  selectedSpecialties, setSelectedSpecialties,
  customSpecialty, setCustomSpecialty,
  showCustomModal, setShowCustomModal,
  errors, setShowArKeyboard,
}) => (
  <div className="space-y-6 animate-in fade-in duration-300">
    <div className="text-center mb-6">
      <h2 className="text-2xl font-black text-slate-900">Spécialités</h2>
      <p className="text-sm text-slate-500">Sélectionnez vos domaines d'expertise.</p>
    </div>

    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-3">
        {SPECIALTIES_DICT.map((spec) => (
          <button
            key={spec.id}
            onClick={() => {
              setSelectedSpecialties(prev =>
                prev.includes(spec.id) ? prev.filter(id => id !== spec.id) : [...prev, spec.id]
              );
            }}
            className={cn(
              "p-4 rounded-2xl border-2 text-left transition-all relative overflow-hidden group bg-card",
              selectedSpecialties.includes(spec.id)
                ? "border-primary bg-primary/5 shadow-md"
                : "border-border-main hover:border-border-hover"
            )}
          >
            <div className="flex items-center gap-3 mb-1">
              <div className={cn(
                "w-16 h-16 rounded-2xl flex items-center justify-center transition-all duration-300",
                selectedSpecialties.includes(spec.id)
                  ? "bg-primary text-white shadow-xl shadow-primary/30 scale-105"
                  : "bg-background text-text-muted group-hover:bg-primary/10 group-hover:text-primary group-hover:scale-105"
              )}>
                <spec.icon size={32} />
              </div>
              <span className={cn(
                "font-black text-xs transition-colors",
                selectedSpecialties.includes(spec.id) ? "text-primary" : "text-slate-900"
              )}>{spec.fr}</span>
            </div>
            <div className="text-[10px] text-slate-400 font-medium text-right font-arabic">{spec.ar}</div>
            {selectedSpecialties.includes(spec.id) && (
              <div className="absolute top-2 right-2 w-4 h-4 rounded-full bg-primary flex items-center justify-center">
                <Check size={10} className="text-white" />
              </div>
            )}
          </button>
        ))}

        <button
          onClick={() => setShowCustomModal(true)}
          className="p-4 rounded-2xl border-2 border-dashed border-slate-200 flex items-center justify-center gap-2 text-slate-500 hover:border-primary hover:text-primary transition-all"
        >
          <Plus size={16} />
          <span className="font-bold text-xs">Autre spécialité...</span>
        </button>
      </div>
    </div>

    {showCustomModal && (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
        <div className="bg-white w-full max-w-md rounded-[32px] overflow-hidden shadow-2xl border border-white/20 animate-in zoom-in-95 duration-200">
          <div className="p-8 space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-black text-slate-900">Spécialité Personnalisée</h3>
              <button onClick={() => setShowCustomModal(false)} className="p-2 rounded-full hover:bg-slate-100"><X size={20} /></button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-1">En Français</label>
                <input
                  type="text"
                  value={customSpecialty.fr}
                  onChange={e => setCustomSpecialty(prev => ({ ...prev, fr: e.target.value }))}
                  className="w-full p-4 rounded-xl border border-slate-200 focus:ring-2 focus:ring-primary/20 transition-all font-bold text-slate-900"
                  placeholder="Ex: Pédodontie"
                />
              </div>
              <div>
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-1">En Arabe (Clavier)</label>
                <div className="relative">
                  <input
                    type="text"
                    dir="rtl"
                    value={customSpecialty.ar}
                    onChange={e => setCustomSpecialty(prev => ({ ...prev, ar: e.target.value }))}
                    onFocus={() => setShowArKeyboard({ show: true, target: 'custom_spec' })}
                    className="w-full p-4 rounded-xl border border-slate-200 focus:ring-2 focus:ring-primary/20 transition-all font-bold text-slate-900 font-arabic text-lg"
                    placeholder="Ex: طب أسنان الأطفال"
                  />
                  <button
                    onClick={() => setShowArKeyboard({ show: true, target: 'custom_spec' })}
                    className="absolute left-3 top-1/2 -translate-y-1/2 p-2 bg-slate-100 rounded-lg text-slate-400 hover:text-primary transition-colors"
                  >
                    <Type size={16} />
                  </button>
                </div>
              </div>
            </div>
            <button
              onClick={() => setShowCustomModal(false)}
              className="w-full py-4 bg-primary text-white rounded-2xl font-black text-sm"
            >
              Valider
            </button>
          </div>
        </div>
      </div>
    )}
    {errors.specialties && <p className="text-[10px] text-red-500 font-bold text-center">{errors.specialties}</p>}
  </div>
);
