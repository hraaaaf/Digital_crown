import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MobilePatientsView, type MobilePatientsPreviewData } from './MobilePatientsView';
import { mobileFetch } from '../../../../services/zka/mobileFetch';
import { MobileStorage } from '../../../../services/zka/MobileStorage';

vi.mock('../../../../services/zka/mobileFetch', () => ({ mobileFetch: vi.fn() }));
vi.mock('../../../../services/zka/MobileStorage', () => ({ MobileStorage: { getCredentials: vi.fn() } }));

beforeEach(() => {
  vi.clearAllMocks();
  window.history.replaceState({}, '', '/mobile/dashboard?tab=patients');
});

afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});

const PREVIEW: MobilePatientsPreviewData = {
  initialSelectedId: 101,
  results: [{ id: 101, name: 'Patient Démo', phone: '+212600000001', numero_dossier: 'P-0101', has_medical_alert: false }],
  cockpit: {
    patient: { id: 101, name: 'Patient Démo', has_medical_alert: false },
    next_appointment: null,
    clinical_context: {
      motif_consultation: 'Douleur secteur 2',
      latest_acte: {
        id: 88,
        label: 'Contrôle occlusion',
        type: 'SOIN',
        date: '2026-09-26T15:30:00',
        note: 'Sensibilité au froid, contrôle occlusion.',
      },
    },
    finance: null,
  },
  resources: { documents: [], panoramics: [] },
};

describe('MobilePatientsView MOB-5F', () => {
  it('shows clinical capture only when the server provides clinical context', () => {
    render(<MobilePatientsView onClose={() => undefined} previewData={PREVIEW} />);
    expect(screen.getByText('Contexte clinique')).toBeTruthy();
    expect(screen.getByText('Douleur secteur 2')).toBeTruthy();
    expect(screen.getByText('Sensibilité au froid, contrôle occlusion.')).toBeTruthy();
    expect(screen.getByRole('button', { name: /Photo clinique/i })).toBeTruthy();
    expect(screen.getByRole('button', { name: /Scanner/i })).toBeTruthy();
    expect(screen.queryByRole('button', { name: /Créer un document/i })).toBeNull();
    expect(mobileFetch).not.toHaveBeenCalled();
  });

  it('keeps an operational patient view free of clinical actions when clinical context is denied', () => {
    const restricted: MobilePatientsPreviewData = {
      ...PREVIEW,
      cockpit: {
        ...PREVIEW.cockpit,
        patient: { ...PREVIEW.cockpit.patient, has_medical_alert: false, medical_alert_summary: null },
        clinical_context: null,
      },
      resources: { documents: [], panoramics: [] },
    };
    render(<MobilePatientsView onClose={() => undefined} previewData={restricted} />);
    expect(screen.queryByText('Contexte clinique')).toBeNull();
    expect(screen.queryByRole('button', { name: /Photo clinique/i })).toBeNull();
    expect(screen.queryByRole('button', { name: /Scanner/i })).toBeNull();
  });

  it('opens a directly selected patient through the cockpit API without putting the patient id in the URL', async () => {
    vi.mocked(MobileStorage.getCredentials).mockResolvedValue({
      access_token: 'mobile-token',
      api_base_url: 'http://127.0.0.1:8005',
      masterKey: 'test-master-key',
    } as never);

    vi.mocked(mobileFetch).mockImplementation(async (input) => {
      const url = String(input);
      if (url.endsWith('/resources')) {
        return new Response(JSON.stringify({ documents: [], panoramics: [] }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }
      return new Response(JSON.stringify({
        patient: { id: 101, name: 'Patient Direct', has_medical_alert: false },
        next_appointment: null,
        clinical_context: null,
        finance: null,
      }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    });

    window.history.replaceState({}, '', '/mobile/dashboard?tab=patients');
    render(<MobilePatientsView onClose={() => undefined} initialSelectedId={101} />);

    expect(await screen.findByText('Patient Direct')).toBeTruthy();
    expect(window.location.search).toBe('?tab=patients');
    expect(window.location.search).not.toContain('patient_id=');
    expect(vi.mocked(mobileFetch).mock.calls.some(([input]) => String(input).includes('/patient-cockpit/101'))).toBe(true);
  });
});
