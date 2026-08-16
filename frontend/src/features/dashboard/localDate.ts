export const formatLocalDateKey = (date: Date = new Date()): string => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

export const getLocalDayBounds = (date: Date = new Date()) => {
  const key = formatLocalDateKey(date);
  return {
    start: `${key}T00:00:00`,
    end: `${key}T23:59:59`,
  };
};
