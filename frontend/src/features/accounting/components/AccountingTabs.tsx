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
  <div className="flex gap-2 p-1.5 bg-slate-100 rounded-2xl w-fit">
    <button 
      onClick={() => setActiveTab('history')}
      className={cn(
        "px-8 py-3 rounded-xl text-[11px] font-black uppercase tracking-widest transition-all",
        activeTab === 'history' ? "bg-white shadow-lg text-primary" : "text-slate-500 hover:text-slate-800"
      )}
      style={activeTab === 'history' ? { color: 'var(--primary)' } : {}}
    >
      Historique des Encaissements
    </button>
    <button 
      onClick={() => setActiveTab('treasury')}
      className={cn(
        "px-8 py-3 rounded-xl text-[11px] font-black uppercase tracking-widest transition-all flex items-center gap-2 relative",
        activeTab === 'treasury' ? "bg-white shadow-lg text-indigo-600" : "text-slate-500 hover:text-slate-800"
      )}
    >
      <Calculator size={14} /> Ghost Treasury Hub
      {treasuryData?.pending_count > 0 && (
        <span className="ml-1 px-1.5 py-0.5 bg-indigo-100 text-indigo-600 text-[9px] rounded-full font-black animate-pulse">
          {treasuryData.pending_count}
        </span>
      )}
    </button>
    <button
      onClick={() => setActiveTab('insights')}
      className={cn(
        "px-8 py-3 rounded-xl text-[11px] font-black uppercase tracking-widest transition-all flex items-center gap-2 relative",
        activeTab === 'insights' ? "bg-white shadow-lg text-primary" : "text-slate-500 hover:text-slate-800"
      )}
      style={activeTab === 'insights' ? { color: 'var(--primary)' } : {}}
    >
      <BarChart2 size={14} /> Visual Insights
    </button>
    <button
      onClick={() => setActiveTab('unpaid')}
      className={cn(
        "px-8 py-3 rounded-xl text-[11px] font-black uppercase tracking-widest transition-all flex items-center gap-2 relative",
        activeTab === 'unpaid' ? "bg-white shadow-lg" : "text-slate-500 hover:text-slate-800"
      )}
      style={activeTab === 'unpaid' ? { color: 'var(--primary)' } : {}}
    >
      <AlertCircle size={14} />
      Impayés
      {debtData && debtData.total_patients > 0 && (
        <span className="ml-1 px-1.5 py-0.5 bg-red-100 text-red-600 text-[9px] rounded-full font-black">
          {debtData.total_patients}
        </span>
      )}
    </button>
  </div>
);
