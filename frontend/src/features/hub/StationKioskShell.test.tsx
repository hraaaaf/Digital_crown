import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { StationKioskShell } from './StationKioskShell';
import { stationPatientSessionService } from '../../services/stationPatientSession';

vi.mock('../../services/stationPatientSession', () => ({
  stationPatientSessionService: {
    create: vi.fn(),
    status: vi.fn(),
    fallback: vi.fn(),
    todayAppointments: vi.fn(),
    arrive: vi.fn(),
    purge: vi.fn(),
    requestStaffAssistance: vi.fn(),
  },
}));

describe('StationKioskShell', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(stationPatientSessionService.create).mockReturnValue(new Promise(() => undefined));
    vi.mocked(stationPatientSessionService.purge).mockResolvedValue(undefined);
  });
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

  it('keeps the appointment flow bounded and returns to public home after inactivity', () => {
    vi.useFakeTimers();
    const { container } = render(<StationKioskShell onAdminTap={vi.fn()} idleTimeoutMs={1} />);

    fireEvent.click(screen.getByRole('button', { name: /J’ai rendez-vous/i }));
    expect(container.querySelector('[data-station-screen="appointment"]')).toBeInTheDocument();
    expect(screen.getByText('Identification et arrivée au cabinet')).toBeInTheDocument();

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

  it('purges the patient session when kiosk inactivity returns home', async () => {
    vi.useFakeTimers();
    vi.mocked(stationPatientSessionService.create).mockResolvedValue({
      sessionId: 'session-timeout',
      handoffUrl: 'https://cabinet.local/companion?stationSession=opaque',
      nfcPayload: 'https://cabinet.local/companion?stationSession=opaque',
      qrDataUrl: 'data:image/png;base64,AAAA',
      expiresAt: new Date(Date.now() + 120_000).toISOString(),
      fallbackMode: 'disabled',
    });
    vi.mocked(stationPatientSessionService.status).mockResolvedValue({
      status: 'pending',
      sessionId: 'session-timeout',
      expiresAt: new Date(Date.now() + 120_000).toISOString(),
    });

    const { container } = render(<StationKioskShell onAdminTap={vi.fn()} idleTimeoutMs={30_000} />);
    fireEvent.click(screen.getByRole('button', { name: /J’ai rendez-vous/i }));
    expect(await screen.findByAltText('QR d’identification Patient Companion')).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(30_000);
    });

    expect(container.querySelector('[data-station-screen="home"]')).toBeInTheDocument();
    await act(async () => {
      await Promise.resolve();
    });
    expect(stationPatientSessionService.purge).toHaveBeenCalledWith('session-timeout');
    expect(screen.queryByText(/session-timeout/i)).toBeNull();
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

  it('includes reduced-motion guards on animated kiosk controls', () => {
    render(<StationKioskShell onAdminTap={vi.fn()} />);
    const appointment = screen.getByRole('button', { name: /J’ai rendez-vous/i });
    expect(appointment.className).toContain('motion-reduce:transition-none');
    expect(appointment.className).toContain('motion-reduce:hover:translate-y-0');
  });

  it('keeps the admin gesture hidden behind the Digital Crown control', () => {
    const onAdminTap = vi.fn();
    render(<StationKioskShell onAdminTap={onAdminTap} />);

    expect(screen.queryByText(/Administration du poste/i)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Digital Crown' }));
    expect(onAdminTap).toHaveBeenCalledTimes(1);
  });
  it('propagates English and Arabic into the appointment identity flow with RTL preserved', async () => {
    const { container } = render(<StationKioskShell onAdminTap={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: 'English' }));
    fireEvent.click(screen.getByRole('button', { name: /I have an appointment/i }));
    expect(await screen.findByText('Preparing the secure session…')).toBeInTheDocument();
    expect(container.querySelector('[data-station-language="en"]')).toHaveAttribute('dir', 'ltr');

    fireEvent.click(screen.getByRole('button', { name: 'العربية' }));
    fireEvent.click(screen.getByRole('button', { name: /لدي موعد/i }));
    expect(await screen.findByText('جارٍ إعداد الجلسة الآمنة…')).toBeInTheDocument();
    expect(container.querySelector('[data-station-language="ar"]')).toHaveAttribute('dir', 'rtl');
  });

});
