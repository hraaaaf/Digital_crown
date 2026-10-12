import { act, cleanup, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { DENY_POCKET_READ, parsePocketReadAccess } from '../pocketReadCapabilities';

const mocks = vi.hoisted(() => ({ fetch: vi.fn(), credentials: vi.fn(), decrypt: vi.fn() }));
vi.mock('../../../../services/zka/mobileApi', () => ({ mobileApiFetch: mocks.fetch }));
vi.mock('../../../../services/zka/MobileStorage', () => ({ MobileStorage: { getCredentials: mocks.credentials } }));
vi.mock('../../../../services/zka/CryptoService', () => ({ CryptoService: { decryptPayload: mocks.decrypt } }));
import { usePocketReadCapabilities } from './usePocketReadCapabilities';

const contract = (patients = true, finance = false) => ({
  version: 1, principal_kind: 'staff', capabilities: {
    'agenda.read': { allowed: true, scope: 'cabinet' },
    'cabinet.patients.read': { allowed: patients, scope: patients ? 'cabinet' : null },
    'cabinet.clinical.read': { allowed: patients, scope: patients ? 'cabinet' : null },
    'cabinet.finance.read': { allowed: finance, scope: finance ? 'cabinet' : null },
  },
});
const response = (payload: unknown, status = 200) => new Response(JSON.stringify(
  status !== 200 || (payload && typeof payload === 'object' && 'payload' in payload)
    ? payload : { payload: JSON.stringify(payload) },
), {
  status, headers: { 'Content-Type': 'application/json' },
});

beforeEach(() => {
  vi.resetAllMocks();
  mocks.credentials.mockResolvedValue({ masterKey: 'test-key' });
  mocks.decrypt.mockImplementation(async (serialized: string) => JSON.parse(serialized));
  mocks.fetch.mockResolvedValue(response(contract()));
});
afterEach(cleanup);

describe('Pocket server read permissions', () => {
  it('starts denied and decrypts staff permissions before enabling destinations', async () => {
    mocks.fetch.mockResolvedValue(response({ payload: 'ciphertext' }));
    mocks.decrypt.mockResolvedValue(contract(true, true));
    const { result } = renderHook(() => usePocketReadCapabilities());
    expect(result.current.access).toEqual(DENY_POCKET_READ);
    await waitFor(() => expect(result.current.status).toBe('ready'));
    expect(result.current.access.finance).toBe(true);
    expect(mocks.decrypt).toHaveBeenCalledWith('ciphertext', 'test-key');
    expect(mocks.fetch).toHaveBeenCalledWith('/capabilities', expect.objectContaining({ cache: 'no-store', signal: expect.any(AbortSignal) }));
  });

  it.each([401, 403, 500])('removes stale grants after HTTP %s', async status => {
    const { result } = renderHook(() => usePocketReadCapabilities());
    await waitFor(() => expect(result.current.access.patients).toBe(true));
    mocks.fetch.mockResolvedValue(response({ detail: 'Refus' }, status));
    await act(() => result.current.refresh());
    expect(result.current.status).toBe('unavailable');
    expect(result.current.access).toEqual(DENY_POCKET_READ);
  });

  it('rejects network failure without retaining previously granted permissions', async () => {
    const { result } = renderHook(() => usePocketReadCapabilities());
    await waitFor(() => expect(result.current.status).toBe('ready'));
    mocks.fetch.mockRejectedValue(new TypeError('Offline'));
    await act(() => result.current.refresh());
    expect(result.current.access).toEqual(DENY_POCKET_READ);
    expect(result.current.status).toBe('unavailable');
  });

  it('does not fetch or grant access when pairing credentials are missing', async () => {
    mocks.credentials.mockResolvedValue(null);
    const { result } = renderHook(() => usePocketReadCapabilities());
    await waitFor(() => expect(result.current.status).toBe('unavailable'));
    expect(mocks.fetch).not.toHaveBeenCalled();
    expect(result.current.access).toEqual(DENY_POCKET_READ);
  });

  it('fails closed if an encrypted policy cannot be decrypted', async () => {
    mocks.fetch.mockResolvedValue(response({ payload: 'ciphertext' }));
    mocks.decrypt.mockRejectedValue(new Error('Invalid ciphertext'));
    const { result } = renderHook(() => usePocketReadCapabilities());
    await waitFor(() => expect(result.current.status).toBe('unavailable'));
    expect(result.current.access).toEqual(DENY_POCKET_READ);
  });

  it('rejects an unexpected unencrypted staff response', async () => {
    mocks.fetch.mockResolvedValue(new Response(JSON.stringify(contract())));
    const { result } = renderHook(() => usePocketReadCapabilities());
    await waitFor(() => expect(result.current.status).toBe('unavailable'));
    expect(mocks.decrypt).not.toHaveBeenCalled();
    expect(result.current.access).toEqual(DENY_POCKET_READ);
  });

  it('reloads on a new snapshot and on returning to the foreground', async () => {
    const { result, rerender } = renderHook(({ key }) => usePocketReadCapabilities(key), { initialProps: { key: 'one' } });
    await waitFor(() => expect(result.current.status).toBe('ready'));
    mocks.fetch.mockResolvedValue(response(contract(false)));
    rerender({ key: 'two' });
    await waitFor(() => expect(result.current.status).toBe('ready'));
    expect(result.current.access.patients).toBe(false);
    mocks.fetch.mockResolvedValue(response(contract(true)));
    act(() => window.dispatchEvent(new Event('focus')));
    await waitFor(() => expect(result.current.access.patients).toBe(true));
  });

  it('ignores an older response that grants rights after a newer response denies them', async () => {
    let resolveOld!: (value: Response) => void;
    mocks.fetch.mockImplementationOnce(() => new Promise(resolve => { resolveOld = resolve; }));
    const { result } = renderHook(() => usePocketReadCapabilities());
    await waitFor(() => expect(mocks.fetch).toHaveBeenCalledTimes(1));
    mocks.fetch.mockResolvedValue(response(contract(false)));
    await act(() => result.current.refresh());
    expect(result.current.access.patients).toBe(false);
    await act(async () => { resolveOld(response(contract(true))); });
    expect(result.current.access.patients).toBe(false);
  });

  it.each([
    null,
    { ...contract(), version: 2 },
    { ...contract(), principal_kind: 'patient' },
    { ...contract(), capabilities: {} },
    { ...contract(), capabilities: { ...contract().capabilities, 'agenda.read': { allowed: 'true', scope: 'cabinet' } } },
    { ...contract(), capabilities: { ...contract().capabilities, 'agenda.read': { allowed: true, scope: 'patient_context' } } },
  ])('rejects malformed, wrong-population and mismatched-scope contracts', value => {
    expect(() => parsePocketReadAccess(value)).toThrow();
  });
});
