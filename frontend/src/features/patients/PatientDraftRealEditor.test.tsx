import { transferableAbortController } from 'node:util';
import { useState } from 'react';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';
import { createMemoryRouter, RouterProvider, Routes, Route, useLocation, useNavigate, useParams } from 'react-router-dom';
import { LibreForm } from '../admin/DocumentStudio/Forms/LibreForm';
import { isLibreDirty } from '../admin/DocumentStudio/LibreDirtyState';
import { PatientDraftRouteGuard } from './PatientDraftRouteGuard';
import { resetPatientDocumentBoundary } from './patientDocumentBoundary';
import { useAuthStore } from '../../stores/useAuthStore';
import type { AppUser } from '../../types';

// Use the REAL clinical Document Libre editor. Only the T2 backend is stubbed
// for this component test. Nothing writes to any real clinic or saves a draft.
vi.mock('../../services/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../services/api')>();
  return {
    ...actual,
    api: {
      ...actual.api,
      get: vi.fn(async () => ({ data: [] })),
      post: vi.fn(),
    },
  };
});

class NativeRequestAbortController {
  private readonly controller = transferableAbortController();
  readonly signal = this.controller.signal;
  abort(reason?: unknown) { this.controller.abort(reason); }
}
beforeAll(() => vi.stubGlobal('AbortController', NativeRequestAbortController));
afterAll(() => vi.unstubAllGlobals());
beforeEach(() => useAuthStore.setState({
  user: {id:'t2-real-editor',role:'DENTISTE',employer_id:null,permissions:{patients:true}} as unknown as AppUser,
  isAuthenticated:true,isLoading:false,
}));
afterEach(() => {
  cleanup();
  resetPatientDocumentBoundary();
  useAuthStore.setState({user:null,isAuthenticated:false,isLoading:false});
});

function ActualLibreEditor() {
  const { id } = useParams();
  const navigate = useNavigate();
  const activeTab = new URLSearchParams(useLocation().search).get('tab') || 'tracking';
  const [title,setTitle] = useState('Note médicale');
  const [content,setContent] = useState('');
  const [customPatient,setCustomPatient] = useState('');
  const [customDate,setCustomDate] = useState('');
  const [hideHeader,setHideHeader] = useState(false);
  const [pageSize,setPageSize] = useState<'A5'|'A4'>('A5');
  const [alignment,setAlignment] = useState<'left'|'center'|'right'|'justify'>('left');
  return (
    <main>
      <span data-testid="patient-id">T2 dossier {id}</span>
      <button onClick={() => navigate('/patients/' + (id === '17' ? '18' : '17'))}>Patient suivant</button>
      <button onClick={() => navigate('/patients/' + id + '?tab=admin')}>Onglet documents</button>
      {activeTab === 'admin' ? <LibreForm
        title={title} setTitle={setTitle}
        content={content} setContent={setContent}
        customPatient={customPatient} setCustomPatient={setCustomPatient}
        customDate={customDate} setCustomDate={setCustomDate}
        hideHeader={hideHeader} setHideHeader={setHideHeader}
        pageSize={pageSize} setPageSize={setPageSize}
        alignment={alignment} setAlignment={setAlignment}
      /> : <p>Suivi patient synthétique — éditeur non monté</p>}
    </main>
  );
}
function ActualClinicalRoute() {
  const location = useLocation();
  const user = useAuthStore(s => s.user);
  const key = JSON.stringify([location.pathname,user?.id,user?.employer_id,user?.permissions]);
  return (
    <PatientDraftRouteGuard>
      <div key={key}>
        <Routes><Route path="/patients/:id" element={<ActualLibreEditor/>}/></Routes>
      </div>
    </PatientDraftRouteGuard>
  );
}
function setup() {
  const router = createMemoryRouter([{path:'*',element:<ActualClinicalRoute/>}],{
    initialEntries:['/patients/17?tab=admin'],
  });
  render(<RouterProvider router={router}/>);
  return router;
}
const editor = () => screen.getByPlaceholderText(/Rédigez votre document ici/i) as HTMLTextAreaElement;

