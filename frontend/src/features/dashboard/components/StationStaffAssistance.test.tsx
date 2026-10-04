import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { StationStaffAssistance } from './StationStaffAssistance';
import { stationStaffAssistanceService } from '../../../services/stationStaffAssistance';

vi.mock('../../../services/stationStaffAssistance', () => ({
  stationStaffAssistanceService: { list: vi.fn(), acknowledge: vi.fn() },
}));

describe('StationStaffAssistance V1.5-03.4', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(stationStaffAssistanceService.acknowledge).mockResolvedValue();
  });

  it('surfaces a durable station request without patient identity and acknowledges it', async () => {
    vi.mocked(stationStaffAssistanceService.list).mockResolvedValue([
      { alertId: 7, requestedAt: '2026-10-04T10:00:00' },
    ]);
    render(<StationStaffAssistance visible />);
    expect(await screen.findByText('Assistance demandée à la station')).toBeInTheDocument();
    expect(screen.getByText(/Une personne identifiée/)).toBeInTheDocument();
    expect(screen.queryByText(/Aya|Audit/)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Pris en charge' }));
    await waitFor(() => expect(stationStaffAssistanceService.acknowledge).toHaveBeenCalledWith(7));
    await waitFor(() => expect(screen.queryByText('Assistance demandée à la station')).not.toBeInTheDocument());
  });

  it('reports an acknowledgement failure without removing the request', async () => {
    vi.mocked(stationStaffAssistanceService.list).mockResolvedValue([{ alertId: 8, requestedAt: '2026-10-04T10:05:00' }]);
    vi.mocked(stationStaffAssistanceService.acknowledge).mockRejectedValue(new Error('request failed'));
    render(<StationStaffAssistance visible />);
    fireEvent.click(await screen.findByRole('button', { name: 'Pris en charge' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/Acquittement non enregistré/);
    expect(screen.getByText(/demande #8/)).toBeInTheDocument();
  });

  it('fails visibly when the staff feed cannot be checked', async () => {
    vi.mocked(stationStaffAssistanceService.list).mockRejectedValue(new Error('offline'));
    render(<StationStaffAssistance visible />);
    expect(await screen.findByText('Signal station indisponible')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent(/Vérifiez directement la station/);
  });

  it('renders nothing when the staff feed is empty', async () => {
    vi.mocked(stationStaffAssistanceService.list).mockResolvedValue([]);
    const { container } = render(<StationStaffAssistance visible />);
    await waitFor(() => expect(stationStaffAssistanceService.list).toHaveBeenCalled());
    expect(container).toBeEmptyDOMElement();
  });
});
