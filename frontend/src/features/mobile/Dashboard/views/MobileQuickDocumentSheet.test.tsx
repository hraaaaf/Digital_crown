import { readFileSync } from 'node:fs';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { MobileQuickDocumentSheet } from './MobileQuickDocumentSheet';
import { mobileFetch } from '../../../../services/zka/mobileFetch';
import { MobileStorage } from '../../../../services/zka/MobileStorage';

vi.mock('../../../../services/zka/mobileFetch', () => ({ mobileFetch: vi.fn() }));
vi.mock('../../../../services/zka/MobileStorage', () => ({ MobileStorage: { getCredentials: vi.fn() } }));

const mockedFetch = vi.mocked(mobileFetch);
const mockedCredentials = vi.mocked(MobileStorage.getCredentials);

describe('MobileQuickDocumentSheet', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('consumes shared desktop theme status and overlay tokens, never fixed palette classes', () => {
    const component = readFileSync(new URL('./MobileQuickDocumentSheet.tsx', import.meta.url), 'utf8');
    const theme = readFileSync(new URL('../../../../index.css', import.meta.url), 'utf8');
    expect(component).not.toMatch(/\b(?:bg|text|border)-(?:rose|emerald|red|green|black|white)(?:-\d+)?(?:\/\d+)?\b/);
    expect(component).not.toMatch(/#[0-9a-fA-F]{3,8}\b|rgba?\s*\(/);
    expect(component).toContain('bg-modal-scrim');
    expect(component).toContain('bg-success-surface');
    expect(component).toContain('bg-danger-surface');
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
        headers: { 'Content-Type': 'application/pdf' },
      });
    });
    render(<MobileQuickDocumentSheet patient={{ id: 101, name: 'Patient Démo' }} onClose={() => undefined} />);
    fireEvent.click(await screen.findByRole('button', { name: /Certificat/i }));
    fireEvent.click(screen.getByRole('button', { name: /Prévisualiser/i }));
    await waitFor(() => expect(screen.getByText(/Aperçu validé/i)).toBeTruthy());
    fireEvent.click(screen.getByRole('button', { name: /Archiver le document/i }));
    await waitFor(() => expect(screen.getByText(/Document généré et archivé/i)).toBeTruthy());
    const urls = mockedFetch.mock.calls.map(([input]) => String(input));
    expect(urls.some((url) => url.endsWith('/api/mobile/documents/preview'))).toBe(true);
    expect(urls.some((url) => url.endsWith('/api/mobile/documents/archive'))).toBe(true);
    expect(urls.some((url) => url.includes('/api/documents/generate'))).toBe(false);
    expect((screen.getByRole('button', { name: /Déjà archivé/i }) as HTMLButtonElement).disabled).toBe(true);
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
