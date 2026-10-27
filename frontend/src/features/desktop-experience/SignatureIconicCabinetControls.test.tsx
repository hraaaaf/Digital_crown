import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import fs from 'node:fs';
import path from 'node:path';
import { SignatureIconicCabinetControls } from './SignatureIconicCabinetControls';

afterEach(() => cleanup());

describe('LOT07 R4 — authentic Cabinet pages remain Core by default', () => {
  it('offers reversible accessible controls without storage, backend call or new clinical state', () => {
    const setItem = vi.spyOn(Storage.prototype, 'setItem');
    const onChange = vi.fn();
    const { rerender } = render(<SignatureIconicCabinetControls mode="core" onChange={onChange} />);
    const core = screen.getByRole('button', { name: 'Signature Core' });
    const iconic = screen.getByRole('button', { name: 'Signature Iconic' });
    expect(core).toHaveAttribute('aria-pressed', 'true');
    fireEvent.click(iconic);
    expect(onChange).toHaveBeenCalledWith('iconic');
    rerender(<SignatureIconicCabinetControls mode="iconic" onChange={onChange} />);
    fireEvent.click(core);
    expect(onChange).toHaveBeenLastCalledWith('core');
    expect(setItem).not.toHaveBeenCalled();
    setItem.mockRestore();
  });

  it('only connects to four real Cabinet routes behind both DEV and opt-in', () => {
    const main = fs.readFileSync(path.resolve(__dirname, '../../components/Layout/MainLayout.tsx'), 'utf8');
    expect(main).toContain("import.meta.env.DEV");
    expect(main).toContain("import.meta.env.VITE_V15_07_R4_SIGNATURE_LAB === 'true'");
    expect(main).toContain('data-r4-signature={r4SignaturePreviewEnabled ? r4SignatureMode : undefined}');
    expect(main).toContain('SignatureIconicCabinetControls mode={r4SignatureMode}');
    expect(main).toContain("isCommandCabinetLab");
    expect(main).toContain("location.pathname");
  });
  it('inherits all R4 Iconic colors from the current Cabinet theme tokens', () => {
    const css = fs.readFileSync(path.resolve(__dirname, './SignatureIconicCabinetPreview.css'), 'utf8');
    const palette = fs.readFileSync(path.resolve(__dirname, '../../index.css'), 'utf8');
    const expected = ['--primary', '--card-bg', '--text-main', '--text-muted', '--border-color'];
    const consumed = [...css.matchAll(/var\\((--[a-z-]+)/g)].map(match => match[1]);
    expect(new Set(consumed)).toEqual(new Set(expected));
    for (const token of expected) {
      expect(palette).toContain(token + ':');
    }
    expect(css).not.toMatch(/#[a-f\\d]{3,8}\\b|(?:rgba?|hsla?|oklch|lab)\\s*\\(/i);
    expect(css).not.toContain('var(--border-main)');
    expect(palette).toContain('--color-primary: var(--primary)');
    expect(palette).toContain('--color-border-main: var(--border-color)');
    for (const theme of ['emerald', 'rose', 'prestige', 'ocean', 'graphite', 'dark', 'high-contrast']) {
      expect(palette).toContain("[data-theme='" + theme + "']");
    }
  });

});
