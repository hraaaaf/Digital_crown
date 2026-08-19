import { describe, expect, it } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import { isTimeWithinSchedule, type DaySchedule } from '../features/agenda/agendaSchedule';

const splitDay: DaySchedule = {
  is_open: true,
  is_continuous: false,
  morning_start: '09:00',
  morning_end: '13:00',
  afternoon_start: '14:00',
  afternoon_end: '18:00',
};

describe('R7 authoritative booking windows', () => {
  it('rejects the midday pause and closing boundary', () => {
    expect(isTimeWithinSchedule('09:00', splitDay)).toBe(true);
    expect(isTimeWithinSchedule('12:45', splitDay)).toBe(true);
    expect(isTimeWithinSchedule('13:00', splitDay)).toBe(false);
    expect(isTimeWithinSchedule('13:30', splitDay)).toBe(false);
    expect(isTimeWithinSchedule('14:00', splitDay)).toBe(true);
    expect(isTimeWithinSchedule('18:00', splitDay)).toBe(false);
  });

  it('uses one contiguous interval for a continuous day', () => {
    const continuous = { ...splitDay, is_continuous: true, morning_end: '17:00' };
    expect(isTimeWithinSchedule('13:30', continuous)).toBe(true);
    expect(isTimeWithinSchedule('17:00', continuous)).toBe(false);
  });

  it('wires the guard into both exact-time agenda views', () => {
    const daily = fs.readFileSync(path.join(process.cwd(), 'src/features/agenda/DailyView.tsx'), 'utf8');
    const weekly = fs.readFileSync(path.join(process.cwd(), 'src/features/agenda/WeeklyView.tsx'), 'utf8');
    expect(daily).toContain('isTimeWithinSchedule(timeString, daySchedule)');
    expect(weekly).toContain('isTimeWithinSchedule(timeString, getDaySchedule(date, agendaSettings))');
  });
});
