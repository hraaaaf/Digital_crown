import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { DEMO_SUPERADMIN } from '../../superadmin/previewData';
import { MobileSuperAdminView } from './MobileSuperAdminView';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('MobileSuperAdminView', () => {
  it('exposes the five SuperAdmin domains in isolated preview without network calls', () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal('fetch', fetchSpy);

    render(
      <MemoryRouter>
        <MobileSuperAdminView previewData={DEMO_SUPERADMIN} />
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { name: 'SuperAdmin' })).toBeTruthy();
    expect(screen.getByText('MODE DÉMO — SUPERADMIN')).toBeTruthy();
    expect(screen.getByText('Clients & licences')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Clients' }));
    expect(screen.getByText('Cabinet Atlas Démo')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: /Cabinet Atlas Démo/ }));
    expect(screen.getByRole('dialog', { name: 'Cabinet Atlas Démo' })).toBeTruthy();
    expect(screen.getByRole('button', { name: /Révoquer licence/i })).toBeTruthy();
    expect(screen.getByRole('button', { name: /Historique/i })).toBeTruthy();
    expect(screen.getByRole('button', { name: /Relance/i })).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Fermer' }));

    fireEvent.click(screen.getByRole('button', { name: 'Essais' }));
    expect(screen.getByText('DC-DEMO-42A1-8BC2')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Marketplace' }));
    expect(screen.getByText('Dental Supply Demo')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Catalogue' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Incidents' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Audit' })).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Opérations' }));
    expect(screen.getByText('CMD-PART-DEMO-7001')).toBeTruthy();
    expect(screen.getByText('Commandes multi-cabinets')).toBeTruthy();

    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it('opens an operational order with dispatch, procurement, finance and receipt controls', async () => {
    render(
      <MemoryRouter>
        <MobileSuperAdminView previewData={DEMO_SUPERADMIN} />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Opérations' }));
    fireEvent.click(screen.getByRole('button', { name: /CMD-PART-DEMO-7001/ }));

    expect(await screen.findByRole('dialog', { name: 'CMD-PART-DEMO-7001' })).toBeTruthy();
    expect(screen.getByRole('button', { name: /Dispatch fournisseur/i })).toBeTruthy();
    expect(screen.getByRole('button', { name: /Accuser réception fournisseur/i })).toBeTruthy();
    expect(screen.getByRole('button', { name: /Enregistrer facture/i })).toBeTruthy();
    expect(screen.getByRole('button', { name: /Enregistrer réception/i })).toBeTruthy();
  });
});
