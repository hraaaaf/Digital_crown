import React from 'react';
import { Check } from 'lucide-react';
import { cn } from '../../../../utils/cn';
import type { ContactConfig, ContactType, IdentityState } from '../../types';

interface Props {
  contacts: ContactConfig;
  setContacts: React.Dispatch<React.SetStateAction<ContactConfig>>;
  identity: IdentityState;
  setIdentity: React.Dispatch<React.SetStateAction<IdentityState>>;
  errors: Record<string, string>;
}

export const Step3Contacts: React.FC<Props> = ({ contacts, setContacts, identity, setIdentity, errors }) => (
  <div className="space-y-6 animate-in fade-in duration-300">
    <div className="text-center mb-8">
      <h2 className="text-2xl font-black text-slate-900">Coordonnées</h2>
      <p className="text-sm text-slate-500">Comment les patients peuvent-ils vous joindre ?</p>
    </div>
    <div className="space-y-3">
      {(['fixe', 'mobile', 'whatsapp', 'instagram'] as ContactType[]).map(type => (
        <div key={type} className={cn("p-4 rounded-2xl border-2 transition-all", contacts[type].enabled ? "border-primary bg-primary/5" : "border-slate-100 bg-white")}>
          <div className="flex items-center gap-3 mb-2">
            <button
              onClick={() => setContacts(prev => ({ ...prev, [type]: { ...prev[type], enabled: !prev[type].enabled } }))}
              className={cn("w-5 h-5 rounded flex items-center justify-center border-2 transition-all", contacts[type].enabled ? "bg-primary border-primary" : "border-slate-200")}
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

    <div className="pt-4 border-t border-slate-100">
      <h3 className="text-sm font-black text-slate-800 mb-4">Identifiants Légaux (Optionnel)</h3>
      <p className="text-[10px] text-slate-500 mb-3">Requis pour les notes d'honoraires et devis.</p>
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'I.C.E', key: 'ice' as const, placeholder: 'N° ICE' },
          { label: 'I.F', key: 'if' as const, placeholder: 'Id. Fiscal' },
          { label: 'I.N.P.E', key: 'inpe' as const, placeholder: 'N° INPE' },
        ].map(({ label, key, placeholder }) => (
          <div key={key}>
            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-1">{label}</label>
            <input
              type="text"
              value={(identity as any)[key] || ''}
              onChange={e => setIdentity(prev => ({ ...prev, [key]: e.target.value }))}
              className="w-full p-2.5 rounded-xl border border-slate-200 focus:ring-2 focus:ring-primary/20 transition-all font-bold text-slate-900 shadow-sm text-xs"
              placeholder={placeholder}
            />
          </div>
        ))}
      </div>
    </div>
    {errors.contacts && <p className="text-[10px] text-red-500 font-bold text-center">{errors.contacts}</p>}
  </div>
);
