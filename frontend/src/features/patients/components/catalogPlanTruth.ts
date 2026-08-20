export type CatalogActChoice = {
  id: number;
  name: string;
  code?: string | null;
  basePrice: number;
  specialtyName: string;
};

export type PlanCatalogSnapshot = {
  act_id: number;
  code?: string | null;
  name: string;
  price: number;
};

export type PlanStepPayload = {
  title: string;
  assistant: string;
  status: string;
  date_str: string;
  order_index: number;
  catalog_snapshot?: PlanCatalogSnapshot | null;
};

type CatalogSpecialty = {
  name?: string;
  acts?: Array<{
    id: number;
    name: string;
    code?: string | null;
    base_price?: number;
    is_active?: boolean;
  }>;
};

export const flattenActiveCatalogActs = (specialties: CatalogSpecialty[]): CatalogActChoice[] =>
  specialties.flatMap((specialty) =>
    (specialty.acts || [])
      .filter((act) => act.is_active !== false)
      .map((act) => ({
        id: act.id,
        name: act.name,
        code: act.code || null,
        basePrice: Number(act.base_price || 0),
        specialtyName: specialty.name || 'Catalogue cabinet',
      })),
  );

export const buildCatalogPlanStep = (
  act: CatalogActChoice,
  finalName: string,
  finalPrice: number,
  dateLabel: string,
  orderIndex: number,
): PlanStepPayload => {
  const safeName = finalName.trim();
  const safePrice = Number.isFinite(finalPrice) ? Math.max(0, finalPrice) : 0;
  const assistant = [
    'Catalogue cabinet',
    act.code?.trim() || null,
    `${safePrice.toLocaleString('fr-FR')} DH`,
    'Tarif capturé',
  ].filter(Boolean).join(' · ');

  return {
    title: safeName,
    assistant,
    status: 'pending',
    date_str: dateLabel,
    order_index: orderIndex,
    catalog_snapshot: {
      act_id: act.id,
      code: act.code?.trim() || null,
      name: safeName,
      price: safePrice,
    },
  };
};

export const normalizePersistedPlanStep = (step: any, orderIndex: number): PlanStepPayload => ({
  title: String(step?.title || ''),
  assistant: String(step?.assistant || 'general'),
  status: String(step?.status || 'pending'),
  date_str: String(step?.date_str || ''),
  order_index: orderIndex,
  catalog_snapshot: step?.catalog_snapshot || null,
});
