export interface HonorairesInstallmentLike {
  id: number;
  date: string;
  amount: number;
  label: string;
}

/**
 * Starting a new Global/Planned Honoraires note must never silently reuse the
 * latest patient installment plan that DocumentHub may have loaded for P5.
 *
 * We clear only on the explicit Unique -> Global transition. Existing draft
 * installments remain stable while the document stays global.
 */
export function installmentsAfterGlobalNoteToggle<T extends HonorairesInstallmentLike>(
  currentIsGlobal: boolean,
  nextIsGlobal: boolean,
  installments: T[],
): T[] {
  if (!currentIsGlobal && nextIsGlobal) return [];
  return installments;
}
