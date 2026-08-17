import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAccountingStore } from '../store/useAccountingStore';
import { isPrescriptionDirty, setPrescriptionDirty } from './PrescriptionDirtyState';
import { isCertificateDirty, setCertificateDirty } from './CertificateDirtyState';
import { isInstallmentDirty, setInstallmentDirty } from './InstallmentDirtyState';
import { isLibreDirty, setLibreDirty } from './LibreDirtyState';
import { isP7Dirty, setP7Dirty } from './P7DirtyState';
import { shouldGuardDocumentTabTransition } from './DocumentTabNavigationPolicy';
import {
  isCertifiableDocumentStudioTab,
  type CertifiableDocumentStudioTab,
} from './DocumentStudioVocabulary';

type TabChangeSource = 'ui' | 'url';

type UseDocumentHubNavigationParams = {
  hasAccountingDraft: boolean;
  resetHonorairesFinancialDraft: () => void;
};

export function useDocumentHubNavigation({
  hasAccountingDraft,
  resetHonorairesFinancialDraft,
}: UseDocumentHubNavigationParams) {
  const [searchParams, setSearchParams] = useSearchParams();
  const requestedDocumentTab = searchParams.get('documentTab');
  const [activeTab, setActiveTab] = useState<CertifiableDocumentStudioTab>(() =>
    isCertifiableDocumentStudioTab(requestedDocumentTab) ? requestedDocumentTab : 'ordonnance'
  );
  const [pendingTab, setPendingTab] = useState<CertifiableDocumentStudioTab | null>(null);
  const [pendingTabSource, setPendingTabSource] = useState<TabChangeSource>('ui');

  const dirtySnapshot = () => ({
    prescription: isPrescriptionDirty(),
    certificate: isCertificateDirty(),
    accounting: hasAccountingDraft,
    installment: isInstallmentDirty(),
    libre: isLibreDirty(),
    plan: isP7Dirty(),
  });

  const clearDirtyForTab = (tab: CertifiableDocumentStudioTab) => {
    switch (tab) {
      case 'ordonnance':
        setPrescriptionDirty(false);
        break;
      case 'certificat':
        setCertificateDirty(false);
        break;
      case 'devis':
      case 'honoraires':
        useAccountingStore.getState().reset();
        break;
      case 'echeancier':
        setInstallmentDirty(false);
        break;
      case 'libre':
        setLibreDirty(false);
        break;
      case 'plan':
        setP7Dirty(false);
        break;
      default:
        break;
    }
  };

  const syncDocumentTab = (tab: CertifiableDocumentStudioTab) => {
    if (searchParams.get('documentTab') === tab) return;
    const nextParams = new URLSearchParams(searchParams);
    nextParams.set('documentTab', tab);
    setSearchParams(nextParams, { replace: true });
  };

  const commitTabChange = (newTab: CertifiableDocumentStudioTab, source: TabChangeSource) => {
    setActiveTab(newTab);
    if (source === 'ui') syncDocumentTab(newTab);
  };

  const handleTabChange = (
    newTab: CertifiableDocumentStudioTab,
    source: TabChangeSource = 'ui'
  ) => {
    if (newTab === activeTab) return;

    if (activeTab === 'devis' && newTab === 'honoraires') {
      resetHonorairesFinancialDraft();
      commitTabChange(newTab, source);
      return;
    }

    if (shouldGuardDocumentTabTransition(activeTab, newTab, dirtySnapshot())) {
      setPendingTab(newTab);
      setPendingTabSource(source);
      return;
    }

    commitTabChange(newTab, source);
  };

  useEffect(() => {
    const nextTab = searchParams.get('documentTab');
    if (isCertifiableDocumentStudioTab(nextTab) && nextTab !== activeTab) {
      handleTabChange(nextTab, 'url');
    }
  // Deliberately reacts only to URL/search changes; current dirty state is read at transition time.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const cancelPendingTab = () => {
    if (pendingTabSource === 'url') {
      const nextParams = new URLSearchParams(searchParams);
      nextParams.set('documentTab', activeTab);
      setSearchParams(nextParams, { replace: true });
    }
    setPendingTab(null);
    setPendingTabSource('ui');
  };

  const confirmPendingTab = () => {
    if (!pendingTab) return;
    const nextTab = pendingTab;
    const source = pendingTabSource;
    clearDirtyForTab(activeTab);
    setPendingTab(null);
    setPendingTabSource('ui');
    commitTabChange(nextTab, source);
  };

  useEffect(() => {
    const handler = (event: BeforeUnloadEvent) => {
      if ((activeTab === 'devis' || activeTab === 'honoraires') && hasAccountingDraft) {
        event.preventDefault();
        event.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [activeTab, hasAccountingDraft]);

  return {
    activeTab,
    setActiveTab,
    pendingTab,
    handleTabChange,
    cancelPendingTab,
    confirmPendingTab,
    syncDocumentTab,
  };
}
