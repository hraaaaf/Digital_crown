import React, { useEffect, useMemo } from 'react';
import { AccountingStudio as AccountingStudioLegacy } from './AccountingStudioLegacy';
import { repairLocalActSuggestionPrices } from './DocumentStudio/AccountingActSuggestionPolicy';
import { normalizeStructuredAccountingItems } from './DocumentStudio/AccountingOdontogramSourcePolicy';
import { useCatalogStore } from './Settings/hooks/useCatalogStore';
import { useAccountingStore } from './store/useAccountingStore';

type AccountingStudioProps = React.ComponentProps<typeof AccountingStudioLegacy>;

export const AccountingStudio: React.FC<AccountingStudioProps> = props => {
  const items = useAccountingStore(state => state.items);
  const setItems = useAccountingStore(state => state.setItems);
  const actSuggestions = useAccountingStore(state => state.actSuggestions);
  const setActSuggestions = useAccountingStore(state => state.setActSuggestions);
  const paymentStatusGuardMessage = useAccountingStore(state => state.paymentStatusGuardMessage);
  const clearPaymentStatusGuard = useAccountingStore(state => state.clearPaymentStatusGuard);
  const specialties = useCatalogStore(state => state.specialties);

  const repairedSuggestions = useMemo(
    () => repairLocalActSuggestionPrices(actSuggestions, specialties),
    [actSuggestions, specialties],
  );

  const canonicalItems = useMemo(
    () => props.isDevis ? normalizeStructuredAccountingItems(items) : items,
    [items, props.isDevis],
  );

  useEffect(() => {
    if (!repairedSuggestions.changed) return;
    setActSuggestions(repairedSuggestions.suggestions);
  }, [repairedSuggestions, setActSuggestions]);

  useEffect(() => {
    if (!props.isDevis) return;
    const changed = canonicalItems.some((item, index) => item !== items[index]);
    if (changed) setItems(canonicalItems);
  }, [canonicalItems, items, props.isDevis, setItems]);

  return (
    <div className="space-y-3">
      {!props.isDevis && paymentStatusGuardMessage && (
        <div
          role="alert"
          className="mx-auto flex max-w-5xl items-start justify-between gap-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-900"
        >
          <div>
            <div className="text-xs font-black uppercase tracking-wider">Paiement partiel</div>
            <div className="mt-1 text-xs font-semibold">{paymentStatusGuardMessage}</div>
          </div>
          <button
            type="button"
            onClick={clearPaymentStatusGuard}
            className="shrink-0 rounded-xl border border-amber-300 bg-white px-3 py-2 text-[10px] font-black uppercase tracking-wider"
          >
            Compris
          </button>
        </div>
      )}
      <AccountingStudioLegacy {...props} />
    </div>
  );
};