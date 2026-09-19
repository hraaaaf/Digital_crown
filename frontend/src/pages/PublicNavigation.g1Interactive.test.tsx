import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { DownloadPage } from './DownloadPage';
import { LegalPage } from './LegalPage';

afterEach(() => cleanup());

describe('G1 public navigation contracts', () => {
  it('keeps DownloadPage internal destinations canonical', () => {
    render(<MemoryRouter><DownloadPage /></MemoryRouter>);

    expect(screen.getByRole('link', { name: /Retour au site/i }).getAttribute('href')).toBe('/landing');
    expect(screen.getByRole('link', { name: /code d.activation/i }).getAttribute('href')).toBe('/activate');
    expect(screen.getAllByRole('link').some(link => link.getAttribute('href') === '/mobile/onboarding')).toBe(true);
  });

  it.each(['terms', 'privacy'] as const)('keeps %s legal page return destination on login', (type) => {
    render(<MemoryRouter><LegalPage type={type} /></MemoryRouter>);
    expect(screen.getByRole('link', { name: /Retour/i }).getAttribute('href')).toBe('/login');
  });
});
