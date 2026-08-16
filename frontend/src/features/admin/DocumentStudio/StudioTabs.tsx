import React from 'react';
import { Pill, FileBadge, Calculator, Receipt, Type, Brain } from 'lucide-react';
import { cn } from '../../../utils/cn';
import { useAccountingStore } from '../store/useAccountingStore';
import { isPrescriptionDirty, setPrescriptionDirty } from './PrescriptionDirtyState';
import { isCertificateDirty, setCertificateDirty } from './CertificateDirtyState';
import { isInstallmentDirty, setInstallmentDirty } from './InstallmentDirtyState';
import { isLibreDirty, setLibreDirty } from './LibreDirtyState';
import { isP7Dirty, setP7Dirty } from './P7DirtyState';
import { shouldGuardDocumentTabTransition } from './DocumentTabNavigationPolicy';

interface StudioTabsProps {
  activeTab: import('../DocumentHub').HubDocumentType;
  onTabChange: (tab: import('../DocumentHub').HubDocumentType) => void;
  'data-tour'?: string;
}

const discardMessage: Partial<Record<import('../DocumentHub').HubDocumentType, string>> = {
  ordonnance: 'Des modifications non enregistrées sont présentes dans l’ordonnance. Quitter cet onglet et les abandonner ?',
  certificat: 'Des modifications non enregistrées sont présentes dans le certificat. Quitter cet onglet et les abandonner ?',
  devis: 'Des actes non enregistrés sont présents dans le devis. Quitter cet espace et les abandonner ?',
  honoraires: 'Des actes non enregistrés sont présents dans la note d’honoraires. Quitter cet espace et les abandonner ?',
  echeancier: 'Un échéancier non enregistré contient des modifications. Quitter cet onglet et les abandonner ?',
  libre: 'Des modifications non enregistrées sont présentes dans le document libre. Quitter cet onglet et les abandonner ?',
  plan: 'Une proposition diagnostique non convertie contient des modifications. Quitter cet onglet et les abandonner ?',
};

export const StudioTabs: React.FC<StudioTabsProps> = ({ activeTab, onTabChange, 'data-tour': dataTour }) => {
  const accountingItems = useAccountingStore(state => state.items);
  const resetAccounting = useAccountingStore(state => state.reset);

  const requestTabChange = (tab: import('../DocumentHub').HubDocumentType) => {
    const dirty = {
      prescription: isPrescriptionDirty(),
      certificate: isCertificateDirty(),
      accounting: accountingItems.some(item => item.description.trim()),
      installment: isInstallmentDirty(),
      libre: isLibreDirty(),
      plan: isP7Dirty(),
    };

    if (!shouldGuardDocumentTabTransition(activeTab, tab, dirty)) {
      onTabChange(tab);
      return;
    }

    const confirmed = window.confirm(discardMessage[activeTab] || 'Abandonner les modifications non enregistrées ?');
    if (!confirmed) return;

    switch (activeTab) {
      case 'ordonnance':
        setPrescriptionDirty(false);
        break;
      case 'certificat':
        setCertificateDirty(false);
        break;
      case 'devis':
      case 'honoraires':
        resetAccounting();
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

    onTabChange(tab);
  };

  return (
    <div data-tour={dataTour} className="flex w-full justify-start xl:justify-center bg-slate-200/50 p-1 rounded-xl gap-1 overflow-x-auto shrink-0 relative z-50 scroll-smooth">
      <TabButton active={activeTab === 'ordonnance'} onClick={() => requestTabChange('ordonnance')} icon={<Pill size={16} />} label="Ordonnance" tourId="tab-ordonnance" />
      <TabButton active={activeTab === 'certificat'} onClick={() => requestTabChange('certificat')} icon={<FileBadge size={16} />} label="Certificat" tourId="tab-certificat" />
      <TabButton active={activeTab === 'devis'} onClick={() => requestTabChange('devis')} icon={<Calculator size={16} />} label="Devis" tourId="tab-devis" />
      <TabButton active={activeTab === 'honoraires'} onClick={() => requestTabChange('honoraires')} icon={<Receipt size={16} />} label="Note Honoraires" tourId="tab-honoraires" />
      <TabButton active={activeTab === 'echeancier'} onClick={() => requestTabChange('echeancier')} icon={<Calculator size={16} />} label="Suivi Paiement" tourId="tab-suivi" />
      <TabButton active={activeTab === 'libre'} onClick={() => requestTabChange('libre')} icon={<Type size={16} />} label="Document Libre" tourId="tab-libre" />
      <TabButton active={activeTab === 'plan'} onClick={() => requestTabChange('plan')} icon={<Brain size={16} />} label="Compagnon Diagnostique" tourId="tab-strategie" />
    </div>
  );
};

const TabButton = ({ active, onClick, icon, label, tourId }: { active: boolean, onClick: () => void, icon: React.ReactNode, label: string, tourId?: string }) => (
  <button
    type="button"
    onClick={onClick}
    data-tour={tourId}
    className={cn(
      "flex shrink-0 items-center gap-2 px-3 sm:px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all whitespace-nowrap",
      active ? "bg-white text-primary shadow-lg shadow-black/5" : "text-slate-500 hover:text-primary hover:bg-white/40"
    )}
    style={active ? { color: 'var(--primary)' } : {}}
  >
    {icon}
    <span>{label}</span>
  </button>
);