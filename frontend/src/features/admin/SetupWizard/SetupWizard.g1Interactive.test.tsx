import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { SetupWizard } from './SetupWizard';
import { cabinetApi } from '../../../services/templateApi';
import { useSetupStore } from './store/useSetupStore';

vi.mock('../../../services/templateApi', () => ({
  cabinetApi: {
    getPractitionerIdentity: vi.fn(),
    getMine: vi.fn(),
    create: vi.fn(),
    uploadLogo: vi.fn(),
    uploadLetterhead: vi.fn(),
    completeSetup: vi.fn(),
  },
}));

vi.mock('../../../hooks/useFlowHandoff', () => ({
  useFlowHandoff: () => vi.fn(),
}));

vi.mock('../components/CrownGuide', () => ({
  CrownGuide: () => null,
}));

vi.mock('../components/ArabicKeyboard', () => ({
  ArabicKeyboard: () => null,
}));

vi.mock('../components/LiveDocumentStudio', () => ({
  LiveDocumentStudio: () => <div>Live preview</div>,
}));

function renderWizard() {
  return render(
    <MemoryRouter initialEntries={['/setup']}>
      <Routes>
        <Route path="/setup" element={<SetupWizard />} />
        <Route path="/dashboard" element={<div>Dashboard destination</div>} />
        <Route path="/landing" element={<div>Landing destination</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

function primeValidIdentity() {
  useSetupStore.getState().setIdentity({
    nomCabinet: 'Cabinet Test',
    nomPraticien: 'Dr Test',
    nomPraticienAR: '',
    adresse: 'Rabat',
    ice: '',
    if: '',
    inpe: '',
    inpeEtablissement: '',
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  sessionStorage.clear();
  localStorage.clear();
  useSetupStore.getState().reset();

  vi.mocked(cabinetApi.getPractitionerIdentity).mockRejectedValue({ response: { status: 404 } } as never);
  vi.mocked(cabinetApi.getMine).mockRejectedValue({ response: { status: 404 } } as never);
  vi.mocked(cabinetApi.create).mockResolvedValue({} as never);
  vi.mocked(cabinetApi.completeSetup).mockResolvedValue({} as never);
  vi.mocked(cabinetApi.uploadLogo).mockResolvedValue({} as never);
  vi.mocked(cabinetApi.uploadLetterhead).mockResolvedValue({} as never);
});

afterEach(() => cleanup());

describe('SetupWizard G1 interactive matrix', () => {
  it('blocks Continue on step 1 while required identity fields are missing', async () => {
    renderWizard();
    fireEvent.click(screen.getByRole('button', { name: /Continuer/i }));

    expect(useSetupStore.getState().currentStep).toBe(1);
    expect(cabinetApi.create).not.toHaveBeenCalled();
  });

  it('advances from step 1 when canonical required identity fields are present', async () => {
    primeValidIdentity();
    renderWizard();

    fireEvent.click(screen.getByRole('button', { name: /Continuer/i }));
    await waitFor(() => expect(useSetupStore.getState().currentStep).toBe(2));
  });

  it('finalizes backend first, persists theme only after ACK, resets draft and navigates', async () => {
    primeValidIdentity();
    useSetupStore.getState().setSelectedTheme('emerald');
    useSetupStore.getState().setCurrentStep(7);

    renderWizard();
    fireEvent.click(screen.getByRole('button', { name: /Finaliser l.Installation/i }));

    await waitFor(() => expect(cabinetApi.create).toHaveBeenCalledTimes(1));
    expect(cabinetApi.completeSetup).toHaveBeenCalledTimes(1);
    expect(localStorage.getItem('digitalcrown_theme')).toBe('emerald');
    expect(useSetupStore.getState().currentStep).toBe(1);
    expect(await screen.findByText('Dashboard destination')).toBeTruthy();
  });

  it('does not persist theme, reset draft or navigate when backend creation fails', async () => {
    primeValidIdentity();
    useSetupStore.getState().setSelectedTheme('rose');
    useSetupStore.getState().setCurrentStep(7);
    vi.mocked(cabinetApi.create).mockRejectedValueOnce(new Error('backend down') as never);

    renderWizard();
    fireEvent.click(screen.getByRole('button', { name: /Finaliser l.Installation/i }));

    await waitFor(() => expect(cabinetApi.create).toHaveBeenCalledTimes(1));
    expect(cabinetApi.completeSetup).not.toHaveBeenCalled();
    expect(localStorage.getItem('digitalcrown_theme')).toBeNull();
    expect(useSetupStore.getState().currentStep).toBe(7);
    expect(screen.queryByText('Dashboard destination')).toBeNull();
  });

  it('Quitter navigates to landing without mutating backend', async () => {
    primeValidIdentity();
    renderWizard();

    fireEvent.click(screen.getByRole('button', { name: /Quitter/i }));
    expect(await screen.findByText('Landing destination')).toBeTruthy();
    expect(cabinetApi.create).not.toHaveBeenCalled();
    expect(cabinetApi.completeSetup).not.toHaveBeenCalled();
  });
});
