import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { FinanceView } from './views/FinanceView';
import { StockView, type MobileStockItem } from './views/StockView';
import { LabView } from './views/LabView';
import { LabJobStatus, type LabJob } from '../../../types/labJob';
import type { Snapshot } from './types';

afterEach(() => cleanup());

const SNAPSHOT: Snapshot = {
  generated_at: '2026-10-11T09:00:00', role: 'DENTISTE',
  appointments: [],
  finance: {
    today_revenue: 1200, month_revenue: 4500, month_variation: 8,
    appointments_count: 3, weekly_revenue: [{ date: '2026-10-10', amount: 1200 }], total_patients: 12, total_debt: 500,
  },
  debtors: [{ id: 7, name: 'Personne Privée', amount: 500, phone: '+212600000001' }],
};
const STOCK: MobileStockItem[] = [{ id: 1, nom: 'Gants', categorie: 'CONSOMMABLE', quantite: 0, seuil_alerte: 5, unite: 'boîte', alerte: true }];

const JOBS: LabJob[] = [
  { id: 21, patient_id: 8, act_id: 1, type: 'Couronne', material: 'Zircone', tooth_number: '26', deadline: '2026-10-12', status: LabJobStatus.PRESCRIPTION, is_remake: false, is_late: false, created_at: '2026-10-11', updated_at: '2026-10-11' },
  { id: 22, patient_id: 9, act_id: 2, type: 'Essayage', material: 'Résine', deadline: '2026-10-15', status: LabJobStatus.READY, is_remake: false, is_late: false, created_at: '2026-10-11', updated_at: '2026-10-11' },
];

describe('P2 Pocket bounded business workflows', () => {
  it('renders high-level finance KPIs but never debtor identities or export CTA', () => {
    const openWhatsApp = vi.fn();
    render(
      <FinanceView snapshot={SNAPSHOT} syncStatus="success" selectedDate="2026-10-11" openWhatsApp={openWhatsApp} handleExportPDF={() => undefined} pocketSummaryOnly />,
    );
    expect(screen.getByText('Aperçu financier · lecture seule')).toBeTruthy();
    expect(screen.getByText('Recettes du jour')).toBeTruthy();
    expect(screen.queryByText('Personne Privée')).toBeNull();
    expect(screen.queryByRole('button', { name: /WhatsApp|Exporter/i })).toBeNull();
    expect(openWhatsApp).not.toHaveBeenCalled();
  });

  it('keeps stock reads and alert indicators, but hides creation in quick mode and blocks offline edits', () => {
    const { rerender } = render(<StockView previewData={STOCK} quickMode isOnline={false} />);
    expect(screen.getByText('Gants')).toBeTruthy();
    expect(screen.getByText(/création et la configuration/)).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Ajouter un article' })).toBeNull();
    expect(screen.getByRole('button', { name: 'Ajouter une boîte à Gants' }).hasAttribute('disabled')).toBe(true);
    expect(screen.getByRole('status').textContent).toContain('hors ligne');

    rerender(<StockView previewData={STOCK} quickMode isOnline />);
    expect(screen.queryByRole('button', { name: 'Ajouter un article' })).toBeNull();
  });

  it('shows all lab statuses and never labels an unverified draft as sent', () => {
    const handleWhatsAppSend = vi.fn();
    render(<LabView labJobs={JOBS} handleWhatsAppSend={handleWhatsAppSend} isOnline />);
    expect(screen.getByText('Brouillon')).toBeTruthy();
    expect(screen.getByText('Prêt')).toBeTruthy();
    expect(screen.queryByText('Envoyer')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Copier le brouillon' }));
    expect(handleWhatsAppSend).toHaveBeenCalledWith(JOBS[0]);
    expect(handleWhatsAppSend).toHaveBeenCalledTimes(1);
  });

  it('keeps the lab draft preparation disabled while offline', () => {
    render(<LabView labJobs={JOBS} handleWhatsAppSend={() => undefined} isOnline={false} />);
    expect(screen.getByRole('button', { name: 'Copier le brouillon' }).hasAttribute('disabled')).toBe(true);
  });
});
