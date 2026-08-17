export type AccountingLearningEvent =
  | 'SELECT'
  | 'EDIT'
  | 'PREVIEW'
  | 'GENERATE'
  | 'ARCHIVE_SUCCESS';

export function shouldLearnAccountingAct(event: AccountingLearningEvent): boolean {
  return event === 'ARCHIVE_SUCCESS';
}

export function filterLearnableAccountingRows<T extends { description?: string; price?: number }>(rows: T[]): T[] {
  return rows.filter(row => {
    const description = (row.description || '').trim();
    const price = Number(row.price);
    return description.length > 0 && Number.isFinite(price) && price >= 0 && !description.startsWith('--- ');
  });
}
