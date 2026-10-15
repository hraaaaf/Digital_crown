import { useSyncExternalStore } from 'react';
import { PatientMediaTimeline } from '../patients/components/PatientMediaTimeline';
import { ViewSlotThemeFrame } from './ViewSlotThemeFrame';

const DESKTOP_QUERY = '(min-width: 1280px)';

// The existing protected Cabinet/Patient route must authorize the patient first.
// This purely presentational opt-in is NOT a new RBAC or patient authorization gate.
function observeDesktop(onChange: () => void): () => void {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return () => undefined;
  }
  const query = window.matchMedia(DESKTOP_QUERY);
  query.addEventListener('change', onChange);
  return () => query.removeEventListener('change', onChange);
}

function desktopSnapshot(): boolean {
  return typeof window !== 'undefined'
    && typeof window.matchMedia === 'function'
    && window.matchMedia(DESKTOP_QUERY).matches;
}

export interface CabinetMediaViewPilotProps {
  patientId: number;
}

/**
 * The FIRST and ONLY authentic module in this isolated G1 pilot.
 * OFF by default; activated only in a test build with the explicit env flag.
 * Never duplicates the media tree, fetches or stores new patient information.
 * Narrow screens retain the original, unwrapped media view.
 */
export function CabinetMediaViewPilot({ patientId }: CabinetMediaViewPilotProps) {
  const desktop = useSyncExternalStore(observeDesktop, desktopSnapshot, () => false);
  const enabled = import.meta.env.VITE_V15_07_G1_MEDIA_FRAME_PILOT === '1';
  const media = <PatientMediaTimeline patientId={patientId} />;

  if (!enabled || !desktop || !Number.isInteger(patientId) || patientId <= 0) {
    return media;
  }

  return (
    <ViewSlotThemeFrame
      title="Médiathèque clinique"
      description="Dossier en cours — même patient, même autorisation"
    >
      {media}
    </ViewSlotThemeFrame>
  );
}
