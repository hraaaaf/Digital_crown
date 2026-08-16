import { isAccountingPhaseSeparator } from './AccountingPhasePolicy';

export interface AccountingTotalItem {
  description: string;
  price: number | string;
}

export function accountingDocumentTotal(items: AccountingTotalItem[]): number {
  return items.reduce((total, item) => {
    if (isAccountingPhaseSeparator(item.description)) return total;
    const price = Number(item.price);
    return total + (Number.isFinite(price) ? price : 0);
  }, 0);
}
