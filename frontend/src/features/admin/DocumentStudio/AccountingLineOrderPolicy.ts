export type AccountingLineDirection = 'UP' | 'DOWN';

export interface AccountingLineLike {
  id: number;
  description?: string;
}

function isPhaseSeparator(description?: string): boolean {
  return /^---\s+.+\s+---$/.test((description || '').trim());
}

/**
 * Reorder ordinary Devis rows without corrupting phase presentation blocks.
 * Once visual phase separators exist, their relative structure is locked and
 * manual line reordering must be performed before applying phase sequencing.
 */
export function moveAccountingLine<T extends AccountingLineLike>(
  items: T[],
  itemId: number,
  direction: AccountingLineDirection,
): T[] {
  if (items.some(item => isPhaseSeparator(item.description))) return items;

  const index = items.findIndex(item => item.id === itemId);
  if (index < 0) return items;

  const targetIndex = direction === 'UP' ? index - 1 : index + 1;
  if (targetIndex < 0 || targetIndex >= items.length) return items;

  const next = [...items];
  [next[index], next[targetIndex]] = [next[targetIndex], next[index]];
  return next;
}
