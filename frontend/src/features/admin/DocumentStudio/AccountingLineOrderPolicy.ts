export type AccountingLineDirection = 'UP' | 'DOWN';

export interface AccountingLineLike {
  id: number;
  description?: string;
}

export function moveAccountingLine<T extends AccountingLineLike>(
  items: T[],
  itemId: number,
  direction: AccountingLineDirection,
): T[] {
  const index = items.findIndex(item => item.id === itemId);
  if (index < 0) return items;

  const targetIndex = direction === 'UP' ? index - 1 : index + 1;
  if (targetIndex < 0 || targetIndex >= items.length) return items;

  const next = [...items];
  [next[index], next[targetIndex]] = [next[targetIndex], next[index]];
  return next;
}
