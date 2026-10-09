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

    expect(screen.getByRole('button', { name: 'Chercher un patient' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Ajout rapide' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Ouvrir Digital Crown Pocket' })).toBeTruthy();
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
    expect(trigger.getAttribute('aria-expanded')).toBe('true');
    expect(screen.getByRole('menu')).toBeTruthy();

    await user.keyboard('{Escape}');
    expect(trigger.getAttribute('aria-expanded')).toBe('false');
    expect(document.activeElement).toBe(trigger);
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

  it('positionne la recherche et ses résultats dans le cadre du header mobile sans modifier le desktop', () => {
    render(
      <MemoryRouter>
        <DashboardHeader
          {...baseProps()}
          search={{
            isExpanded: true,
            query: 'Doe',
            results: [{ id: 7, nom: 'DOE', prenom: 'Jane', numero_dossier: 'D-007' }],
            loading: false,
            open: vi.fn(),
            close: vi.fn(),
            change: vi.fn(),
          }}
        />
      </MemoryRouter>,
    );

    const input = screen.getByRole('textbox', { name: 'Chercher un patient' });
    const panel = input.parentElement?.parentElement as HTMLElement;
    const anchor = panel.parentElement as HTMLElement;
    const header = input.closest('header') as HTMLElement;
    const results = screen.getByRole('list');

    // On narrow screens the zero-width toolbar slot cannot anchor a 288px
    // absolute panel. The containing block must be the full-width header.
    expect(header.classList.contains('relative')).toBe(true);
    expect(anchor.classList.contains('static')).toBe(true);
    expect(anchor.classList.contains('md:relative')).toBe(true);
    expect(panel.classList.contains('inset-x-0')).toBe(true);
    expect(panel.classList.contains('top-full')).toBe(true);
    expect(panel.classList.contains('md:right-0')).toBe(true);
    // Desktop must also open below the toolbar, never on top of the welcome title.
    expect(panel.classList.contains('md:top-auto')).toBe(false);
    expect(panel.classList.contains('md:mt-0')).toBe(false);
    expect(panel.classList.contains('top-full')).toBe(true);
    expect(input.parentElement?.classList.contains('w-full')).toBe(true);
    expect(input.parentElement?.classList.contains('md:w-72')).toBe(true);
    expect(results.classList.contains('inset-x-0')).toBe(true);
    expect(results.classList.contains('md:w-72')).toBe(true);
    expect(screen.getByRole('button', { name: /DOE Jane D-007/i })).toBeTruthy();
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

    expect(screen.queryByText('Statut système')).toBeNull();
    expect(screen.queryByText('Système opérationnel')).toBeNull();
  });
});
