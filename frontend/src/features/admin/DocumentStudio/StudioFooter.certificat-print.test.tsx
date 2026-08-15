import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { StudioFooter } from './StudioFooter';

const baseProps = {
  loading: false,
  showPrintWarning: false,
  onCloseWarning: vi.fn(),
  hasChanges: false,
  sideStudioType: 'PREVIEW' as const,
  onTogglePreview: vi.fn(),
};

describe('P3 certificate print safety', () => {
  it('prepares and archives a fresh certificate PDF instead of direct-printing the current preview', () => {
    const onGenerate = vi.fn();

    render(
      <StudioFooter
        {...baseProps}
        activeTab="certificat"
        onGenerate={onGenerate}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: /Préparer impression/i }));

    expect(onGenerate).toHaveBeenCalledWith(true, false, false, false);
    expect(screen.queryByRole('button', { name: /^Imprimer$/i })).toBeNull();
  });

  it('does not change direct-print behavior for other document types', () => {
    const onGenerate = vi.fn();

    render(
      <StudioFooter
        {...baseProps}
        activeTab="ordonnance"
        onGenerate={onGenerate}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: /^Imprimer$/i }));

    expect(onGenerate).toHaveBeenCalledWith(false, true, false, false);
  });
});
