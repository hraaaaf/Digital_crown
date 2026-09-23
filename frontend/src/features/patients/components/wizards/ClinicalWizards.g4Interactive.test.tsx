import React from 'react';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AssistantParo } from './AssistantParo';
import { AssistantEndo } from './AssistantEndo';
import { AssistantChirurgie } from './AssistantChirurgie';
import { AssistantProthese } from './AssistantProthese';
import { AssistantPedo } from './AssistantPedo';
import { AssistantOrtho } from './AssistantOrtho';
import { AssistantATM } from './AssistantATM';
import { AssistantPatho } from './AssistantPatho';
import { AssistantExamenComplet } from './AssistantExamenComplet';

vi.mock('framer-motion', async () => {
  const ReactModule = await import('react');
  const make = (tag: string) => ReactModule.forwardRef(({ children, initial, animate, exit, transition, layout, ...props }: any, ref: any) =>
    ReactModule.createElement(tag, { ...props, ref }, children)
  );
  return {
    AnimatePresence: ({ children }: any) => ReactModule.createElement(ReactModule.Fragment, null, children),
    motion: new Proxy({}, { get: (_target, tag) => make(String(tag)) }),
  };
});

type WizardComponent = React.ComponentType<{
  onComplete: (...args: any[]) => void;
  onCancel: () => void;
}>;

const wizards: Array<[string, WizardComponent, boolean]> = [
  ['Parodontologie', AssistantParo, false],
  ['Endodontie', AssistantEndo, false],
  ['Chirurgie', AssistantChirurgie, false],
  ['Prothèse', AssistantProthese, false],
  ['Pédodontie', AssistantPedo, false],
  ['Orthodontie', AssistantOrtho, false],
  ['ATM', AssistantATM, false],
  ['Pathologie', AssistantPatho, false],
  ['Examen complet', AssistantExamenComplet, true],
];

const controlRegex = /Annuler|Retour|Triage/i;

function actionableButtons() {
  return screen
    .queryAllByRole('button')
    .filter(button => !controlRegex.test(button.textContent || ''));
}

function renderWizard(Component: WizardComponent) {
  const onComplete = vi.fn();
  const onCancel = vi.fn();
  render(<Component onComplete={onComplete} onCancel={onCancel} />);
  return { onComplete, onCancel };
}

function tick(ms = 350) {
  act(() => {
    vi.advanceTimersByTime(ms);
  });
}

beforeEach(() => {
  vi.useFakeTimers();
  vi.clearAllMocks();
});

afterEach(() => {
  cleanup();
  vi.runOnlyPendingTimers();
  vi.useRealTimers();
});

describe.each(wizards)('%s G4 wizard controls', (_name, Component, hasTriage) => {
  it('cancels explicitly without producing a clinical conclusion', () => {
    const { onCancel, onComplete } = renderWizard(Component);

    fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));

    expect(onCancel).toHaveBeenCalledTimes(1);
    expect(onComplete).not.toHaveBeenCalled();
  });

  it('supports backward navigation after progressing', () => {
    renderWizard(Component);

    if (hasTriage) {
      fireEvent.click(screen.getByRole('button', { name: /Urgence \/ Douleur aiguë/i }));
    }

    const first = actionableButtons()[0];
    if (!first) throw new Error('first wizard option missing');
    fireEvent.click(first);
    tick();

    const back = screen.queryByRole('button', { name: /Retour/i });
    if (!back) throw new Error('back control missing after progress');
    fireEvent.click(back);

    expect(actionableButtons().length).toBeGreaterThan(0);
  });

  it('completes through explicit option choices and returns only a structured proposal', () => {
    const { onComplete } = renderWizard(Component);

    if (hasTriage) {
      fireEvent.click(screen.getByRole('button', { name: /Urgence \/ Douleur aiguë/i }));
    }

    for (let step = 0; step < 10 && onComplete.mock.calls.length === 0; step += 1) {
      const buttons = actionableButtons();
      if (buttons.length === 0) {
        tick(1800);
        break;
      }
      fireEvent.click(buttons[buttons.length - 1]);
      tick();
    }

    if (onComplete.mock.calls.length === 0) tick(2000);

    expect(onComplete).toHaveBeenCalledTimes(1);
    const [summary, plan] = onComplete.mock.calls[0];
    expect(typeof summary).toBe('string');
    expect(summary.length).toBeGreaterThan(20);
    expect(Array.isArray(plan)).toBe(true);
  });
});

describe('Examen complet G4 triage controls', () => {
  it('lets the user return from a branch to triage without producing a conclusion', () => {
    const onComplete = vi.fn();
    render(<AssistantExamenComplet onComplete={onComplete} onCancel={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: /Urgence \/ Douleur aiguë/i }));
    expect(screen.getByText('Protocole Urgence')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: /Triage/i }));
    expect(screen.getByRole('button', { name: /Contrôle de routine \/ Bilan/i })).toBeTruthy();
    expect(onComplete).not.toHaveBeenCalled();
  });
});