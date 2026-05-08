import React from 'react';
import { Building2, MapPin, Stethoscope, Phone } from 'lucide-react';
import { BRAND_IDENTITIES } from '../../constants';
import type { IdentityState } from '../../types';

interface QRConfig {
  enabled: boolean;
  type: string;
  label: string;
}

interface Props {
  identity: IdentityState;
  specialtyStrings: { fr: string; ar: string };
  contactString: string;
  selectedFont: string;
  selectedIdentity: string;
  selectedTheme: string;
  qrConfig: QRConfig;
  errors: Record<string, string>;
}

export const Step7Confirmation: React.FC<Props> = ({
  identity, specialtyStrings, contactString,
  selectedFont, selectedIdentity, selectedTheme,
  qrConfig, errors,
}) => (
  <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
    <div className="text-center">
      <h2 className="text-2xl font-black text-text-main tracking-tight">C'est presque prêt !</h2>
      <p className="text-slate-500 text-sm mt-1">Vérifiez vos préférences finales avant l'activation.</p>
    </div>
    <div className="space-y-4">
      <div className="p-6 bg-primary/5 rounded-3xl border border-border-main shadow-inner">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-sm font-black text-text-main uppercase tracking-tighter">Votre Cabinet</h3>
            <p className="text-lg font-bold text-primary">Dr. {identity.nomPraticien || '...'}</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-primary/5 flex items-center justify-center"><Building2 size={20} className="text-primary" /></div>
        </div>
        <div className="space-y-3 pt-4 border-t border-border-main">
          <div className="flex items-center gap-2 text-xs text-slate-600 font-medium"><MapPin size={14} className="text-slate-400" /> {identity.adresse || '...'}</div>
          <div className="flex items-center gap-2 text-xs text-slate-600 font-medium"><Stethoscope size={14} className="text-slate-400" /> {specialtyStrings.fr || '...'}</div>
          <div className="flex items-center gap-2 text-xs text-slate-600 font-medium"><Phone size={14} className="text-slate-400" /> {contactString || '...'}</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-primary/5 rounded-2xl border border-primary/10">
          <p className="text-[9px] font-black text-primary uppercase tracking-widest mb-1">Police & Identité</p>
          <p className="text-xs font-bold text-text-main capitalize">{selectedFont} / {BRAND_IDENTITIES.find(i => i.id === selectedIdentity)?.name}</p>
        </div>
        <div className="p-4 bg-emerald-50 rounded-2xl border border-emerald-100">
          <p className="text-[9px] font-black text-emerald-600 uppercase tracking-widest mb-1">Ambiance Applicative</p>
          <p className="text-xs font-bold text-text-main capitalize">{selectedTheme}</p>
        </div>
        <div className="p-4 bg-primary/5 rounded-2xl border border-primary/10 col-span-2">
          <p className="text-[9px] font-black text-primary uppercase tracking-widest mb-1">Signature Digitale</p>
          <p className="text-xs font-bold text-text-main capitalize">
            {qrConfig.enabled ? `${qrConfig.type} : ${qrConfig.label}` : 'Désactivée'}
          </p>
        </div>
      </div>
    </div>
    {errors.submit && <div className="p-4 bg-red-50 text-red-600 text-xs font-bold rounded-2xl border border-red-100 text-center">{errors.submit}</div>}
  </div>
);
