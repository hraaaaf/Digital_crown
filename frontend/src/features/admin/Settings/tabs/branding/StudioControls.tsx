import React from 'react';
import { UserCircle, Link, Instagram, MessageCircle, MapPin, Shield, CreditCard, RotateCcw } from 'lucide-react';
import { cn } from '../../../../../utils/cn';
import { StudioControls as StudioControlsCore } from './StudioControlsCore';

interface StudioControlsProps {
  profile: any;
  updateProfile: (data: any) => void;
}

type QrKind = 'VCARD' | 'WEBSITE' | 'INSTAGRAM' | 'WHATSAPP' | 'LOCATION' | 'VALIDATION' | 'PAYMENT';

const QR_TYPES: Array<{ id: QrKind; label: string; icon: React.ReactNode }> = [
  { id: 'VCARD', label: 'Contact', icon: <UserCircle size={14} /> },
  { id: 'WEBSITE', label: 'Site Web', icon: <Link size={14} /> },
  { id: 'INSTAGRAM', label: 'Instagram', icon: <Instagram size={14} /> },
  { id: 'WHATSAPP', label: 'WhatsApp', icon: <MessageCircle size={14} /> },
  { id: 'LOCATION', label: 'Maps', icon: <MapPin size={14} /> },
  { id: 'VALIDATION', label: 'Vérification du document', icon: <Shield size={14} /> },
  { id: 'PAYMENT', label: 'Suivi du paiement', icon: <CreditCard size={14} /> },
];

const QR_HELP: Record<QrKind, { title: string; text: string; destination?: string }> = {
  VCARD: {
    title: 'Contact',
    text: 'Le QR crée une carte de contact à partir du profil du cabinet.',
  },
  WEBSITE: {
    title: 'Site Web',
    text: 'Le QR ouvre l’adresse Web saisie ci-dessous.',
  },
  INSTAGRAM: {
    title: 'Instagram',
    text: 'Le QR ouvre le profil Instagram indiqué ci-dessous.',
  },
  WHATSAPP: {
    title: 'WhatsApp',
    text: 'Le QR ouvre une conversation WhatsApp avec le numéro indiqué.',
  },
  LOCATION: {
    title: 'Maps',
    text: 'Le QR ouvre Google Maps à partir de l’adresse du cabinet enregistrée dans le profil.',
    destination: 'Source : adresse du cabinet',
  },
  VALIDATION: {
    title: 'Vérification du document',
    text: 'Le QR ouvre la page de vérification du document généré.',
    destination: '/api/documents/verify/<document>',
  },
  PAYMENT: {
    title: 'Suivi du paiement',
    text: 'Le QR ouvre l’état de paiement du document. Aucun paiement n’est encaissé ici.',
    destination: '/api/documents/track/<document>',
  },
};

const INPUT_COPY: Partial<Record<QrKind, { label: string; placeholder: string; help: string }>> = {
  WEBSITE: {
    label: 'Adresse du site Web',
    placeholder: 'https://cabinet.ma',
    help: 'Adresse complète ou domaine du site.',
  },
  INSTAGRAM: {
    label: 'Profil Instagram',
    placeholder: '@cabinet ou https://instagram.com/cabinet',
    help: 'Identifiant @cabinet ou URL complète.',
  },
  WHATSAPP: {
    label: 'Numéro WhatsApp',
    placeholder: '+212 6 00 00 00 00',
    help: 'Numéro destiné aux demandes de rendez-vous.',
  },
};

const DEFAULT_CONTENT_TOP_CM = 3.6;
const CONTENT_TOP_MIN_CM = 2.8;
const CONTENT_TOP_MAX_CM = 5.1;

const ContentPositionControl: React.FC<StudioControlsProps> = ({ profile, updateProfile }) => {
  const top = Number.isFinite(Number(profile.margin_top)) ? Number(profile.margin_top) : DEFAULT_CONTENT_TOP_CM;
  const offsetMm = Math.round((top - DEFAULT_CONTENT_TOP_CM) * 10);
  const positionLabel = offsetMm === 0 ? 'Neutre' : offsetMm < 0 ? `${Math.abs(offsetMm)} mm plus haut` : `${offsetMm} mm plus bas`;

  return (
    <div className="bg-[var(--card-bg)] border border-[var(--border-color)] rounded-2xl p-6 transition-shadow hover:shadow-[0_8px_24px_-16px_rgba(11,15,23,0.18)] hover:-translate-y-[2px]">
      <div className="flex items-start justify-between gap-4 mb-5">
        <div>
          <h3 className="font-bold text-[11px] text-[var(--text-muted)] tracking-[0.12em] uppercase">
            Position du contenu
          </h3>
          <p className="mt-1 text-[11px] leading-relaxed text-[var(--text-muted)]">
            Déplace verticalement le titre, les informations patient et le tableau. L’en-tête et le pied de page restent fixes.
          </p>
        </div>
        <button
          type="button"
          onClick={() => updateProfile({ margin_top: DEFAULT_CONTENT_TOP_CM })}
          className="shrink-0 flex items-center gap-1.5 rounded-lg border border-[var(--border-color)] px-2.5 py-1.5 text-[11px] font-medium text-[var(--text-muted)] hover:border-[var(--text-muted)] hover:text-[var(--text-main)] transition-colors"
          aria-label="Réinitialiser la position verticale du contenu"
        >
          <RotateCcw size={12} />
          0
        </button>
      </div>

      <div className="flex items-center justify-between mb-2 text-[11px] text-[var(--text-muted)]">
        <span>Plus haut</span>
        <span className="font-semibold text-[var(--text-main)]">{positionLabel}</span>
        <span>Plus bas</span>
      </div>
      <input
        aria-label="Position verticale du contenu"
        type="range"
        min={CONTENT_TOP_MIN_CM}
        max={CONTENT_TOP_MAX_CM}
        step="0.1"
        value={top}
        onChange={(event) => updateProfile({ margin_top: parseFloat(event.target.value) })}
        className="w-full h-1.5 bg-[var(--border-color)] rounded-full appearance-none outline-none accent-[var(--text-main)]"
      />
      <div className="mt-2 flex justify-between text-[10px] text-[var(--text-muted)]">
        <span>-8 mm</span>
        <span>Le moteur bloque automatiquement toute remontée qui chevaucherait l’en-tête.</span>
        <span>+15 mm</span>
      </div>
    </div>
  );
};

