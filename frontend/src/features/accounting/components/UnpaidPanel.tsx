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
      <div className="bg-white p-6 rounded-[2rem] border border-slate-200 shadow-sm">
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Patients Débiteurs</p>
        <p className="text-3xl font-black text-slate-800">{debtData?.total_patients ?? '—'}</p>
      </div>
      <div className="bg-red-50 p-6 rounded-[2rem] border border-red-100 shadow-sm">
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Total Impayé</p>
        <p className="text-3xl font-black text-red-600">
          {debtData ? `${debtData.total_amount.toLocaleString('fr-MA')} MAD` : '—'}
        </p>
      </div>
    </div>

    {/* Table patients débiteurs */}
    <div className="bg-white rounded-[2rem] border border-slate-200 shadow-sm overflow-hidden">
      {loadingDebts ? (
        <div className="flex justify-center py-16">
          <Loader2 className="animate-spin text-slate-300" size={32} />
        </div>
      ) : !debtData || debtData.items.length === 0 ? (
        <div className="flex flex-col items-center py-16 text-slate-400">
          <CheckCheck size={40} className="text-emerald-300 mb-3" />
          <p className="font-bold">Aucun impayé — excellent !</p>
        </div>
      ) : (
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-100">
              <th className="text-left px-6 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Patient</th>
              <th className="text-left px-6 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Téléphone</th>
              <th className="text-right px-6 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Facturé</th>
              <th className="text-right px-6 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Encaissé</th>
              <th className="text-right px-6 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Restant Dû</th>
              <th className="px-6 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {debtData.items.map(item => (
              <tr key={item.patient_id} className="hover:bg-slate-50 transition-colors">
                <td className="px-6 py-4">
                  <p className="font-black text-sm text-slate-800">{item.nom} {item.prenom}</p>
                  {item.assurance && item.assurance !== 'AUCUNE' && (
                    <p className="text-[10px] text-slate-400 font-bold mt-0.5">{item.assurance}</p>
                  )}
                </td>
                <td className="px-6 py-4 text-sm text-slate-600 font-medium">{item.telephone}</td>
                <td className="px-6 py-4 text-right text-sm font-bold text-slate-600">
                  {item.total_billed.toLocaleString('fr-MA')}
                </td>
                <td className="px-6 py-4 text-right text-sm font-bold text-emerald-600">
                  {item.total_paid.toLocaleString('fr-MA')}
                </td>
                <td className="px-6 py-4 text-right">
                  <span className="text-sm font-black text-red-600">
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
