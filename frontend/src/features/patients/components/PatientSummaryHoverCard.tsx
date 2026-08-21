import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { Activity, Calendar, Clock, DollarSign, Loader2, ShieldAlert } from 'lucide-react';
import { api } from '../../../services/api';
import { cn } from '../../../utils/cn';

interface PatientSummaryHoverCardProps {
  patientId: number;
  patientName: string;
  patientDossier: string;
  triggerRect: DOMRect | null;
}

interface IntelligenceData {
  patient_summary: {
    last_visit: { date: string; acte: string; days_ago: number } | null;
    next_visit: { date: string; time: string; motif: string } | null;
    clinical_summary: string;
    alerts: string[];
    risk_level: 'low' | 'moderate' | 'high';
    acts_last_90d: number;
    last_panoramic_findings: string[];
    cephalo_trend: string;
  };
  insights: Array<{
    id: string;
    type: string;
    title: string;
    content: string;
    actionLabel?: string;
    source_type?: string;
    trust_level?: number;
  }>;
  intelligence_score: number | null;
  timestamp: string;
}

export const PatientSummaryHoverCard = ({ patientId, patientName, patientDossier, triggerRect }: PatientSummaryHoverCardProps) => {
  const [data, setData] = useState<IntelligenceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [frame, setFrame] = useState({ top: 0, left: 0, width: 380 });

  useEffect(() => {
    if (!patientId) return;
    let mounted = true;
    setLoading(true);
    setError(false);
    api.get(`/intelligence/patient/${patientId}`)
      .then(res => {
        if (!mounted) return;
        setData(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching patient dossier markers:', err);
        if (!mounted) return;
        setError(true);
        setLoading(false);
      });
    return () => { mounted = false; };
  }, [patientId]);

  useEffect(() => {
    if (!triggerRect) return;
    const padding = 12;
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    const width = Math.min(380, Math.max(280, viewportWidth - padding * 2));
    const estimatedHeight = 430;
    let left = triggerRect.right + padding + window.scrollX;
    let top = triggerRect.top + window.scrollY;

    if (left + width > viewportWidth + window.scrollX) {
      left = triggerRect.left - width - padding + window.scrollX;
    }
    if (left < window.scrollX + padding) {
      left = window.scrollX + padding;
      top = triggerRect.bottom + padding + window.scrollY;
    }
    if (top + estimatedHeight > viewportHeight + window.scrollY) {
      top = Math.max(window.scrollY + padding, viewportHeight + window.scrollY - estimatedHeight - padding);
    }
    setFrame({ top, left, width });
  }, [triggerRect]);

  if (!triggerRect) return null;

  const otherInsights = data?.insights.filter(i => !['financial_risk', 'financial', 'safety'].includes(i.type)) ?? [];
  const financialInsights = data?.insights.filter(i => i.type === 'financial_risk' || i.type === 'financial') ?? [];

  return createPortal(
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.97, y: 8 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.97, y: 8 }}
        transition={{ duration: 0.18, ease: 'easeOut' }}
        style={{ position: 'absolute', top: frame.top, left: frame.left, width: frame.width, zIndex: 99999 }}
        className="pointer-events-none flex max-w-[calc(100vw-24px)] select-none flex-col gap-4 rounded-[2rem] border border-border-main/80 bg-card-bg/95 p-5 font-sans text-text-main shadow-[0_20px_50px_rgba(0,0,0,0.15)] backdrop-blur-2xl dark:border-white/10 dark:bg-[#0f172a]/95"
      >
        <div className="border-b border-border-main/50 pb-3">
          <p className="text-[9px] font-black uppercase tracking-widest text-text-muted">Repères du dossier</p>
          <h4 className="mt-1 break-words text-base font-black leading-tight tracking-tight text-primary uppercase">{patientName}</h4>
          <span className="font-mono text-[10px] font-bold tracking-wider text-text-muted">{patientDossier}</span>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center gap-2 py-8">
            <Loader2 className="animate-spin text-primary" size={24} />
            <span className="text-[9px] font-black uppercase tracking-widest text-text-muted">Chargement des repères...</span>
          </div>
        ) : error || !data ? (
          <div className="py-4 text-center text-xs italic text-text-muted">Impossible de charger les repères du dossier.</div>
        ) : (
          <div className="space-y-4 text-xs">
            {data.patient_summary.alerts?.length > 0 && (
              <div className="flex items-start gap-2.5 rounded-xl border border-red-500/20 bg-red-500/10 p-3">
                <ShieldAlert className="mt-0.5 flex-shrink-0 text-red-500" size={16} />
                <div>
                  <h5 className="text-[10px] font-black uppercase tracking-wider text-red-500">Vigilance dossier</h5>
                  <p className="mt-1 text-[10px] font-bold leading-normal text-red-500">{data.patient_summary.alerts.join(', ')}</p>
                </div>
              </div>
            )}

            <div className="space-y-2">
              <span className="block text-[9px] font-black uppercase tracking-widest text-text-muted">Résumé du dossier</span>
              <p className="rounded-xl border border-primary/5 bg-primary/5 p-2.5 text-[11px] font-medium leading-relaxed">
                {data.patient_summary.clinical_summary || 'Aucune information clinique disponible.'}
              </p>
              {data.patient_summary.cephalo_trend && data.patient_summary.cephalo_trend !== 'données insuffisantes' && (
                <p className="text-[9px] font-bold text-text-muted">Céphalométrie : {data.patient_summary.cephalo_trend}</p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div className="flex min-w-0 items-start gap-2 rounded-xl border border-border-main bg-card-bg p-2.5">
                <Clock className="mt-0.5 flex-shrink-0 text-blue-500" size={14} />
                <div className="min-w-0">
                  <span className="block text-[8px] font-black uppercase tracking-widest text-text-muted">Dernière visite</span>
                  {data.patient_summary.last_visit ? (
                    <><span className="mt-0.5 block truncate text-[10px] font-bold">{data.patient_summary.last_visit.acte}</span><span className="font-mono text-[9px] text-text-muted">il y a {data.patient_summary.last_visit.days_ago} jours</span></>
                  ) : <span className="mt-0.5 block text-[10px] text-text-muted">—</span>}
                </div>
              </div>
              <div className="flex min-w-0 items-start gap-2 rounded-xl border border-border-main bg-card-bg p-2.5">
                <Calendar className="mt-0.5 flex-shrink-0 text-emerald-500" size={14} />
                <div className="min-w-0">
                  <span className="block text-[8px] font-black uppercase tracking-widest text-text-muted">Prochain RDV</span>
                  {data.patient_summary.next_visit ? (
                    <><span className="mt-0.5 block truncate text-[10px] font-bold">{data.patient_summary.next_visit.motif || 'Soin'}</span><span className="mt-0.5 block font-mono text-[9px] text-text-muted">{new Date(data.patient_summary.next_visit.date).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })} à {data.patient_summary.next_visit.time}</span></>
                  ) : <span className="mt-0.5 block text-[10px] font-bold text-amber-600">Aucun RDV futur</span>}
                </div>
              </div>
            </div>

            {financialInsights.length > 0 && (
              <div className="space-y-1 border-t border-border-main/50 pt-3">
                {financialInsights.map(i => (
                  <div key={i.id} className={cn('flex items-start gap-2 rounded-xl border px-3 py-2 text-[10px]', i.type === 'financial_risk' ? 'border-amber-500/20 bg-amber-500/10 font-black text-amber-600' : 'border-primary/10 bg-primary/5 font-bold text-primary')}>
                    <DollarSign size={14} className="mt-0.5 flex-shrink-0" />
                    <span className="flex-1">{i.content}</span>
                  </div>
                ))}
              </div>
            )}

            {otherInsights.length > 0 && (
              <div className="space-y-2 border-t border-border-main/50 pt-3">
                <span className="block text-[8px] font-black uppercase tracking-widest text-text-muted">Repères & actions</span>
                <div className="max-h-28 space-y-2 overflow-y-auto pr-1">
                  {otherInsights.slice(0, 3).map(i => (
                    <div key={i.id} className="flex items-start gap-2 rounded-lg bg-primary/[0.03] p-2">
                      <Activity className="mt-0.5 flex-shrink-0 text-primary" size={12} />
                      <div className="min-w-0 leading-tight">
                        <span className="block text-[9px] font-bold text-primary">{i.title}</span>
                        <p className="mt-0.5 text-[9px] font-medium leading-normal text-text-muted">{i.content}</p>
                        <p className="mt-1 text-[8px] font-bold text-slate-400">{i.source_type === 'DETERMINISTIC' ? 'Source : dossier · règle déterministe' : 'Source : dossier'}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        <div className="mt-1 text-center text-[8px] font-bold uppercase tracking-widest text-text-muted">Données du dossier • règles déterministes</div>
      </motion.div>
    </AnimatePresence>,
    document.body,
  );
};
