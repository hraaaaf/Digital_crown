import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { MobilePatientsView, type MobilePatientsPreviewData } from './MobilePatientsView';
import { mobileFetch } from '../../../../services/zka/mobileFetch';

vi.mock('../../../../services/zka/mobileFetch', () => ({ mobileFetch: vi.fn() }));
vi.mock('../../../../services/zka/MobileStorage', () => ({ MobileStorage: { getCredentials: vi.fn() } }));

const PREVIEW: MobilePatientsPreviewData = {
  initialSelectedId: 101,
  results: [{ id: 101, name: 'Patient Démo', phone: '+212600000001', numero_dossier: 'P-0101', has_medical_alert: false }],
  cockpit: {
    patient: { id: 101, name: 'Patient Démo', has_medical_alert: false },
    next_appointment: null,
    finance: null,
  },
  resources: { documents: [], panoramics: [] },
};

describe('MobilePatientsView MOB-5F', () => {
  it('adds one primary document CTA without breaking preview isolation', () => {
    render(<MobilePatientsView onClose={() => undefined} previewData={PREVIEW} />);
    fireEvent.click(screen.getByRole('button', { name: /Créer un document/i }));
    expect(screen.getByText(/Quick Document Studio/i)).toBeTruthy();
    expect(screen.getByRole('button', { name: /Ordonnance/i })).toBeTruthy();
    expect(mobileFetch).not.toHaveBeenCalled();
  });
});
