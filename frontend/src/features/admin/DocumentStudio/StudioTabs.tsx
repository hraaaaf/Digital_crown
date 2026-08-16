import React from 'react';
import { Pill, FileBadge, Calculator, Receipt, Type, Brain } from 'lucide-react';
import { cn } from '../../../utils/cn';
import { DOCUMENT_STUDIO_LABELS, type CertifiableDocumentStudioTab } from './DocumentStudioVocabulary';

interface StudioTabsProps {
  activeTab: CertifiableDocumentStudioTab;
  onTabChange: (tab: CertifiableDocumentStudioTab) => void;
  'data-tour'?: string;
}

export const StudioTabs: React.FC<StudioTabsProps> = ({ activeTab, onTabChange, 'data-tour': dataTour }) => (
  <div
    data-tour={dataTour}
    aria-label="Types de documents"
    className="flex w-full justify-start xl:justify-center bg-slate-100/90 dark:bg-slate-900/80 p-1.5 rounded-2xl gap-1 overflow-x-auto shrink-0 relative z-50 scroll-smooth border border-slate-200/70 dark:border-white/10 shadow-inner"
  >
    <TabButton active={activeTab === 'ordonnance'} onClick={() => onTabChange('ordonnance')} icon={<Pill size={16} />} label={DOCUMENT_STUDIO_LABELS.ordonnance} tourId="tab-ordonnance" />
    <TabButton active={activeTab === 'certificat'} onClick={() => onTabChange('certificat')} icon={<FileBadge size={16} />} label={DOCUMENT_STUDIO_LABELS.certificat} tourId="tab-certificat" />
    <TabButton active={activeTab === 'devis'} onClick={() => onTabChange('devis')} icon={<Calculator size={16} />} label={DOCUMENT_STUDIO_LABELS.devis} tourId="tab-devis" />
    <TabButton active={activeTab === 'honoraires'} onClick={() => onTabChange('honoraires')} icon={<Receipt size={16} />} label={DOCUMENT_STUDIO_LABELS.honoraires} tourId="tab-honoraires" />
    <TabButton active={activeTab === 'echeancier'} onClick={() => onTabChange('echeancier')} icon={<Calculator size={16} />} label={DOCUMENT_STUDIO_LABELS.echeancier} tourId="tab-suivi" />
    <TabButton active={activeTab === 'libre'} onClick={() => onTabChange('libre')} icon={<Type size={16} />} label={DOCUMENT_STUDIO_LABELS.libre} tourId="tab-libre" />
    <TabButton active={activeTab === 'plan'} onClick={() => onTabChange('plan')} icon={<Brain size={16} />} label={DOCUMENT_STUDIO_LABELS.plan} tourId="tab-strategie" />
  </div>
);

const TabButton = ({ active, onClick, icon, label, tourId }: { active: boolean, onClick: () => void, icon: React.ReactNode, label: string, tourId?: string }) => (
  <button
    type="button"
    onClick={onClick}
    data-tour={tourId}
    aria-pressed={active}
    className={cn(
      "flex min-h-11 shrink-0 items-center gap-2 px-3 sm:px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-[0.08em] sm:tracking-widest transition-all whitespace-nowrap focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50",
      active
        ? "bg-white dark:bg-slate-800 text-primary shadow-sm ring-1 ring-black/5 dark:ring-white/10"
        : "text-slate-500 dark:text-slate-400 hover:text-primary hover:bg-white/70 dark:hover:bg-slate-800/70"
    )}
    style={active ? { color: 'var(--primary)' } : {}}
  >
    {icon}
    <span>{label}</span>
  </button>
);
