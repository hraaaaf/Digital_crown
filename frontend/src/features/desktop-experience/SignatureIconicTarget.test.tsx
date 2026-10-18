import { fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import { SignatureIconicTarget } from './SignatureIconicTarget';

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('LOT07 07-B Signature Iconic visual target (inert)', () => {
  it('defaults to Signature Core, with explicit nonclinical label', () => {
    render(<SignatureIconicTarget />);
    const root = screen.getByRole('region', { name: /Laboratoire visuel Signature Core et Iconic/i });
    expect(root.getAttribute('data-preview-experience')).toBe('core');
    expect(screen.getByRole('button', { name: /Signature Core/i }).getAttribute('aria-pressed')).toBe('true');
    expect(screen.getByLabelText('Aperçu non clinique')).toBeTruthy();
    expect(screen.getByText(/aucune donnée clinique, aucune préférence enregistrée/i)).toBeTruthy();
  });

  it('previews Iconic, then safely returns to Core with same four functions', () => {
    render(<SignatureIconicTarget />);
    const root = screen.getByRole('region', { name: /Laboratoire visuel Signature Core et Iconic/i });
    const choices = screen.getByRole('group', { name: /Style à prévisualiser/i });
    const navigation = screen.getByRole('navigation', { name: 'Écrans témoins' });
    const names = ['Tableau de bord', 'Agenda', 'Dossier patient', 'Imagerie'];

    for (const name of names) {
      expect(within(navigation).getByRole('button', { name })).toBeTruthy();
    }

    fireEvent.click(within(choices).getByRole('button', { name: /Signature Iconic/i }));
    expect(root.getAttribute('data-preview-experience')).toBe('iconic');

    fireEvent.click(within(navigation).getByRole('button', { name: 'Imagerie' }));
    expect(within(navigation).getByRole('button', { name: 'Imagerie' }).getAttribute('aria-current')).toBe('page');
    expect(screen.getByRole('heading', { name: /Imagerie/i })).toBeTruthy();

    fireEvent.click(within(choices).getByRole('button', { name: /Signature Core/i }));
    expect(root.getAttribute('data-preview-experience')).toBe('core');
    expect(within(navigation).getByRole('button', { name: 'Imagerie' }).getAttribute('aria-current')).toBe('page');
    expect(within(navigation).getAllByRole('button')).toHaveLength(4);
  });

  it('does not persist choice or alter the cabinet palette', () => {
    document.documentElement.dataset.theme = 'prestige';
    const beforeTheme = document.documentElement.dataset.theme;
    const setItem = vi.spyOn(Storage.prototype, 'setItem');
    const fetch = vi.spyOn(globalThis, 'fetch');
    render(<SignatureIconicTarget />);
    fireEvent.click(screen.getByRole('button', { name: /Signature Iconic/i }));
    fireEvent.click(screen.getByRole('button', { name: /Agenda/i }));
    expect(document.documentElement.dataset.theme).toBe(beforeTheme);
    expect(setItem).not.toHaveBeenCalled();
    expect(fetch).not.toHaveBeenCalled();
    delete document.documentElement.dataset.theme;
  });
});
