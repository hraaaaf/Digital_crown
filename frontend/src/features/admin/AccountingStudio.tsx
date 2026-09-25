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

  return <AccountingStudioLegacy {...props} />;
};