describe('R2 actual Document Libre editor under draft route guard (synthetic patient IDs)', () => {
  it('preserves real LibreForm text and dirty state when cancelling A->B', async () => {
    const router=setup();
    await screen.findByTestId('patient-id');
    fireEvent.change(editor(),{target:{value:'T2_SYNTHETIC_REAL_FORM_A_NOT_SAVED'}});
    expect(isLibreDirty()).toBe(true);
    fireEvent.click(screen.getByRole('button',{name:'Patient suivant'}));
    await screen.findByRole('alertdialog');
    expect(router.state.location.pathname).toBe('/patients/17');
    expect(editor().value).toBe('T2_SYNTHETIC_REAL_FORM_A_NOT_SAVED');
    fireEvent.click(screen.getByRole('button',{name:'Rester sur ce dossier'}));
    expect(editor().value).toBe('T2_SYNTHETIC_REAL_FORM_A_NOT_SAVED');
    expect(isLibreDirty()).toBe(true);
  });

  it('discards real LibreForm A before B mounts and returns cleanly to A', async () => {
    const router=setup();
    fireEvent.change(editor(),{target:{value:'T2_SYNTHETIC_A_ONLY_NOT_SAVED'}});
    fireEvent.click(screen.getByRole('button',{name:'Patient suivant'}));
    await screen.findByRole('alertdialog');
    fireEvent.click(screen.getByRole('button',{name:'Quitter sans sauvegarder'}));
    await waitFor(()=>expect(router.state.location.pathname).toBe('/patients/18'));
    expect(editor().value).toBe('');
    expect(isLibreDirty()).toBe(false);
    fireEvent.click(screen.getByRole('button',{name:'Patient suivant'}));
    await waitFor(()=>expect(router.state.location.pathname).toBe('/patients/17'));
    expect(editor().value).toBe('');
  });

  it('blocks same-patient browser Back from Documents to Tracking before REAL LibreForm unmount', async () => {
    const router = createMemoryRouter([{path:'*',element:<ActualClinicalRoute/>}],{
      initialEntries:['/patients/17?tab=tracking','/patients/17?tab=admin'],initialIndex:1,
    });
    render(<RouterProvider router={router}/>);
    fireEvent.change(editor(),{target:{value:'T2_REAL_EDITOR_SAME_PATIENT_BACK'}});
    void router.navigate(-1);
    await screen.findByRole('alertdialog');
    expect(router.state.location.search).toBe('?tab=admin');
    expect(editor().value).toBe('T2_REAL_EDITOR_SAME_PATIENT_BACK');
    fireEvent.click(screen.getByRole('button',{name:'Rester sur ce dossier'}));
    expect(editor().value).toBe('T2_REAL_EDITOR_SAME_PATIENT_BACK');
    void router.navigate(-1);
    await screen.findByRole('alertdialog');
    fireEvent.click(screen.getByRole('button',{name:'Quitter sans sauvegarder'}));
    await waitFor(()=>expect(router.state.location.search).toBe('?tab=tracking'));
    expect(screen.queryByPlaceholderText(/Rédigez votre document ici/i)).toBeNull();
    expect(isLibreDirty()).toBe(false);
  });

  it('keeps the real LibreForm draft across search-only tab navigation', async () => {
    const router=setup();
    fireEvent.change(editor(),{target:{value:'T2_SYNTHETIC_SAME_PATIENT_TAB'}});
    fireEvent.click(screen.getByRole('button',{name:'Onglet documents'}));
    await waitFor(()=>expect(router.state.location.search).toBe('?tab=admin'));
    expect(screen.queryByRole('alertdialog')).toBeNull();
    expect(editor().value).toBe('T2_SYNTHETIC_SAME_PATIENT_TAB');
    expect(isLibreDirty()).toBe(true);
  });
});
