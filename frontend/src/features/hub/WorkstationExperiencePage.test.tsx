import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { WorkstationExperiencePage } from './WorkstationExperiencePage';
import { workstationModeService } from '../../services/workstationMode';

vi.mock('../../services/workstationMode', () => ({
  workstationModeService: {
    authorizeStationEscape: vi.fn(),
  },
}));

const unlockAdmin = () => {
  const logo = screen.getByRole('button', { name: 'Digital Crown' });
  for (let index = 0; index < 5; index += 1) fireEvent.click(logo);
};

describe('WorkstationExperiencePage Station escape', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('exposes no patient-visible exit or admin control until the hidden admin gesture', () => {
    render(<MemoryRouter><WorkstationExperiencePage experience="station" /></MemoryRouter>);
    expect(screen.queryByRole('button', { name: /Retour au Hub/i })).not.toBeInTheDocument();
    expect(screen.queryByText('Administration du poste')).not.toBeInTheDocument();

    unlockAdmin();

    expect(screen.getByText('Administration du poste')).toBeInTheDocument();
    expect(screen.getByLabelText('PIN propriétaire')).toBeInTheDocument();
  });

  it('expires an incomplete hidden admin gesture after three seconds', () => {
    vi.useFakeTimers();
    render(<MemoryRouter><WorkstationExperiencePage experience="station" /></MemoryRouter>);

    const logo = screen.getByRole('button', { name: 'Digital Crown' });
    for (let index = 0; index < 4; index += 1) fireEvent.click(logo);

    act(() => {
      vi.advanceTimersByTime(3_000);
    });
    fireEvent.click(logo);

    expect(screen.queryByText('Administration du poste')).not.toBeInTheDocument();
  });

  it('rejects malformed owner PIN locally without calling the server', async () => {
    render(<MemoryRouter><WorkstationExperiencePage experience="station" /></MemoryRouter>);

    unlockAdmin();
    fireEvent.change(screen.getByLabelText('PIN propriétaire'), { target: { value: '12' } });
    fireEvent.click(screen.getByRole('button', { name: 'Autoriser l’accès au Hub' }));

    expect(await screen.findByRole('status')).toHaveTextContent('PIN propriétaire requis.');
    expect(workstationModeService.authorizeStationEscape).not.toHaveBeenCalled();
  });

  it('leaves Station only after hidden admin activation and server-authorized owner PIN escape', async () => {
    vi.mocked(workstationModeService.authorizeStationEscape).mockResolvedValue({ expiresAt: Math.floor(Date.now() / 1000) + 300 });

    render(
      <MemoryRouter initialEntries={['/station']}>
        <Routes>
          <Route path="/station" element={<WorkstationExperiencePage experience="station" />} />
          <Route path="/hub" element={<div>HUB AUTHORIZED</div>} />
        </Routes>
      </MemoryRouter>,
    );

    unlockAdmin();
    fireEvent.change(screen.getByLabelText('PIN propriétaire'), { target: { value: '2468' } });
    fireEvent.click(screen.getByRole('button', { name: 'Autoriser l’accès au Hub' }));

    await waitFor(() => expect(workstationModeService.authorizeStationEscape).toHaveBeenCalledWith('2468'));
    await screen.findByText('HUB AUTHORIZED');
  });
});
