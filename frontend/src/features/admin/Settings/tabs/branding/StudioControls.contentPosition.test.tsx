import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('./StudioControlsCore', () => ({
  StudioControls: () => <div data-testid="studio-core" />,
}));

import { StudioControls } from './StudioControls';

describe('document content vertical position control', () => {
  it('moves the persisted top margin through the dedicated slider', () => {
    const updateProfile = vi.fn();
    render(<StudioControls profile={{ margin_top: 3.6, qr_code_enabled: false }} updateProfile={updateProfile} />);

    const slider = screen.getByRole('slider', { name: 'Position verticale du contenu' });
    expect(slider).toHaveAttribute('min', '2.8');
    expect(slider).toHaveAttribute('max', '5.1');
    expect(slider).toHaveValue('3.6');

    fireEvent.change(slider, { target: { value: '4.4' } });
    expect(updateProfile).toHaveBeenCalledWith({ margin_top: 4.4 });
  });

  it('resets the body position without touching header or footer controls', () => {
    const updateProfile = vi.fn();
    render(<StudioControls profile={{ margin_top: 4.5, qr_code_enabled: false }} updateProfile={updateProfile} />);

    fireEvent.click(screen.getByRole('button', { name: 'Réinitialiser la position verticale du contenu' }));
    expect(updateProfile).toHaveBeenCalledWith({ margin_top: 3.6 });
  });
});
