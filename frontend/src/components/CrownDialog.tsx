import { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { cn } from '../utils/cn';

interface CrownDialogProps {
  open: boolean;
  onClose: () => void;
  ariaLabel: string;
  children: React.ReactNode;
  className?: string;
}

const FOCUSABLE = [
  'button:not([disabled])',
  'a[href]',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',');

export function CrownDialog({ open, onClose, ariaLabel, children, className }: CrownDialogProps) {
  const surfaceRef = useRef<HTMLDivElement>(null);
  const openerRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!open) return;

    openerRef.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const previousBodyOverflow = document.body.style.overflow;
    const previousHtmlOverflow = document.documentElement.style.overflow;
    document.body.style.overflow = 'hidden';
    document.documentElement.style.overflow = 'hidden';

    const surface = surfaceRef.current;
    const focusables = () => Array.from(surface?.querySelectorAll<HTMLElement>(FOCUSABLE) ?? []);
    requestAnimationFrame(() => {
      const preferred = surface?.querySelector<HTMLElement>('[data-dialog-autofocus]');
      (preferred ?? focusables()[0] ?? surface)?.focus({ preventScroll: true });
    });

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key !== 'Tab') return;
      const items = focusables();
      if (!items.length) {
        event.preventDefault();
        surface?.focus();
        return;
      }
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('keydown', onKeyDown);
      document.body.style.overflow = previousBodyOverflow;
      document.documentElement.style.overflow = previousHtmlOverflow;
      openerRef.current?.focus({ preventScroll: true });
    };
  }, [open, onClose]);

  if (!open || typeof document === 'undefined') return null;

  return createPortal(
    <div
      role="dialog"
      aria-modal="true"
      aria-label={ariaLabel}
      className="fixed inset-0 z-[12000] flex h-[100dvh] w-screen items-center justify-center overflow-y-auto bg-black/60 p-4 backdrop-blur-md sm:p-6"
    >
      <div
        ref={surfaceRef}
        tabIndex={-1}
        className={cn('max-h-[calc(100dvh-2rem)] w-full overflow-y-auto overscroll-contain sm:max-h-[calc(100dvh-3rem)]', className)}
      >
        {children}
      </div>
    </div>,
    document.body,
  );
}
