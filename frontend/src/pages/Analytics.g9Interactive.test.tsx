import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

const refetchFin = vi.fn();
const refetchOp = vi.fn();
let queryMode: 'success' | 'error' = 'success';

vi.mock('@tanstack/react-query', () => ({
  useQuery: vi.fn(({ queryKey }: { queryKey: string[] }) => {
    if (queryMode === 'error') {
      return {
        data: undefined,
        isLoading: false,
        isError: true,
        refetch: queryKey.includes('financial') ? refetchFin : refetchOp,
      };
    }

    if (queryKey.includes('financial')) {
      return {
        data: {
          revenu_mois: 12000,
          latent_cash: 4500,
          today_revenue: 800,
          month_revenue: 9000,
          total_debt: 1200,
          top_relances: [{
            nom: 'Test',
            prenom: 'Patient',
            soin: 'Couronne',
            montant: 2500,
            telephone: '+212 600 000 001',
          }],
        },
        isLoading: false,
        isError: false,
        refetch: refetchFin,
      };
    }

    return {
      data: {
        patients_total: 25,
        appointments_today: 4,
        no_show_rate: 0.1,
      },
      isLoading: false,
      isError: false,
      refetch: refetchOp,
    };
  }),
}));

vi.mock('../features/analytics/AnalyticsCharts', () => ({
  AnalyticsCharts: () => <div>analytics charts</div>,
}));

vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
  },
}));

import toast from 'react-hot-toast';
import { Analytics } from './Analytics';

describe('Analytics G9 interaction proof', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    queryMode = 'success';

    Object.defineProperty(URL, 'createObjectURL', {
      value: vi.fn(() => 'blob:g9-analytics'),
      configurable: true,
    });
    Object.defineProperty(URL, 'revokeObjectURL', {
      value: vi.fn(),
      configurable: true,
    });
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
  });

  it('retries both canonical data sources when the analytics read fails', () => {
    queryMode = 'error';
    render(<Analytics />);

    fireEvent.click(screen.getByRole('button', { name: /Réessayer/i }));

    expect(refetchFin).toHaveBeenCalledTimes(1);
    expect(refetchOp).toHaveBeenCalledTimes(1);
  });

  it('exports the visible financial report only from loaded backend data', () => {
    render(<Analytics />);

    fireEvent.click(screen.getByRole('button', { name: /Exporter CSV/i }));

    expect(URL.createObjectURL).toHaveBeenCalledTimes(1);
    expect(HTMLAnchorElement.prototype.click).toHaveBeenCalledTimes(1);
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:g9-analytics');
    expect(vi.mocked(toast.success)).toHaveBeenCalledWith('Rapport CSV téléchargé');
  });

  it('opens and closes the WhatsApp recovery modal with a generated patient link', () => {
    render(<Analytics />);

    fireEvent.click(screen.getByText(/Générer relances WhatsApp/i));

    expect(screen.getByText('Relances intelligentes')).toBeInTheDocument();
    const link = screen.getByRole('link', { name: /Envoyer/i });
    expect(link).toHaveAttribute('href', expect.stringContaining('https://wa.me/212600000001?text='));

    fireEvent.click(screen.getByRole('button', { name: /Fermer/i }));
    expect(screen.queryByText('Relances intelligentes')).not.toBeInTheDocument();
  });
});
