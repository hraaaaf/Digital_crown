import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { FDIResearchPanel } from './FDIResearchPanel';

afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals(); });

describe('LOT05/J10F lab within Imagerie — artificial research image only', () => {
  it('requires explicit launch of sample; no patient image and no automatic confirmation', () => {
    render(<FDIResearchPanel />);
    expect(screen.getByText(/Ni image patient liée/i)).toBeTruthy();
    expect(screen.queryByText(/3 propositions/i)).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Exemple synthétique' }));
    expect(screen.getByText('3 propositions')).toBeTruthy();
    expect(screen.getByText('0 confirmées')).toBeTruthy();
    expect(screen.getByTestId('fdi-overlay')).toBeTruthy();
  });
  it('corrects the numbered tooth, confirms it, then revokes confirmation after geometry change', () => {
    render(<FDIResearchPanel />);
    fireEvent.click(screen.getByRole('button', { name: 'Exemple synthétique' }));
    fireEvent.click(screen.getByRole('button', { name: /36 · à vérifier/ }));
    fireEvent.change(screen.getByLabelText('Corriger numéro FDI'), { target: { value: '35' } });
    fireEvent.click(screen.getByRole('button', { name: 'Confirmer FDI' }));
    expect(screen.getByText('1 confirmées')).toBeTruthy();
    fireEvent.change(screen.getByLabelText('Rectangle X min'), { target: { value: '22' } });
    fireEvent.click(screen.getByRole('button', { name: 'Corriger rectangle' }));
    expect(screen.getByText('0 confirmées')).toBeTruthy();
  });
  it('does not connect to backend or fetch a clinical image when using synthetic samples', async () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal('fetch', fetchSpy);
    render(<FDIResearchPanel />);
    fireEvent.click(screen.getByRole('button', { name: 'Exemple synthétique' }));
    expect(screen.getByText(/aucune sauvegarde patient/i)).toBeTruthy();
    await waitFor(() => expect(fetchSpy).not.toHaveBeenCalled());
  });
  it('never accepts an act before FDI is confirmed', () => {
    render(<FDIResearchPanel />);
    fireEvent.click(screen.getByRole('button', { name: 'Exemple synthétique' }));
    fireEvent.click(screen.getByRole('button', { name: /36 · à vérifier/ }));
    fireEvent.change(screen.getByLabelText('Libellé de l’acte manuel'), { target: { value: 'Acte test manuel' } });
    fireEvent.click(screen.getByRole('button', { name: 'Ajouter un acte' }));
    fireEvent.click(screen.getByRole('button', { name: 'Associer manuellement à la dent confirmée' }));
    expect(screen.getByRole('status').textContent).toMatch(/Confirmer la dent avant tout acte/);
  });
});
