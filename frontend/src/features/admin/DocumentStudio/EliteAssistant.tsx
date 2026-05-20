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
  AlertCircle
} from 'lucide-react';
import { cn } from '../../../utils/cn';
import { useEliteStore } from '../../../stores/useEliteStore';
import { HouseWizard } from './HouseWizard';

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
  const {
    insights: storeInsights,
    intelligenceScore: storeScore,
    isLoading,
    isAssistantExpanded: isExpanded,
    setAssistantExpanded: setIsExpanded,
    lastFetchTime,
    analyzeAgendaDensity,
    setInsights,
    setIntelligenceScore
  } = useEliteStore();

  const isStale = lastFetchTime && (Date.now() - lastFetchTime > 86400000); // 24h

  const insights = propInsights.length > 0 ? propInsights : storeInsights;
  const intelligenceScore = propInsights.length > 0 ? propScore : storeScore;
  const hasFinancialRisk = insights.some(i => i.type === 'financial_risk');

  const [activeInsightIndex, setActiveInsightIndex] = useState(0);
  const [showStats, setShowStats] = useState(false);
  const [showHouseWizard, setShowHouseWizard] = useState(false);

  // Initialize Global Agenda Insight
  useEffect(() => {
    analyzeAgendaDensity();
  }, [analyzeAgendaDensity]);

  const currentInsight = insights[activeInsightIndex];

  const assistantContent = (
    <div className={cn(
      isEmbedded ? "relative flex flex-col items-center" : "fixed bottom-8 right-8 z-[500] flex flex-col items-end gap-4 pointer-events-none"
    )}>

      {/* 1. INSIGHT CARD */}
      <AnimatePresence>
        {isExpanded && !showHouseWizard && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: isEmbedded ? -20 : 20, filter: 'blur(10px)' }}
            animate={{ opacity: 1, scale: 1, y: 0, filter: 'blur(0px)' }}
            exit={{ opacity: 0, scale: 0.9, y: isEmbedded ? -20 : 20, filter: 'blur(10px)' }}
            className={cn(
              "pointer-events-auto w-72 bg-white/90 dark:bg-slate-900/80 backdrop-blur-3xl border border-slate-200/50 dark:border-white/10 rounded-[2rem] shadow-[0_20px_50px_rgba(0,0,0,0.1)] dark:shadow-[0_20px_50px_rgba(0,0,0,0.3)] overflow-hidden z-[10002]",
              isEmbedded ? "absolute top-20 right-2" : "mb-2"
            )}
          >
            {/* Header - More Compact */}
            <div className="px-5 py-3 bg-gradient-to-r from-primary/10 to-transparent flex items-center justify-between border-b border-slate-100 dark:border-white/5">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 bg-primary rounded-lg flex items-center justify-center shadow-lg shadow-primary/20">
                  <Brain size={14} className="text-white" />
                </div>
                <div>
                  <h4 className="text-[9px] font-black text-slate-800 dark:text-white uppercase tracking-widest">Ghost Brain</h4>
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
                        <span className="text-[10px] font-bold text-slate-600 dark:text-slate-300">Actes Maîtrisés</span>
                      </div>
                      <span className="text-[10px] font-black text-slate-900 dark:text-white">12</span>
                    </div>
                    <div className="p-2.5 bg-slate-50/50 dark:bg-white/5 rounded-xl border border-slate-100 dark:border-white/5 flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <Sparkles size={12} className="text-primary" />
                        <span className="text-[10px] font-bold text-slate-600 dark:text-slate-300">Protocoles</span>
                      </div>
                      {isLoading ? (
                        <span className="text-[6px] font-black animate-pulse opacity-50">MISE À JOUR...</span>
                      ) : isStale ? (
                        <span className="text-[6px] font-black text-amber-500 flex items-center gap-1">
                          <AlertCircle size={8} /> DONNÉES ANCIENNES
                        </span>
                      ) : (
                        <span className="text-[6px] font-black text-emerald-500 opacity-50 flex items-center gap-1">
                          <ShieldCheck size={8} /> TEMPS RÉEL
                        </span>
                      )}
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
                      "w-fit px-2.5 py-0.5 rounded-full text-[7px] font-black uppercase tracking-widest flex items-center gap-1.5",
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

                    <p className="text-[11px] font-semibold text-slate-700 dark:text-slate-200 leading-normal px-1">
                      {currentInsight.content}
                    </p>

                    {currentInsight.actionLabel && (
                      <button
                        onClick={currentInsight.onAction}
                        className="w-full mt-1 py-2.5 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-xl font-black text-[9px] uppercase tracking-widest hover:opacity-90 transition-all shadow-lg flex items-center justify-center gap-2 group"
                      >
                        {currentInsight.actionLabel}
                        <ChevronRight size={12} className="group-hover:translate-x-1 transition-transform" />
                      </button>
                    )}

                    <button
                      onClick={() => setShowHouseWizard(true)}
                      className="w-full mt-2 py-2.5 bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-600 hover:to-yellow-600 text-white rounded-xl font-black text-[9px] uppercase tracking-widest hover:opacity-90 transition-all shadow-lg flex items-center justify-center gap-1.5"
                    >
                      <Brain size={12} className="animate-pulse" />
                      Mode Expert
                    </button>
                  </motion.div>
                ) : (
                  <div className="text-center py-2 space-y-3">
                    <div className="w-10 h-10 bg-slate-100 dark:bg-white/5 rounded-xl mx-auto flex items-center justify-center text-slate-300 dark:text-white/20">
                      <Sparkles size={20} />
                    </div>
                    <p className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">
                      Audit Live Actif...
                    </p>
                    <button
                      onClick={() => setShowHouseWizard(true)}
                      className="w-full py-2 bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-600 hover:to-yellow-600 text-white rounded-xl font-black text-[9px] uppercase tracking-widest hover:opacity-90 transition-all shadow-lg flex items-center justify-center gap-1.5"
                    >
                      <Brain size={12} className="animate-pulse" />
                      Mode Expert
                    </button>
                  </div>
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

            <div
              onClick={() => setShowStats(true)}
              className="px-5 py-3 bg-slate-50 dark:bg-black/20 flex items-center justify-between border-t border-slate-100 dark:border-white/5 cursor-pointer hover:bg-slate-100 dark:hover:bg-black/30 transition-all"
            >
              <span className="text-[8px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest">IAmina Score</span>
              <div className="flex items-center gap-2">
                <div className="w-16 h-1 bg-slate-200 dark:bg-white/10 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${intelligenceScore}%` }}
                    className="h-full bg-primary"
                  />
                </div>
                <span className="text-[9px] font-black text-primary">{intelligenceScore}%</span>
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


      {/* 2. FLOATING TRIGGER (The Orb style button) */}
      <motion.button
        layout
        data-tour="elite-orb"
        {...(!isEmbedded ? {
          drag: true,
          dragConstraints: { left: -window.innerWidth + 100, right: 0, top: -window.innerHeight + 100, bottom: 0 },
          dragElastic: 0.1,
          whileDrag: { scale: 1.1, cursor: 'grabbing', boxShadow: hasFinancialRisk ? '0 0 30px rgba(245,158,11,0.6)' : '0 0 30px rgba(var(--primary-rgb), 0.4)' }
        } : {})}
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

  return assistantContent;
};
