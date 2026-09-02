import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('./StudioControlsCore', () => ({
  StudioControls: () => <div data-testid="studio-core" />,
}));

import { StudioControls } from './StudioControls';

describe('document content vertical position control', () => {
  it('persists a dedicated body offset without mutating the safety margin', () => {
    const updateProfile = vi.fn();
    render(
      <StudioControls
        profile={{ content_offset_y: 0, margin_top: 3.6, qr_code_enabled: false }}
        updateProfile={updateProfile}
      />,
    );

    const slider = screen.getByRole('slider', { name: 'Position verticale du contenu' });
    expect(slider).toHaveAttribute('min', '-0.8');
    expect(slider).toHaveAttribute('max', '1.5');
    expect(slider).toHaveValue('0');

    fireEvent.change(slider, { target: { value: '0.8' } });
    expect(updateProfile).toHaveBeenCalledWith({ content_offset_y: 0.8 });
    expect(updateProfile).not.toHaveBeenCalledWith(expect.objectContaining({ margin_top: expect.anything() }));
  });

  it('resets only the body offset', () => {
    const updateProfile = vi.fn();
    render(
      <StudioControls
        profile={{ content_offset_y: 0.9, margin_top: 4.5, qr_code_enabled: false }}
        updateProfile={updateProfile}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Réinitialiser la position verticale du contenu' }));
    expect(updateProfile).toHaveBeenCalledWith({ content_offset_y: 0 });
  });
});
