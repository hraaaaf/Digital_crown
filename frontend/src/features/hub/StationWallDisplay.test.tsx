import { render, screen, waitFor } from '@testing-library/react';
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
    vi.clearAllMocks();
  });

  it('renders only pseudonymous waiting identifiers', async () => {
    vi.mocked(stationWallDisplayService.snapshot).mockResolvedValue({
      waitingCount: 2,
      entries: [
        { ticketNumber: 12, initials: 'A. B.' },
        { ticketNumber: 23, initials: 'N. E.' },
      ],
      currentCall: null,
      callTtlSeconds: 20,
    });

    const { container } = render(<StationWallDisplay />);

    expect((await screen.findAllByText('N° de file')).length).toBe(2);
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('A. B.')).toBeInTheDocument();
    expect(container.querySelector('[data-wall-state="waiting"]')).toBeInTheDocument();
    expect(container.textContent).not.toMatch(/diagnostic|motif|téléphone/i);
  });

  it('bounds waiting cards to eight even if the feed regresses', async () => {
    vi.mocked(stationWallDisplayService.snapshot).mockResolvedValue({
      waitingCount: 12,
      entries: Array.from({ length: 12 }, (_, index) => ({
        ticketNumber: 100 + index,
        initials: 'P. T.',
      })),
      currentCall: null,
      callTtlSeconds: 20,
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

  it('shows one bounded staff call without changing the public data contract', async () => {
    vi.mocked(stationWallDisplayService.snapshot).mockResolvedValue({
      waitingCount: 1,
      entries: [{ ticketNumber: 44, initials: 'S. A.' }],
      currentCall: {
        ticketNumber: 44,
        initials: 'S. A.',
        expiresAt: new Date(Date.now() + 10_000).toISOString(),
      },
      callTtlSeconds: 20,
    });

    const { container } = render(<StationWallDisplay />);

    expect(await screen.findByText('Patient appelé')).toBeInTheDocument();
    expect(screen.getByText('N° 44')).toBeInTheDocument();
    expect(screen.getByText('S. A.')).toBeInTheDocument();
    await waitFor(() => {
      expect(container.querySelector('[data-wall-state="calling"]')).toBeInTheDocument();
    });
  });

  it('fails closed to an unavailable public state when the wall feed cannot be read', async () => {
    vi.mocked(stationWallDisplayService.snapshot).mockRejectedValue(new Error('offline'));

    const { container } = render(<StationWallDisplay />);

    expect(await screen.findByText('Affichage momentanément indisponible')).toBeInTheDocument();
    expect(container.querySelector('[data-wall-state="unavailable"]')).toBeInTheDocument();
  });
});
