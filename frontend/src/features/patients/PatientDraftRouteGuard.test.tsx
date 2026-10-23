import { transferableAbortController } from 'node:util';
import { useState } from 'react';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';
import { createMemoryRouter, RouterProvider, Routes, Route, useNavigate, useLocation, useParams } from 'react-router-dom';
import { PatientDraftRouteGuard } from './PatientDraftRouteGuard';
import { isPrescriptionDirty, setPrescriptionDirty } from '../admin/DocumentStudio/PrescriptionDirtyState';
import { resetPatientDocumentBoundary } from './patientDocumentBoundary';
import { useAuthStore } from '../../stores/useAuthStore';
import type { AppUser } from '../../types';

// Node's undici Request requires a native AbortSignal, not jsdom's.
class NativeRequestAbortController {
  private readonly native = transferableAbortController();
  readonly signal = this.native.signal;
  abort(reason?: unknown) { this.native.abort(reason); }
}
beforeAll(() => vi.stubGlobal('AbortController', NativeRequestAbortController));
afterAll(() => vi.unstubAllGlobals());
beforeEach(() => {
  useAuthStore.setState({
    user: { id:'r2-actor', role:'DENTISTE', employer_id:null, permissions:{patients:true} } as unknown as AppUser,
    isAuthenticated:true, isLoading:false,
  });
});
afterEach(() => {
  cleanup();
  resetPatientDocumentBoundary();
  useAuthStore.setState({ user:null, isAuthenticated:false, isLoading:false });
});

function SyntheticEditor() {
  const { id } = useParams();
  const [text, setText] = useState('');
  const navigate = useNavigate();
  return (
    <section>
      <p data-testid="patient-identity">Dossier {id}</p>
      <label>Éditeur synthétique
        <input aria-label="Éditeur synthétique" value={text}
          onChange={event => {
            setText(event.target.value);
            setPrescriptionDirty(event.target.value.length > 0);
          }} />
      </label>
      <button onClick={() => navigate('/patients/' + (id === '17' ? '18' : '17'))}>Changer patient</button>
      <button onClick={() => navigate('/patients/' + id + '?tab=clinical')}>Changer onglet</button>
      <button onClick={() => navigate('/agenda')}>Aller Agenda</button>
      <button onClick={() => navigate('/login')}>Sortir</button>
    </section>
  );
}

function CurrentPathContent() {
  const location = useLocation();
  const user = useAuthStore(state => state.user);
  const actorKey = user
    ? JSON.stringify([user.id, user.employer_id, user.role, user.permissions])
    : 'anonymous';
  return (
    // Mirrors real MainLayout actor-scoped remount plus pathname-keyed animation.
    <div key={actorKey + ':' + location.pathname}>
      <Routes>
        <Route path="/patients/:id" element={<SyntheticEditor />} />
        <Route path="/agenda" element={<p>Agenda synthétique</p>} />
        <Route path="/login" element={<p>Login synthétique</p>} />
      </Routes>
    </div>
  );
}
function RootRoute() {
  return (
    <PatientDraftRouteGuard>
      <CurrentPathContent />
    </PatientDraftRouteGuard>
  );
}
function mount(initialEntries=['/patients/17?tab=admin'],initialIndex=0) {
  const router=createMemoryRouter([{path:'*',element:<RootRoute/>}],{initialEntries,initialIndex});
  render(<RouterProvider router={router}/>);
  return router;
}

