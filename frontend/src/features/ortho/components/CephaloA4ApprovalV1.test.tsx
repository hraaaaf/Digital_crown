import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { CephaloA4ApprovalV1 } from './CephaloA4ApprovalV1';
import { api } from '../../../services/api';

const state = vi.hoisted(() => ({
  patientId: 7,
  analysisId: 99,
  local: { landmarks: [{ id:'S', x:10, y:20 }] },
  mmPerPixel: 0.2,
  isPrinting: false,
  isPreviewLoading: false,
  silentSave: vi.fn(),
}));

vi.mock('../stores/useOrthoStore', () => ({
  useOrthoStore: Object.assign(() => state, { getState: () => state }),
}));
vi.mock('../cephaloDocumentSource', () => ({
  prepareBoundCephaloDocumentSource: vi.fn(async () => ({
    analysis_id: 99, expected_revision: 3,
  })),
}));
vi.mock('../../../services/api', () => ({
  api: { post: vi.fn() },
}));
vi.mock('react-hot-toast', () => {
  const toast: any = vi.fn();
  toast.success = vi.fn();
  toast.error = vi.fn();
  return { default: toast };
});
vi.mock('../cephaloArchiveGate', () => ({
  cephaloArchiveErrorMessage: vi.fn(async () => 'Refus de test'),
}));

const P: any = { border:'#ccc', bgCard:'#fff', text:'#111', textMuted:'#555', accent:'#003380' };
const pdfBase64 = 'JVBERi0xLjQKJUVPRg==';
const preview = {
  analysis_id: 99, expected_revision: 3,
  practitioner_name:'Dr TEST', cabinet_stamp_name:'TEST CABINET',
  pdf_sha256:'a'.repeat(64),
  pdf_base64:pdfBase64,
  approval_token:'test-mac-proof-bound-to-pdf',
  document_kind:'CEPH_A4_DESCRIPTIVE_APPROVAL_V1',
  clinical_diagnosis_validated:false,
};

beforeEach(() => {
  vi.clearAllMocks();
  state.patientId = 7;
  state.analysisId = 99;
  state.local.landmarks = [{id:'S',x:10,y:20}];
  state.mmPerPixel = .2;
  state.silentSave.mockResolvedValue(undefined);
  vi.mocked(api.post).mockImplementation(async (path: string) => {
    if (path.endsWith('/prepare')) return { data: preview } as never;
    if (path.endsWith('/archive')) return {
      data: new Blob(['%PDF-1.4']),
      headers: { 'x-cephalo-analysis-id': '99', 'x-cephalo-revision': '3' },
    } as never;
    throw Error('unexpected endpoint ' + path);
  });
  vi.stubGlobal('URL', {
    createObjectURL:vi.fn(() => 'blob:synthetic-reviewed-a4'),
    revokeObjectURL:vi.fn(),
  });
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('CEPH A4 descriptive approval V1 — no automatic archive', () => {
  it('requires explicit acknowledgment before print or archive', async () => {
    render(<CephaloA4ApprovalV1 P={P} />);
    fireEvent.click(screen.getByRole('button', {name:/Préparer l'aperçu A4 à valider/i}));
    await waitFor(() => expect(screen.getByRole('dialog',{name:'Vérification finale du bilan A4'})).toBeTruthy());
    expect(api.post).toHaveBeenCalledWith('/patients/7/cephalo-a4/prepare', {
      analysis_id:99,expected_revision:3,
    });
    const print=screen.getByRole('button',{name:/Imprimer ce bilan A4/i}) as HTMLButtonElement;
    const archive=screen.getByRole('button',{name:/Valider et archiver ce bilan A4/i}) as HTMLButtonElement;
    expect(print.disabled).toBe(true);
    expect(archive.disabled).toBe(true);
    expect(api.post).toHaveBeenCalledTimes(1);

    const checkbox=screen.getByRole('checkbox') as HTMLInputElement;
    fireEvent.click(checkbox);
    expect(print.disabled).toBe(false);
    expect(archive.disabled).toBe(false);

    const printDocument=document.implementation.createHTMLDocument('synthetic-print');
    const popup={
      document:printDocument, addEventListener:vi.fn(), focus:vi.fn(),
    };
    const open=vi.spyOn(window, 'open').mockReturnValue(popup as unknown as Window);
    fireEvent.click(print);
    expect(open).toHaveBeenCalledTimes(1);
    expect(api.post).toHaveBeenCalledTimes(1);
    expect(printDocument.querySelector('iframe')?.getAttribute('src'))
      .toBe('blob:synthetic-reviewed-a4');
    open.mockRestore();

    fireEvent.click(archive);
    await waitFor(() => expect(api.post).toHaveBeenCalledTimes(2));
    expect(api.post).toHaveBeenNthCalledWith(2,
      '/patients/7/cephalo-a4/archive', {
        analysis_id:99,
        expected_revision:3,
        approval_token:preview.approval_token,
        pdf_base64:pdfBase64,
        approved:true,
      }, {responseType:'blob'},
    );
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
  });

  it('rejects local scientific edits after preview before any archive request', async () => {
    render(<CephaloA4ApprovalV1 P={P} />);
    fireEvent.click(screen.getByRole('button',{name:/Préparer l'aperçu/i}));
    await waitFor(() => expect(screen.getByRole('dialog')).toBeTruthy());
    fireEvent.click(screen.getByRole('checkbox'));
    state.local.landmarks = [{id:'S',x:11,y:20}];
    fireEvent.click(screen.getByRole('button',{name:/Valider et archiver/i}));
    expect(api.post).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('invalidates pending approval on a different study', async () => {
    const view=render(<CephaloA4ApprovalV1 P={P}/>);
    fireEvent.click(screen.getByRole('button',{name:/Préparer l'aperçu/i}));
    await waitFor(() => expect(screen.getByRole('dialog')).toBeTruthy());
    state.analysisId=100;
    view.rerender(<CephaloA4ApprovalV1 P={P}/>);
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    expect(api.post).toHaveBeenCalledTimes(1);
  });
});
