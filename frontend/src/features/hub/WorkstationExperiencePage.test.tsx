import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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

  it('exposes no patient-visible exit or admin control until the hidden admin gesture', () => {
    render(<MemoryRouter><WorkstationExperiencePage experience="station" /></MemoryRouter>);
    expect(screen.queryByRole('button', { name: /Retour au Hub/i })).not.toBeInTheDocument();
    expect(screen.queryByText('Administration du poste')).not.toBeInTheDocument();

    unlockAdmin();

    expect(screen.getByText('Administration du poste')).toBeInTheDocument();
    expect(screen.getByLabelText('PIN propriétaire')).toBeInTheDocument();
  });

  it('leaves Station only after hidden admin activation and server-authorized owner PIN escape', async () => {
    vi.mocked(workstationModeService.authorizeStationEscape).mockResolvedValue();

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
