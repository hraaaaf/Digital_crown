import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MobileQuickDocumentSheet } from './MobileQuickDocumentSheet';
import { mobileFetch } from '../../../../services/zka/mobileFetch';
import { MobileStorage } from '../../../../services/zka/MobileStorage';

vi.mock('../../../../services/zka/mobileFetch', () => ({ mobileFetch: vi.fn() }));
vi.mock('../../../../services/zka/MobileStorage', () => ({
  MobileStorage: {
    getCredentials: vi.fn(),
    getPendingDocumentArchive: vi.fn().mockResolvedValue(null),
    savePendingDocumentArchive: vi.fn().mockResolvedValue(undefined),
    clearPendingDocumentArchive: vi.fn().mockResolvedValue(undefined),
  },
}));

const mockedFetch = vi.mocked(mobileFetch);
const mockedCredentials = vi.mocked(MobileStorage.getCredentials);

describe('MobileQuickDocumentSheet', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('consumes shared desktop theme status and overlay tokens, never fixed palette classes', () => {
    const component = readFileSync(resolve(process.cwd(), 'src/features/mobile/Dashboard/views/MobileQuickDocumentSheet.tsx'), 'utf8');
    const theme = readFileSync(resolve(process.cwd(), 'src/index.css'), 'utf8');
    expect(component).not.toMatch(/\b(?:bg|text|border)-(?:rose|emerald|red|green|black|white)(?:-\d+)?(?:\/\d+)?\b/);
    expect(component).not.toMatch(/#[0-9a-fA-F]{3,8}\b|rgba?\s*\(/);
    expect(component).toContain('bg-modal-scrim');
    expect(component).toContain('bg-success-surface');
    expect(component).toContain('bg-danger-surface');
    expect(component).toContain('text-on-primary');
    expect(component).not.toContain('text-primary-foreground');
    expect(theme).toContain('--color-success: var(--status-success)');
    expect(theme).toContain('--color-danger: var(--status-danger)');
    expect(theme).toContain('--color-modal-scrim: var(--modal-scrim)');
    expect(theme).toContain("[data-theme='high-contrast']");
  });

  it('exposes the five canonical quick document families in isolated preview', () => {
    render(<MobileQuickDocumentSheet patient={{ id: 101, name: 'Patient Démo' }} preview onClose={() => undefined} />);
    for (const label of ['Ordonnance', 'Certificat', 'Devis', 'Honoraires', 'Document libre']) {
      expect(screen.getByRole('button', { name: new RegExp(label, 'i') })).toBeTruthy();
    }
  });

  it('previews then simulates archive without any network in preview mode', () => {
    render(<MobileQuickDocumentSheet patient={{ id: 101, name: 'Patient Démo' }} preview onClose={() => undefined} />);
    fireEvent.click(screen.getByRole('button', { name: /Certificat/i }));
    fireEvent.click(screen.getByRole('button', { name: /Prévisualiser/i }));
    expect(screen.getByText(/Aperçu isolé prêt/i)).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: /Archiver le document/i }));
    expect(screen.getByText(/archivage simulé/i)).toBeTruthy();
    expect(mockedFetch).not.toHaveBeenCalled();
  });

  it('keeps the patient medical alert visible inside the prescription flow', () => {
    render(<MobileQuickDocumentSheet patient={{ id: 101, name: 'Patient Démo', medicalAlert: 'Allergie pénicilline' }} preview onClose={() => undefined} />);
    fireEvent.click(screen.getByRole('button', { name: /Ordonnance/i }));
    expect(screen.getByText(/Alerte médicale/i)).toBeTruthy();
    expect(screen.getByText(/Allergie pénicilline/i)).toBeTruthy();
    expect(mockedFetch).not.toHaveBeenCalled();
  });

  it('fails closed and exposes only server-authorized document families', async () => {
    mockedCredentials.mockResolvedValue({
      publicId: '0123456789abcdef',
      masterKey: 'a'.repeat(64),
      access_token: 'mobile-token',
      api_base_url: 'http://127.0.0.1:8005',
    });
    mockedFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        can_create_prescription: false,
        can_create_certificate: true,
        can_create_devis: false,
        can_create_honoraires: false,
        can_create_free_document: true,
      }),
    } as Response);

    render(<MobileQuickDocumentSheet patient={{ id: 101, name: 'Patient Démo' }} onClose={() => undefined} />);

    await waitFor(() => expect(screen.getByRole('button', { name: /Certificat/i })).toBeTruthy());
    expect(screen.getByRole('button', { name: /Document libre/i })).toBeTruthy();
    expect(screen.queryByRole('button', { name: /Ordonnance/i })).toBeNull();
    expect(screen.queryByRole('button', { name: /Devis/i })).toBeNull();
    expect(screen.queryByRole('button', { name: /Honoraires/i })).toBeNull();
  });

  it('routes live preview and archive through authenticated Pocket PDF endpoints', async () => {
    mockedCredentials.mockResolvedValue({
      publicId: '0123456789abcdef', masterKey: 'a'.repeat(64),
      access_token: 'mobile-token', api_base_url: 'http://127.0.0.1:8005',
    });
    const createObjectURL = vi.fn(() => 'blob:test-pdf');
    vi.stubGlobal('URL', Object.assign(URL, { createObjectURL, revokeObjectURL: vi.fn() }));
    mockedFetch.mockImplementation(async (input) => {
      if (String(input).includes('/quick-actions/capabilities')) {
        return new Response(JSON.stringify({
          can_create_prescription: false, can_create_certificate: true,
          can_create_devis: false, can_create_honoraires: false, can_create_free_document: false,
        }), { headers: { 'Content-Type': 'application/json' } });
      }
      return new Response(new Blob(['%PDF-1.4'], { type: 'application/pdf' }), {
        headers: {
          'Content-Type': 'application/pdf',
          'X-Document-Id': '42',
        },
      });
    });
    render(<MobileQuickDocumentSheet patient={{ id: 101, name: 'Patient Démo' }} onClose={() => undefined} />);
    fireEvent.click(await screen.findByRole('button', { name: /Certificat/i }));
    fireEvent.click(screen.getByRole('button', { name: /Prévisualiser/i }));
    await waitFor(() => expect(screen.getByText(/Aperçu validé/i)).toBeTruthy());
    fireEvent.click(screen.getByRole('button', { name: /Archiver le document/i }));
    await waitFor(() => expect(screen.getByText(/Document archivé et reçu confirmé/i)).toBeTruthy());
    const urls = mockedFetch.mock.calls.map(([input]) => String(input));
    expect(urls.some((url) => url.endsWith('/api/mobile/documents/preview'))).toBe(true);
    expect(urls.some((url) => url.endsWith('/api/mobile/documents/archive'))).toBe(true);
    expect(urls.some((url) => url.includes('/api/documents/generate'))).toBe(false);
    const archiveCall = mockedFetch.mock.calls.find(([url]) => String(url).endsWith('/api/mobile/documents/archive'));
    expect(archiveCall).toBeTruthy();
    expect((archiveCall?.[1]?.headers as Record<string, string>)['Idempotency-Key']).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/,
    );
    expect(MobileStorage.savePendingDocumentArchive).toHaveBeenCalledTimes(1);
    expect(MobileStorage.clearPendingDocumentArchive).toHaveBeenCalledTimes(1);
    expect((screen.getByRole('button', { name: /Déjà archivé/i }) as HTMLButtonElement).disabled).toBe(true);
    vi.unstubAllGlobals();
  });

  it('does not create an archive intent if cabinet receipt schema is not enabled', async () => {
    mockedCredentials.mockResolvedValue({
      publicId: '0123456789abcdef', masterKey: 'a'.repeat(64),
      access_token: 'mobile-token', device_id: 'paired-device', api_base_url: 'http://127.0.0.1:8005',
    });
    vi.stubGlobal('URL', Object.assign(URL, {
      createObjectURL: vi.fn(() => 'blob:preview'), revokeObjectURL: vi.fn(),
    }));
    mockedFetch.mockImplementation(async (input) => {
      const url = String(input);
      if (url.includes('/quick-actions/capabilities')) {
        return new Response(JSON.stringify({
          can_create_prescription: false, can_create_certificate: true,
          can_create_devis: false, can_create_honoraires: false, can_create_free_document: false,
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (url.endsWith('/api/mobile/documents/archive/ready')) {
        return new Response(JSON.stringify({ detail: 'not activated' }), { status: 503 });
      }
      return new Response(new Blob(['%PDF-1.4'], { type: 'application/pdf' }), {
        status: 200, headers: { 'Content-Type': 'application/pdf' },
      });
    });
    render(<MobileQuickDocumentSheet patient={{ id: 101, name: 'Patient Démo' }} onClose={() => undefined} />);
    fireEvent.click(await screen.findByRole('button', { name: /Certificat/i }));
    fireEvent.click(screen.getByRole('button', { name: /Prévisualiser/i }));
    await screen.findByText(/Aperçu validé/i);
    fireEvent.click(screen.getByRole('button', { name: /Archiver le document/i }));
    await screen.findByText(/Archivage Pocket non activé/i);
    expect(MobileStorage.savePendingDocumentArchive).not.toHaveBeenCalled();
    expect(mockedFetch.mock.calls.filter(([u]) => String(u).endsWith('/api/mobile/documents/archive'))).toHaveLength(0);
    vi.unstubAllGlobals();
  });

  it('never sends a second archive POST after an uncertain network result', async () => {
    mockedCredentials.mockResolvedValue({
      publicId: '0123456789abcdef', masterKey: 'a'.repeat(64),
      access_token: 'mobile-token', device_id: 'paired-device', api_base_url: 'http://127.0.0.1:8005',
    });
    vi.stubGlobal('URL', Object.assign(URL, {
      createObjectURL: vi.fn(() => 'blob:preview'), revokeObjectURL: vi.fn(),
    }));
    mockedFetch.mockImplementation(async (input) => {
      const target = String(input);
      if (target.includes('/quick-actions/capabilities')) {
        return new Response(JSON.stringify({
          can_create_prescription: false, can_create_certificate: true,
          can_create_devis: false, can_create_honoraires: false, can_create_free_document: false,
        }), { headers: { 'Content-Type': 'application/json' } });
      }
      if (target.endsWith('/api/mobile/documents/archive')) {
        throw new Error('network lost after write');
      }
      return new Response(new Blob(['%PDF-1.4'], { type: 'application/pdf' }), {
        headers: { 'Content-Type': 'application/pdf' },
      });
    });
    render(<MobileQuickDocumentSheet patient={{ id: 101, name: 'Patient Démo' }} onClose={() => undefined} />);
    fireEvent.click(await screen.findByRole('button', { name: /Certificat/i }));
    fireEvent.click(screen.getByRole('button', { name: /Prévisualiser/i }));
    await screen.findByText(/Aperçu validé/i);
    fireEvent.click(screen.getByRole('button', { name: /Archiver le document/i }));
    await screen.findByText(/Archivage non confirmé/i);
    expect(screen.getByRole('button', { name: /Vérifier le reçu/i })).toBeTruthy();
    expect((screen.getByRole('button', { name: /Archiver le document/i }) as HTMLButtonElement).disabled).toBe(true);
    expect(mockedFetch.mock.calls.filter(([u]) => String(u).endsWith('/api/mobile/documents/archive'))).toHaveLength(1);
    expect(MobileStorage.clearPendingDocumentArchive).not.toHaveBeenCalled();
    vi.unstubAllGlobals();
  });

  it('rejects a zero-value honoraires line before preview', () => {
    render(<MobileQuickDocumentSheet patient={{ id: 101, name: 'Patient Démo' }} preview onClose={() => undefined} />);
    fireEvent.click(screen.getByRole('button', { name: /Honoraires/i }));
    fireEvent.change(screen.getByPlaceholderText('Acte'), { target: { value: 'Consultation' } });
    fireEvent.change(screen.getByPlaceholderText('MAD'), { target: { value: '0' } });
    fireEvent.click(screen.getByRole('button', { name: /Prévisualiser/i }));
    expect(screen.getByText(/strictement positif/i)).toBeTruthy();
    expect(mockedFetch).not.toHaveBeenCalled();
  });
});
