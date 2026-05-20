import React from 'react';
import { QrCode, Phone, Camera, MessageSquare, MapPin, Sparkles, CheckCircle2, Image as ImageIcon } from 'lucide-react';
import { cn } from '../../../../utils/cn';

interface QRConfig {
  enabled: boolean;
  type: 'VCARD' | 'WEBSITE' | 'INSTAGRAM' | 'VALIDATION' | 'PAYMENT' | 'WHATSAPP' | 'LOCATION';
  value: string;
  label: string;
  color: string | null;
  style: string;
}

interface Props {
  qrConfig: QRConfig;
  setQrConfig: React.Dispatch<React.SetStateAction<QRConfig>>;
}

const QR_OPTIONS = [
  { id: 'VCARD', label: 'Contact (vCard)', icon: Phone, desc: 'Ajout auto répertoire' },
  { id: 'WEBSITE', label: 'Site Web', icon: ImageIcon, desc: 'Lien vers cabinet' },
  { id: 'INSTAGRAM', label: 'Instagram', icon: Camera, desc: 'Suivi réseaux' },
  { id: 'WHATSAPP', label: 'WhatsApp', icon: MessageSquare, desc: 'Contact direct' },
  { id: 'LOCATION', label: 'Localisation', icon: MapPin, desc: 'GPS Cabinet' },
  { id: 'PAYMENT', label: 'Suivi Paiement', icon: Sparkles, desc: 'Progression & Règlements' },
  { id: 'VALIDATION', label: 'Authenticité', icon: CheckCircle2, desc: 'Vérification doc' },
] as const;

export const StepQR: React.FC<Props> = ({ qrConfig, setQrConfig }) => (
  <div className="space-y-6 animate-in fade-in duration-300">
    <div className="text-center mb-8">
      <h2 className="text-2xl font-black text-slate-900">Signature Digitale</h2>
      <p className="text-sm text-slate-500">Transformez vos documents en passerelles interactives.</p>
    </div>

    <div className="p-6 rounded-[2.5rem] bg-slate-50 border-2 border-slate-100 space-y-6">
      <div className="flex items-center justify-between p-4 bg-white rounded-3xl shadow-sm border border-slate-100">
        <div className="flex items-center gap-3">
          <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center transition-colors", qrConfig.enabled ? "bg-primary/10 text-primary" : "bg-slate-100 text-slate-400")}>
            <QrCode size={20} />
          </div>
          <div>
            <p className="text-sm font-black text-slate-800 uppercase tracking-tighter">Activer le QR Code</p>
            <p className="text-[10px] text-slate-400 font-medium">Affiché sur tous les documents PDF</p>
          </div>
        </div>
        <button
          onClick={() => setQrConfig(prev => ({ ...prev, enabled: !prev.enabled }))}
          className={cn("w-12 h-6 rounded-full transition-all relative", qrConfig.enabled ? "bg-primary" : "bg-slate-200")}
        >
          <div className={cn("absolute top-1 w-4 h-4 bg-white rounded-full transition-all", qrConfig.enabled ? "right-1" : "left-1")} />
        </button>
      </div>

      {qrConfig.enabled && (
        <div className="space-y-4 animate-in slide-in-from-top-4 duration-300">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest text-center">Objectif du Scan</p>
          <div className="grid grid-cols-2 gap-3">
            {QR_OPTIONS.map(opt => (
              <button
                key={opt.id}
                onClick={() => setQrConfig(prev => ({ ...prev, type: opt.id as QRConfig['type'] }))}
                className={cn(
                  "p-4 rounded-3xl border-2 transition-all flex flex-col items-center text-center gap-2",
                  qrConfig.type === opt.id ? "border-primary bg-white shadow-xl shadow-primary/5" : "border-transparent bg-white/50 hover:bg-white"
                )}
              >
                <opt.icon size={20} className={qrConfig.type === opt.id ? "text-primary" : "text-slate-400"} />
                <div>
                  <p className="text-[10px] font-black text-slate-800">{opt.label}</p>
                  <p className="text-[8px] text-slate-400 font-medium leading-tight">{opt.desc}</p>
                </div>
              </button>
            ))}
          </div>

          {['WEBSITE', 'INSTAGRAM'].includes(qrConfig.type) && (
            <div className="space-y-2 animate-in fade-in duration-300">
              <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block px-2">
                {qrConfig.type === 'WEBSITE' ? 'URL du Site Web' : 'Pseudo Instagram'}
              </label>
              <input
                type="text"
                value={qrConfig.value}
                onChange={e => setQrConfig(prev => ({ ...prev, value: e.target.value }))}
                className="w-full p-3.5 rounded-2xl border-2 border-slate-100 focus:border-primary bg-white transition-all font-bold text-xs"
                placeholder={qrConfig.type === 'WEBSITE' ? 'www.moncabinet.ma' : '@mon_cabinet_dentaire'}
              />
            </div>
          )}

          <div className="space-y-2">
            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block px-2">Texte d'accompagnement</label>
            <input
              type="text"
              value={qrConfig.label}
              onChange={e => setQrConfig(prev => ({ ...prev, label: e.target.value }))}
              className="w-full p-3.5 rounded-2xl border-2 border-slate-100 focus:border-primary bg-white transition-all font-bold text-xs"
              placeholder="Ex: Scannez pour me contacter..."
            />
          </div>
        </div>
      )}
    </div>
  </div>
);
