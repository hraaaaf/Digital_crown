import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { StationWallDisplay } from './StationWallDisplay';
import { stationWallDisplayService } from '../../services/stationWallDisplay';

vi.mock('../../services/stationWallDisplay', () => ({
  stationWallDisplayService: {
    snapshot: vi.fn(),
    callPatient: vi.fn(),
  },
}));

describe('StationWallDisplay', () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
    vi.unstubAllGlobals();
  });

  it('renders initials by default without clinical data', async () => {
    vi.mocked(stationWallDisplayService.snapshot).mockResolvedValue({
      waitingCount: 2,
      entries: [
        { ticketNumber: 12, identityLabel: 'A. B.' },
        { ticketNumber: 23, identityLabel: 'N. E.' },
      ],
      currentCall: null,
      callTtlSeconds: 20,
      identityMode: 'initials',
    });

    const { container } = render(<StationWallDisplay />);

    expect((await screen.findAllByText('N° de file')).length).toBe(2);
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('A. B.')).toBeInTheDocument();
    expect(container.querySelector('[data-wall-state="waiting"]')).toBeInTheDocument();
    expect(container.textContent).not.toMatch(/diagnostic|motif|téléphone/i);
  });

  it('renders full name only when explicitly configured', async () => {
    vi.mocked(stationWallDisplayService.snapshot).mockResolvedValue({
      waitingCount: 1,
      entries: [{ ticketNumber: 12, identityLabel: 'Aya Benali' }],
      currentCall: null,
      callTtlSeconds: 20,
      identityMode: 'full_name',
    });

    render(<StationWallDisplay />);

    expect(await screen.findByText('Aya Benali')).toBeInTheDocument();
    expect(screen.getByText(/nom complet/i)).toBeInTheDocument();
  });

  it('renders ticket numbers only when configured', async () => {
    vi.mocked(stationWallDisplayService.snapshot).mockResolvedValue({
      waitingCount: 1,
      entries: [{ ticketNumber: 12, identityLabel: null }],
      currentCall: null,
      callTtlSeconds: 20,
      identityMode: 'number_only',
    });

    render(<StationWallDisplay />);

    expect(await screen.findByText('12')).toBeInTheDocument();
    expect(screen.queryByText('A. B.')).toBeNull();
    expect(screen.getByText(/numéro uniquement/i)).toBeInTheDocument();
  });

  it('bounds waiting cards to eight even if the feed regresses', async () => {
    vi.mocked(stationWallDisplayService.snapshot).mockResolvedValue({
      waitingCount: 12,
      entries: Array.from({ length: 12 }, (_, index) => ({
        ticketNumber: 100 + index,
        identityLabel: 'P. T.',
      })),
      currentCall: null,
      callTtlSeconds: 20,
      identityMode: 'initials',
    });

    render(<StationWallDisplay />);

    expect((await screen.findAllByText('N° de file')).length).toBe(8);
    expect(screen.queryByText('108')).toBeNull();
    expect(screen.getByText('Certaines arrivées sont prises en charge directement par l’accueil.')).toBeInTheDocument();
  });

  it('does not present an unverified feed as an empty waiting room before first read', () => {
    vi.mocked(stationWallDisplayService.snapshot).mockReturnValue(new Promise(() => undefined));

    const { container } = render(<StationWallDisplay />);

    expect(screen.getByText('Synchronisation de l’affichage…')).toBeInTheDocument();
    expect(container.querySelector('[data-wall-state="loading"]')).toBeInTheDocument();
  });

  it('primes audio from the explicit user gesture before later calls', async () => {
    vi.mocked(stationWallDisplayService.snapshot).mockResolvedValue({
      waitingCount: 0,
      entries: [],
      currentCall: null,
      callTtlSeconds: 20,
      identityMode: 'initials',
    });
    let instance: { state: string; resume: ReturnType<typeof vi.fn> } | null = null;
    class FakeAudioContext {
      state = 'suspended';
      currentTime = 0;
      destination = {};
      resume = vi.fn(async () => { this.state = 'running'; });
      close = vi.fn(async () => { this.state = 'closed'; });
      createOscillator = vi.fn();
      createGain = vi.fn();
      constructor() { instance = this; }
    }
    vi.stubGlobal('AudioContext', FakeAudioContext);

    render(<StationWallDisplay />);
    await screen.findByText('Merci de patienter');
    fireEvent.click(screen.getByRole('button', { name: 'Activer le son' }));

    await screen.findByRole('button', { name: 'Son activé' });
    expect(instance).not.toBeNull();
    expect(instance!.resume).toHaveBeenCalledTimes(1);
  });

  it('shows one bounded staff call without changing the public data contract', async () => {
    vi.mocked(stationWallDisplayService.snapshot).mockResolvedValue({
      waitingCount: 1,
      entries: [{ ticketNumber: 44, identityLabel: 'S. A.' }],
      currentCall: {
        ticketNumber: 44,
        identityLabel: 'S. A.',
        expiresAt: new Date(Date.now() + 10_000).toISOString(),
      },
      callTtlSeconds: 20,
      identityMode: 'initials',
    });

    const { container } = render(<StationWallDisplay />);

    expect(await screen.findByText('Patient appelé')).toBeInTheDocument();
    expect(screen.getByText('N° 44')).toBeInTheDocument();
    expect(screen.getByText('S. A.')).toBeInTheDocument();
    await waitFor(() => {
      expect(container.querySelector('[data-wall-state="calling"]')).toBeInTheDocument();
    });
  });

  it('ignores a stale poll response that resolves after a newer call state', async () => {
    vi.useFakeTimers();
    let resolveFirst!: (value: Awaited<ReturnType<typeof stationWallDisplayService.snapshot>>) => void;
    let resolveSecond!: (value: Awaited<ReturnType<typeof stationWallDisplayService.snapshot>>) => void;
    const first = new Promise<Awaited<ReturnType<typeof stationWallDisplayService.snapshot>>>(resolve => { resolveFirst = resolve; });
    const second = new Promise<Awaited<ReturnType<typeof stationWallDisplayService.snapshot>>>(resolve => { resolveSecond = resolve; });
    vi.mocked(stationWallDisplayService.snapshot)
      .mockReturnValueOnce(first)
      .mockReturnValueOnce(second);

    const { container } = render(<StationWallDisplay />);

    await act(async () => {
      vi.advanceTimersByTime(2_000);
    });
    await act(async () => {
      resolveSecond({
        waitingCount: 1,
        entries: [{ ticketNumber: 44, identityLabel: 'S. A.' }],
        currentCall: {
          ticketNumber: 44,
          identityLabel: 'S. A.',
          expiresAt: new Date(Date.now() + 10_000).toISOString(),
        },
        callTtlSeconds: 20,
      identityMode: 'initials',
      });
      await Promise.resolve();
    });
    expect(container.querySelector('[data-wall-state="calling"]')).toBeInTheDocument();

    await act(async () => {
      resolveFirst({
        waitingCount: 1,
        entries: [{ ticketNumber: 44, identityLabel: 'S. A.' }],
        currentCall: null,
        callTtlSeconds: 20,
      identityMode: 'initials',
      });
      await Promise.resolve();
    });
    expect(container.querySelector('[data-wall-state="calling"]')).toBeInTheDocument();
  });

  it('fails closed to an unavailable public state when the wall feed cannot be read', async () => {
    vi.mocked(stationWallDisplayService.snapshot).mockRejectedValue(new Error('offline'));

    const { container } = render(<StationWallDisplay />);

    expect(await screen.findByText('Affichage momentanément indisponible')).toBeInTheDocument();
    expect(container.querySelector('[data-wall-state="unavailable"]')).toBeInTheDocument();
  });
});
