import React from 'react';
import { Building2, MapPin, Stethoscope, Phone, BadgeCheck, UserRound, QrCode } from 'lucide-react';
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

const valueOrDash = (value?: string) => value?.trim() || 'Non renseigné';

export const Step7Confirmation: React.FC<Props> = ({
  identity, specialtyStrings, contactString,
  selectedFont, selectedIdentity, selectedTheme,
  qrConfig, errors,
}) => (
  <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
    <div className="text-center">
      <h2 className="text-2xl font-black text-text-main tracking-tight">Vérification finale</h2>
      <p className="text-slate-500 text-sm mt-1">Ce résumé reflète les mêmes propriétaires de données que Réglages.</p>
    </div>

    <div className="space-y-4">
      <section className="p-5 sm:p-6 bg-blue-50/60 rounded-3xl border border-blue-100 shadow-inner">
        <div className="flex justify-between items-start mb-4 gap-4">
          <div className="min-w-0">
            <p className="text-[9px] font-black text-blue-700 uppercase tracking-widest">Structure d’exercice</p>
            <h3 className="mt-1 text-lg font-black text-text-main break-words">{valueOrDash(identity.nomCabinet)}</h3>
          </div>
          <div className="w-10 h-10 shrink-0 rounded-xl bg-white flex items-center justify-center"><Building2 size={20} className="text-primary" /></div>
        </div>
        <div className="space-y-3 pt-4 border-t border-blue-100">
          <div className="flex items-start gap-2 text-xs text-slate-600 font-medium"><MapPin size={14} className="mt-0.5 shrink-0 text-slate-400" /> {valueOrDash(identity.adresse)}</div>
          <div className="flex items-start gap-2 text-xs text-slate-600 font-medium"><Stethoscope size={14} className="mt-0.5 shrink-0 text-slate-400" /> {valueOrDash(specialtyStrings.fr)}</div>
          <div className="flex items-start gap-2 text-xs text-slate-600 font-medium"><Phone size={14} className="mt-0.5 shrink-0 text-slate-400" /> {valueOrDash(contactString)}</div>
        </div>
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-2">
          <div className="rounded-xl bg-white p-3"><p className="text-[8px] font-black uppercase tracking-widest text-slate-400">ICE</p><p className="mt-1 text-[11px] font-bold break-all">{valueOrDash(identity.ice)}</p></div>
          <div className="rounded-xl bg-white p-3"><p className="text-[8px] font-black uppercase tracking-widest text-slate-400">IF</p><p className="mt-1 text-[11px] font-bold break-all">{valueOrDash(identity.if)}</p></div>
          <div className="rounded-xl bg-white p-3"><p className="text-[8px] font-black uppercase tracking-widest text-slate-400">INPE établissement</p><p className="mt-1 text-[11px] font-bold break-all">{valueOrDash(identity.inpeEtablissement)}</p></div>
        </div>
      </section>

      <section className="p-5 sm:p-6 bg-primary/5 rounded-3xl border border-primary/10">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 shrink-0 rounded-xl bg-white flex items-center justify-center text-primary"><UserRound size={20} /></div>
          <div className="min-w-0">
            <p className="text-[9px] font-black text-primary uppercase tracking-widest">Praticien principal</p>
            <p className="mt-1 text-sm font-black text-text-main break-words">{valueOrDash(identity.nomPraticien)}</p>
            {identity.nomPraticienAR && <p dir="rtl" className="mt-1 text-sm font-bold font-arabic text-slate-600">{identity.nomPraticienAR}</p>}
            <div className="mt-3 flex items-center gap-2 text-xs text-slate-600"><BadgeCheck size={14} className="text-primary" /> INPE professionnel : {valueOrDash(identity.inpe)}</div>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="p-4 bg-primary/5 rounded-2xl border border-primary/10">
          <p className="text-[9px] font-black text-primary uppercase tracking-widest mb-1">Police & Identité visuelle</p>
          <p className="text-xs font-bold text-text-main capitalize">{selectedFont} / {BRAND_IDENTITIES.find(i => i.id === selectedIdentity)?.name}</p>
        </div>
        <div className="p-4 bg-emerald-50 rounded-2xl border border-emerald-100">
          <p className="text-[9px] font-black text-emerald-600 uppercase tracking-widest mb-1">Design & Ambiance</p>
          <p className="text-xs font-bold text-text-main capitalize">{selectedTheme}</p>
        </div>
        <div className="p-4 bg-primary/5 rounded-2xl border border-primary/10 sm:col-span-2">
          <div className="flex items-start gap-3">
            <QrCode size={18} className="shrink-0 text-primary" />
            <div>
              <p className="text-[9px] font-black text-primary uppercase tracking-widest mb-1">QR Code</p>
              <p className="text-xs font-bold text-text-main">
                {qrConfig.enabled ? `${qrConfig.type} : ${qrConfig.label || 'Sans libellé'}` : 'Désactivé'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    {errors.submit && <div className="p-4 bg-red-50 text-red-600 text-xs font-bold rounded-2xl border border-red-100 text-center">{errors.submit}</div>}
  </div>
);
