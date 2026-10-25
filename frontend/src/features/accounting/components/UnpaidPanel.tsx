import { CheckCheck, Loader2 } from 'lucide-react';

interface DebtData {
  total_patients: number;
  total_amount: number;
  items: Array<{
    patient_id: number;
    nom: string;
    prenom: string;
    telephone: string;
    assurance: string;
    total_billed: number;
    total_paid: number;
    remaining_due: number;
  }>;
}

interface UnpaidPanelProps {
  debtData: DebtData | null;
  loadingDebts: boolean;
}

export const UnpaidPanel = ({ debtData, loadingDebts }: UnpaidPanelProps) => (
  <div className="space-y-6 animate-in slide-in-from-bottom-4 duration-500">
    {/* KPI summary */}
    <div className="grid grid-cols-2 gap-4">
      <div className="bg-card text-text-main p-6 rounded-[2rem] border border-border-main shadow-sm">
        <p className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-2">Patients Débiteurs</p>
        <p className="text-3xl font-black text-text-main">{debtData?.total_patients ?? '—'}</p>
      </div>
      <div className="bg-danger-surface text-danger p-6 rounded-[2rem] border border-danger-border shadow-sm">
        <p className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-2">Total Impayé</p>
        <p className="text-3xl font-black text-danger">
          {debtData ? `${debtData.total_amount.toLocaleString('fr-MA')} MAD` : '—'}
        </p>
      </div>
    </div>

    {/* Table patients débiteurs */}
    <div className="bg-card text-text-main rounded-[2rem] border border-border-main shadow-sm overflow-hidden">
      {loadingDebts ? (
        <div className="flex justify-center py-16">
          <Loader2 className="animate-spin text-text-muted" size={32} />
        </div>
      ) : !debtData || debtData.items.length === 0 ? (
        <div className="flex flex-col items-center py-16 text-text-muted">
          <CheckCheck size={40} className="text-success mb-3" />
          <p className="font-bold">Aucun impayé — excellent !</p>
        </div>
      ) : (
        <table className="w-full">
          <thead>
            <tr className="border-b border-border-main">
              <th className="text-left px-6 py-3 text-[10px] font-black text-text-muted uppercase tracking-widest">Patient</th>
              <th className="text-left px-6 py-3 text-[10px] font-black text-text-muted uppercase tracking-widest">Téléphone</th>
              <th className="text-right px-6 py-3 text-[10px] font-black text-text-muted uppercase tracking-widest">Facturé</th>
              <th className="text-right px-6 py-3 text-[10px] font-black text-text-muted uppercase tracking-widest">Encaissé</th>
              <th className="text-right px-6 py-3 text-[10px] font-black text-text-muted uppercase tracking-widest">Restant Dû</th>
              <th className="px-6 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-main">
            {debtData.items.map(item => (
              <tr key={item.patient_id} className="hover:bg-input-field transition-colors">
                <td className="px-6 py-4">
                  <p className="font-black text-sm text-text-main">{item.nom} {item.prenom}</p>
                  {item.assurance && item.assurance !== 'AUCUNE' && (
                    <p className="text-[10px] text-text-muted font-bold mt-0.5">{item.assurance}</p>
                  )}
                </td>
                <td className="px-6 py-4 text-sm text-text-muted font-medium">{item.telephone}</td>
                <td className="px-6 py-4 text-right text-sm font-bold text-text-muted">
                  {item.total_billed.toLocaleString('fr-MA')}
                </td>
                <td className="px-6 py-4 text-right text-sm font-bold text-success">
                  {item.total_paid.toLocaleString('fr-MA')}
                </td>
                <td className="px-6 py-4 text-right">
                  <span className="text-sm font-black text-danger">
                    {item.remaining_due.toLocaleString('fr-MA')} MAD
                  </span>
                </td>
                <td className="px-6 py-4">
                  <a
                    href={`/patients/${item.patient_id}?tab=finances`}
                    className="text-[10px] font-black uppercase tracking-widest px-3 py-1.5 rounded-lg border border-primary/20 hover:bg-primary/5 transition-colors whitespace-nowrap"
                    style={{ color: 'var(--primary)' }}
                  >
                    Voir Dossier
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  </div>
);
