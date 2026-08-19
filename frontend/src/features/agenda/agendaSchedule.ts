export type WeekdayKey = 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday';

export type DaySchedule = {
  is_open: boolean;
  is_continuous: boolean;
  morning_start: string;
  morning_end: string;
  afternoon_start: string;
  afternoon_end: string;
};

export type WeeklySchedule = Record<WeekdayKey, DaySchedule>;

export type AgendaSettingsLike = {
  opening_time_morning?: string;
  closing_time_morning?: string;
  opening_time_afternoon?: string;
  closing_time_afternoon?: string;
  is_continuous?: boolean;
  weekly_schedule?: Partial<WeeklySchedule> | null;
};

const WEEKDAY_KEYS: WeekdayKey[] = [
  'sunday',
  'monday',
  'tuesday',
  'wednesday',
  'thursday',
  'friday',
  'saturday',
];

const validTime = (value: unknown, fallback: string): string =>
  typeof value === 'string' && /^\d{2}:\d{2}$/.test(value) ? value : fallback;

export const timeToMinutes = (value: string): number => {
  const [hours, minutes] = value.split(':').map(Number);
  return hours * 60 + minutes;
};

export const buildLegacyDay = (settings?: AgendaSettingsLike | null): DaySchedule => ({
  is_open: true,
  is_continuous: settings?.is_continuous ?? false,
  morning_start: validTime(settings?.opening_time_morning, '09:00'),
  morning_end: validTime(settings?.closing_time_morning, '13:00'),
  afternoon_start: validTime(settings?.opening_time_afternoon, '14:00'),
  afternoon_end: validTime(settings?.closing_time_afternoon, '18:00'),
});

export const getDaySchedule = (date: Date, settings?: AgendaSettingsLike | null): DaySchedule => {
  const legacy = buildLegacyDay(settings);
  const key = WEEKDAY_KEYS[date.getDay()];
  const configured = settings?.weekly_schedule?.[key];
  return configured ? { ...legacy, ...configured } : legacy;
};

export const getDayBounds = (schedule: DaySchedule): { startHour: number; endHour: number } => {
  const startMinutes = timeToMinutes(schedule.morning_start);
  const endMinutes = timeToMinutes(schedule.is_continuous ? schedule.morning_end : schedule.afternoon_end);
  return {
    startHour: Math.floor(startMinutes / 60),
    endHour: Math.max(Math.floor(startMinutes / 60) + 1, Math.ceil(endMinutes / 60)),
  };
};

export const getWeekBounds = (days: Date[], settings?: AgendaSettingsLike | null): { startHour: number; endHour: number } => {
  const openSchedules = days
    .map((date) => getDaySchedule(date, settings))
    .filter((schedule) => schedule.is_open);

  if (openSchedules.length === 0) {
    const fallback = getDayBounds(buildLegacyDay(settings));
    return fallback;
  }

  const starts = openSchedules.map((schedule) => timeToMinutes(schedule.morning_start));
  const ends = openSchedules.map((schedule) =>
    timeToMinutes(schedule.is_continuous ? schedule.morning_end : schedule.afternoon_end),
  );

  return {
    startHour: Math.floor(Math.min(...starts) / 60),
    endHour: Math.ceil(Math.max(...ends) / 60),
  };
};

export const formatScheduleSummary = (schedule: DaySchedule): string => {
  if (!schedule.is_open) return 'Fermé';
  if (schedule.is_continuous) return `${schedule.morning_start}–${schedule.morning_end}`;
  return `${schedule.morning_start}–${schedule.morning_end} · ${schedule.afternoon_start}–${schedule.afternoon_end}`;
};
