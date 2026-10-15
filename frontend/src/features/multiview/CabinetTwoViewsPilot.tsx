import { useRef, useState, useSyncExternalStore, type KeyboardEvent, type PointerEvent } from 'react';
import { PatientMediaTimeline } from '../patients/components/PatientMediaTimeline';
import { OrthoLongitudinalComparePanel } from '../ortho/OrthoLongitudinalComparePanel';
import { ViewSlotThemeFrame } from './ViewSlotThemeFrame';

const DESKTOP = '(min-width: 1280px)';
const MIN_RATIO = 37;
const MAX_RATIO = 63;

function observeDesktop(callback: () => void): () => void {
  if (typeof window === 'undefined' || !window.matchMedia) return () => undefined;
  const mq = window.matchMedia(DESKTOP);
  mq.addEventListener('change', callback);
  return () => mq.removeEventListener('change', callback);
}
function desktopSnapshot(): boolean {
  return typeof window !== 'undefined' && Boolean(window.matchMedia?.(DESKTOP).matches);
}
function clamp(value: number): number {
  return Math.max(MIN_RATIO, Math.min(MAX_RATIO, Math.round(value)));
}

export interface CabinetTwoViewsPatient {
  id: number;
  numero_dossier: string;
  nom: string;
  prenom: string;
  date_naissance: string;
  telephone: string;
  email?: string;
  assurance: string;
  antecedents_medicaux?: string;
  motif_consultation?: string;
  dossier?: { is_ortho_active: boolean };
}

export interface CabinetTwoViewsPilotProps {
  patient: CabinetTwoViewsPatient;
  canCephalo: boolean;
}

type LeftView = 'dossier' | 'suivi';

/**
 * Protected-route opt-in ONLY. One patient, two independently scrollable
 * presentation frames, actual parent patient data and the existing media/ortho
 * components. The parent route owns patient, tenant and RBAC boundaries.
 *
 * No patient data or workspace preferences are persisted. This is NOT the full
 * arbitrary-module MultiView registry. Never enable outside test before gates.
 */
