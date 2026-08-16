import React from 'react';
import { Pill, FileBadge, Calculator, Receipt, Type, Brain } from 'lucide-react';
import { cn } from '../../../utils/cn';
import { isPrescriptionDirty, setPrescriptionDirty } from './PrescriptionDirtyState';
import { isLibreDirty, setLibreDirty } from './LibreDirtyState';
import { isDiagnosticCompanionDirty, setDiagnosticCompanionDirty } from './DiagnosticCompanionDirtyState';
import { requiresDevisToHonorairesConfirmation } from './AccountingDocumentTransitionPolicy';

interface StudioTabsProps {
  activeTab: import('../DocumentHub').HubDocumentType;
  onTabChange: (tab: import('../DocumentHub').HubDocumentType) => void;
  'data-tour'?: string;
}

export const StudioTabs: React.FC<StudioTabsProps> = ({ activeTab, onTabChange, 'data-tour': dataTour }) => {
  const requestTabChange = (tab: import('../DocumentHub').HubDocumentType) => {
    if (tab === activeTab) return;
    if (requiresDevisToHonorairesConfirmation(activeTab, tab)) {
      const confirmed = window.confirm(
        'Convertir ce devis en Note d\'Honoraires ? Les actes et montants seront conservés. Aucun paiement n\'est enregistré par ce changement d\'onglet.',
      );
      if (!confirmed) return;
    }
    if (activeTab === 'ordonnance' && isPrescriptionDirty()) {
      const confirmed = window.confirm(
        'Des modifications non enregistrées sont présentes dans l’ordonnance. Quitter cet onglet et les abandonner ?',
      );
      if (!confirmed) return;
      setPrescriptionDirty(false);
    }
    if (activeTab === 'libre' && isLibreDirty()) {
      const confirmed = window.confirm(
        'Des modifications non enregistrées sont présentes dans le document libre. Quitter cet onglet et les abandonner ?',
      );
      if (!confirmed) return;
      setLibreDirty(false);
    }
    if (activeTab === 'plan' && isDiagnosticCompanionDirty()) {
      const confirmed = window.confirm(
        'Des actes saisis par le praticien n’ont pas encore été transférés. Quitter le compagnon et les abandonner ?',
      );
      if (!confirmed) return;
      setDiagnosticCompanionDirty(false);
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
