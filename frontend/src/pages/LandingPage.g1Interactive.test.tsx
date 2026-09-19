import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { LandingPage } from './LandingPage';
import { api } from '../services/api';
import toast from 'react-hot-toast';

vi.mock('../services/api', () => ({ api: { post: vi.fn() } }));
vi.mock('react-hot-toast', () => ({ default: { success: vi.fn(), error: vi.fn() } }));

function renderPage() {
  return render(<MemoryRouter><LandingPage /></MemoryRouter>);
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.post).mockResolvedValue({ data: {} } as never);
});
afterEach(() => cleanup());

describe('LandingPage G1 interactive matrix', () => {
  it('does not mutate demo endpoint while required business fields are incomplete', () => {
    renderPage();
    fireEvent.submit(screen.getByRole('button', { name: /Envoyer ma demande/i }).closest('form')!);
    expect(api.post).not.toHaveBeenCalled();
  });

  it('submits exact demo request and renders success only after backend ACK', async () => {
    renderPage();
    fireEvent.change(screen.getByPlaceholderText('Votre nom *'), { target: { value: 'Dr Test' } });
    fireEvent.change(screen.getByPlaceholderText('Email professionnel *'), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByPlaceholderText('Nom du cabinet *'), { target: { value: 'Cabinet Test' } });
    const form = screen.getByRole('button', { name: /Envoyer ma demande/i }).closest('form')!;
    fireEvent.submit(form);

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/public/demo-request', expect.objectContaining({
      nom: 'Dr Test', email: 'test@example.com', cabinet: 'Cabinet Test',
    })));
    expect(await screen.findByText('Demande envoyée !')).toBeTruthy();
    expect(toast.success).toHaveBeenCalledTimes(1);
  });

  it('surfaces backend failure without false success', async () => {
    vi.mocked(api.post).mockRejectedValueOnce(new Error('offline') as never);
    renderPage();
    fireEvent.change(screen.getByPlaceholderText('Votre nom *'), { target: { value: 'Dr Test' } });
    fireEvent.change(screen.getByPlaceholderText('Email professionnel *'), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByPlaceholderText('Nom du cabinet *'), { target: { value: 'Cabinet Test' } });
    fireEvent.submit(screen.getByRole('button', { name: /Envoyer ma demande/i }).closest('form')!);

    await waitFor(() => expect(api.post).toHaveBeenCalledTimes(1));
    expect(screen.queryByText('Demande envoyée !')).toBeNull();
    expect(toast.error).toHaveBeenCalledTimes(1);
  });

  it('exposes canonical public navigation targets', () => {
    renderPage();
    expect(screen.getByRole('link', { name: 'Connexion' }).getAttribute('href')).toBe('/login');
    expect(screen.getAllByRole('link', { name: /Télécharger/i }).some(link => link.getAttribute('href') === '/download')).toBe(true);
    expect(screen.getAllByRole('link', { name: 'Commencer' }).every(link => link.getAttribute('href') === '/register')).toBe(true);
  });
});
