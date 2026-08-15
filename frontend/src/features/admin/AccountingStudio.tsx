import React, { useEffect, useMemo } from 'react';
import { AccountingStudio as AccountingStudioLegacy } from './AccountingStudioLegacy';
import { repairLocalActSuggestionPrices } from './DocumentStudio/AccountingActSuggestionPolicy';
import { useCatalogStore } from './Settings/hooks/useCatalogStore';
import { useAccountingStore } from './store/useAccountingStore';

type AccountingStudioProps = React.ComponentProps<typeof AccountingStudioLegacy>;

export const AccountingStudio: React.FC<AccountingStudioProps> = props => {
  const actSuggestions = useAccountingStore(state => state.actSuggestions);
  const setActSuggestions = useAccountingStore(state => state.setActSuggestions);
  const specialties = useCatalogStore(state => state.specialties);

  const repairedSuggestions = useMemo(
    () => repairLocalActSuggestionPrices(actSuggestions, specialties),
    [actSuggestions, specialties],
  );

  useEffect(() => {
    if (!repairedSuggestions.changed) return;
    setActSuggestions(repairedSuggestions.suggestions);
  }, [repairedSuggestions, setActSuggestions]);

  return <AccountingStudioLegacy {...props} />;
};
