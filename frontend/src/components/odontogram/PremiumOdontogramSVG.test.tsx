import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { PremiumOdontogramSVG } from './PremiumOdontogramSVG';

describe('PremiumOdontogramSVG', () => {
  it('renders correct adult FDI teeth and exposes direct tooth controls', () => {
    const onToothClick = vi.fn();
    render(<PremiumOdontogramSVG type="ADULT" onToothClick={onToothClick} />);

    expect(screen.getByRole('group', { name: 'Odontogramme adulte' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Dent 18' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Dent 21' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Dent 48' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Dent 31' })).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Dent 11' }));
    expect(onToothClick).toHaveBeenCalledWith(11);
  });

  it('renders pediatric FDI teeth without adult quadrants', () => {
    render(<PremiumOdontogramSVG type="PEDIATRIC" />);

    expect(screen.getByRole('group', { name: 'Odontogramme enfant' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Dent 55' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Dent 61' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Dent 85' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Dent 71' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Dent 18' })).toBeNull();
  });

  it('keeps selected state accessible and keyboard-activatable', () => {
    const onToothClick = vi.fn();
    render(
      <PremiumOdontogramSVG
        type="ADULT"
        selectedTooth={11}
        multiSelectedTeeth={[12]}
        onToothClick={onToothClick}
      />,
    );

    expect(screen.getByRole('button', { name: 'Dent 11' }).getAttribute('aria-pressed')).toBe('true');
    expect(screen.getByRole('button', { name: 'Dent 12' }).getAttribute('aria-pressed')).toBe('true');

    fireEvent.keyDown(screen.getByRole('button', { name: 'Dent 21' }), { key: 'Enter' });
    expect(onToothClick).toHaveBeenCalledWith(21);
  });

  it('uses semantic theme classes instead of hardcoded primary selection colors', () => {
    const { container } = render(<PremiumOdontogramSVG type="ADULT" selectedTooth={11} />);
    const markup = container.innerHTML;

    expect(markup).toContain('fill-primary');
    expect(markup).toContain('stroke-primary');
    expect(markup).toContain('stroke-card');
    expect(markup).toContain('fill-text-muted');
    expect(markup).toContain('data-odontogram-asset="approved-raster-reference-v1"');
    expect(markup).not.toMatch(/#003380|#059669|#db2777|#0284c7|#475569|#4f46e5|rgb\(|hsl\(/i);
  });
});
