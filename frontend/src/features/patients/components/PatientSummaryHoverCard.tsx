import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Calendar, 
  Clock, 
  Activity, 
  DollarSign, 
  ShieldAlert,
  Loader2
} from 'lucide-react';
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
    last_visit: {
      date: string;
      acte: string;
      days_ago: number;
    } | null;
    next_visit: {
      date: string;
      time: string;
      motif: string;
    } | null;
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
  intelligence_score: number;
  timestamp: string;
}

export const PatientSummaryHoverCard = ({
  patientId,
  patientName,
  patientDossier,
  triggerRect
}: PatientSummaryHoverCardProps) => {
  const [data, setData] = useState<IntelligenceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [coords, setCoords] = useState({ top: 0, left: 0 });

  useEffect(() => {
    if (!patientId) return;

    let isMounted = true;
    setLoading(true);
    setError(false);

    api.get(`/intelligence/patient/${patientId}`)
      .then(res => {
        if (isMounted) {
          setData(res.data);
          setLoading(false);
        }
      })
      .catch(err => {
        console.error("Error fetching patient hover intelligence:", err);
        if (isMounted) {
          setError(true);
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [patientId]);

  // Calcul du positionnement dynamique par rapport au rectangle déclencheur (triggerRect)
  useEffect(() => {
    if (!triggerRect) return;

    const padding = 12;
    const cardWidth = 380;
    const cardHeight = 350; // estimation
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    let top = triggerRect.top + window.scrollY;
    let left = triggerRect.right + padding + window.scrollX;

    // Si pas assez de place à droite, on l'affiche à gauche
    if (left + cardWidth > viewportWidth + window.scrollX) {
      left = triggerRect.left - cardWidth - padding + window.scrollX;
    }

    // Si toujours pas assez de place à gauche (mobile/petit écran), on centre verticalement et horizontalement au-dessus/en-dessous
    if (left < window.scrollX) {
      left = Math.max(window.scrollX + padding, (viewportWidth - cardWidth) / 2 + window.scrollX);
      top = triggerRect.bottom + padding + window.scrollY;
    }

    // Ajustement de la hauteur par rapport aux limites de l'écran
    if (top + cardHeight > viewportHeight + window.scrollY) {
      top = Math.max(window.scrollY + padding, viewportHeight + window.scrollY - cardHeight - padding);
    }

    setCoords({ top, left });
  }, [triggerRect]);

  if (!triggerRect) return null;

  const cardContent = (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 10 }}
        transition={{ duration: 0.2, ease: 'easeOut' }}
        style={{
          position: 'absolute',
          top: coords.top,
          left: coords.left,
          width: 380,
          zIndex: 99999,
        }}
        className="bg-card-bg/95 dark:bg-[#0f172a]/95 backdrop-blur-2xl border border-border-main/80 dark:border-white/10 rounded-[2rem] p-6 shadow-[0_20px_50px_rgba(0,0,0,0.15)] pointer-events-none select-none flex flex-col gap-4 font-sans text-text-main"
      >
        {/* Header : Patient & Dossier */}
        <div className="flex items-center justify-between border-b border-border-main/50 pb-3">
          <div>
            <h4 className="font-black text-primary text-base leading-tight tracking-tight uppercase">
              {patientName}
            </h4>
            <span className="text-[10px] font-bold text-text-muted font-mono tracking-wider">
              {patientDossier}
            </span>
          </div>
          
          {/* Score circulaire intelligent */}
          {!loading && !error && data && (
            <div className="flex items-center gap-2">
              <div className="relative w-10 h-10 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                  <path
                    className="text-border-main/30"
                    strokeWidth="3.5"
                    stroke="currentColor"
                    fill="none"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                  <motion.path
                    initial={{ strokeDasharray: "0, 100" }}
                    animate={{ strokeDasharray: `${data.intelligence_score}, 100` }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className="text-primary"
                    strokeWidth="3.5"
                    strokeDasharray="0, 100"
                    strokeLinecap="round"
                    stroke="currentColor"
                    fill="none"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  />
                </svg>
                <div className="absolute font-black text-[11px] text-primary">
                  {data.intelligence_score}
                </div>
              </div>
            </div>
          )}
        </div>

        {loading ? (
          <div className="py-8 flex flex-col items-center justify-center gap-2">
            <Loader2 className="animate-spin text-primary" size={24} />
            <span className="text-[9px] font-black uppercase text-text-muted tracking-widest">
              Analyse clinique...
            </span>
          </div>
        ) : error || !data ? (
          <div className="py-4 text-center text-xs text-text-muted italic">
            Impossible de charger la synthèse clinique.
          </div>
        ) : (
          <div className="space-y-4 text-xs">
            {/* ALERTES CRITIQUES / MÉDICALES */}
            {data.patient_summary.alerts && data.patient_summary.alerts.length > 0 && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 flex gap-2.5 items-start animate-pulse">
                <ShieldAlert className="text-red-500 flex-shrink-0 mt-0.5" size={16} />
                <div>
                  <h5 className="font-black text-red-500 text-[10px] uppercase tracking-wider">Vigilance Médicale</h5>
                  <p className="text-[10px] font-bold text-red-400 mt-1 leading-normal">
                    {data.patient_summary.alerts.join(', ')}
                  </p>
                </div>
              </div>
            )}

            {/* SYNTHÈSE CLINIQUE */}
            <div className="space-y-2">
              <span className="text-[9px] font-black text-text-muted uppercase tracking-widest block">
                Résumé Clinique
              </span>
              <p className="text-[11px] font-medium leading-relaxed bg-primary/5 rounded-xl p-2.5 border border-primary/5">
                {data.patient_summary.clinical_summary || "Aucune information clinique disponible."}
              </p>
            </div>

            {/* DÉTAILS VISITES */}
            <div className="grid grid-cols-2 gap-3">
              {/* Dernière Visite */}
              <div className="bg-card-bg border border-border-main p-2.5 rounded-xl flex items-start gap-2.5">
                <Clock className="text-blue-500 flex-shrink-0 mt-0.5" size={14} />
                <div>
                  <span className="text-[8px] font-black text-text-muted uppercase tracking-widest block">Dernière Visite</span>
                  {data.patient_summary.last_visit ? (
                    <>
                      <span className="font-bold text-[10px] leading-tight block truncate mt-0.5">
                        {data.patient_summary.last_visit.acte}
                      </span>
                      <span className="text-[9px] font-mono text-text-muted">
                        il y a {data.patient_summary.last_visit.days_ago} jours
                      </span>
                    </>
                  ) : (
                    <span className="text-[10px] font-medium text-text-muted block mt-0.5">—</span>
                  )}
                </div>
              </div>

              {/* Prochain RDV */}
              <div className="bg-card-bg border border-border-main p-2.5 rounded-xl flex items-start gap-2.5">
                <Calendar className="text-emerald-500 flex-shrink-0 mt-0.5" size={14} />
                <div>
                  <span className="text-[8px] font-black text-text-muted uppercase tracking-widest block">Prochain RDV</span>
                  {data.patient_summary.next_visit ? (
                    <>
                      <span className="font-bold text-[10px] leading-tight block truncate mt-0.5">
                        {data.patient_summary.next_visit.motif || "Soin"}
                      </span>
                      <span className="text-[9px] font-mono text-text-muted block mt-0.5">
                        {new Date(data.patient_summary.next_visit.date).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })} à {data.patient_summary.next_visit.time}
                      </span>
                    </>
                  ) : (
                    <span className="text-[10px] font-medium text-text-muted block mt-0.5">—</span>
                  )}
                </div>
              </div>
            </div>

            {/* DÉCISIONS COMPTABLES ET FINANCIÈRES */}
            {data.insights.some(i => i.type === 'financial_risk' || i.type === 'financial') && (
              <div className="border-t border-border-main/50 pt-3">
                {data.insights
                  .filter(i => i.type === 'financial_risk' || i.type === 'financial')
                  .map(i => (
                    <div 
                      key={i.id} 
                      className={cn(
                        "flex items-center gap-2 px-3 py-2 rounded-xl border text-[10px]",
                        i.type === 'financial_risk'
                          ? "bg-amber-500/10 border-amber-500/20 text-amber-500 font-black animate-pulse"
                          : "bg-primary/5 border-primary/10 text-primary font-bold"
                      )}
                    >
                      <DollarSign size={14} />
                      <span className="flex-1">{i.content}</span>
                    </div>
                  ))}
              </div>
            )}

            {/* AUTRES INSIGHTS PRÉDICTIFS */}
            {data.insights.some(i => i.type !== 'financial_risk' && i.type !== 'financial' && i.type !== 'safety') && (
              <div className="border-t border-border-main/50 pt-3 space-y-2">
                <span className="text-[8px] font-black text-text-muted uppercase tracking-widest block">
                  Alertes IA & Suggestion
                </span>
                <div className="max-h-20 overflow-y-auto pr-1 space-y-1.5">
                  {data.insights
                    .filter(i => i.type !== 'financial_risk' && i.type !== 'financial' && i.type !== 'safety')
                    .slice(0, 2)
                    .map(i => (
                      <div key={i.id} className="flex gap-2 items-start p-1.5 rounded-lg hover:bg-primary/5 transition-all">
                        <Activity className="text-primary flex-shrink-0 mt-0.5" size={12} />
                        <div className="leading-tight">
                          <span className="font-bold text-[9px] block text-primary">{i.title}</span>
                          <p className="text-[9px] font-medium text-text-muted mt-0.5">{i.content}</p>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Footer info */}
        <div className="text-[8px] font-bold text-text-muted text-center uppercase tracking-widest mt-1">
          Assistant Virtuel ODF • Temps réel
        </div>
      </motion.div>
    </AnimatePresence>
  );

  return createPortal(cardContent, document.body);
};
