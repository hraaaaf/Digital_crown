import { useCallback } from 'react';

interface FlowHandoffOptions {
  focusSelector?: string;
  block?: ScrollLogicalPosition;
}

const DEFAULT_FOCUS_SELECTOR = [
  '[data-flow-autofocus]',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  'button:not([disabled])',
  'a[href]',
].join(',');

export function useFlowHandoff() {
  return useCallback((target: HTMLElement | null, options: FlowHandoffOptions = {}) => {
    if (!target) return;

    const rect = target.getBoundingClientRect();
    const safeTop = 16;
    const safeBottom = window.innerHeight - 16;
    const sufficientlyVisible = rect.top >= safeTop && Math.min(rect.bottom, safeBottom) > safeTop + 80;

    if (!sufficientlyVisible) {
      target.scrollIntoView({ behavior: 'smooth', block: options.block ?? 'start', inline: 'nearest' });
    }

    window.setTimeout(() => {
      const focusTarget = target.querySelector<HTMLElement>(options.focusSelector ?? DEFAULT_FOCUS_SELECTOR);
      focusTarget?.focus({ preventScroll: true });
    }, 180);
  }, []);
}
