import { createRef } from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { DashboardHeader } from './DashboardHeader';

const systemStatus = {
  label: 'Système opérationnel',
  dotClassName: 'bg-emerald-500',
  isLoading: false,
} as const;

const baseProps = () => ({
  displayName: 'Dr Test',
  dateLabel: 'Dimanche 16 août 2026',
  canReadPatients: true,
  canUseAgenda: true,
  canAdmin: true,
  systemStatus,
  onNavigatePatient: vi.fn(),
  onOpenMobile: vi.fn(),
  mobileButtonRef: createRef<HTMLButtonElement>(),
});

describe('DashboardHeader — accessibilité clavier D6', () => {
  it('expose des noms accessibles pour les actions icônes', () => {
    render(
      <MemoryRouter>
        <DashboardHeader
          {...baseProps()}
          search={{
            isExpanded: false,
            query: '',
            results: [],
            loading: false,
            open: vi.fn(),
            close: vi.fn(),
            change: vi.fn(),
          }}
        />
      </MemoryRouter>,
    );

    expect(screen.getByRole('button', { name: 'Chercher un patient' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Ajout rapide' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Appairer le téléphone mobile' })).toBeInTheDocument();
  });

  it('ouvre le menu rapide, Escape le ferme et rend le focus au déclencheur', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <DashboardHeader
          {...baseProps()}
          search={{
            isExpanded: false,
            query: '',
            results: [],
            loading: false,
            open: vi.fn(),
            close: vi.fn(),
            change: vi.fn(),
          }}
        />
      </MemoryRouter>,
    );

    const trigger = screen.getByRole('button', { name: 'Ajout rapide' });
    await user.click(trigger);
    expect(trigger).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByRole('menu')).toBeInTheDocument();

    await user.keyboard('{Escape}');
    expect(trigger).toHaveAttribute('aria-expanded', 'false');
    expect(trigger).toHaveFocus();
  });

  it('Escape ferme la recherche et un résultat patient est activable au clavier', async () => {
    const close = vi.fn();
    const navigate = vi.fn();
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <DashboardHeader
          {...baseProps()}
          onNavigatePatient={navigate}
          search={{
            isExpanded: true,
            query: 'Doe',
            results: [{ id: 7, nom: 'DOE', prenom: 'Jane', numero_dossier: 'D-007' }],
            loading: false,
            open: vi.fn(),
            close,
            change: vi.fn(),
          }}
        />
      </MemoryRouter>,
    );

    const input = screen.getByRole('textbox', { name: 'Chercher un patient' });
    fireEvent.keyDown(input, { key: 'Escape' });
    expect(close).toHaveBeenCalledTimes(1);

    const patient = screen.getByRole('button', { name: /DOE Jane D-007/i });
    patient.focus();
    await user.keyboard('{Enter}');
    expect(navigate).toHaveBeenCalledWith(7);
  });

  it('masque strictement le statut système hors admin', () => {
    render(
      <MemoryRouter>
        <DashboardHeader
          {...baseProps()}
          canAdmin={false}
          search={{
            isExpanded: false,
            query: '',
            results: [],
            loading: false,
            open: vi.fn(),
            close: vi.fn(),
            change: vi.fn(),
          }}
        />
      </MemoryRouter>,
    );

    expect(screen.queryByText('Statut système')).not.toBeInTheDocument();
    expect(screen.queryByText('Système opérationnel')).not.toBeInTheDocument();
  });
});
