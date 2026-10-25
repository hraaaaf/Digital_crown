import { AlertCircle, BarChart2, Calculator } from 'lucide-react';
import { cn } from '../../../utils/cn';

type AccountingTab = 'history' | 'treasury' | 'insights' | 'unpaid';

interface AccountingTabsProps {
  activeTab: AccountingTab;
  setActiveTab: (tab: AccountingTab) => void;
  treasuryData: any;
  debtData: { total_patients: number } | null;
}

export const AccountingTabs = ({ activeTab, setActiveTab, treasuryData, debtData }: AccountingTabsProps) => (
  <div className="flex gap-2 p-1.5 bg-input-field rounded-2xl w-fit">
    <button 
      onClick={() => setActiveTab('history')}
      className={cn(
        "px-8 py-3 rounded-xl text-[11px] font-black uppercase tracking-widest transition-all focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary",
        activeTab === 'history' ? "bg-card shadow-lg text-primary" : "text-text-muted hover:text-text-main"
      )}
     
    >
      Historique des Encaissements
    </button>
    <button 
      onClick={() => setActiveTab('treasury')}
      className={cn(
        "px-8 py-3 rounded-xl text-[11px] font-black uppercase tracking-widest transition-all flex items-center gap-2 relative",
        activeTab === 'treasury' ? "bg-card shadow-lg text-info" : "text-text-muted hover:text-text-main"
      )}
    >
      <Calculator size={14} /> Trésorerie
      {treasuryData?.pending_count > 0 && (
        <span className="ml-1 px-1.5 py-0.5 bg-info-surface text-info text-[9px] rounded-full font-black animate-pulse">
          {treasuryData.pending_count}
        </span>
      )}
    </button>
    <button
      onClick={() => setActiveTab('insights')}
      className={cn(
        "px-8 py-3 rounded-xl text-[11px] font-black uppercase tracking-widest transition-all flex items-center gap-2 relative",
        activeTab === 'insights' ? "bg-card shadow-lg text-primary" : "text-text-muted hover:text-text-main"
      )}
     
    >
      <BarChart2 size={14} /> Visual Insights
    </button>
    <button
      onClick={() => setActiveTab('unpaid')}
      className={cn(
        "px-8 py-3 rounded-xl text-[11px] font-black uppercase tracking-widest transition-all flex items-center gap-2 relative",
        activeTab === 'unpaid' ? "bg-card shadow-lg text-primary" : "text-text-muted hover:text-text-main"
      )}
     
    >
      <AlertCircle size={14} />
      Impayés
      {debtData && debtData.total_patients > 0 && (
        <span className="ml-1 px-1.5 py-0.5 bg-danger-surface text-danger text-[9px] rounded-full font-black">
          {debtData.total_patients}
        </span>
      )}
    </button>
  </div>
);
