import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../../services/api';
import { cn } from '../../../utils/cn';
import { Banknote, Clock, CheckCircle2, AlertTriangle, Calendar, TrendingUp, CreditCard } from 'lucide-react';
import { EliteGhostLoader } from '../../../components/EliteGhostLoader';
import { QuickPayModal } from './QuickPayModal';
import { PayActeModal, type ActeBillingItem } from './PayActeModal';
import { InstallmentPlanModal } from './InstallmentPlanModal';

interface PatientFinancesProps {
  patientId: number;
}

const PAYMENT_METHOD_LABELS: Record<string, string> = {
  ESPECES: 'Espèces',
  CARTE: 'Carte',
  VIREMENT: 'Virement',
  CHEQUE: 'Chèque',
};

const STATUT_LABELS: Record<string, { label: string; className: string }> = {
  EN_ATTENTE: { label: 'En attente', className: 'bg-amber-500/10 text-amber-600 border-amber-500/20' },
  A_ENCAISSER: { label: 'À encaisser', className: 'bg-blue-500/10 text-blue-600 border-blue-500/20' },
  PARTIEL: { label: 'Partiel', className: 'bg-orange-500/10 text-orange-600 border-orange-500/20' },
  PAYE: { label: 'Payé', className: 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20' },
};

export const PatientFinances = ({ patientId }: PatientFinancesProps) => {
  const [isPayModalOpen, setIsPayModalOpen] = useState(false);
  const [payingActe, setPayingActe] = useState<ActeBillingItem | null>(null);
  const [planActe, setPlanActe] = useState<ActeBillingItem | null>(null);

  const { data: snapshot, isLoading, refetch } = useQuery({
    queryKey: ['patient-financial-snapshot', patientId],
    queryFn: async () => {
      const res = await api.get(`/patients/${patientId}/financial-snapshot`);
      return res.data;
    },
  });

  const { data: actesBilling, refetch: refetchBilling } = useQuery({
    queryKey: ['actes-billing', patientId],
    queryFn: async () => {
      const res = await api.get(`/accounting/actes-billing/patient/${patientId}`);
      return res.data as ActeBillingItem[];
    },
  });

  if (isLoading) {
    return <EliteGhostLoader text="Chargement des finances..." size="medium" />;
  }

  if (!snapshot) return null;

  const recoveryRate =
    snapshot.total_billed > 0
      ? Math.round((snapshot.total_collected / snapshot.total_billed) * 100)
      : 100;

  return (
    <div className="space-y-8 pb-10">

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-card-bg p-6 rounded-[2rem] border border-border-main shadow-sm">
          <p className="text-[10px] font-black uppercase tracking-[0.12em] text-text-muted mb-2">Total Facturé</p>
          <div className="text-3xl font-black text-slate-800">
            {snapshot.total_billed.toLocaleString('fr-MA')}
          </div>
          <div className="text-xs text-text-muted font-bold mt-1">MAD</div>
        </div>

        <div className="bg-card-bg p-6 rounded-[2rem] border border-border-main shadow-sm">
          <p className="text-[10px] font-black uppercase tracking-[0.12em] text-text-muted mb-2">Total Encaissé</p>
          <div className="text-3xl font-black text-emerald-600">
            {snapshot.total_collected.toLocaleString('fr-MA')}
          </div>
          <div className="text-xs text-text-muted font-bold mt-1">MAD</div>
        </div>

        <div className={cn(
          "p-6 rounded-[2rem] border shadow-sm",
          snapshot.remaining_due > 0
            ? "bg-red-50 border-red-100"
            : "bg-card-bg border-border-main"
        )}>
          <p className="text-[10px] font-black uppercase tracking-[0.12em] text-text-muted mb-2">Reste Dû</p>
          <div className={cn(
            "text-3xl font-black",
            snapshot.remaining_due > 0 ? "text-red-600" : "text-emerald-600"
          )}>
            {snapshot.remaining_due.toLocaleString('fr-MA')}
          </div>
          <div className="text-xs text-text-muted font-bold mt-1">MAD</div>
        </div>

        <div className="bg-card-bg p-6 rounded-[2rem] border border-border-main shadow-sm">
          <p className="text-[10px] font-black uppercase tracking-[0.12em] text-text-muted mb-2">Taux Recouvrement</p>
          <div className={cn(
            "text-3xl font-black",
            recoveryRate >= 80 ? "text-emerald-600" : recoveryRate >= 50 ? "text-amber-600" : "text-red-600"
          )}>
            {recoveryRate}%
          </div>
          <div className="text-xs text-text-muted font-bold mt-1">Encaissé / Facturé</div>
        </div>
      </div>

      {/* Actes & Paiements */}
      {actesBilling && actesBilling.length > 0 && (
        <div className="bg-card-bg rounded-[2rem] border border-border-main shadow-sm overflow-hidden">
          <div className="flex items-center justify-between px-6 py-4 border-b border-border-main">
            <div className="flex items-center gap-2">
              <CreditCard size={16} style={{ color: 'var(--primary)' }} />
              <h3 className="text-[11px] font-black uppercase tracking-[0.12em]">Actes &amp; Paiements</h3>
            </div>
            {actesBilling.filter(a => a.remaining_due > 0.01).length > 0 && (
              <span className="text-[10px] font-black text-amber-600 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-lg">
                {actesBilling.filter(a => a.remaining_due > 0.01).length} à régler
              </span>
            )}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-main bg-slate-50/50">
                  <th className="px-5 py-3 text-left text-[10px] font-black uppercase tracking-widest text-text-muted">Date</th>
                  <th className="px-5 py-3 text-left text-[10px] font-black uppercase tracking-widest text-text-muted">Acte</th>
                  <th className="px-5 py-3 text-right text-[10px] font-black uppercase tracking-widest text-text-muted">Montant</th>
                  <th className="px-5 py-3 text-right text-[10px] font-black uppercase tracking-widest text-text-muted">Encaissé</th>
                  <th className="px-5 py-3 text-right text-[10px] font-black uppercase tracking-widest text-text-muted">Reste</th>
                  <th className="px-5 py-3 text-center text-[10px] font-black uppercase tracking-widest text-text-muted">Statut</th>
                  <th className="px-5 py-3 text-right text-[10px] font-black uppercase tracking-widest text-text-muted">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-main">
                {actesBilling.map(acte => {
                  const statut = STATUT_LABELS[acte.statut_paiement] || STATUT_LABELS['EN_ATTENTE'];
                  const isPaid = acte.remaining_due <= 0.01;
                  return (
                    <tr key={acte.id} className={cn(
                      "hover:bg-primary/[0.02] transition-colors",
                      isPaid && "opacity-60"
                    )}>
                      <td className="px-5 py-3 text-[11px] text-text-muted font-medium whitespace-nowrap">
                        {acte.date_debut ? new Date(acte.date_debut).toLocaleDateString('fr-FR') : '—'}
                      </td>
                      <td className="px-5 py-3 max-w-[200px]">
                        <p className="font-bold text-main truncate">{acte.libelle}</p>
                        {acte.type_acte && (
                          <p className="text-[10px] text-text-muted font-medium">{acte.type_acte}</p>
                        )}
                      </td>
                      <td className="px-5 py-3 text-right font-black text-slate-700 whitespace-nowrap">
                        {acte.montant.toLocaleString('fr-MA')} MAD
                      </td>
                      <td className="px-5 py-3 text-right font-black text-emerald-600 whitespace-nowrap">
                        {acte.total_paid.toLocaleString('fr-MA')} MAD
                      </td>
                      <td className="px-5 py-3 text-right whitespace-nowrap">
                        {isPaid ? (
                          <CheckCircle2 size={16} className="inline text-emerald-500" />
                        ) : (
                          <span className="font-black text-red-600">
                            {acte.remaining_due.toLocaleString('fr-MA')} MAD
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-3 text-center">
                        <span className={cn(
                          "text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-lg border",
                          statut.className
                        )}>
                          {statut.label}
                        </span>
                      </td>
                      <td className="px-5 py-3">
                        {!isPaid ? (
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              onClick={() => setPayingActe(acte)}
                              className="flex items-center gap-1 text-[10px] font-black uppercase tracking-wider px-2.5 py-1.5 rounded-lg bg-primary/5 border border-primary/20 transition-colors hover:bg-primary/10"
                              style={{ color: 'var(--primary)' }}
                            >
                              <Banknote size={11} /> Payer
                            </button>
                            <button
                              onClick={() => setPlanActe(acte)}
                              className="flex items-center gap-1 text-[10px] font-black uppercase tracking-wider px-2.5 py-1.5 rounded-lg bg-blue-500/5 border border-blue-500/20 text-blue-600 transition-colors hover:bg-blue-500/10"
                            >
                              <Calendar size={11} /> Plan
                            </button>
                          </div>
                        ) : (
                          <div className="flex justify-end">
                            <CheckCircle2 size={16} className="text-emerald-500" />
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Impayés */}
        <div className="bg-card-bg rounded-[2rem] border border-border-main shadow-sm overflow-hidden">
          <div className="flex items-center justify-between px-6 py-4 border-b border-border-main">
            <div className="flex items-center gap-2">
              <AlertTriangle size={16} className="text-amber-500" />
              <h3 className="text-[11px] font-black uppercase tracking-[0.12em]">
                Impayés ({snapshot.overdue_count})
              </h3>
            </div>
            {snapshot.overdue_count > 0 && (
              <span className="text-sm font-black text-red-600">
                {snapshot.overdue_total.toLocaleString('fr-MA')} MAD
              </span>
            )}
          </div>

          {snapshot.overdue_items.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 text-text-muted">
              <CheckCircle2 size={32} className="text-emerald-400 mb-2" />
              <p className="text-sm font-bold">Aucun impayé</p>
            </div>
          ) : (
            <div className="divide-y divide-border-main">
              {snapshot.overdue_items.map((item: any) => {
                const statut = STATUT_LABELS[item.statut_paiement] || STATUT_LABELS['EN_ATTENTE'];
                return (
                  <div key={item.id} className="flex items-center justify-between px-6 py-3 hover:bg-primary/2 transition-colors">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-bold text-main truncate">{item.libelle}</p>
                      {item.date_debut && (
                        <p className="text-[10px] text-text-muted font-medium mt-0.5">
                          {new Date(item.date_debut).toLocaleDateString('fr-FR')}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-3 ml-3">
                      <span className={cn(
                        "text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-lg border",
                        statut.className
                      )}>
                        {statut.label}
                      </span>
                      <span className="text-sm font-black text-slate-800 whitespace-nowrap">
                        {item.montant.toLocaleString('fr-MA')} MAD
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          <div className="px-6 py-4 border-t border-border-main">
            <button
              onClick={() => setIsPayModalOpen(true)}
              className="w-full flex items-center justify-center gap-2 py-2.5 bg-primary/5 hover:bg-primary/10 border border-primary/20 rounded-xl text-[11px] font-black uppercase tracking-widest transition-colors"
              style={{ color: 'var(--primary)' }}
            >
              <Banknote size={14} />
              Enregistrer un paiement
            </button>
          </div>
        </div>

        {/* Échéances à venir */}
        <div className="bg-card-bg rounded-[2rem] border border-border-main shadow-sm overflow-hidden">
          <div className="flex items-center justify-between px-6 py-4 border-b border-border-main">
            <div className="flex items-center gap-2">
              <Calendar size={16} className="text-blue-500" />
              <h3 className="text-[11px] font-black uppercase tracking-[0.12em]">
                Échéances à venir ({snapshot.upcoming_installments_count})
              </h3>
            </div>
            {snapshot.upcoming_installments_count > 0 && (
              <span className="text-sm font-black text-blue-600">
                {snapshot.upcoming_installments_total.toLocaleString('fr-MA')} MAD
              </span>
            )}
          </div>

          {snapshot.upcoming_installments_count === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 text-text-muted">
              <Calendar size={32} className="text-slate-300 mb-2" />
              <p className="text-sm font-bold">Aucune échéance à venir</p>
            </div>
          ) : (
            <div className="divide-y divide-border-main">
              {snapshot.upcoming_installments?.map((inst: any) => (
                <div key={inst.id} className="flex items-center justify-between px-6 py-3">
                  <div>
                    <p className="text-sm font-bold text-main">{inst.label}</p>
                    {inst.due_date && (
                      <p className="text-[10px] text-text-muted font-medium mt-0.5">
                        Échéance : {new Date(inst.due_date).toLocaleDateString('fr-FR')}
                      </p>
                    )}
                  </div>
                  <span className="text-sm font-black text-blue-600 whitespace-nowrap ml-3">
                    {inst.amount.toLocaleString('fr-MA')} MAD
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Historique paiements récents */}
      <div className="bg-card-bg rounded-[2rem] border border-border-main shadow-sm overflow-hidden">
        <div className="flex items-center gap-2 px-6 py-4 border-b border-border-main">
          <TrendingUp size={16} className="text-emerald-500" />
          <h3 className="text-[11px] font-black uppercase tracking-[0.12em]">
            Derniers paiements reçus
          </h3>
        </div>

        {snapshot.recent_payments.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 text-text-muted">
            <Clock size={32} className="text-slate-300 mb-2" />
            <p className="text-sm font-bold">Aucun paiement enregistré</p>
          </div>
        ) : (
          <div className="divide-y divide-border-main">
            {snapshot.recent_payments.map((p: any) => (
              <div key={p.id} className="flex items-center justify-between px-6 py-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center">
                    <CreditCard size={14} className="text-emerald-500" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-main">
                      {PAYMENT_METHOD_LABELS[p.payment_method] || p.payment_method}
                    </p>
                    {p.payment_date && (
                      <p className="text-[10px] text-text-muted font-medium">
                        {new Date(p.payment_date).toLocaleDateString('fr-FR')}
                      </p>
                    )}
                  </div>
                </div>
                <span className="text-sm font-black text-emerald-600 whitespace-nowrap">
                  +{p.amount.toLocaleString('fr-MA')} MAD
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Répartition par méthode */}
        {Object.keys(snapshot.payment_methods).length > 0 && (
          <div className="px-6 py-4 border-t border-border-main">
            <p className="text-[10px] font-black uppercase tracking-[0.12em] text-text-muted mb-3">
              Répartition par méthode
            </p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(snapshot.payment_methods).map(([method, data]: [string, any]) => (
                <div key={method} className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50 border border-emerald-100 rounded-xl">
                  <span className="text-[10px] font-black text-emerald-700 uppercase">
                    {PAYMENT_METHOD_LABELS[method] || method}
                  </span>
                  <span className="text-[10px] text-emerald-600 font-bold">
                    {data.total.toLocaleString('fr-MA')} MAD
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <QuickPayModal
        isOpen={isPayModalOpen}
        onClose={() => {
          setIsPayModalOpen(false);
          refetch();
        }}
        patientId={patientId}
      />

      {payingActe && (
        <PayActeModal
          acte={payingActe}
          patientId={patientId}
          isOpen={true}
          onClose={() => setPayingActe(null)}
          onPaid={() => {
            setPayingActe(null);
            refetch();
            refetchBilling();
          }}
        />
      )}

      {planActe && (
        <InstallmentPlanModal
          acte={planActe}
          patientId={patientId}
          isOpen={true}
          onClose={() => setPlanActe(null)}
          onCreated={() => {
            setPlanActe(null);
            refetch();
            refetchBilling();
          }}
        />
      )}
    </div>
  );
};
