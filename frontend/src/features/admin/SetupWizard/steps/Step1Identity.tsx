import React from 'react';
import { Building2, Stethoscope, Type, UserRound } from 'lucide-react';
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
      <h2 className="text-2xl font-black text-text-main">Profil Cabinet</h2>
      <p className="text-sm text-slate-500">Les mêmes identités que dans Réglages, configurées une première fois.</p>
    </div>

    <section className="space-y-5 rounded-3xl border border-blue-100 bg-blue-50/50 p-4 sm:p-6">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white text-primary shadow-sm"><Building2 size={18} /></div>
        <div>
          <p className="text-[10px] font-black uppercase tracking-widest text-blue-700">Structure d’exercice · Source cabinet</p>
          <p className="mt-1 text-xs font-medium text-blue-900/70">Type, nom et adresse appartiennent à l’établissement.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <button
          type="button"
          onClick={() => setCabinetType('PRIVE')}
          className={cn(
            "p-5 rounded-2xl border-2 transition-all flex items-center sm:flex-col sm:items-center gap-3 text-left sm:text-center",
            cabinetType === 'PRIVE' ? "border-primary bg-white shadow-lg" : "border-slate-100 bg-white/70 opacity-70 hover:opacity-100"
          )}
        >
          <div className="w-11 h-11 shrink-0 rounded-xl bg-primary/10 flex items-center justify-center text-primary"><Building2 size={22} /></div>
          <div>
            <span className="block font-black text-text-main text-sm">Cabinet Privé</span>
            <span className="text-[10px] text-slate-500">Structure d’exercice privée</span>
          </div>
        </button>

        <button
          type="button"
          onClick={() => setCabinetType('CLINIQUE')}
          className={cn(
            "p-5 rounded-2xl border-2 transition-all flex items-center sm:flex-col sm:items-center gap-3 text-left sm:text-center",
            cabinetType === 'CLINIQUE' ? "border-emerald-500 bg-white shadow-lg" : "border-slate-100 bg-white/70 opacity-70 hover:opacity-100"
          )}
        >
          <div className="w-11 h-11 shrink-0 rounded-xl bg-emerald-100 flex items-center justify-center text-emerald-600"><Stethoscope size={22} /></div>
          <div>
            <span className="block font-black text-text-main text-sm">Clinique / Centre</span>
            <span className="text-[10px] text-slate-500">Structure multi-praticiens</span>
          </div>
        </button>
      </div>

      <div>
        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2">Nom de l’établissement *</label>
        <input
          type="text"
          value={identity.nomCabinet}
          onChange={e => setIdentity(prev => ({ ...prev, nomCabinet: e.target.value }))}
          className={cn("w-full p-4 rounded-xl border focus:ring-2 focus:ring-primary/20 transition-all font-bold text-text-main shadow-sm bg-input-field", errors.nomCabinet ? "border-red-300" : "border-border-main")}
          placeholder={cabinetType === 'CLINIQUE' ? "Ex: Centre Dentaire Al Massira" : "Ex: Cabinet Dentaire Alami"}
        />
      </div>

      <div>
        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2">Adresse complète *</label>
        <textarea
          value={identity.adresse}
          onChange={e => setIdentity(prev => ({ ...prev, adresse: e.target.value }))}
          className={cn("w-full p-4 rounded-xl border focus:ring-2 focus:ring-primary/20 transition-all font-medium text-slate-600 text-sm h-24 shadow-sm bg-input-field", errors.adresse ? "border-red-300" : "border-border-main")}
          placeholder="Étage, Résidence, Rue, Ville..."
        />
      </div>
    </section>

    <section className="space-y-5 rounded-3xl border border-primary/15 bg-primary/5 p-4 sm:p-6">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white text-primary shadow-sm"><UserRound size={18} /></div>
        <div>
          <p className="text-[10px] font-black uppercase tracking-widest text-primary">Praticien principal · Source compte praticien</p>
          <p className="mt-1 text-xs font-medium text-slate-600">Prérempli depuis votre compte. Les modifications suivent la même vérité que Réglages.</p>
        </div>
      </div>

      <div>
        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2">Nom du praticien *</label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
              type="button"
              onClick={() => setShowArKeyboard({ show: true, target: 'identity' })}
              className="absolute left-3 top-1/2 -translate-y-1/2 p-2 bg-slate-100 rounded-lg text-slate-400 hover:text-primary transition-colors"
              aria-label="Ouvrir le clavier arabe"
            >
              <Type size={16} />
            </button>
          </div>
        </div>
      </div>

      <div>
        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-2">INPE professionnel <span className="normal-case tracking-normal font-semibold">(optionnel)</span></label>
        <input
          type="text"
          value={identity.inpe}
          onChange={e => setIdentity(prev => ({ ...prev, inpe: e.target.value }))}
          className="w-full p-4 rounded-xl border border-border-main focus:ring-2 focus:ring-primary/20 transition-all font-bold text-text-main shadow-sm bg-input-field"
          placeholder="INPE du praticien"
        />
      </div>
    </section>
  </div>
);
