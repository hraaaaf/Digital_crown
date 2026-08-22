import React from 'react';
import { Check, Building2 } from 'lucide-react';
import { cn } from '../../../../utils/cn';
import type { ContactConfig, ContactType, IdentityState } from '../../types';

interface Props {
  contacts: ContactConfig;
  setContacts: React.Dispatch<React.SetStateAction<ContactConfig>>;
  identity: IdentityState;
  setIdentity: React.Dispatch<React.SetStateAction<IdentityState>>;
  errors: Record<string, string>;
}

export const Step3Contacts: React.FC<Props> = ({ contacts, setContacts, identity, setIdentity }) => (
  <div className="space-y-6 animate-in fade-in duration-300">
    <div className="text-center mb-8">
      <h2 className="text-2xl font-black text-slate-900">Contacts & Identifiants</h2>
      <p className="text-sm text-slate-500">Même bloc que Réglages › Profil Cabinet. Tout est facultatif à cette étape.</p>
    </div>

    <div className="space-y-3">
      {(['fixe', 'mobile', 'whatsapp', 'instagram'] as ContactType[]).map(type => (
        <div key={type} className={cn("p-4 rounded-2xl border-2 transition-all", contacts[type].enabled ? "border-primary bg-primary/5" : "border-slate-100 bg-white")}>
          <div className="flex items-center gap-3 mb-2">
            <button
              type="button"
              onClick={() => setContacts(prev => ({ ...prev, [type]: { ...prev[type], enabled: !prev[type].enabled } }))}
              className={cn("w-5 h-5 rounded flex items-center justify-center border-2 transition-all", contacts[type].enabled ? "bg-primary border-primary" : "border-slate-200")}
              aria-label={`${contacts[type].enabled ? 'Désactiver' : 'Activer'} ${type}`}
            >
              {contacts[type].enabled && <Check size={12} className="text-white" />}
            </button>
            <span className="font-bold text-slate-800 text-sm capitalize">{type}</span>
          </div>
          {contacts[type].enabled && (
            <input
              type="text"
              value={contacts[type].value}
              onChange={e => setContacts(prev => ({ ...prev, [type]: { ...prev[type], value: e.target.value } }))}
              className="w-full p-2.5 rounded-xl border border-slate-200 bg-white text-xs font-bold"
              placeholder={`Numéro ou pseudo ${type}...`}
            />
          )}
        </div>
      ))}
    </div>

    <section className="rounded-3xl border border-blue-100 bg-blue-50/50 p-4 sm:p-5">
      <div className="mb-4 flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white text-primary shadow-sm"><Building2 size={18} /></div>
        <div>
          <h3 className="text-sm font-black text-slate-800">Identifiants de l’établissement</h3>
          <p className="mt-1 text-[10px] text-slate-500">ICE, IF et INPE établissement appartiennent à la structure. Ils restent modifiables ensuite dans Réglages.</p>
        </div>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-1">I.C.E</label>
          <input
            type="text"
            value={identity.ice}
            onChange={e => setIdentity(prev => ({ ...prev, ice: e.target.value }))}
            className="w-full p-2.5 rounded-xl border border-slate-200 focus:ring-2 focus:ring-primary/20 transition-all font-bold text-slate-900 shadow-sm text-xs bg-white"
            placeholder="N° ICE"
          />
        </div>
        <div>
          <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-1">I.F</label>
          <input
            type="text"
            value={identity.if}
            onChange={e => setIdentity(prev => ({ ...prev, if: e.target.value }))}
            className="w-full p-2.5 rounded-xl border border-slate-200 focus:ring-2 focus:ring-primary/20 transition-all font-bold text-slate-900 shadow-sm text-xs bg-white"
            placeholder="Id. Fiscal"
          />
        </div>
        <div>
          <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-1">INPE établissement</label>
          <input
            type="text"
            value={identity.inpeEtablissement}
            onChange={e => setIdentity(prev => ({ ...prev, inpeEtablissement: e.target.value }))}
            className="w-full p-2.5 rounded-xl border border-slate-200 focus:ring-2 focus:ring-primary/20 transition-all font-bold text-slate-900 shadow-sm text-xs bg-white"
            placeholder="INPE établissement"
          />
        </div>
      </div>
    </section>
  </div>
);
