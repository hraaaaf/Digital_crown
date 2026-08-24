import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { buildTimelineSlots } from '../features/mobile/Dashboard/views/AgendaView';

const modalSource = readFileSync(
  resolve(process.cwd(), 'src/features/mobile/Dashboard/components/AddApptModal.tsx'),
  'utf8',
);
const agendaSource = readFileSync(
  resolve(process.cwd(), 'src/features/mobile/Dashboard/views/AgendaView.tsx'),
  'utf8',
);

describe('Mobile M6.3 canonical patient and agenda contract', () => {
  it('uses canonical patient and appointment creation routes with patient identity fields', () => {
    expect(modalSource).toContain('/api/patients/');
    expect(modalSource).toContain('/api/appointments/');
    expect(modalSource).not.toContain('/api/mobile/patients');
    expect(modalSource).not.toContain('/api/mobile/appointments');
    expect(modalSource).toContain('patient_id');
    expect(modalSource).toContain('date_naissance');
    expect(modalSource).toContain("sexe: '' as '' | 'F' | 'M'");
    expect(modalSource).toContain('existing_patient?.id');
  });

  it('keeps critical modal controls at least 44px high', () => {
    expect(modalSource).toContain('min-h-11');
    expect(modalSource).toContain('min-h-12');
    expect(modalSource).toContain('min-h-[52px]');
    expect(modalSource).toContain('items-end sm:items-center');
  });

  it('renders quarter-hour and out-of-standard-range appointments in day timeline', () => {
    const slots = buildTimelineSlots([
      { time: '08:45' },
      { time: '09:15:00' },
      { time: '19:10' },
    ]);
    expect(slots).toContain('08:45');
    expect(slots).toContain('09:15');
    expect(slots).toContain('19:10');
    expect(slots).toContain('09:00');
    expect(slots.indexOf('08:45')).toBeLessThan(slots.indexOf('09:00'));
    expect(slots.indexOf('19:10')).toBeGreaterThan(slots.indexOf('18:30'));
  });

  it('reschedules through canonical PUT and not the legacy PATCH route', () => {
    expect(agendaSource).toContain('/api/appointments/${id}');
    expect(agendaSource).toContain("method: 'PUT'");
    expect(agendaSource).not.toContain('/api/mobile/appointments/${id}');
    expect(agendaSource).toContain('res.status === 409');
  });
});
