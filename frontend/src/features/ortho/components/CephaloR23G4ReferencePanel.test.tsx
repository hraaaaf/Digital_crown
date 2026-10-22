import React from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';

const st = vi.hoisted(() => ({
  current: {
    patientId: 7 as number | null, analysisId: 9 as number | undefined,
    imageSrc: 'synthetic-9.png' as string | undefined,
    anglesData: { scientific_read_path: { revision: 2 } } as any,
  },
}));
const request = vi.hoisted(() => vi.fn());
vi.mock('../stores/useOrthoStore', () => ({
  useOrthoStore: (selector: (x: typeof st.current) => any) => selector(st.current),
}));
vi.mock('../cephaloRepository', () => ({
  cephaloRepository: { getR23G4ReferenceProfiles: request },
}));
import CephaloR23G4ReferencePanel from './CephaloR23G4ReferencePanel';

const P = {
  bgPanel: '#ffffff', bgCard: '#f8fafc', border: '#ddd',
  text: '#111', textMuted: '#666', accent: '#235', accentSuccess: '#064',
  accentWarning: '#b40', shadowLg: 'none',
};
const serverPayload = (study = 9, revision = 2, withFocus = false) => {
  const id = 'COM_DC_LEGACY_V1';
  const rows = Array.from({ length: 10 }, (_, i) => ({
    order: i + 1, canonical_measurement_id: `M_COM_${i + 1}_MM_V1`,
    label: `Facteur ${i + 1}`, unit: 'mm',
    contract_state: i === 0 ? 'EXECUTABLE' : 'PENDING_EQUIVALENCE',
    source_contract: id, classification_authority: false,
    availability_status: i === 0 && withFocus ? 'AVAILABLE' : 'NOT_COMPUTABLE',
    value: i === 0 && withFocus ? 3.4 : null,
    measurement_refs: i === 0 && withFocus ? ['m:one'] : [],
    value_authority_method_id: i === 0 && withFocus ? 'M:EXACT' : null,
    ...(i === 0 && withFocus ? { focus_evidence: {
      authority: 'ACTIVE_RUNTIME_MEASUREMENT_EVIDENCE_V1',
      canonical_measurement_id: 'M_COM_1_MM_V1', measurement_ref: 'm:one',
      value_authority_method_id: 'M:EXACT', landmark_ids: ['A','B'],
      construction_ids: [], calibration_required: false,
    } } : {}),
  }));
  return { analysis_id: study, revision, authority: 'EVIDENCE_GRAPH_V1',
    active_chain: 'VERIFIED', clinical_release: false, reference_display_only: true,
    profiles: { com: {
      protocol_profile_id: id, profile_status: 'WORKING_V1__DISPLAY_ONLY__NO_CLINICAL_APPROVAL',
      source_lock_gate: 'HISTORICAL_WORKING_REFERENCE_ONLY', classification_authority: false, rows,
    } },
  };
};
afterEach(() => { cleanup(); vi.clearAllMocks(); });
beforeEach(() => {
  st.current = {
    patientId: 7, analysisId: 9, imageSrc: 'synthetic-9.png',
    anglesData: { scientific_read_path: { revision: 2 } },
  };
});
describe('R23-G4 COM compact UI, read-only Focus', () => {
  it('identifies only the isolated T2 plate as synthetic and keeps last rows scrollable', async () => {
    st.current.imageSrc = 'http://127.0.0.1:8005/api/static/uploads/radios/t2-cephalo-seeded.png';
    request.mockResolvedValue(serverPayload());
    render(<CephaloR23G4ReferencePanel P={P} analysis="com" />);
    await screen.findByRole('table');
    expect(screen.getByText(/Image synthétique de certification T2/)).toBeTruthy();
    expect(document.querySelector('[data-r23g4-reference-panel="com"] .overflow-auto')?.classList.contains('pb-36')).toBe(true);
    expect(screen.getAllByText('NC')).toHaveLength(10);
  });

  it('does not present any real or generic radiograph as the T2 QA plate', async () => {
    request.mockResolvedValue(serverPayload());
    render(<CephaloR23G4ReferencePanel P={P} analysis="com" />);
    await screen.findByRole('table');
    expect(document.querySelector('[data-r23g4-qa-image]')).toBeNull();
  });
  it('renders ten NC factors from the exact authenticated reference payload', async () => {
    request.mockResolvedValue(serverPayload());
    render(<CephaloR23G4ReferencePanel P={P} analysis="com" />);
    const table = await screen.findByRole('table');
    expect(table.getAttribute('data-r23g4-row-count')).toBe('10');
    expect(screen.getByText('0/10 valeurs prouvées · 10 facteurs documentés')).toBeTruthy();
    expect(screen.getAllByText('NC')).toHaveLength(10);
    expect(screen.getByText(/non certifiée cliniquement/)).toBeTruthy();
    expect(request).toHaveBeenCalledWith(9, 2, expect.anything());
  });

  it('never creates Focus for an NC row and clears it on another study', async () => {
    request.mockResolvedValue(serverPayload());
    const received: unknown[] = [];
    const handler = (event: Event) => received.push((event as CustomEvent).detail);
    window.addEventListener('digital-crown:cephalo-metric', handler);
    const rendered = render(<CephaloR23G4ReferencePanel P={P} analysis="com" />);
    await screen.findByRole('table');
    fireEvent.click(screen.getByRole('button', { name: /^Facteur 1$/ }));
    expect(screen.getByText(/Focus non autorisé/)).toBeTruthy();
    expect(received.every(x => x === null)).toBe(true);
    st.current = { patientId: 7, analysisId: 10, imageSrc: 'synthetic-10.png',
      anglesData: { scientific_read_path: { revision: 1 } } };
    request.mockImplementation(async () => serverPayload(10, 1));
    rendered.rerender(<CephaloR23G4ReferencePanel P={P} analysis="com" />);
    await waitFor(() => expect(request).toHaveBeenCalledWith(10, 1, expect.anything()));
    expect(screen.queryByText(/Focus prouvé/)).toBeNull();
    window.removeEventListener('digital-crown:cephalo-metric', handler);
  });

  it('emits exact Focus evidence with no synthetic geometry and revokes on unmount', async () => {
    request.mockResolvedValue(serverPayload(9, 2, true));
    const received: any[] = [];
    const handler = (event: Event) => received.push((event as CustomEvent).detail);
    window.addEventListener('digital-crown:cephalo-metric', handler);
    const rendered = render(<CephaloR23G4ReferencePanel P={P} analysis="com" />);
    await screen.findByRole('table');
    fireEvent.click(screen.getByRole('button', { name: /^Facteur 1$/ }));
    await waitFor(() => expect(received.some(x => x?.authority === 'ACTIVE_RUNTIME_MEASUREMENT_EVIDENCE_V1')).toBe(true));
    const focus = received.find(x => x?.authority === 'ACTIVE_RUNTIME_MEASUREMENT_EVIDENCE_V1');
    expect(focus.points).toEqual(['A', 'B']);
    expect(focus.lines).toEqual([]);
    act(() => rendered.unmount());
    expect(received.at(-1)).toBeNull();
    window.removeEventListener('digital-crown:cephalo-metric', handler);
  });

  it('revokes Focus immediately after a local unsaved landmark change and does not refetch stale values', async () => {
    request.mockResolvedValue(serverPayload(9, 2, true));
    const received: any[] = [];
    const handler = (event: Event) => received.push((event as CustomEvent).detail);
    window.addEventListener('digital-crown:cephalo-metric', handler);
    const rendered = render(<CephaloR23G4ReferencePanel P={P} analysis="com" />);
    await screen.findByRole('table');
    fireEvent.click(screen.getByRole('button', { name: /^Facteur 1$/ }));
    await waitFor(() => expect(received.some(x => x?.authority === 'ACTIVE_RUNTIME_MEASUREMENT_EVIDENCE_V1')).toBe(true));
    const calls = request.mock.calls.length;
    (st.current as any).local = { version: 8 };
    (st.current as any).syncState = 'syncing';
    rendered.rerender(<CephaloR23G4ReferencePanel P={P} analysis="com" />);
    expect(screen.queryByRole('table')).toBeNull();
    expect(received.at(-1)).toBeNull();
    (st.current as any).syncState = 'idle';
    rendered.rerender(<CephaloR23G4ReferencePanel P={P} analysis="com" />);
    expect(screen.queryByRole('table')).toBeNull();
    expect(request.mock.calls.length).toBe(calls);
    window.removeEventListener('digital-crown:cephalo-metric', handler);
  });

  it('refuses a stale response from the wrong study even when all names coincide', async () => {
    request.mockResolvedValue(serverPayload(8, 2, true));
    render(<CephaloR23G4ReferencePanel P={P} analysis="com" />);
    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(screen.queryByRole('table')).toBeNull();
    expect(screen.getByRole('status')).toBeTruthy();
  });
});
