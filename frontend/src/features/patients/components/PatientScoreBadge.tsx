import { useEffect, useRef, useState } from 'react';
import { CalendarCheck2, Loader2, RefreshCcw, Tag, WalletCards } from 'lucide-react';
import { api } from '../../../services/api';
import { cn } from '../../../utils/cn';
import { usePatientScoresStore } from '../../../stores/usePatientScoresStore';

interface PatientScoreBadgeProps {
  patientId: number;
  className?: string;
  onUpdate?: () => void;
}

const MANUAL_TAGS = {
  PLATINUM: 'VIP',
  GOLD: 'Fidèle',
  SILVER: 'Standard',
  BRONZE: 'À recontacter',
} as const;

const money = (value: number) => value.toLocaleString('fr-MA', { maximumFractionDigits: 0 });

export const PatientScoreBadge = ({ patientId, className, onUpdate }: PatientScoreBadgeProps) => {
  const data = usePatientScoresStore(state => state.scores[patientId]) || null;
  const storeLoading = usePatientScoresStore(state => state.loading);
  const loaded = usePatientScoresStore(state => state.loaded);
  const fetchScores = usePatientScoresStore(state => state.fetchScores);
  const [showMenu, setShowMenu] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!loaded && !storeLoading) fetchScores();
  }, [loaded, storeLoading, fetchScores]);

  useEffect(() => {
    if (!showMenu) return;
    const close = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) setShowMenu(false);
    };
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, [showMenu]);

  const updateManualTag = async (grade: keyof typeof MANUAL_TAGS | null) => {
    setIsUpdating(true);
    try {
      await api.patch(`/patients/${patientId}/grade`, {
        grade,
        comment: grade ? 'Tag cabinet manuel.' : null,
      });
      await fetchScores(true);
      onUpdate?.();
      setShowMenu(false);
    } catch (error) {
      console.error('Erreur mise à jour tag cabinet', error);
    } finally {
      setIsUpdating(false);
    }
  };

  if (!loaded && !data) {
    return <Loader2 size={14} className={cn('animate-spin text-slate-300', className)} />;
  }
  if (!data) return null;

  const { rdv_honores, rdv_annules, has_billing_data, total_facture, total_encaisse } = data.details;
  const hasRdvHistory = rdv_honores + rdv_annules > 0;
  const manualLabel = data.is_manual && data.grade ? MANUAL_TAGS[data.grade] : null;

  return (
    <div className={cn('relative inline-flex max-w-full flex-wrap items-center gap-1.5', className)} ref={menuRef}>
      <span className="inline-flex max-w-full items-center gap-1 rounded-lg border border-indigo-100 bg-indigo-50 px-2 py-1 text-[9px] font-black text-indigo-700 whitespace-nowrap">
        <CalendarCheck2 size={11} />
        {hasRdvHistory ? `${rdv_honores} RDV honoré${rdv_honores > 1 ? 's' : ''} · ${rdv_annules} annulé${rdv_annules > 1 ? 's' : ''}` : 'Aucun historique RDV'}
      </span>

      <span className="inline-flex max-w-full items-center gap-1 rounded-lg border border-emerald-100 bg-emerald-50 px-2 py-1 text-[9px] font-black text-emerald-700 whitespace-nowrap">
        <WalletCards size={11} />
        {has_billing_data ? `${money(total_encaisse)} / ${money(total_facture)} MAD encaissés` : 'Facturation indéterminée'}
      </span>

      <button
        type="button"
        onClick={(event) => { event.stopPropagation(); setShowMenu(value => !value); }}
        className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2 py-1 text-[9px] font-black text-slate-500 hover:bg-slate-50 whitespace-nowrap"
        aria-label="Tag cabinet manuel"
        title="Tag cabinet manuel"
      >
        <Tag size={10} /> {manualLabel ? `Tag cabinet · ${manualLabel}` : 'Tag cabinet'}
      </button>

      {showMenu && (
        <div onClick={event => event.stopPropagation()} className="absolute left-0 top-full z-[9999] mt-2 w-64 rounded-2xl border border-slate-100 bg-white p-3 text-left shadow-2xl">
          <p className="px-2 pb-2 text-[9px] font-black uppercase tracking-widest text-slate-400">Tag cabinet manuel</p>
          <p className="px-2 pb-3 text-[10px] font-medium leading-relaxed text-slate-500">Ce tag est choisi par le cabinet. Il n'est jamais calculé automatiquement.</p>
          <div className="space-y-1">
            {(Object.keys(MANUAL_TAGS) as Array<keyof typeof MANUAL_TAGS>).map(grade => (
              <button
                key={grade}
                type="button"
                disabled={isUpdating}
                onClick={() => updateManualTag(grade)}
                className="w-full rounded-xl px-3 py-2 text-left text-xs font-bold text-slate-700 hover:bg-slate-50"
              >
                {MANUAL_TAGS[grade]}
              </button>
            ))}
          </div>
          {data.is_manual && (
            <button
              type="button"
              disabled={isUpdating}
              onClick={() => updateManualTag(null)}
              className="mt-2 flex w-full items-center justify-center gap-1 border-t border-slate-100 pt-3 text-[9px] font-black uppercase tracking-wider text-blue-600"
            >
              <RefreshCcw size={11} /> Retirer le tag
            </button>
          )}
        </div>
      )}
    </div>
  );
};
