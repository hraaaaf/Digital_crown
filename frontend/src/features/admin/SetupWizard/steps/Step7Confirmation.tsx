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
      <p className="text-text-muted text-sm mt-1">Ce résumé reflète les mêmes propriétaires de données que Réglages.</p>
    </div>

    <div className="space-y-4">
      <section className="p-5 sm:p-6 bg-card/60 rounded-3xl border border-border-main shadow-inner">
        <div className="flex justify-between items-start mb-4 gap-4">
          <div className="min-w-0">
            <p className="text-[9px] font-black text-text-main uppercase tracking-widest">Structure d’exercice</p>
            <h3 className="mt-1 text-lg font-black text-text-main break-words">{valueOrDash(identity.nomCabinet)}</h3>
          </div>
          <div className="w-10 h-10 shrink-0 rounded-xl bg-card flex items-center justify-center"><Building2 size={20} className="text-text-main" /></div>
        </div>
        <div className="space-y-3 pt-4 border-t border-border-main">
          <div className="flex items-start gap-2 text-xs text-text-main font-medium"><MapPin size={14} className="mt-0.5 shrink-0 text-text-muted" /> {valueOrDash(identity.adresse)}</div>
          <div className="flex items-start gap-2 text-xs text-text-main font-medium"><Stethoscope size={14} className="mt-0.5 shrink-0 text-text-muted" /> {valueOrDash(specialtyStrings.fr)}</div>
          <div className="flex items-start gap-2 text-xs text-text-main font-medium"><Phone size={14} className="mt-0.5 shrink-0 text-text-muted" /> {valueOrDash(contactString)}</div>
        </div>
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-2">
          <div className="rounded-xl bg-card p-3"><p className="text-[8px] font-black uppercase tracking-widest text-text-muted">ICE</p><p className="mt-1 text-[11px] font-bold break-all">{valueOrDash(identity.ice)}</p></div>
          <div className="rounded-xl bg-card p-3"><p className="text-[8px] font-black uppercase tracking-widest text-text-muted">IF</p><p className="mt-1 text-[11px] font-bold break-all">{valueOrDash(identity.if)}</p></div>
          <div className="rounded-xl bg-card p-3"><p className="text-[8px] font-black uppercase tracking-widest text-text-muted">INPE établissement</p><p className="mt-1 text-[11px] font-bold break-all">{valueOrDash(identity.inpeEtablissement)}</p></div>
        </div>
      </section>

      <section className="p-5 sm:p-6 bg-primary/5 rounded-3xl border border-primary/10">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 shrink-0 rounded-xl bg-card flex items-center justify-center text-text-main"><UserRound size={20} /></div>
          <div className="min-w-0">
            <p className="text-[9px] font-black text-text-main uppercase tracking-widest">Praticien principal</p>
            <p className="mt-1 text-sm font-black text-text-main break-words">{valueOrDash(identity.nomPraticien)}</p>
            {identity.nomPraticienAR && <p dir="rtl" className="mt-1 text-sm font-bold font-arabic text-text-main">{identity.nomPraticienAR}</p>}
            <div className="mt-3 flex items-center gap-2 text-xs text-text-main"><BadgeCheck size={14} className="text-text-main" /> INPE professionnel : {valueOrDash(identity.inpe)}</div>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="p-4 bg-primary/5 rounded-2xl border border-primary/10">
          <p className="text-[9px] font-black text-text-main uppercase tracking-widest mb-1">Police & Identité visuelle</p>
          <p className="text-xs font-bold text-text-main capitalize">{selectedFont} / {BRAND_IDENTITIES.find(i => i.id === selectedIdentity)?.name}</p>
        </div>
        <div className="p-4 bg-card rounded-2xl border border-border-main">
          <p className="text-[9px] font-black text-text-main uppercase tracking-widest mb-1">Design & Ambiance</p>
          <p className="text-xs font-bold text-text-main capitalize">{selectedTheme}</p>
        </div>
        <div className="p-4 bg-primary/5 rounded-2xl border border-primary/10 sm:col-span-2">
          <div className="flex items-start gap-3">
            <QrCode size={18} className="shrink-0 text-text-main" />
            <div>
              <p className="text-[9px] font-black text-text-main uppercase tracking-widest mb-1">QR Code</p>
              <p className="text-xs font-bold text-text-main">
                {qrConfig.enabled ? `${qrConfig.type} : ${qrConfig.label || 'Sans libellé'}` : 'Désactivé'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    {errors.submit && <div className="p-4 bg-danger-surface text-danger text-xs font-bold rounded-2xl border border-danger-border text-center">{errors.submit}</div>}
  </div>
);
