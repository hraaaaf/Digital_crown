import type { PriceItem } from '../store/useAccountingStore';

export interface PlanActForQuote {
  id?: string | number;
  act?: string;
  suggested_act?: string;
  fdi?: string | number;
  toothNumber?: string | number;
  phase?: string;
}

const NON_FINANCIAL_PLAN_PATTERNS = [
  /\bprescription\b/i,
  /\bordonnance\b/i,
  /antibiot/i,
  /antalg/i,
  /anti[-\s]?inflamm/i,
  /corticost/i,
  /\bm[ée]dicament/i,
  /\bposologie\b/i,
  /\bsurveillance\b/i,
  /\benseignement\b/i,
];

/**
 * A P7 treatment-plan proposal may contain clinical guidance in addition to
 * billable procedures. Clinical medication/follow-up instructions must never
 * become financial Devis rows automatically.
 */
export function isPlanProposalQuoteEligible(act: PlanActForQuote): boolean {
  const description = String(act.suggested_act ?? act.act ?? '').trim();
  if (!description) return false;
  return !NON_FINANCIAL_PLAN_PATTERNS.some(pattern => pattern.test(description));
}

/**
 * Convert eligible treatment-plan proposals into neutral Devis rows.
 * A plan may suggest WHAT to do, but it must not invent a financial amount.
 * Pricing is resolved later by the authoritative catalog / practitioner input.
 */
export function convertPlanActsToQuoteItems(acts: PlanActForQuote[]): PriceItem[] {
  return acts
    .filter(isPlanProposalQuoteEligible)
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
    });
}
