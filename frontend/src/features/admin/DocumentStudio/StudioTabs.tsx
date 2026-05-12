import React from 'react';
import { Pill, FileBadge, Calculator, Receipt, Type, Brain } from 'lucide-react';
import { cn } from '../../../utils/cn';

interface StudioTabsProps {
  activeTab: string;
  onTabChange: (tab: any) => void;
  'data-tour'?: string;
}

export const StudioTabs: React.FC<StudioTabsProps> = ({ activeTab, onTabChange, 'data-tour': dataTour }) => {
  return (
    <div data-tour={dataTour} className="flex bg-slate-200/50 p-1 rounded-xl gap-1 overflow-x-auto shrink-0 relative z-50">
      <TabButton 
        active={activeTab === 'ordonnance'} 
        onClick={() => onTabChange('ordonnance')} 
        icon={<Pill size={16} />} 
        label="Ordonnance" 
        tourId="tab-ordonnance"
      />
      <TabButton 
        active={activeTab === 'certificat'} 
        onClick={() => onTabChange('certificat')} 
        icon={<FileBadge size={16} />} 
        label="Certificat" 
        tourId="tab-certificat"
      />
      <TabButton 
        active={activeTab === 'devis'} 
        onClick={() => onTabChange('devis')} 
        icon={<Calculator size={16} />} 
        label="Devis" 
        tourId="tab-devis"
      />
      <TabButton 
        active={activeTab === 'honoraires'} 
        onClick={() => onTabChange('honoraires')} 
        icon={<Receipt size={16} />} 
        label="Note Honoraires" 
        tourId="tab-honoraires"
      />
      <TabButton 
        active={activeTab === 'libre'} 
        onClick={() => onTabChange('libre')} 
        icon={<Type size={16} />} 
        label="Document Libre" 
        tourId="tab-libre"
      />
      <TabButton 
        active={activeTab === 'ai'} 
        onClick={() => onTabChange('ai')} 
        icon={<Brain size={16} />} 
        label="Analyse IA" 
        tourId="tab-ai"
      />
    </div>
  );
};

const TabButton = ({ active, onClick, icon, label, tourId }: { active: boolean, onClick: () => void, icon: React.ReactNode, label: string, tourId?: string }) => (
  <button
    onClick={onClick}
    data-tour={tourId}
    className={cn(
      "flex items-center gap-2 px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all whitespace-nowrap",
      active 
        ? "bg-white text-primary shadow-lg shadow-black/5" 
        : "text-slate-500 hover:text-primary hover:bg-white/40"
    )}
    style={active ? { color: 'var(--primary)' } : {}}
  >
    {icon}
    <span>{label}</span>
  </button>
);
