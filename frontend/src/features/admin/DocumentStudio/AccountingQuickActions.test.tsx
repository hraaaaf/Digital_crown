import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

import { AccountingQuickActions } from './AccountingQuickActions';

const acts = [
  { name: 'Consultation', price: 300, category: 'CONSERVATRICE' },
  { name: 'Détartrage', price: 500, category: 'PREVENTION' },
];

describe('AccountingQuickActions P2-C', () => {
  it('s’ouvre par une action explicite sans dépendre du hover', () => {
    render(<AccountingQuickActions acts={acts} onSelect={vi.fn()} onAddManual={vi.fn()} />);

    const toggle = screen.getByRole('button', { name: 'Actes rapides' });
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByRole('button', { name: /Consultation/ })).not.toBeInTheDocument();

    fireEvent.click(toggle);

    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByRole('button', { name: /Consultation/ })).toBeInTheDocument();
  });

  it('transmet l’acte choisi et expose un ajout manuel', () => {
    const onSelect = vi.fn();
    const onAddManual = vi.fn();
    render(<AccountingQuickActions acts={acts} onSelect={onSelect} onAddManual={onAddManual} />);

    fireEvent.click(screen.getByRole('button', { name: 'Actes rapides' }));
    fireEvent.click(screen.getByRole('button', { name: /Détartrage/ }));
    fireEvent.click(screen.getByRole('button', { name: 'Nouvel acte' }));

    expect(onSelect).toHaveBeenCalledWith(acts[1]);
    expect(onAddManual).toHaveBeenCalledTimes(1);
  });
});
