import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

import { PrescriptionContextualChoice } from './PrescriptionContextualChoice';

describe('PrescriptionContextualChoice', () => {
  it('selects an existing alternative', () => {
    const onSelect = vi.fn();
    render(
      <PrescriptionContextualChoice
        ariaLabel="Dose"
        value="1 g"
        placeholder="Dose"
        options={[
          { value: '500 mg', label: '500 mg' },
          { value: '1 g', label: '1 g' },
        ]}
        onSelect={onSelect}
        onManual={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Dose' }));
    fireEvent.click(screen.getByRole('menuitem', { name: /500 mg/i }));
    expect(onSelect).toHaveBeenCalledWith('500 mg');
  });

  it('always exposes a manual override path', () => {
    const onManual = vi.fn();
    render(
      <PrescriptionContextualChoice
        ariaLabel="Durée ou limite"
        value="3 jours"
        placeholder="Durée"
        options={[{ value: '3 jours', label: '3 jours' }]}
        onSelect={vi.fn()}
        onManual={onManual}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Durée ou limite' }));
    fireEvent.click(screen.getByRole('menuitem', { name: /Modifier manuellement/i }));
    fireEvent.change(screen.getByRole('textbox', { name: /Valeur personnalisée/i }), {
      target: { value: '8 jours' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Appliquer' }));
    expect(onManual).toHaveBeenCalledWith('8 jours');
  });
});
