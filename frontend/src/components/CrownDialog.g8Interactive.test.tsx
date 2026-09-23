import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { CrownDialog } from './CrownDialog';

beforeEach(() => {
  vi.stubGlobal('requestAnimationFrame', (cb: FrameRequestCallback) => { cb(0); return 1; });
  document.body.style.overflow = '';
  document.documentElement.style.overflow = '';
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('CrownDialog G8 transverse interaction matrix', () => {
  it('locks page scroll, focuses preferred control and restores both on close', () => {
    const opener = document.createElement('button');
    opener.textContent='Opener';
    document.body.appendChild(opener);
    opener.focus();

    const onClose=vi.fn();
    const view=render(
      <CrownDialog open onClose={onClose} ariaLabel="Test dialog">
        <button>First</button>
        <button data-dialog-autofocus>Preferred</button>
      </CrownDialog>,
    );

    expect(screen.getByRole('dialog',{name:'Test dialog'})).toBeTruthy();
    expect(document.body.style.overflow).toBe('hidden');
    expect(document.documentElement.style.overflow).toBe('hidden');
    expect(document.activeElement).toBe(screen.getByRole('button',{name:'Preferred'}));

    view.rerender(
      <CrownDialog open={false} onClose={onClose} ariaLabel="Test dialog">
        <button>First</button>
      </CrownDialog>,
    );
    expect(document.body.style.overflow).toBe('');
    expect(document.documentElement.style.overflow).toBe('');
    expect(document.activeElement).toBe(opener);
    opener.remove();
  });

  it('preserves the original opener when the close callback identity changes while open', () => {
    const opener = document.createElement('button');
    opener.textContent='Stable opener';
    document.body.appendChild(opener);
    opener.focus();

    const firstClose=vi.fn();
    const secondClose=vi.fn();
    const view=render(
      <CrownDialog open onClose={firstClose} ariaLabel="Stable dialog">
        <button data-dialog-autofocus>Inside</button>
      </CrownDialog>,
    );

    expect(document.activeElement).toBe(screen.getByRole('button',{name:'Inside'}));

    view.rerender(
      <CrownDialog open onClose={secondClose} ariaLabel="Stable dialog">
        <button data-dialog-autofocus>Inside</button>
      </CrownDialog>,
    );

    view.rerender(
      <CrownDialog open={false} onClose={secondClose} ariaLabel="Stable dialog">
        <button>Inside</button>
      </CrownDialog>,
    );

    expect(document.activeElement).toBe(opener);
    opener.remove();
  });

  it('closes on Escape through the single explicit close callback', () => {
    const onClose=vi.fn();
    render(<CrownDialog open onClose={onClose} ariaLabel="Test dialog"><button>Inside</button></CrownDialog>);
    fireEvent.keyDown(document,{key:'Escape'});
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('cycles focus from last to first with Tab and first to last with Shift+Tab', () => {
    render(
      <CrownDialog open onClose={vi.fn()} ariaLabel="Test dialog">
        <button>First</button>
        <button>Last</button>
      </CrownDialog>,
    );
    const first=screen.getByRole('button',{name:'First'});
    const last=screen.getByRole('button',{name:'Last'});

    last.focus();
    fireEvent.keyDown(document,{key:'Tab'});
    expect(document.activeElement).toBe(first);

    first.focus();
    fireEvent.keyDown(document,{key:'Tab',shiftKey:true});
    expect(document.activeElement).toBe(last);
  });

  it('does not render or lock scroll when closed', () => {
    render(<CrownDialog open={false} onClose={vi.fn()} ariaLabel="Test dialog"><button>Inside</button></CrownDialog>);
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(document.body.style.overflow).toBe('');
  });
});
