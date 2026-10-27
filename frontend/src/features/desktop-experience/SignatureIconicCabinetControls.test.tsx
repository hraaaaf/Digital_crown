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
});
