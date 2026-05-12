import React from 'react';
import { ClipboardCheck, Activity, AlertTriangle, Pill, User } from 'lucide-react';
import { cn } from '../../utils/cn';

interface TabsProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export const ClinicalRefTabs: React.FC<TabsProps> = ({ activeTab, onTabChange }) => {
  const tabs = [
    { id: 'checklist', icon: <ClipboardCheck size={18} />, label: 'Check' },
    { id: 'steps', icon: <Activity size={18} />, label: 'Etapes' },
    { id: 'pitfalls', icon: <AlertTriangle size={18} />, label: 'Risques' },
    { id: 'drugs', icon: <Pill size={18} />, label: 'Meds' },
    { id: 'patient', icon: <User size={18} />, label: 'Patient' },
  ];

  return (
    <div className="flex items-center justify-between bg-[var(--bg-medical-pearl)] p-1 rounded-2xl mb-6 border border-[var(--border-color)]/30">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={cn(
            "flex flex-col items-center justify-center py-2.5 px-1 rounded-xl transition-all flex-1 gap-1.5",
            activeTab === tab.id 
              ? "bg-[var(--card-bg)] shadow-lg shadow-[var(--primary)]/5 text-[var(--primary)] scale-[1.02]" 
              : "text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--card-bg)]/50"
          )}
          style={{ color: activeTab === tab.id ? 'var(--primary)' : undefined }}
        >
          {tab.icon}
          <span className="text-[10px] font-black uppercase tracking-tight">{tab.label}</span>
        </button>
      ))}
    </div>
  );
};
