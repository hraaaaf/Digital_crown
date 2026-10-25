import { Download, FileSpreadsheet, Loader2, Receipt, TrendingUp } from 'lucide-react';

interface AccountingHeaderProps {
  breakdown: Record<string, number>;
  totalAmount: number;
  totalCollected: number;
  exportingCsv: boolean;
  exporting: boolean;
  itemsCount: number;
  handleExportCsv: () => void | Promise<void>;
  handleExport: () => void | Promise<void>;
}

export const AccountingHeader = ({
  breakdown,
  totalAmount,
  totalCollected,
  exportingCsv,
  exporting,
  itemsCount,
  handleExportCsv,
  handleExport,
}: AccountingHeaderProps) => (
  <header className="flex flex-col md:flex-row md:items-center justify-between gap-6 bg-card/80 backdrop-blur-xl border border-border-main p-8 rounded-[2.5rem] shadow-lg">
    <div className="flex items-center gap-5">
      <div className="w-14 h-14 bg-primary text-on-primary rounded-2xl flex items-center justify-center shadow-lg shadow-primary/20">
        <Receipt size={28} />
      </div>
      <div>
        <h1 className="text-3xl font-black tracking-tight text-primary">Comptabilité & Honoraires</h1>
        <p className="text-text-muted font-medium mt-1 uppercase text-[10px] tracking-widest flex items-center gap-2">
          <TrendingUp size={14} className="text-success" />
          Suivi des encaissements par assurance
        </p>
      </div>
    </div>

    <div className="flex flex-wrap items-center gap-4">
      <div className="flex gap-2 mr-4">
        {Object.entries(breakdown).map(([ass, amount]) => amount > 0 && (
          <div key={ass} className="px-3 py-2 bg-background border border-border-main rounded-xl flex flex-col items-center min-w-[80px]">
            <span className="text-[9px] font-black text-text-muted uppercase tracking-tighter">{ass === 'MUTUELLE_FAR' ? 'FAR' : ass}</span>
            <span className="text-[11px] font-bold text-primary">{amount.toLocaleString('fr-FR')}</span>
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <div className="bg-background px-6 py-4 rounded-3xl border border-border-main flex flex-col items-end shadow-sm">
          <span className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-1">Total Facturé</span>
          <span className="text-xl font-black text-text-muted">{totalAmount.toLocaleString('fr-FR')} MAD</span>
        </div>
        <div className="bg-success-surface px-6 py-4 rounded-3xl border border-success-border flex flex-col items-end shadow-sm">
          <span className="text-[10px] font-black text-success uppercase tracking-widest mb-1">Total Encaissé</span>
          <span className="text-2xl font-black text-success">{totalCollected.toLocaleString('fr-FR')} MAD</span>
        </div>
      </div>

      <button
        onClick={handleExportCsv}
        disabled={exportingCsv || itemsCount === 0}
        className="flex items-center gap-2 px-5 py-4 bg-primary text-on-primary focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary rounded-[1.5rem] font-black uppercase text-[11px] tracking-widest shadow-lg hover:-translate-y-1 transition-all active:scale-95 disabled:opacity-50 disabled:translate-y-0"
      >
        {exportingCsv ? <Loader2 className="animate-spin" size={18} /> : <FileSpreadsheet size={18} />}
        CSV
      </button>
      <button
        onClick={handleExport}
        disabled={exporting || itemsCount === 0}
        className="flex items-center gap-3 px-6 py-4 bg-primary text-on-primary focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary rounded-[1.5rem] font-black uppercase text-[12px] tracking-widest shadow-xl shadow-primary/20 hover:-translate-y-1 transition-all active:scale-95 disabled:opacity-50 disabled:translate-y-0"
       
      >
        {exporting ? <Loader2 className="animate-spin" size={20} /> : <Download size={20} />}
        {exporting ? "Génération..." : "PDF"}
      </button>
    </div>
  </header>
);
