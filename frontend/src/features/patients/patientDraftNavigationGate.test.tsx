import { transferableAbortController } from 'node:util';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from 'vitest';
import { createMemoryRouter, RouterProvider, useNavigate, useParams } from 'react-router-dom';
import { isPrescriptionDirty, setPrescriptionDirty } from '../admin/DocumentStudio/PrescriptionDirtyState';
import { shouldBlockPatientDraftExit, usePatientDraftExitBlocker } from './patientDraftNavigationGate';
import { resetPatientDocumentBoundary } from './patientDocumentBoundary';
import { useState } from 'react';

// Vitest jsdom installs its own AbortController, while Node's native undici
// Request demands a Node-native AbortSignal. Keep real cancellation semantics
// through node:util, exclusively inside this synthetic Data Router test suite.
class NativeRequestAbortController {
  private readonly nativeController = transferableAbortController();
  readonly signal = this.nativeController.signal;
  abort(reason?: unknown) { this.nativeController.abort(reason); }
}

beforeAll(() => vi.stubGlobal('AbortController', NativeRequestAbortController));
afterAll(() => vi.unstubAllGlobals());

afterEach(() => {
  cleanup();
  resetPatientDocumentBoundary();
});

function DraftInput({ patientId }: { patientId: string }) {
  const [draft, setDraft] = useState('');
  return (
    <label>
      Brouillon patient {patientId}
      <input
        aria-label="Brouillon clinique"
        value={draft}
        onChange={(event) => {
          setDraft(event.target.value);
          setPrescriptionDirty(Boolean(event.target.value));
        }}
      />
    </label>
  );
}

function GuardedDossier() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { blocker, stayOnPatient, discardAndProceed } = usePatientDraftExitBlocker();

  return (
    <main>
      <p data-testid="active-patient">Dossier {id}</p>
      <DraftInput patientId={String(id)} key={id} />
      <button onClick={() => navigate('/patients/18')}>Ouvrir patient B</button>
      <button onClick={() => navigate('/patients/17')}>Retour au patient A</button>
      <button onClick={() => navigate('/patients/17?tab=clinical')}>Changer onglet</button>
      {blocker.state === 'blocked' && (
        <div role="alertdialog" aria-label="Brouillon non enregistré">
          <p>Vous avez des modifications non enregistrées.</p>
          <button onClick={stayOnPatient}>Rester sur ce dossier</button>
          <button onClick={discardAndProceed}>Quitter sans sauvegarder</button>
        </div>
      )}
    </main>
  );
}

function renderDataRouter() {
  const router = createMemoryRouter(
    [{ path: '/patients/:id', element: <GuardedDossier /> }],
    { initialEntries: ['/patients/17?tab=admin'] },
  );
  render(<RouterProvider router={router} />);
  return router;
}

describe('LOT07 R2 dormant data-router patient-draft exit policy', () => {
  it('blocks a dossier change, lets user cancel, and preserves the original draft exactly', async () => {
    renderDataRouter();
    fireEvent.change(screen.getByLabelText('Brouillon clinique'), { target: { value: 'synthetic draft A' } });
    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir patient B' }));
    expect(await screen.findByRole('alertdialog')).toBeTruthy();
    expect(screen.getByTestId('active-patient').textContent).toBe('Dossier 17');
    expect((screen.getByLabelText('Brouillon clinique') as HTMLInputElement).value).toBe('synthetic draft A');
    expect(isPrescriptionDirty()).toBe(true);
    fireEvent.click(screen.getByRole('button', { name: 'Rester sur ce dossier' }));
    expect(screen.queryByRole('alertdialog')).toBeNull();
    expect(screen.getByTestId('active-patient').textContent).toBe('Dossier 17');
    expect((screen.getByLabelText('Brouillon clinique') as HTMLInputElement).value).toBe('synthetic draft A');
    expect(isPrescriptionDirty()).toBe(true);
  });

  it('clears a discarded draft BEFORE entering B and remounts an empty patient-scoped editor', async () => {
    renderDataRouter();
    fireEvent.change(screen.getByLabelText('Brouillon clinique'), { target: { value: 'private synthetic A' } });
    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir patient B' }));
    expect(await screen.findByRole('alertdialog')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Quitter sans sauvegarder' }));
    await waitFor(() => expect(screen.getByTestId('active-patient').textContent).toBe('Dossier 18'));
    expect((screen.getByLabelText('Brouillon clinique') as HTMLInputElement).value).toBe('');
    expect(screen.queryByText('private synthetic A')).toBeNull();
    expect(isPrescriptionDirty()).toBe(false);
  });

  it('keeps A isolated across the complete A->B->A synthetic route sequence', async () => {
    renderDataRouter();
    fireEvent.change(screen.getByLabelText('Brouillon clinique'), { target: { value: 'T2_A_private_draft' } });
    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir patient B' }));
    await screen.findByRole('alertdialog');
    fireEvent.click(screen.getByRole('button', { name: 'Quitter sans sauvegarder' }));
    await waitFor(() => expect(screen.getByTestId('active-patient').textContent).toBe('Dossier 18'));
    expect((screen.getByLabelText('Brouillon clinique') as HTMLInputElement).value).toBe('');
    fireEvent.click(screen.getByRole('button', { name: 'Retour au patient A' }));
    await waitFor(() => expect(screen.getByTestId('active-patient').textContent).toBe('Dossier 17'));
    expect((screen.getByLabelText('Brouillon clinique') as HTMLInputElement).value).toBe('');
    expect(isPrescriptionDirty()).toBe(false);
  });

  it('allows tab/search changes on the same dossier without clearing its draft', async () => {
    const router = renderDataRouter();
    fireEvent.change(screen.getByLabelText('Brouillon clinique'), { target: { value: 'tab-safe A' } });
    fireEvent.click(screen.getByRole('button', { name: 'Changer onglet' }));
    await waitFor(() => expect(router.state.location.search).toBe('?tab=clinical'));
    expect(screen.queryByRole('alertdialog')).toBeNull();
    expect((screen.getByLabelText('Brouillon clinique') as HTMLInputElement).value).toBe('tab-safe A');
    expect(isPrescriptionDirty()).toBe(true);
  });

  it('does not block clean drafts or unrelated paths', () => {
    expect(shouldBlockPatientDraftExit('/patients/17', '/patients/18', false)).toBe(false);
    expect(shouldBlockPatientDraftExit('/patients/17', '/patients/17', true)).toBe(false);
    expect(shouldBlockPatientDraftExit('/agenda', '/patients/18', true)).toBe(false);
    expect(shouldBlockPatientDraftExit('/patients/17', '/patients/18', true)).toBe(true);
    expect(shouldBlockPatientDraftExit('/patients/17', '/login', true)).toBe(true);
  });
});
