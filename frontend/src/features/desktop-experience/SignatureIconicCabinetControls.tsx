/** R4 07-B — opt-in styling control on genuine, authenticated Cabinet routes.
 * This is a local preview, never a saved user/workstation preference (R5).
 */
import { Eye, Sparkles } from 'lucide-react';

export type CabinetSignaturePreview = 'core' | 'iconic';

export function SignatureIconicCabinetControls({
  mode, onChange, persisted = false,
}: { mode: CabinetSignaturePreview; onChange: (mode: CabinetSignaturePreview) => void; persisted?: boolean }) {
  return (
    <div role="group" aria-label={persisted ? 'R5 · Signature du compte et poste' : "Aperçu Signature sur l'écran Cabinet réel"}
      className="dc07-r4-signature-controls" data-testid="r4-real-signature-preview">
      <span className="dc07-r4-signature-controls__label">{persisted
        ? 'R5 · Préférence enregistrable par compte et poste'
        : 'R4 · Aperçu local non persisté'}</span>
      <button type="button" aria-pressed={mode === 'core'} onClick={() => onChange('core')}
        className={persisted ? (mode === 'core'
          ? 'rounded-lg border-2 border-primary bg-primary/15 px-3 py-2 font-bold text-text-main ring-2 ring-primary/20'
          : 'rounded-lg border border-border-main px-3 py-2 text-text-main') : undefined}>
        <Eye size={15} aria-hidden="true" /> Signature Core
      </button>
      <button type="button" aria-pressed={mode === 'iconic'} onClick={() => onChange('iconic')}
        className={persisted ? (mode === 'iconic'
          ? 'rounded-lg border-2 border-primary bg-primary/15 px-3 py-2 font-bold text-text-main ring-2 ring-primary/20'
          : 'rounded-lg border border-border-main px-3 py-2 text-text-main') : undefined}>
        <Sparkles size={15} aria-hidden="true" /> Signature Iconic
      </button>
    </div>
  );
}
