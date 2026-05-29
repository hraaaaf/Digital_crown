import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain,
  Sparkles,
  ChevronRight,
  X,
  Zap,
  ShieldCheck,
  Clock,
  ChevronLeft,
  AlertCircle,
  ThumbsUp,
  ThumbsDown,
  CalendarDays,
} from 'lucide-react';
import { cn } from '../../../utils/cn';
import { useEliteStore } from '../../../stores/useEliteStore';
import { HouseWizard } from './HouseWizard';
import { api } from '../../../services/api';
import toast from 'react-hot-toast';
import { PriceBrain } from '../../../components/odontogram/PriceBrain';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../../stores/useAuthStore';

export interface Insight {
  id: string;
  type: 'suggestion' | 'safety' | 'habit' | 'financial_risk' | 'financial';
  title: string;
  content: string;
  actionLabel?: string;
  onAction?: () => void;
  source_type?: 'DETERMINISTIC' | 'HEURISTIC';
  trust_level?: number;
}

interface EliteAssistantProps {
  insights?: Insight[];
  intelligenceScore?: number; // 0 to 100
  isEmbedded?: boolean;
}

export const EliteAssistant: React.FC<EliteAssistantProps> = ({
  insights: propInsights = [],
  intelligenceScore: propScore = 85,
  isEmbedded = false
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    insights: storeInsights,
    intelligenceScore: storeScore,
    isLoading,
    isAssistantExpanded: isExpanded,
    setAssistantExpanded: setIsExpanded,
    lastFetchTime,
    lastPatientId,
    setInsights,
    setIntelligenceScore
  } = useEliteStore();

  const { user } = useAuthStore();
  const employerId = user?.employer_id || user?.id;

  // Real-time WebSocket connection for proactive insights (Ghost Brain V2)
  useEffect(() => {
    if (!employerId || !isEmbedded) return;
    
    let ws: WebSocket;
    let reconnectTimer: NodeJS.Timeout;

    const connectWS = () => {
      const wsUrl = `${api.defaults.baseURL?.replace(/^http/, 'ws') || 'ws://localhost:8000'}/api/ws/ghost-insights/${employerId}`;
      ws = new WebSocket(wsUrl);

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.insights && Array.isArray(data.insights)) {
            // Transform realtime insights into EliteAssistant format
            const wsInsights: Insight[] = data.insights.map((item: any) => ({
              id: `ws-${item.id}`,
              type: item.insight_type === 'FINANCIAL' ? 'financial' : 'suggestion',
              title: item.insight_type || 'Ghost Insight',
              content: item.content,
              source_type: 'HEURISTIC'
            }));
            
            // Add new WS insights at the beginning, avoiding duplicates
            const currentInsights = useEliteStore.getState().insights;
            const newInsights = wsInsights.filter(wsI => !currentInsights.some(cI => cI.id === wsI.id));
            if (newInsights.length > 0) {
              setInsights([...newInsights, ...currentInsights]);
            }
          }
        } catch (err) {
          // parse error
        }
      };

      ws.onclose = () => {
        reconnectTimer = setTimeout(connectWS, 5000);
      };
    };

    connectWS();

    return () => {
      clearTimeout(reconnectTimer);
      if (ws) ws.close();
    };
  }, [employerId, isEmbedded, setInsights]);

  // eslint-disable-next-line react-hooks/purity
  const isStale = lastFetchTime && (Date.now() - lastFetchTime > 86400000); // 24h

  const rawInsights = propInsights.length > 0 ? propInsights : storeInsights;
  
  // OPTION 1: Filter insights based on current tab to avoid intrusive UX
  const searchParams = new URLSearchParams(location.search);
  const activeTab = searchParams.get('tab');
  const insights = rawInsights.filter(insight => {
    const isRadiologyAlert = insight.id.startsWith('pano_detect') || insight.id.startsWith('rag_pano');
    if (isRadiologyAlert && (activeTab === 'admin' || activeTab === 'archives')) {
      return false; // Hide radiology alerts when in Documents or Archives tabs
    }
    return true;
  });

  const intelligenceScore = propInsights.length > 0 ? propScore : storeScore;
  const hasFinancialRisk = insights.some(i => i.type === 'financial_risk');

  const [activeInsightIndex, setActiveInsightIndex] = useState(0);
  const [showStats, setShowStats] = useState(false);
  const [showHouseWizard, setShowHouseWizard] = useState(false);
  const [feedbackSent, setFeedbackSent] = useState<Record<string, boolean>>({});

  type BriefingPatient = { patient_id: number; nom: string; prenom: string; appointment_time: string; solde_attente: number };
  type BriefingData = { date: string; total_patients: number; total_outstanding: number; patients: BriefingPatient[] };
  const [briefingData, setBriefingData] = useState<BriefingData | null>(null);

  type UpcomingPrescription = { appointment_date: string; motif: string; days_until: number; prescription_suggestion: any };
  const [upcomingPrescription, setUpcomingPrescription] = useState<UpcomingPrescription | null>(null);

  const submitFeedback = async (insight: Insight, action: 'accept' | 'reject') => {
    if (!lastPatientId || feedbackSent[insight.id]) return;
    try {
      await api.post('/ai/feedback', {
        patient_id: lastPatientId,
        insight_type: insight.type,
        insight_content: insight.content,
        action,
      });
      setFeedbackSent(prev => ({ ...prev, [insight.id]: true }));
      toast.success('Retour enregistré — merci !', { duration: 1500 });
    } catch {
      // best-effort, no blocking toast
    }
  };

  useEffect(() => {
    // --- Algorithmic Daily Briefing (Backend Driven) ---
    api.get('/intelligence/briefing-today').then(res => {
      setBriefingData(res.data);
    }).catch(() => {});
  }, []);

  // --- Algorithmic Upcoming Prescription (Backend Driven) ---
  useEffect(() => {
    if (!lastPatientId) { setUpcomingPrescription(null); return; }
    
    api.get(`/intelligence/patient/${lastPatientId}/upcoming-prescription`).then(res => {
      const suggestion = res.data;
      if (suggestion && suggestion.motif && (suggestion.motif.toLowerCase().includes('extraction') || suggestion.motif.toLowerCase().includes('implant'))) {
        setUpcomingPrescription({
          appointment_date: suggestion.appointment_date || 'Prochain RDV',
          motif: suggestion.motif,
          days_until: suggestion.days_until || 0,
          prescription_suggestion: {}
        });
      } else {
        setUpcomingPrescription(null);
      }
    }).catch(() => setUpcomingPrescription(null));
  }, [lastPatientId]);

  const currentInsight = insights[activeInsightIndex];

  const assistantContent = (
    <div className="relative flex flex-col items-center">

      {/* 1. INSIGHT CARD */}
      <AnimatePresence>
        {isExpanded && !showHouseWizard && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: -20, filter: 'blur(10px)' }}
            animate={{ opacity: 1, scale: 1, y: 0, filter: 'blur(0px)' }}
            exit={{ opacity: 0, scale: 0.9, y: -20, filter: 'blur(10px)' }}
            className={cn(
              "pointer-events-auto w-72 bg-white/90 dark:bg-slate-900/80 backdrop-blur-3xl border border-slate-200/50 dark:border-white/10 rounded-[2rem] shadow-[0_20px_50px_rgba(0,0,0,0.1)] dark:shadow-[0_20px_50px_rgba(0,0,0,0.3)] overflow-hidden z-[10002]",
              "absolute top-12 right-0 mt-2"
            )}
          >
            {/* Header - More Compact */}
            <div className="px-5 py-3 bg-gradient-to-r from-primary/10 to-transparent flex items-center justify-between border-b border-slate-100 dark:border-white/5">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 bg-primary rounded-lg flex items-center justify-center shadow-lg shadow-primary/20">
                  <Brain size={14} className="text-white" />
                </div>
                <div>
                  <h4 className="text-[10px] font-black text-slate-800 dark:text-white uppercase tracking-widest">Ghost Brain</h4>
                </div>
              </div>
              <button
                onClick={() => setIsExpanded(false)}
                className="p-1.5 text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
              >
                <X size={14} />
              </button>
            </div>

            {/* Content - Optimized Spacing */}
            <div className="p-5 space-y-3">
              {showStats ? (
                <motion.div
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="space-y-3"
                >
                  <div className="flex items-center justify-between px-1">
                    <h5 className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Intelligence Stats</h5>
                    <div className="px-1.5 py-0.5 bg-primary/20 rounded-full text-[8px] font-black text-primary">
                      {intelligenceScore}%
                    </div>
                  </div>

                    <div className="space-y-1.5">
                      <div className="p-2.5 bg-slate-50/50 dark:bg-white/5 rounded-xl border border-slate-100 dark:border-white/5 flex items-center justify-between">
                        <div className="flex items-center gap-2.5">
                          <Zap size={12} className="text-amber-500" />
                          <span className="text-[11px] font-bold text-slate-600 dark:text-slate-300">Actes Maîtrisés</span>
                        </div>
                        <span className="text-[11px] font-black text-slate-900 dark:text-white">
                          {Object.keys(PriceBrain.getHistory()).length}
                        </span>
                      </div>
                    <div className="p-2.5 bg-slate-50/50 dark:bg-white/5 rounded-xl border border-slate-100 dark:border-white/5 flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <Sparkles size={12} className="text-primary" />
                        <span className="text-[11px] font-bold text-slate-600 dark:text-slate-300">Protocoles & Règles</span>
                      </div>
                      <span className="text-[11px] font-black text-emerald-500 flex items-center gap-1">
                        <ShieldCheck size={10} /> 14 Actifs
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={() => setShowStats(false)}
                    className="w-full py-2 bg-slate-100 dark:bg-white/5 hover:bg-slate-200 dark:hover:bg-white/10 text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white rounded-lg text-[8px] font-black uppercase tracking-widest transition-all"
                  >
                    Retour Suggestions
                  </button>
                </motion.div>
              ) : (
                insights.length > 0 ? (
                  <motion.div
                    key={activeInsightIndex}
                    initial={{ opacity: 0, x: 5 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="space-y-2.5"
                  >
                    <div className={cn(
                      "w-fit px-2.5 py-0.5 rounded-full text-[9px] font-black uppercase tracking-widest flex items-center gap-1.5",
                      currentInsight.type === 'safety' ? "bg-rose-500/10 text-rose-600 border border-rose-500/20" :
                        currentInsight.type === 'financial_risk' ? "bg-amber-500/10 text-amber-600 border border-amber-500/20 animate-pulse" :
                          currentInsight.type === 'financial' ? "bg-emerald-500/10 text-emerald-600 border border-emerald-500/20" :
                            currentInsight.type === 'habit' ? "bg-amber-500/10 text-amber-600 border border-amber-500/20" :
                              "bg-primary/10 text-primary border border-primary/20"
                    )}>
                      {currentInsight.type === 'safety' && <ShieldCheck size={9} />}
                      {currentInsight.type === 'financial_risk' && <AlertCircle size={9} />}
                      {currentInsight.type === 'financial' && <Sparkles size={9} />}
                      {currentInsight.type === 'habit' && <Clock size={9} />}
                      {currentInsight.type === 'suggestion' && <Sparkles size={9} />}
                      {currentInsight.title}
                      {currentInsight.source_type && (
                        <span className={cn(
                          "ml-1.5 px-1.5 py-0.5 rounded-sm text-[6px] font-black tracking-tighter flex items-center gap-1",
                          currentInsight.source_type === 'DETERMINISTIC'
                            ? "bg-emerald-500/20 text-emerald-600"
                            : "bg-blue-500/20 text-blue-600"
                        )}>
                          {currentInsight.source_type === 'DETERMINISTIC' ? '🛡️ VÉRIFIÉ' : '🤖 IA'}
                        </span>
                      )}
                    </div>

                    <p className="text-[12px] font-semibold text-slate-700 dark:text-slate-200 leading-normal px-1">
                      {currentInsight.content}
                    </p>

                    {currentInsight.actionLabel && (
                      <button
                        onClick={() => {
                          if (currentInsight.onAction) {
                            currentInsight.onAction();
                          } else {
                            // Fallback for backend insights missing an explicit onAction
                            const idStr = currentInsight.id || '';
                            const actionLabel = currentInsight.actionLabel || '';
                            
                            if (idStr.startsWith('pano_detect') || idStr.startsWith('rag_pano')) {
                              navigate(`/patients/${lastPatientId}?tab=radiology&radioTab=panoramic`);
                            } else if (idStr.startsWith('financial_alert')) {
                              navigate(`/patients/${lastPatientId}?tab=admin`);
                            } else if (idStr.startsWith('rag_history')) {
                              navigate(`/patients/${lastPatientId}?tab=archives`);
                            } else if (idStr.startsWith('trigger_')) {
                              if (actionLabel.startsWith('/')) {
                                let path = actionLabel;
                                if (path.includes('/documents/new')) {
                                  path = `/patients/${lastPatientId}?tab=admin`;
                                }
                                navigate(path);
                              } else {
                                const actionLower = actionLabel.toLowerCase();
                                if (actionLower.includes('dossier') || actionLower.includes('compléter')) {
                                  navigate(`/patients/${lastPatientId}/edit`);
                                } else if (actionLower.includes('agenda') || actionLower.includes('planifier') || actionLower.includes('rdv') || actionLower.includes('créneau') || actionLower.includes('reprogrammer') || actionLower.includes('avancer')) {
                                  navigate(`/agenda?patientId=${lastPatientId}`);
                                } else if (actionLower.includes('appeler') || actionLower.includes('rappeler') || actionLower.includes('contacter') || actionLower.includes('whatsapp')) {
                                  navigate(`/patients/${lastPatientId}`);
                                } else if (actionLower.includes('paiement') || actionLower.includes('solde') || actionLower.includes('relancer')) {
                                  navigate(`/patients/${lastPatientId}?tab=admin`);
                                } else if (actionLower.includes('traitement') || actionLower.includes('progression')) {
                                  navigate(`/patients/${lastPatientId}?tab=clinical`);
                                } else {
                                  navigate(`/patients/${lastPatientId}`);
                                }
                              }
                            }
                            setIsExpanded(false);
                          }
                        }}
                        className="w-full mt-1 py-2.5 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-xl font-black text-[10px] uppercase tracking-widest hover:opacity-90 transition-all shadow-lg flex items-center justify-center gap-2 group"
                      >
                        {currentInsight.actionLabel}
                        <ChevronRight size={12} className="group-hover:translate-x-1 transition-transform" />
                      </button>
                    )}

                    {/* Feedback loop — practitioner reaction */}
                    {!feedbackSent[currentInsight.id] ? (
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest flex-1">Utile ?</span>
                        <button
                          onClick={() => submitFeedback(currentInsight, 'accept')}
                          className="p-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-500 transition-all"
                          title="Oui, pertinent"
                        >
                          <ThumbsUp size={12} />
                        </button>
                        <button
                          onClick={() => submitFeedback(currentInsight, 'reject')}
                          className="p-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-400 transition-all"
                          title="Non, pas pertinent"
                        >
                          <ThumbsDown size={12} />
                        </button>
                      </div>
                    ) : (
                      <p className="text-[9px] font-bold text-emerald-500 text-center mt-1">✓ Retour enregistré</p>
                    )}

                    <button
                      onClick={() => setShowHouseWizard(true)}
                      className="w-full mt-2 py-2.5 bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-600 hover:to-yellow-600 text-white rounded-xl font-black text-[10px] uppercase tracking-widest hover:opacity-90 transition-all shadow-lg flex items-center justify-center gap-1.5"
                    >
                      <Brain size={14} className="animate-pulse" />
                      Mode Expert
                    </button>
                  </motion.div>
                ) : (
                  !lastPatientId && briefingData && briefingData.total_patients > 0 ? (
                    <motion.div initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} className="space-y-2.5">
                      <div className="flex items-center gap-2">
                        <CalendarDays size={14} className="text-primary" />
                        <span className="text-[10px] font-black text-slate-700 dark:text-white uppercase tracking-widest">Briefing du Jour</span>
                        <span className="ml-auto text-[9px] font-black text-slate-400">{briefingData.date}</span>
                      </div>
                      <div className="flex gap-2">
                        <div className="flex-1 p-2 bg-primary/5 rounded-xl border border-primary/10 text-center">
                          <div className="text-base font-black text-primary">{briefingData.total_patients}</div>
                          <div className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">Patients</div>
                        </div>
                        <div className="flex-1 p-2 bg-amber-500/5 rounded-xl border border-amber-500/10 text-center">
                          <div className="text-base font-black text-amber-500">{briefingData.total_outstanding.toLocaleString()}</div>
                          <div className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">MAD impayés</div>
                        </div>
                      </div>
                      {briefingData.patients.filter(p => p.solde_attente > 0).slice(0, 3).map(p => (
                        <div 
                          key={p.patient_id} 
                          onClick={() => {
                            navigate(`/patients/${p.patient_id}?tab=accounting`);
                            setIsExpanded(false);
                          }}
                          className="flex items-center justify-between px-2 py-1.5 bg-slate-50 dark:bg-white/5 rounded-lg border border-slate-100 dark:border-white/5 cursor-pointer hover:bg-slate-100 dark:hover:bg-white/10 transition-colors group"
                        >
                          <div>
                            <span className="text-[10px] font-bold text-slate-700 dark:text-slate-200 group-hover:text-primary transition-colors">{p.prenom} {p.nom}</span>
                            <div className="text-[9px] text-slate-400">{p.appointment_time}</div>
                          </div>
                          <span className="text-[10px] font-black text-amber-500">{p.solde_attente.toLocaleString()} MAD</span>
                        </div>
                      ))}
                    </motion.div>
                  ) : (
                  <div className="text-center py-2 space-y-3">
                    <div className="w-10 h-10 bg-slate-100 dark:bg-white/5 rounded-xl mx-auto flex items-center justify-center text-slate-300 dark:text-white/20">
                      <Sparkles size={20} />
                    </div>
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                      Audit Live Actif...
                    </p>
                    <button
                      onClick={() => setShowHouseWizard(true)}
                      className="w-full py-2 bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-600 hover:to-yellow-600 text-white rounded-xl font-black text-[10px] uppercase tracking-widest hover:opacity-90 transition-all shadow-lg flex items-center justify-center gap-1.5"
                    >
                      <Brain size={14} className="animate-pulse" />
                      Mode Expert
                    </button>
                  </div>
                  )
                )
              )}
            </div>

            {/* Navigation & Footer - Slimmer */}
            {!showStats && insights.length > 1 && (
              <div className="px-5 py-2 bg-slate-50 dark:bg-white/5 flex items-center justify-between">
                <div className="flex gap-1">
                  {insights.map((_, i) => (
                    <div
                      key={i}
                      className={cn(
                        "w-1 h-1 rounded-full transition-all",
                        i === activeInsightIndex ? "w-3 bg-primary" : "bg-slate-200 dark:bg-white/10"
                      )}
                    />
                  ))}
                </div>
                <div className="flex gap-1.5">
                  <button
                    onClick={() => setActiveInsightIndex(prev => Math.max(0, prev - 1))}
                    disabled={activeInsightIndex === 0}
                    className="p-1 text-slate-400 dark:text-white/40 hover:text-slate-900 dark:hover:text-white disabled:opacity-20 transition-all"
                  >
                    <ChevronLeft size={14} />
                  </button>
                  <button
                    onClick={() => setActiveInsightIndex(prev => Math.min(insights.length - 1, prev + 1))}
                    disabled={activeInsightIndex === insights.length - 1}
                    className="p-1 text-slate-400 dark:text-white/40 hover:text-slate-900 dark:hover:text-white disabled:opacity-20 transition-all"
                  >
                    <ChevronRight size={14} />
                  </button>
                </div>
              </div>
            )}

            {/* D4 — Ordonnance Anticipée */}
            {upcomingPrescription && (
              <div className="mx-5 mb-3 p-3 bg-violet-50 dark:bg-violet-900/20 border border-violet-200 dark:border-violet-700/30 rounded-xl">
                <div className="flex items-start gap-2">
                  <CalendarDays size={16} className="text-violet-500 mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-[11px] font-black text-violet-700 dark:text-violet-300 uppercase tracking-wider">
                      RDV dans {upcomingPrescription.days_until}j — {upcomingPrescription.appointment_date}
                    </p>
                    {upcomingPrescription.motif && (
                      <p className="text-[11px] text-violet-600 dark:text-violet-400 font-medium truncate">{upcomingPrescription.motif}</p>
                    )}
                    <button
                      onClick={() => {
                        if (lastPatientId) {
                          navigate(`/patients/${lastPatientId}?tab=documents`);
                          setTimeout(() => {
                            window.dispatchEvent(new CustomEvent('perio-create-prescription'));
                          }, 500);
                        }
                        setIsExpanded(false);
                      }}
                      className="mt-1.5 px-3 py-1.5 bg-violet-500 text-white text-[10px] font-black uppercase tracking-widest rounded-lg hover:bg-violet-600 transition-colors"
                    >
                      Préparer l'ordonnance
                    </button>
                  </div>
                </div>
              </div>
            )}

            <div
              onClick={() => setShowStats(true)}
              className="px-5 py-3 bg-slate-50 dark:bg-black/20 flex items-center justify-between border-t border-slate-100 dark:border-white/5 cursor-pointer hover:bg-slate-100 dark:hover:bg-black/30 transition-all"
            >
              <span className="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest">IAmina Score</span>
              <div className="flex items-center gap-2">
                <div className="w-16 h-1.5 bg-slate-200 dark:bg-white/10 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${intelligenceScore}%` }}
                    className="h-full bg-primary"
                  />
                </div>
                <span className="text-[10px] font-black text-primary">{intelligenceScore}%</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 2. HOUSEWIZARD DIALOG OVERLAY */}
      <AnimatePresence>
        {showHouseWizard && (
          <HouseWizard
            onClose={() => setShowHouseWizard(false)}
            onApplyDiagnostic={(diag) => {
              const newInsight: Insight = {
                id: `house-diag-${Date.now()}`,
                type: diag.warnings.length > 0 ? 'safety' : 'suggestion',
                title: diag.title,
                content: `${diag.description} Recommandations : ${diag.protocol.join(', ')}`,
                source_type: 'DETERMINISTIC'
              };
              setInsights([newInsight, ...insights]);
              setIntelligenceScore(100);
              setShowHouseWizard(false);
            }}
          />
        )}
      </AnimatePresence>

      {/* TRIGGER (The Orb style button) */}
      <motion.button
        layout
        data-tour="elite-orb"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          "p-2.5 rounded-xl transition-all relative group flex items-center justify-center",
          isExpanded
            ? "bg-primary/10 text-primary"
            : hasFinancialRisk
              ? "bg-gradient-to-r from-amber-500 to-yellow-500 text-white shadow-[0_0_20px_rgba(245,158,11,0.5)] border border-amber-400"
              : "text-slate-400 hover:text-primary hover:bg-white/80 dark:hover:bg-slate-800"
        )}
      >
        {isExpanded ? (
          <X size={20} className="relative z-10" />
        ) : (
          <div className="relative z-10">
            {insights.length > 0 && (
              <span className={cn(
                "absolute -top-1.5 -right-1.5 w-4 h-4 text-white text-[8px] font-black flex items-center justify-center rounded-full border-2 border-white dark:border-slate-800 animate-bounce",
                hasFinancialRisk ? "bg-rose-600" : "bg-primary"
              )}>
                {insights.length}
              </span>
            )}
            <Brain size={20} className="group-hover:scale-110 transition-transform" />

            {/* Status Pulse */}
            <div className={cn(
              "absolute -inset-1 rounded-full animate-ping opacity-40",
              hasFinancialRisk ? "bg-amber-500/40" : "bg-primary/20"
            )} />
          </div>
        )}
      </motion.button>
    </div>
  );

  if (!isEmbedded) return null;

  return assistantContent;
};
