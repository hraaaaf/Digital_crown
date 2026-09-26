import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { PremiumOdontogramSVG } from './PremiumOdontogramSVG';

const ADULT = [18,17,16,15,14,13,12,11,21,22,23,24,25,26,27,28,48,47,46,45,44,43,42,41,31,32,33,34,35,36,37,38];
const CHILD = [55,54,53,52,51,61,62,63,64,65,85,84,83,82,81,71,72,73,74,75];

describe('PremiumOdontogramSVG', () => {
  it('uses the exact user adult reference and maps all 32 FDI buttons', () => {
    const onToothClick = vi.fn();
    const { container } = render(<PremiumOdontogramSVG type="ADULT" onToothClick={onToothClick} />);

    expect(screen.getByRole('group', { name: 'Odontogramme adulte' })).toBeTruthy();
    expect(screen.getAllByRole('button')).toHaveLength(32);
    expect(container.innerHTML).toContain('digital-crown-adult-reference-v2.png');
    expect(container.innerHTML).toContain('data-odontogram-asset="user-reference-adult-v2"');

    ADULT.forEach((tooth) => fireEvent.click(screen.getByRole('button', { name: `Dent ${tooth}` })));
    expect(onToothClick.mock.calls.map(([tooth]) => tooth)).toEqual(ADULT);
  });

  it('uses the exact user child reference and maps all 20 primary FDI buttons', () => {
    const onToothClick = vi.fn();
    const { container } = render(<PremiumOdontogramSVG type="PEDIATRIC" onToothClick={onToothClick} />);

    expect(screen.getByRole('group', { name: 'Odontogramme enfant' })).toBeTruthy();
    expect(screen.getAllByRole('button')).toHaveLength(20);
    expect(container.innerHTML).toContain('digital-crown-child-reference-v2.png');
    expect(container.innerHTML).toContain('data-odontogram-asset="user-reference-child-v2"');

    CHILD.forEach((tooth) => fireEvent.click(screen.getByRole('button', { name: `Dent ${tooth}` })));
    expect(onToothClick.mock.calls.map(([tooth]) => tooth)).toEqual(CHILD);
  });

  it('keeps selected state accessible and keyboard-activatable', () => {
    const onToothClick = vi.fn();
    render(<PremiumOdontogramSVG type="ADULT" selectedTooth={11} multiSelectedTeeth={[12]} onToothClick={onToothClick} />);

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
    expect(markup).not.toMatch(/#003380|#059669|#db2777|#0284c7|#475569|#4f46e5|rgb\(|hsl\(/i);
  });
});
