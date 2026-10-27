/** R4 07-B — opt-in styling control on genuine, authenticated Cabinet routes.
 * This is a local preview, never a saved user/workstation preference (R5).
 */
import { Eye, Sparkles } from 'lucide-react';

export type CabinetSignaturePreview = 'core' | 'iconic';

export function SignatureIconicCabinetControls({
  mode, onChange,
}: { mode: CabinetSignaturePreview; onChange: (mode: CabinetSignaturePreview) => void }) {
  return (
    <div role="group" aria-label="Aperçu Signature sur l'écran Cabinet réel"
      className="dc07-r4-signature-controls" data-testid="r4-real-signature-preview">
      <span className="dc07-r4-signature-controls__label">R4 · Aperçu local non persisté</span>
      <button type="button" aria-pressed={mode === 'core'} onClick={() => onChange('core')}>
        <Eye size={15} aria-hidden="true" /> Signature Core
      </button>
      <button type="button" aria-pressed={mode === 'iconic'} onClick={() => onChange('iconic')}>
        <Sparkles size={15} aria-hidden="true" /> Signature Iconic
      </button>
    </div>
  );
}