export function CabinetTwoViewsPilot({ patient, canCephalo }: CabinetTwoViewsPilotProps) {
  const desktop = useSyncExternalStore(observeDesktop, desktopSnapshot, () => false);
  const [leftView, setLeftView] = useState<LeftView>('dossier');
  const [leftFirst, setLeftFirst] = useState(true);
  const [ratio, setRatio] = useState(45);
  const containerRef = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);
  const media = <PatientMediaTimeline patientId={patient.id} />;

  if (!desktop || !Number.isInteger(patient.id) || patient.id <= 0) return media;

  const updateRatio = (event: PointerEvent<HTMLDivElement>) => {
    if (!dragging.current || !containerRef.current) return;
    const bounds = containerRef.current.getBoundingClientRect();
    if (bounds.width <= 0) return;
    const x = leftFirst ? event.clientX - bounds.left : bounds.right - event.clientX;
    setRatio(clamp((100 * x) / bounds.width));
  };
  const onSeparatorKey = (event: KeyboardEvent<HTMLDivElement>) => {
    const direction = leftFirst ? 1 : -1;
    if (event.key === 'ArrowLeft') {
      event.preventDefault();
      setRatio(value => clamp(value - 5 * direction));
    } else if (event.key === 'ArrowRight') {
      event.preventDefault();
      setRatio(value => clamp(value + 5 * direction));
    } else if (event.key === 'Home') {
      event.preventDefault();
      setRatio(MIN_RATIO);
    } else if (event.key === 'End') {
      event.preventDefault();
      setRatio(MAX_RATIO);
    }
  };

  return (
    <section data-v15-07-two-views aria-label="Vues multiples du patient actif" className="min-w-0 space-y-2">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-elite-sm border border-border-main bg-card px-3 py-2 text-text-main">
        <div>
          <p className="text-sm font-semibold">Vues multiples — même patient</p>
          <p className="text-xs text-text-muted">Dossier et médias authentifiés · bureau uniquement</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <label className="flex items-center gap-2 text-xs text-text-main">
            Vue de gauche
            <select
              aria-label="Contenu du premier panneau"
              value={leftView}
              onChange={e => setLeftView(e.target.value === 'suivi' ? 'suivi' : 'dossier')}
              className="rounded-lg border border-border-main bg-input-field px-2 py-2 text-text-main focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            >
              <option value="dossier">Dossier patient</option>
              {canCephalo && <option value="suivi">Suivi T0 / T1</option>}
            </select>
          </label>
          <button
            type="button"
            onClick={() => setLeftFirst(v => !v)}
            className="rounded-lg border border-border-main bg-input-field px-3 py-2 text-xs font-semibold text-text-main focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            Échanger les vues
          </button>
          <button
            type="button"
            onClick={() => { setRatio(45); setLeftFirst(true); setLeftView('dossier'); }}
            className="rounded-lg border border-border-main bg-input-field px-3 py-2 text-xs font-semibold text-text-main focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          >
            Réinitialiser
          </button>
        </div>
      </div>

      <div
        ref={containerRef}
        data-v15-07-split-container
        className="flex h-[min(68vh,760px)] min-h-[450px] min-w-0 gap-0 overflow-hidden"
        style={{ flexDirection: leftFirst ? 'row' : 'row-reverse' }}
      >
        <div data-v15-07-first-pane className="h-full min-w-0 shrink-0" style={{ flexBasis: ratio + '%' }}>
          {leftView === 'dossier' || !canCephalo ? (
            <ViewSlotThemeFrame fillHeight title="Dossier patient" description="Données réellement chargées dans le dossier actif">
              <dl data-v15-07-real-dossier className="grid min-w-0 gap-3 text-sm">
                {([
                  ['Patient', [patient.prenom, patient.nom].filter(Boolean).join(' ')],
                  ['N° de dossier', patient.numero_dossier],
                  ['Naissance', patient.date_naissance],
                  ['Téléphone', patient.telephone],
                  ['Courriel', patient.email],
                  ['Assurance', patient.assurance],
                  ['Antécédents médicaux', patient.antecedents_medicaux],
                  ['Motif de consultation', patient.motif_consultation],
                ] as const).map(([label, value]) => (
                  <div key={label} className="min-w-0 rounded-lg border border-border-main bg-medical-pearl p-3">
                    <dt className="text-xs font-semibold text-text-muted">{label}</dt>
                    <dd className="mt-1 whitespace-pre-wrap break-words font-medium text-text-main">{value || 'Non renseigné'}</dd>
                  </div>
                ))}
              </dl>
            </ViewSlotThemeFrame>
          ) : (
            <ViewSlotThemeFrame fillHeight title="Suivi orthodontique T0 / T1" description="Comparaison existante, sans activation de superposition scientifique">
              <OrthoLongitudinalComparePanel patientId={patient.id} />
            </ViewSlotThemeFrame>
          )}
        </div>
        <div
          role="separator"
          aria-label="Redimensionner les vues"
          aria-orientation="vertical"
          aria-valuemin={MIN_RATIO}
          aria-valuemax={MAX_RATIO}
          aria-valuenow={ratio}
          tabIndex={0}
          onKeyDown={onSeparatorKey}
          onPointerDown={event => {
            dragging.current = true;
            event.currentTarget.setPointerCapture(event.pointerId);
          }}
          onPointerMove={updateRatio}
          onPointerUp={event => {
            dragging.current = false;
            if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
          }}
          onPointerCancel={() => { dragging.current = false; }}
          className="group relative z-10 flex w-3 shrink-0 cursor-col-resize touch-none items-center justify-center bg-medical-pearl outline-none focus-visible:ring-2 focus-visible:ring-primary"
        >
          <span aria-hidden="true" className="h-14 w-1 rounded-full bg-border-main group-hover:bg-primary" />
        </div>
        <div data-v15-07-second-pane className="h-full min-w-0 flex-1">
          <ViewSlotThemeFrame fillHeight title="Images et photographies" description="Médiathèque clinique existante — T0 / T1 / T2">
            {media}
          </ViewSlotThemeFrame>
        </div>
      </div>
    </section>
  );
}
