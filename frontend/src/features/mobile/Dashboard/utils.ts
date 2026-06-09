export function greeting(): string {
  const h = new Date().getHours();
  if (h < 12) return 'Bonjour';
  if (h < 18) return 'Bon après-midi';
  return 'Bonsoir';
}

export function fmt(n: number) { return new Intl.NumberFormat('fr-FR').format(Math.round(n)); }

export function dayLabel(dateStr: string, idx: number, total: number): string {
  if (idx === total - 1) return 'Auj.';
  const d = new Date(dateStr);
  return ['D', 'L', 'M', 'M', 'J', 'V', 'S'][d.getDay()];
}