const QrTruthControls: React.FC<StudioControlsProps> = ({ profile, updateProfile }) => {
  const selected = (profile.qr_code_type || 'VCARD') as QrKind;
  const help = QR_HELP[selected] || QR_HELP.VCARD;
  const inputCopy = INPUT_COPY[selected];

  return (
    <div className="bg-[var(--card-bg)] border border-[var(--border-color)] rounded-2xl p-6 transition-shadow hover:shadow-[0_8px_24px_-16px_rgba(11,15,23,0.18)] hover:-translate-y-[2px]">
      <div className="flex items-center justify-between mb-5">
        <h3 className="font-bold text-[11px] text-[var(--text-muted)] tracking-[0.12em] uppercase">Code QR</h3>
        <button
          type="button"
          aria-label={profile.qr_code_enabled ? 'Désactiver le code QR' : 'Activer le code QR'}
          onClick={() => updateProfile({ qr_code_enabled: !profile.qr_code_enabled })}
          className={cn(
            'w-10 h-5 rounded-full relative px-0.5 flex items-center transition-colors',
            profile.qr_code_enabled ? 'bg-[var(--primary)]' : 'bg-[var(--border-color)]',
          )}
        >
          <div className={cn('w-4 h-4 bg-white rounded-full transition-transform', profile.qr_code_enabled ? 'translate-x-5' : 'translate-x-0')} />
        </button>
      </div>

      {profile.qr_code_enabled && (
        <>
          <div className="grid grid-cols-2 gap-3">
            {QR_TYPES.map((type) => {
              const isSelected = selected === type.id;
              return (
                <button
                  type="button"
                  key={type.id}
                  onClick={() => updateProfile({ qr_code_type: type.id })}
                  className={cn(
                    'min-h-[64px] flex flex-col items-center justify-center gap-2 p-3 rounded-xl border transition-all text-[11px] font-medium text-center leading-tight',
                    isSelected
                      ? 'border-[var(--text-main)] bg-[var(--bg-medical-pearl)] text-[var(--text-main)]'
                      : 'border-[var(--border-color)] hover:border-[var(--text-muted)] text-[var(--text-muted)] hover:text-[var(--text-main)]',
                  )}
                >
                  {type.icon}
                  <span>{type.label}</span>
                </button>
              );
            })}
          </div>

          <div className="mt-5 rounded-xl border border-[var(--border-color)] bg-[var(--bg-medical-pearl)] px-4 py-3">
            <p className="text-[12px] font-bold text-[var(--text-main)]">{help.title}</p>
            <p className="mt-1 text-[11px] leading-relaxed text-[var(--text-muted)]">{help.text}</p>
            {help.destination && (
              <p className="mt-2 break-all font-mono text-[10px] text-[var(--text-muted)]">Destination : {help.destination}</p>
            )}
          </div>

          {inputCopy && (
            <div className="mt-5 flex flex-col gap-4">
              <div>
                <label className="block text-[11px] text-[var(--text-muted)] mb-1">{inputCopy.label}</label>
                <input
                  type="text"
                  value={profile.qr_code_value || ''}
                  onChange={(event) => updateProfile({ qr_code_value: event.target.value })}
                  className="w-full bg-[var(--input-bg)] border border-[var(--border-color)] rounded-lg px-3 py-2 text-[13px] text-[var(--text-main)] outline-none focus:border-[var(--text-main)]"
                  placeholder={inputCopy.placeholder}
                />
                <p className="mt-1 text-[10px] text-[var(--text-muted)]">{inputCopy.help}</p>
              </div>
              <div>
                <label className="block text-[11px] text-[var(--text-muted)] mb-1">Texte sous le QR Code</label>
                <input
                  type="text"
                  value={profile.qr_code_label || ''}
                  onChange={(event) => updateProfile({ qr_code_label: event.target.value })}
                  className="w-full bg-[var(--input-bg)] border border-[var(--border-color)] rounded-lg px-3 py-2 text-[13px] text-[var(--text-main)] outline-none focus:border-[var(--text-main)]"
                  placeholder="Ex: Prenez RDV"
                />
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export const StudioControls: React.FC<StudioControlsProps> = (props) => (
  <div className="flex flex-col gap-5">
    <ContentPositionControl {...props} />
    {/* Le dernier bloc du core est l’ancien contrôle QR. Il reste byte-for-byte
        pour préserver l’historique, mais n’est plus présenté à l’utilisateur. */}
    <div className="[&>div>div:last-child]:hidden">
      <StudioControlsCore {...props} />
    </div>
    <QrTruthControls {...props} />
  </div>
);
