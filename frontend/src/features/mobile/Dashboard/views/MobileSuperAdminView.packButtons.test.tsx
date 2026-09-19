import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it } from 'vitest';
import { DEMO_SUPERADMIN } from '../../superadmin/previewData';
import type { MobileSuperAdminPreviewData } from '../../superadmin/useMobileSuperAdmin';
import { MobileSuperAdminView } from './MobileSuperAdminView';

afterEach(() => cleanup());

function renderPreview(data: MobileSuperAdminPreviewData = DEMO_SUPERADMIN) {
  render(
    <MemoryRouter>
      <MobileSuperAdminView previewData={data} />
    </MemoryRouter>,
  );
}

function openClientsSection() {
  const header = document.querySelector('header');
  if (!header) throw new Error('SuperAdmin header unavailable');
  fireEvent.click(within(header).getByRole('button', { name: 'Clients' }));
}

function openClient(cabinetName: string) {
  openClientsSection();
  fireEvent.click(screen.getByRole('button', { name: new RegExp(cabinetName) }));
  return screen.getByRole('dialog', { name: cabinetName });
}

function cancelConfirmation(title: RegExp) {
  const confirmation = screen.getByRole('alertdialog', { name: title });
  fireEvent.click(within(confirmation).getByRole('button', { name: 'Annuler' }));
}

describe('MobileSuperAdmin commercial pack buttons', () => {
  it.each([
    ['Cabinet Atlas Démo', 'ELITE'],
    ['Clinique Horizon Test', 'PREMIUM'],
    ['Centre Dentaire Démonstration', 'GOLD'],
  ])('exercises every pack selector outcome from %s (%s)', async (cabinetName, currentPlan) => {
    renderPreview();
    const dialog = openClient(cabinetName);
    const select = within(dialog).getByRole('combobox') as HTMLSelectElement;

    expect(select.value).toBe(currentPlan);

    for (const target of ['GOLD', 'PREMIUM', 'ELITE']) {
      fireEvent.change(select, { target: { value: target } });
      const confirmation = await screen.findByRole('alertdialog', { name: new RegExp(`Passer en ${target}`) });
      expect(within(confirmation).getByText(/sera modifié côté serveur/)).toBeTruthy();
      fireEvent.click(within(confirmation).getByRole('button', { name: 'Changer le pack' }));
      await waitFor(() => expect(screen.queryByRole('alertdialog')).toBeNull());
      expect(screen.getByRole('status').textContent).toContain(`Pack ${target} attribué`);
    }
  });

  it.each([
    ['Cabinet Atlas Démo', 'Suspendre'],
    ['Clinique Horizon Test', 'Suspendre'],
    ['Centre Dentaire Démonstration', 'Réactiver'],
  ])('wires licence, CRM and sensitive actions for %s', async (cabinetName, suspendLabel) => {
    renderPreview();
    const dialog = openClient(cabinetName);

    for (const label of ['+1M', '+3M', '+6M', '+1AN']) {
      fireEvent.click(within(dialog).getByRole('button', { name: label }));
      cancelConfirmation(new RegExp('Prolonger'));
    }

    const notes = within(dialog).getByPlaceholderText('Notes internes');
    fireEvent.change(notes, { target: { value: 'Note audit boutons' } });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Enregistrer les notes' }));
    expect(screen.getByRole('status').textContent).toContain('Notes internes enregistrées');

    fireEvent.click(within(dialog).getByRole('button', { name: /Historique/i }));
    expect(await within(dialog).findByText('grant')).toBeTruthy();

    fireEvent.click(within(dialog).getByRole('button', { name: /Relance/i }));
    cancelConfirmation(/Envoyer une relance/);

    fireEvent.click(within(dialog).getByRole('button', { name: suspendLabel }));
    cancelConfirmation(new RegExp(suspendLabel === 'Suspendre' ? 'Suspendre ce client' : 'Réactiver ce client'));

    fireEvent.click(within(dialog).getByRole('button', { name: 'Archiver' }));
    cancelConfirmation(/Archiver ce client/);

    fireEvent.click(within(dialog).getByRole('button', { name: /Révoquer licence/i }));
    cancelConfirmation(/Révoquer la licence/);

    fireEvent.click(within(dialog).getByRole('button', { name: 'Fermer' }));
    expect(screen.queryByRole('dialog', { name: cabinetName })).toBeNull();
  });

  it('requires explicit confirmation before validating an inactive GOLD client', () => {
    const gold = DEMO_SUPERADMIN.clients.find(client => client.subscription_plan === 'GOLD');
    if (!gold) throw new Error('GOLD preview client missing');
    const data: MobileSuperAdminPreviewData = {
      ...DEMO_SUPERADMIN,
      clients: [{ ...gold, is_active: false, is_suspended: false }],
    };

    renderPreview(data);
    const dialog = openClient(gold.cabinet_name);
    fireEvent.click(within(dialog).getByRole('button', { name: /Valider \+ essai 30 j/i }));

    const confirmation = screen.getByRole('alertdialog', { name: /Valider ce client/ });
    expect(within(confirmation).getByText(/essai de 30 jours/)).toBeTruthy();
    fireEvent.click(within(confirmation).getByRole('button', { name: 'Annuler' }));

    expect(screen.queryByRole('alertdialog')).toBeNull();
    expect(screen.queryByRole('status')).toBeNull();
  });
});
