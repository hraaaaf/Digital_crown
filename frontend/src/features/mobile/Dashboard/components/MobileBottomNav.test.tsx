import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MobileBottomNav } from './MobileBottomNav';
import type { Snapshot } from '../types';

const SNAPSHOT: Snapshot = {
  generated_at: new Date().toISOString(),
  role: 'DENTISTE',
  is_superadmin: false,
  appointments: [],
  finance: {
    today_revenue: 0,
    month_revenue: 0,
    month_variation: null,
    appointments_count: 0,
    weekly_revenue: [],
    total_patients: 0,
    total_debt: 0,
  },
  debtors: [],
};

afterEach(() => cleanup());

describe('Digital Crown Pocket canonical navigation', () => {
  it('renders the five-entry Pocket navigation and opens Patients directly', () => {
    const setActiveTab = vi.fn();
    const onToggleQuickActions = vi.fn();

    render(
      <MobileBottomNav activeTab="today" setActiveTab={setActiveTab} totalCount={4} termineCount={1} snapshot={SNAPSHOT} quickActionsAvailable quickActionsOpen={false} onToggleQuickActions={onToggleQuickActions} />,
    );

    expect(screen.getByText('Aujourd’hui')).toBeTruthy();
    expect(screen.getByText('Agenda')).toBeTruthy();
    expect(screen.getByText('Patients')).toBeTruthy();
    expect(screen.queryByText('Assistant')).toBeNull();
    expect(screen.getByText('Plus')).toBeTruthy();
    expect(screen.queryByText('Alertes')).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir les actions rapides' }));
    expect(onToggleQuickActions).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByText('Patients'));
    expect(setActiveTab).toHaveBeenCalledWith('patients');

    fireEvent.click(screen.getByText('Agenda'));
    expect(setActiveTab).toHaveBeenCalledWith('agenda');
  });

  it('renders one aligned WhatsApp-inspired glass row and slides the selection between tabs', () => {
    const props = {
      setActiveTab: vi.fn(), totalCount: 1, termineCount: 0, snapshot: SNAPSHOT,
      quickActionsAvailable: true, onToggleQuickActions: vi.fn(),
    };
    const { rerender } = render(<MobileBottomNav {...props} activeTab="today" quickActionsOpen={false} />);
    const nav = document.querySelector('[data-mobile-bottom-nav]') as HTMLElement;
    const targets = [...nav.querySelectorAll<HTMLButtonElement>('[data-mobile-nav-item]')];
    const indicator = nav.querySelector<HTMLElement>('[data-mobile-nav-indicator]');

    expect(nav.hasAttribute('data-pocket-glass-nav')).toBe(true);
    expect(nav.getAttribute('style')).toContain('var(--card-bg)');
    expect(targets.map(target => target.dataset.mobileNavItem)).toEqual([
      'today', 'agenda', 'actions', 'patients', 'more',
    ]);
    expect(targets.every(target => target.className.includes('min-h-[54px]'))).toBe(true);
    expect(targets[2].className).not.toContain('absolute');
    expect(targets[2].className).not.toContain('-top-2.5');
    expect(targets[2].textContent).toContain('Actions');
    expect(indicator?.style.transform).toBe('translate(0%, -50%)');

    rerender(<MobileBottomNav {...props} activeTab="patients" quickActionsOpen={false} />);
    expect(indicator?.style.transform).toBe('translate(300%, -50%)');

    rerender(<MobileBottomNav {...props} activeTab="patients" quickActionsOpen />);
    expect(indicator?.style.transform).toBe('translate(200%, -50%)');
    expect(screen.getByRole('button', { name: 'Fermer les actions rapides' })).toBeTruthy();
  });

  it('restores merged Pocket V1 secondary destinations for practitioners', () => {
    const setActiveTab = vi.fn();
    render(
      <MobileBottomNav activeTab="today" setActiveTab={setActiveTab} totalCount={0} termineCount={0} snapshot={SNAPSHOT} quickActionsAvailable quickActionsOpen={false} onToggleQuickActions={() => undefined} />,
    );

    fireEvent.click(screen.getByText('Plus'));
    expect(screen.getByText('Salle d’attente')).toBeTruthy();
    expect(screen.getByText('Notifications')).toBeTruthy();
    expect(screen.getByText('Accueil')).toBeTruthy();
    expect(screen.getByText('Sécurité')).toBeTruthy();
    expect(screen.getByText('Stock')).toBeTruthy();
    expect(screen.getByText('Bibliothèque')).toBeTruthy();
    expect(screen.getByText('Approvisionnement')).toBeTruthy();
    expect(screen.getByText('Trésorerie')).toBeTruthy();
    expect(screen.getByText('Envois Labo')).toBeTruthy();
    expect(screen.getByText('Équipe')).toBeTruthy();
    expect(screen.getByText('Assistant · En cours de construction')).toBeTruthy();

    // The Safari sheet must be solid, readable and touch-friendly over clinical content.
    const dialog = screen.getByRole('dialog', { name: 'Plus' });
    expect(dialog.getAttribute('style')).toContain('var(--card-bg)');
    expect(dialog.className).toContain('bg-card');
    const stockItem = screen.getByRole('button', { name: 'Stock' });
    expect(stockItem.className).toContain('min-h-[54px]');
    expect(stockItem.querySelector('span.flex-1')?.className).toContain('text-[14px]');
    const nav = document.querySelector('[data-mobile-bottom-nav]') as HTMLElement;
    expect(nav.getAttribute('style')).toContain('var(--card-bg)');

    fireEvent.click(screen.getByText('Salle d’attente'));
    expect(setActiveTab).toHaveBeenCalledWith('waiting-room');
    expect(screen.queryByText('Accès secondaires')).toBeNull();
  });

  it('traps focus inside Plus and restores it to the trigger on Escape', () => {
    render(
      <MobileBottomNav activeTab="today" setActiveTab={() => undefined} totalCount={0} termineCount={0} snapshot={SNAPSHOT} quickActionsAvailable quickActionsOpen={false} onToggleQuickActions={() => undefined} />,
    );

    const trigger = screen.getByText('Plus').closest('button') as HTMLButtonElement;
    const nav = document.querySelector('[data-mobile-bottom-nav]') as HTMLElement;
    expect(nav.hasAttribute('inert')).toBe(false);
    fireEvent.click(trigger);
    // A modal cannot leave the higher z-index bottom bar pointer/keyboard active.
    expect(nav.hasAttribute('inert')).toBe(true);

    const close = screen.getByRole('button', { name: 'Fermer Plus' });
    expect(document.activeElement).toBe(close);

    const firstItem = screen.getByRole('button', { name: 'Salle d’attente' });
    const lastItem = screen.getByRole('button', { name: 'Sécurité' });
    lastItem.focus();
    fireEvent.keyDown(window, { key: 'Tab' });
    expect(document.activeElement).toBe(close);

    close.focus();
    fireEvent.keyDown(window, { key: 'Tab', shiftKey: true });
    expect(document.activeElement).toBe(lastItem);

    firstItem.focus();
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(screen.queryByText('Accès secondaires')).toBeNull();
    expect(nav.hasAttribute('inert')).toBe(false);
    expect(document.activeElement).toBe(trigger);
  });

  it('gives secretary the same bounded Pocket secondary shell', () => {
    render(
      <MobileBottomNav activeTab="today" setActiveTab={() => undefined} totalCount={0} termineCount={0} snapshot={{ ...SNAPSHOT, role: 'SECRETAIRE' }} quickActionsAvailable={false} quickActionsOpen={false} onToggleQuickActions={() => undefined} />,
    );

    expect(screen.getByRole('button', { name: 'Ouvrir les actions rapides' }).hasAttribute('disabled')).toBe(true);
    fireEvent.click(screen.getByText('Plus'));
    expect(screen.getByText('Salle d’attente')).toBeTruthy();
    expect(screen.getByText('Notifications')).toBeTruthy();
    expect(screen.getByText('Accueil')).toBeTruthy();
    expect(screen.getByText('Sécurité')).toBeTruthy();
    expect(screen.getByText('Stock')).toBeTruthy();
    expect(screen.getByText('Équipe')).toBeTruthy();
    expect(screen.getByText('Assistant · En cours de construction')).toBeTruthy();
    expect(screen.queryByText('Bibliothèque')).toBeNull();
    expect(screen.queryByText('Approvisionnement')).toBeNull();
    expect(screen.queryByText('Trésorerie')).toBeNull();
    expect(screen.queryByText('Envois Labo')).toBeNull();
  });

  it('fails closed when role is not loaded yet', () => {
    render(
      <MobileBottomNav activeTab="today" setActiveTab={() => undefined} totalCount={0} termineCount={0} snapshot={null} quickActionsAvailable={false} quickActionsOpen={false} onToggleQuickActions={() => undefined} />,
    );

    fireEvent.click(screen.getByText('Plus'));
    expect(screen.getByText('Aucun accès secondaire disponible pour ce rôle.')).toBeTruthy();
    expect(screen.queryByText('Salle d’attente')).toBeNull();
    expect(screen.queryByText('Accueil')).toBeNull();
    expect(screen.queryByText('Sécurité')).toBeNull();
  });
});
