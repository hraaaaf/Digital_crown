import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeAll, describe, expect, it, vi } from 'vitest';
import { PALETTE } from '../cephaloTheme';
import { StepTab } from './StepTab';

beforeAll(() => {
  if (typeof globalThis.PointerEvent === 'undefined') {
    Object.defineProperty(globalThis, 'PointerEvent', {
      value: MouseEvent,
      configurable: true,
    });
  }
});

describe('StepTab R15bis', () => {
  it('exposes the active step semantically and remains keyboard activatable', async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();

    render(
      <StepTab
        id={3}
        label="Synthèse clinique"
        isActive
        isCompleted={false}
        onClick={onClick}
        P={PALETTE.light}
      />,
    );

    const button = screen.getByRole('button', { name: /3.*Synthèse clinique/i });
    expect(button).toHaveAttribute('aria-current', 'step');
    expect(button).toHaveClass('min-h-11');

    await user.tab();
    expect(button).toHaveFocus();
    await user.keyboard('{Enter}');
    expect(onClick).toHaveBeenCalledTimes(1);
  });
});
