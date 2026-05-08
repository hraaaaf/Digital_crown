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
    <div className="flex items-center justify-between bg-slate-100/50 p-1 rounded-xl mb-4">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={cn(
            "flex flex-col items-center justify-center py-2 px-1 rounded-lg transition-all flex-1 gap-1",
            activeTab === tab.id 
              ? "bg-white shadow-sm text-primary scale-105" 
              : "text-slate-400 hover:text-slate-600 hover:bg-white/30"
          )}
          style={{ color: activeTab === tab.id ? 'var(--primary)' : undefined }}
        >
          {tab.icon}
          <span className="text-[9px] font-black uppercase tracking-tighter">{tab.label}</span>
        </button>
      ))}
    </div>
  );
};
