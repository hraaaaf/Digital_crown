import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { OfflineQueueViewer } from './OfflineQueueViewer';

const state = vi.hoisted(() => ({
  queue: [] as Array<{ id:string; url:string; method:string; timestamp:number }>,
  isOffline: false,
}));

vi.mock('../../hooks/useOfflineQueue', () => ({
  useOfflineQueue: () => state,
}));

beforeEach(() => {
  state.queue = [];
  state.isOffline = false;
});
afterEach(() => cleanup());

describe('OfflineQueueViewer G8 transverse matrix', () => {
  it('stays absent when online with nothing queued', () => {
    render(<OfflineQueueViewer />);
    expect(screen.queryByText('Mode Hors-ligne')).toBeNull();
    expect(screen.queryByText('Synchronisation...')).toBeNull();
  });

  it('shows truthful offline state and queued mutation details', () => {
    state.isOffline = true;
    state.queue = [
      { id:'a1', url:'https://local.test/api/patients/7', method:'PATCH', timestamp:Date.UTC(2026,8,19,10,15) },
      { id:'a2', url:'https://local.test/api/appointments/9', method:'DELETE', timestamp:Date.UTC(2026,8,19,10,16) },
    ];
    render(<OfflineQueueViewer />);

    expect(screen.getByText('Mode Hors-ligne')).toBeTruthy();
    expect(screen.getByText('2 actions')).toBeTruthy();
    expect(screen.getByText('PATCH')).toBeTruthy();
    expect(screen.getByText('DELETE')).toBeTruthy();
    expect(screen.getByText('7')).toBeTruthy();
    expect(screen.getByText('9')).toBeTruthy();
  });

  it('distinguishes online synchronization of pending queue from offline mode', () => {
    state.isOffline = false;
    state.queue = [{ id:'a1', url:'https://local.test/api/patients/7', method:'POST', timestamp:Date.now() }];
    render(<OfflineQueueViewer />);

    expect(screen.getByText('Synchronisation...')).toBeTruthy();
    expect(screen.queryByText('Mode Hors-ligne')).toBeNull();
    expect(screen.getByText('1 action')).toBeTruthy();
  });

  it('shows offline with zero queued actions without claiming pending mutations', () => {
    state.isOffline = true;
    state.queue = [];
    render(<OfflineQueueViewer />);

    expect(screen.getByText('Mode Hors-ligne')).toBeTruthy();
    expect(screen.getByText('0 action')).toBeTruthy();
    expect(screen.getByText('Toutes les actions sont synchronisées.')).toBeTruthy();
  });
});
