import React from 'react';
import { Building2, Stethoscope, Type } from 'lucide-react';
import { cn } from '../../../../utils/cn';
import type { IdentityState } from '../../types';

interface Props {
  cabinetType: 'PRIVE' | 'CLINIQUE';
  setCabinetType: (v: 'PRIVE' | 'CLINIQUE') => void;
  identity: IdentityState;
  setIdentity: React.Dispatch<React.SetStateAction<IdentityState>>;
  errors: Record<string, string>;
  setShowArKeyboard: React.Dispatch<React.SetStateAction<{ show: boolean; target: 'identity' | 'custom_spec' }>>;
}

export const Step1Identity: React.FC<Props> = ({
  cabinetType, setCabinetType, identity, setIdentity, errors, setShowArKeyboard,
}) => (
  <div className="space-y-6 animate-in fade-in duration-300">
    <div className="text-center mb-8">
      <h2 className="text-2xl font-black text-text-main">Structure du Cabinet</h2>
      <p className="text-sm text-slate-500">Définissez le mode d'exercice de votre cabinet.</p>
    </div>

    <div className="grid grid-cols-2 gap-4 mb-8">
      <button
        onClick={() => setCabinetType('PRIVE')}
        className={cn(
          "p-6 rounded-3xl border-2 transition-all flex flex-col items-center gap-3",
          cabinetType === 'PRIVE' ? "border-primary bg-primary/5 shadow-lg" : "border-slate-100 opacity-60 grayscale hover:grayscale-0 hover:opacity-100"
        )}
      >
        <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary"><Building2 size={24} /></div>
        <div className="text-center">
          <span className="block font-black text-text-main text-sm">Cabinet Privé</span>
          <span className="text-[10px] text-slate-500">Mono-praticien</span>
        </div>
      </button>

      <button
        onClick={() => setCabinetType('CLINIQUE')}
        className={cn(
          "p-6 rounded-3xl border-2 transition-all flex flex-col items-center gap-3",
          cabinetType === 'CLINIQUE' ? "border-emerald-500 bg-emerald-50 shadow-lg" : "border-slate-100 opacity-60 grayscale hover:grayscale-0 hover:opacity-100"
        )}
      >
        <div className="w-12 h-12 rounded-2xl bg-emerald-100 flex items-center justify-center text-emerald-600"><Stethoscope size={24} /></div>
        <div className="text-center">
          <span className="block font-black text-text-main text-sm">Clinique / Centre</span>
          <span className="text-[10px] text-slate-500">Multi-spécialistes</span>
        </div>
      </button>
    </div>

    <div className="space-y-4 pt-4 border-t border-slate-100">
      <div>
        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2">Nom de l'établissement *</label>
        <input
          type="text"
          value={identity.nomCabinet}
          onChange={e => setIdentity(prev => ({ ...prev, nomCabinet: e.target.value }))}
          className={cn("w-full p-4 rounded-xl border focus:ring-2 focus:ring-primary/20 transition-all font-bold text-text-main shadow-sm bg-input-field", errors.nomCabinet ? "border-red-300" : "border-border-main")}
          placeholder={cabinetType === 'CLINIQUE' ? "Ex: Centre Dentaire Al Massira" : "Ex: Cabinet Dr. Alami"}
        />
      </div>
      <div>
        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2">Praticien Principal / Titulaire *</label>
        <div className="grid grid-cols-2 gap-4">
          <input
            type="text"
            value={identity.nomPraticien}
            onChange={e => setIdentity(prev => ({ ...prev, nomPraticien: e.target.value }))}
            className={cn("w-full p-4 rounded-xl border focus:ring-2 focus:ring-primary/20 transition-all font-bold text-text-main shadow-sm bg-input-field", errors.nomPraticien ? "border-red-300" : "border-border-main")}
            placeholder="Dr. Jean Dupont"
          />
          <div className="relative">
            <input
              type="text"
              dir="rtl"
              value={identity.nomPraticienAR}
              onChange={e => setIdentity(prev => ({ ...prev, nomPraticienAR: e.target.value }))}
              onFocus={() => setShowArKeyboard({ show: true, target: 'identity' })}
              className={cn("w-full p-4 rounded-xl border focus:ring-2 focus:ring-primary/20 transition-all font-bold text-text-main shadow-sm font-arabic text-lg bg-input-field", errors.nomPraticien ? "border-red-300" : "border-border-main")}
              placeholder="د. الإسم الكامل"
            />
            <button
              onClick={() => setShowArKeyboard({ show: true, target: 'identity' })}
              className="absolute left-3 top-1/2 -translate-y-1/2 p-2 bg-slate-100 rounded-lg text-slate-400 hover:text-primary transition-colors"
            >
              <Type size={16} />
            </button>
          </div>
        </div>
      </div>
      <div>
        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2">Adresse Professionnelle *</label>
        <textarea
          value={identity.adresse}
          onChange={e => setIdentity(prev => ({ ...prev, adresse: e.target.value }))}
          className={cn("w-full p-4 rounded-xl border focus:ring-2 focus:ring-primary/20 transition-all font-medium text-slate-600 text-sm h-24 shadow-sm", errors.adresse ? "border-red-300" : "border-slate-200")}
          placeholder="Étage, Résidence, Rue, Ville..."
        />
      </div>
    </div>
  </div>
);
