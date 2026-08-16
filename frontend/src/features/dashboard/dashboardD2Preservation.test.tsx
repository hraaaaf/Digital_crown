import { createRef } from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { DashboardHeader } from './components/DashboardHeader';

const renderHeader = (canAdmin: boolean) => render(
  <MemoryRouter>
    <DashboardHeader
      displayName="Praticien"
      dateLabel="16 août 2026"
      canReadPatients={false}
      canUseAgenda={false}
      canAdmin={canAdmin}
      systemStatus={{ label: 'Système opérationnel', dotClassName: 'bg-emerald-500', isLoading: false }}
      search={{
        isExpanded: false,
        query: '',
        results: [],
        loading: false,
        open: vi.fn(),
        close: vi.fn(),
        change: vi.fn(),
      }}
      onNavigatePatient={vi.fn()}
      onOpenMobile={vi.fn()}
      mobileButtonRef={createRef<HTMLButtonElement>()}
    />
  </MemoryRouter>,
);

describe('Dashboard D4 — préservation du gate D2', () => {
  it('masque totalement le statut système hors admin', () => {
    renderHeader(false);
    expect(screen.queryByText('Statut système')).toBeNull();
    expect(screen.queryByText('Système opérationnel')).toBeNull();
  });

  it('affiche le statut système pour un admin', () => {
    renderHeader(true);
    expect(screen.getByText('Statut système')).toBeTruthy();
    expect(screen.getByText('Système opérationnel')).toBeTruthy();
  });
});
