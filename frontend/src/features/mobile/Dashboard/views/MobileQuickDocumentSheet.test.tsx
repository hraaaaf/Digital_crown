import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { MobileQuickDocumentSheet } from './MobileQuickDocumentSheet';
import { mobileFetch } from '../../../../services/zka/mobileFetch';

vi.mock('../../../../services/zka/mobileFetch', () => ({ mobileFetch: vi.fn() }));
vi.mock('../../../../services/zka/MobileStorage', () => ({ MobileStorage: { getCredentials: vi.fn() } }));

describe('MobileQuickDocumentSheet', () => {
  it('exposes the five canonical quick document families', () => {
    render(<MobileQuickDocumentSheet patient={{ id: 101, name: 'Patient Démo' }} preview onClose={() => undefined} />);
    for (const label of ['Ordonnance', 'Certificat', 'Devis', 'Honoraires', 'Document libre']) {
      expect(screen.getByRole('button', { name: new RegExp(label, 'i') })).toBeTruthy();
    }
  });

  it('never calls the network in preview mode', () => {
    render(<MobileQuickDocumentSheet patient={{ id: 101, name: 'Patient Démo' }} preview onClose={() => undefined} />);
    fireEvent.click(screen.getByRole('button', { name: /Certificat/i }));
    fireEvent.click(screen.getByRole('button', { name: /Générer et archiver/i }));
    expect(screen.getByText(/Aperçu isolé/i)).toBeTruthy();
    expect(mobileFetch).not.toHaveBeenCalled();
  });
});
