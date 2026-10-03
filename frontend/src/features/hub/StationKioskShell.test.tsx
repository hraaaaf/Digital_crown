import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { StationKioskShell } from './StationKioskShell';

describe('StationKioskShell', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders touch-first public actions without clinical navigation', () => {
    const { container } = render(<StationKioskShell onAdminTap={vi.fn()} />);

    expect(screen.getByRole('heading', { name: 'Bienvenue au cabinet' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /J’ai rendez-vous/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Retirer un document/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Besoin d’aide/i })).toBeInTheDocument();
    expect(container.querySelectorAll('a')).toHaveLength(0);
    expect(container.querySelector('[data-station-screen="home"]')).toBeInTheDocument();
  });

  it('switches FR / AR / EN and applies RTL only to Arabic', () => {
    const { container } = render(<StationKioskShell onAdminTap={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: 'العربية' }));
    expect(screen.getByRole('heading', { name: 'مرحباً بكم في العيادة' })).toBeInTheDocument();
    expect(container.querySelector('[data-station-language="ar"]')).toHaveAttribute('dir', 'rtl');
    expect(container.querySelector('[data-station-language="ar"]')).toHaveAttribute('lang', 'ar');

    fireEvent.click(screen.getByRole('button', { name: 'English' }));
    expect(screen.getByRole('heading', { name: 'Welcome to the clinic' })).toBeInTheDocument();
    expect(container.querySelector('[data-station-language="en"]')).toHaveAttribute('dir', 'ltr');
    expect(container.querySelector('[data-station-language="en"]')).toHaveAttribute('lang', 'en');
  });

  it('keeps 03.1 actions bounded and returns to public home after inactivity', () => {
    vi.useFakeTimers();
    const { container } = render(<StationKioskShell onAdminTap={vi.fn()} idleTimeoutMs={1} />);

    fireEvent.click(screen.getByRole('button', { name: /J’ai rendez-vous/i }));
    expect(container.querySelector('[data-station-screen="appointment"]')).toBeInTheDocument();
    expect(screen.getByText('Cette étape est en cours de construction.')).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(29_999);
    });
    expect(container.querySelector('[data-station-screen="appointment"]')).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(container.querySelector('[data-station-screen="home"]')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Bienvenue au cabinet' })).toBeInTheDocument();
  });

  it('resets the inactivity timer on public interaction', () => {
    vi.useFakeTimers();
    const { container } = render(<StationKioskShell onAdminTap={vi.fn()} idleTimeoutMs={30_000} />);

    fireEvent.click(screen.getByRole('button', { name: /Besoin d’aide/i }));
    act(() => {
      vi.advanceTimersByTime(20_000);
    });
    fireEvent.pointerDown(container.querySelector('[data-station-screen="help"]') as HTMLElement);
    act(() => {
      vi.advanceTimersByTime(20_000);
    });

    expect(container.querySelector('[data-station-screen="help"]')).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(10_000);
    });
    expect(container.querySelector('[data-station-screen="home"]')).toBeInTheDocument();
  });

  it('keeps the admin gesture hidden behind the Digital Crown control', () => {
    const onAdminTap = vi.fn();
    render(<StationKioskShell onAdminTap={onAdminTap} />);

    expect(screen.queryByText(/Administration du poste/i)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Digital Crown' }));
    expect(onAdminTap).toHaveBeenCalledTimes(1);
  });
});
