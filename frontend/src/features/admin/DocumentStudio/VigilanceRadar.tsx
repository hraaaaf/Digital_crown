import React, { useState } from 'react';
import { ShieldCheck, AlertCircle, Sparkles, Clock, CheckCircle2, Check } from 'lucide-react';
import { cn } from '../../../utils/cn';
import { useEliteStore } from '../../../stores/useEliteStore';
import { useNavigate } from 'react-router-dom';
import { api } from '../../../services/api';

export const VigilanceRadar = () => {
  const { insights, lastPatientId } = useEliteStore();
  const navigate = useNavigate();
  const [resolvedIds, setResolvedIds] = useState<Record<string, boolean>>({});

  if (!insights || insights.length === 0) return null;

  const markResolved = async (insight: any) => {
    try {
      await api.post('/ai-feedback/feedback', {
        patient_id: lastPatientId || 0,
        insight_type: insight.type || 'suggestion',
        insight_content: insight.content,
        action: 'resolved'
      });
      setResolvedIds(prev => ({ ...prev, [insight.id]: true }));
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 rounded-[2rem] p-6 shadow-sm border border-slate-200 dark:border-white/10 mt-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
          <ShieldCheck className="text-slate-600 dark:text-slate-300" size={20} />
        </div>
        <div>
          <h3 className="text-sm font-black text-slate-800 dark:text-white uppercase tracking-widest">
            Radar de Vigilance
          </h3>
          <p className="text-xs text-slate-500">Analyses et alertes en temps réel</p>
        </div>
      </div>

      <div className="space-y-3">
        {insights.map((insight, idx) => (
          <div 
            key={insight.id || idx}
            className={cn(
              "p-4 rounded-2xl border flex items-start gap-4 transition-all hover:shadow-md",
              insight.type === 'safety' ? "bg-rose-50/50 border-rose-100 dark:bg-rose-900/10 dark:border-rose-900/30" :
              insight.type === 'financial_risk' ? "bg-amber-50/50 border-amber-100 dark:bg-amber-900/10 dark:border-amber-900/30" :
              insight.type === 'financial' ? "bg-emerald-50/50 border-emerald-100 dark:bg-emerald-900/10 dark:border-emerald-900/30" :
              "bg-slate-50/50 border-slate-100 dark:bg-white/5 dark:border-white/5"
            )}
          >
            <div className={cn(
              "w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5",
              insight.type === 'safety' ? "bg-rose-100 text-rose-600" :
              insight.type === 'financial_risk' ? "bg-amber-100 text-amber-600" :
              insight.type === 'financial' ? "bg-emerald-100 text-emerald-600" :
              insight.type === 'habit' ? "bg-blue-100 text-blue-600" :
              "bg-primary/10 text-primary"
            )}>
              {insight.type === 'safety' && <AlertCircle size={14} />}
              {insight.type === 'financial_risk' && <AlertCircle size={14} />}
              {insight.type === 'financial' && <CheckCircle2 size={14} />}
              {insight.type === 'habit' && <Clock size={14} />}
              {insight.type === 'suggestion' && <Sparkles size={14} />}
            </div>

            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200">
                  {insight.title}
                </h4>
                {insight.source_type === 'DETERMINISTIC' && (
                  <span className="px-1.5 py-0.5 rounded bg-slate-200/50 dark:bg-white/10 text-[8px] font-black tracking-widest text-slate-500">
                    VÉRIFIÉ
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                {insight.content}
              </p>
              
              {insight.actionLabel && !resolvedIds[insight.id] && (
                <div className="flex gap-2 mt-3">
                  <button
                    onClick={() => {
                      if (insight.onAction) {
                        insight.onAction();
                      } else if (lastPatientId) {
                        if (insight.id.startsWith('pano_detect') || insight.id.startsWith('rag_pano')) {
                          navigate(`/patients/${lastPatientId}?tab=radiology&radioTab=panoramic`);
                        } else if (insight.id.startsWith('financial_alert')) {
                          navigate(`/patients/${lastPatientId}?tab=admin`);
                        } else if (insight.id.startsWith('rag_history')) {
                          navigate(`/patients/${lastPatientId}?tab=archives`);
                        }
                      }
                    }}
                    className="px-3 py-1.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-[10px] font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-50 transition-colors shadow-sm"
                  >
                    {insight.actionLabel}
                  </button>
                  <button
                    onClick={() => markResolved(insight)}
                    className="px-3 py-1.5 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 rounded-lg text-[10px] font-bold hover:bg-emerald-100 transition-colors shadow-sm border border-emerald-200 dark:border-emerald-800 flex items-center gap-1"
                    title="Marquer comme résolu"
                  >
                    <Check size={12} /> Résolu
                  </button>
                </div>
              )}
              {resolvedIds[insight.id] && (
                <div className="mt-2 text-[10px] font-bold text-emerald-500 flex items-center gap-1">
                  <CheckCircle2 size={12} /> Traité
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
