import React, { useState } from 'react';
import { Play, CheckCircle2, AlertCircle, Loader2, Terminal } from 'lucide-react';
import { useOrthoStore } from '../stores/useOrthoStore';
import { runCephaloSmokeTest } from '../tests/SmokeTest';

export const SmokeTestUI: React.FC<{ P: any }> = ({ P }) => {
  const store = useOrthoStore();
  const [isRunning, setIsRunning] = useState(false);
  const [report, setReport] = useState<{ success: boolean; logs: string[] } | null>(null);

  const startTest = async () => {
    setIsRunning(true);
    const res = await runCephaloSmokeTest(store);
    setReport(res);
    setIsRunning(false);
  };

  return (
    <div className="mt-12 p-8 rounded-[2.5rem]" style={{ background: P.bgPanel, border: `1px solid ${P.border}` }}>
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-2xl" style={{ background: `${P.accent}15`, color: P.accent }}>
            <Terminal size={24} />
          </div>
          <div>
            <h3 className="text-xl font-black" style={{ color: P.text }}>Laboratoire de Tests</h3>
            <p className="text-sm opacity-60" style={{ color: P.text }}>Vérification automatisée de l'intégrité du workflow.</p>
          </div>
        </div>
        
        <button
          onClick={startTest}
          disabled={isRunning}
          className="flex items-center gap-2 px-6 py-3 rounded-xl font-black uppercase tracking-widest transition-all hover:scale-105 active:scale-95 disabled:opacity-50"
          style={{ background: P.accent, color: 'white', boxShadow: `0 8px 20px ${P.accent}40` }}
        >
          {isRunning ? <Loader2 size={18} className="animate-spin" /> : <Play size={18} />}
          Lancer le Smoke Test
        </button>
      </div>

      {report && (
        <div className="space-y-4 animate-in fade-in slide-in-from-top-4">
          <div className={`p-4 rounded-2xl flex items-center gap-3 border`} 
               style={{ 
                 background: report.success ? `${P.accentSuccess}10` : `${P.accentError}10`,
                 borderColor: report.success ? P.accentSuccess : P.accentError,
                 color: report.success ? P.accentSuccess : P.accentError
               }}>
            {report.success ? <CheckCircle2 size={20} /> : <AlertCircle size={20} />}
            <span className="font-bold">{report.success ? 'Architecture Validée : Prêt pour la production' : 'Échec du test : Anomalie détectée'}</span>
          </div>

          <div className="p-6 rounded-2xl font-mono text-[11px] space-y-1 max-h-60 overflow-y-auto" 
               style={{ background: P.bgInput, border: `1px solid ${P.border}`, color: P.textMuted }}>
            {report.logs.map((log, i) => (
              <div key={i} className={log.includes('❌') ? 'text-red-500' : log.includes('✅') ? 'text-emerald-500' : ''}>
                {log}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