describe('R2 live root guard contract on Data Router (synthetic pages only)', () => {
  it('blocks a clicked dossier switch BEFORE pathname-keyed editor unmount and keeps A intact on Stay', async () => {
    const router=mount();
    fireEvent.change(screen.getByLabelText('Éditeur synthétique'),{target:{value:'A SYNTHETIC UNSAVED'}});
    fireEvent.click(screen.getByRole('button',{name:'Changer patient'}));
    expect(await screen.findByRole('alertdialog',{name:'Brouillon non enregistré'})).toBeTruthy();
    expect(router.state.location.pathname).toBe('/patients/17');
    expect((screen.getByLabelText('Éditeur synthétique') as HTMLInputElement).value).toBe('A SYNTHETIC UNSAVED');
    fireEvent.click(screen.getByRole('button',{name:'Rester sur ce dossier'}));
    expect(screen.queryByRole('alertdialog')).toBeNull();
    expect((screen.getByLabelText('Éditeur synthétique') as HTMLInputElement).value).toBe('A SYNTHETIC UNSAVED');
    expect(isPrescriptionDirty()).toBe(true);
  });

  it('discards A explicitly before B is rendered, and A remains clear on B->A return', async () => {
    const router=mount();
    fireEvent.change(screen.getByLabelText('Éditeur synthétique'),{target:{value:'PRIVATE SYNTHETIC A'}});
    fireEvent.click(screen.getByRole('button',{name:'Changer patient'}));
    expect(await screen.findByRole('alertdialog')).toBeTruthy();
    fireEvent.click(screen.getByRole('button',{name:'Quitter sans sauvegarder'}));
    await waitFor(()=>expect(router.state.location.pathname).toBe('/patients/18'));
    expect(screen.getByTestId('patient-identity').textContent).toContain('18');
    expect((screen.getByLabelText('Éditeur synthétique') as HTMLInputElement).value).toBe('');
    expect(isPrescriptionDirty()).toBe(false);
    fireEvent.click(screen.getByRole('button',{name:'Changer patient'}));
    await waitFor(()=>expect(router.state.location.pathname).toBe('/patients/17'));
    expect((screen.getByLabelText('Éditeur synthétique') as HTMLInputElement).value).toBe('');
  });

  it('does not block a search-param tab change within A, preserving the draft', async () => {
    const router=mount();
    fireEvent.change(screen.getByLabelText('Éditeur synthétique'),{target:{value:'SAFE-TAB-A'}});
    fireEvent.click(screen.getByRole('button',{name:'Changer onglet'}));
    await waitFor(()=>expect(router.state.location.search).toBe('?tab=clinical'));
    expect(screen.queryByRole('alertdialog')).toBeNull();
    expect((screen.getByLabelText('Éditeur synthétique') as HTMLInputElement).value).toBe('SAFE-TAB-A');
  });

  it('blocks browser history POP with dirty B; cancel preserves B, then discard allows A', async () => {
    const router=mount(['/patients/17','/patients/18'],1);
    fireEvent.change(screen.getByLabelText('Éditeur synthétique'),{target:{value:'B SYNTHETIC UNSAVED'}});
    await router.navigate(-1);
    expect(await screen.findByRole('alertdialog')).toBeTruthy();
    expect(router.state.location.pathname).toBe('/patients/18');
    fireEvent.click(screen.getByRole('button',{name:'Rester sur ce dossier'}));
    expect(router.state.location.pathname).toBe('/patients/18');
    await router.navigate(-1);
    expect(await screen.findByRole('alertdialog')).toBeTruthy();
    fireEvent.click(screen.getByRole('button',{name:'Quitter sans sauvegarder'}));
    await waitFor(()=>expect(router.state.location.pathname).toBe('/patients/17'));
    expect((screen.getByLabelText('Éditeur synthétique') as HTMLInputElement).value).toBe('');
  });

  it('discards the stale blocked A navigation and wipes A draft on permission revocation', async () => {
    const router = mount();
    fireEvent.change(screen.getByLabelText('Éditeur synthétique'), { target: { value:'SECRET-A-ROLE-REVOKED' } });
    fireEvent.click(screen.getByRole('button', { name:'Changer patient' }));
    await screen.findByRole('alertdialog');
    useAuthStore.setState({
      user: { id:'r2-actor', role:'DENTISTE', employer_id:null, permissions:{patients:false} } as unknown as AppUser,
      isAuthenticated:true,
    });
    await waitFor(() => expect(screen.queryByRole('alertdialog')).toBeNull());
    expect(router.state.location.pathname).toBe('/patients/17');
    expect((screen.getByLabelText('Éditeur synthétique') as HTMLInputElement).value).toBe('');
    expect(isPrescriptionDirty()).toBe(false);
  });

  it('never proceeds with A blocked navigation after switching to another signed-in tenant', async () => {
    const router = mount();
    fireEvent.change(screen.getByLabelText('Éditeur synthétique'), { target: { value:'SYNTHETIC-TENANT-A' } });
    fireEvent.click(screen.getByRole('button', { name:'Changer patient' }));
    await screen.findByRole('alertdialog');
    useAuthStore.setState({
      user: { id:'r2-new-principal', role:'DENTISTE', employer_id:'other-tenant', permissions:{patients:true} } as unknown as AppUser,
      isAuthenticated:true,
    });
    await waitFor(() => expect(screen.queryByRole('alertdialog')).toBeNull());
    expect(router.state.location.pathname).toBe('/patients/17');
    expect((screen.getByLabelText('Éditeur synthétique') as HTMLInputElement).value).toBe('');
    expect(isPrescriptionDirty()).toBe(false);
  });

  it('purges the editor draft when the logged-in actor loses authorization during a blocked navigation', async () => {
    const router=mount();
    fireEvent.change(screen.getByLabelText('Éditeur synthétique'),{target:{value:'REVOKED-SYNTHETIC-A'}});
    fireEvent.click(screen.getByRole('button',{name:'Sortir'}));
    await screen.findByRole('alertdialog');
    useAuthStore.setState({user:null,isAuthenticated:false,isLoading:false});
    await waitFor(()=>expect(router.state.location.pathname).toBe('/login'));
    expect(screen.queryByRole('alertdialog')).toBeNull();
    expect(screen.getByText('Login synthétique')).toBeTruthy();
    expect(isPrescriptionDirty()).toBe(false);
  });
});
