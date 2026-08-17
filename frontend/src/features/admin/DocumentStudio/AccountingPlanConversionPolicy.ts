import type { PriceItem } from '../store/useAccountingStore';

export interface PlanActForQuote {
  id?: string | number;
  act?: string;
  suggested_act?: string;
  fdi?: string | number;
  toothNumber?: string | number;
  phase?: string;
}

/**
 * Convert a treatment-plan proposal into neutral Devis rows.
 * A plan may suggest WHAT to do, but it must not invent a financial amount.
 * Pricing is resolved later by the authoritative catalog / practitioner input.
 */
export function convertPlanActsToQuoteItems(acts: PlanActForQuote[]): PriceItem[] {
  return acts
    .map((act, index) => {
      const description = String(act.suggested_act ?? act.act ?? '').trim();
      const rawTooth = act.fdi ?? act.toothNumber;
      const tooth = rawTooth === undefined || rawTooth === null ? '' : String(rawTooth).trim();
      const toothNumber = /^\d+$/.test(tooth) ? Number(tooth) : null;

      return {
        id: Date.now() + index,
        description,
        dent: toothNumber ? String(toothNumber) : '0',
        price: 0,
        toothNumbers: toothNumber ? [toothNumber] : [],
        category: act.phase,
      } satisfies PriceItem;
    })
    .filter(item => item.description.length > 0);
}
