import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { FrontdeskView } from './FrontdeskView';

vi.mock('../../../../services/api', () => ({
  api: {
    get: vi.fn().mockResolvedValue({ data: [] }),
    post: vi.fn(),
  },
}));

afterEach(() => cleanup());

describe('Accueil mobile MOB-5B', () => {
  it('renders the dedicated mobile empty state without desktop alerts', async () => {
    render(<FrontdeskView />);
    expect(await screen.findByText('Accueil')).toBeTruthy();
    expect(await screen.findByText('Aucune demande en attente')).toBeTruthy();
    expect(screen.queryByText('Créer demande')).toBeNull();
  });
});
