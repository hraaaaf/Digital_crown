import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { cn } from '../../utils/cn';

interface SummaryData {
  last_visit: { date: string; acte: string; days_ago: number };
  clinical_summary: string;
  alerts: string[];
  risk_level: 'low' | 'moderate' | 'high';
}

export const FlashSummary: React.FC<{ patientId: number; patientName: string }> = ({ patientId, patientName }) => {
  const [data, setData] = useState<SummaryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const fetchSummary = async () => {
      setError(false);
      try {
        const resp = await api.get(`/patients/${patientId}/ai-summary`);
        setData(resp.data);
      } catch (e) {
        console.error('❌ Erreur fetch flash summary', e);
        setError(true);
      } finally {
        setLoading(false);
      }
    };
    fetchSummary();
  }, [patientId]);

  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const mainEl = document.querySelector('main');
    if (!mainEl) return;
    
    const handleScroll = (e: Event) => {
      const target = e.target as HTMLElement;
      setIsScrolled(target.scrollTop > 50);
    };
    
    mainEl.addEventListener('scroll', handleScroll);
    return () => mainEl.removeEventListener('scroll', handleScroll);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <span className="animate-pulse">Chargement du résumé IA...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 px-4 py-3 bg-amber-50 border border-amber-200 rounded-xl text-sm text-amber-700 font-medium">
        <span>⚠️ Résumé clinique indisponible — vérifiez la connexion.</span>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className={cn(
      'bg-white/70 backdrop-blur-xl border border-white/50 rounded-2xl shadow-md transition-all duration-500 overflow-hidden sticky top-4 z-40',
      isScrolled ? 'p-3 flex items-center justify-between gap-4 max-w-4xl mx-auto cursor-pointer hover:bg-white' : 'p-6'
    )}
    onClick={() => isScrolled && document.querySelector('main')?.scrollTo({ top: 0, behavior: 'smooth' })}
    >
      <div className={cn("flex items-center gap-3", !isScrolled && "mb-2")}>
        <h3 className={cn("font-black text-primary transition-all", isScrolled ? "text-sm" : "text-lg")} style={{ color: 'var(--primary)' }}>
          {patientName} <span className="font-medium opacity-60">— Résumé</span>
        </h3>
        {isScrolled && (
          <div className="flex items-center gap-4 text-xs">
            <span className="text-slate-500"><span className="font-black">Dernière visite:</span> {data.last_visit ? data.last_visit.acte : 'Aucune'}</span>
            <span style={{ color: data.risk_level === 'high' ? 'var(--primary)' : 'inherit' }} className="font-black">Risque: {data.risk_level.toUpperCase()}</span>
          </div>
        )}
      </div>

      {!isScrolled && (
        <div className="animate-in fade-in duration-500">
          <p className="text-sm mb-2">
            <span className="font-medium">Dernière visite :</span> {data.last_visit ? `${data.last_visit.acte} (${data.last_visit.days_ago} jours)` : 'Aucune visite enregistrée'}
          </p>
          <p className="text-sm mb-2">
            <span className="font-medium">Synthèse :</span> {data.clinical_summary}
          </p>
          {data.alerts.length > 0 && (
            <ul className="list-disc list-inside text-sm text-amber-600">
              {data.alerts.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          )}
          <div className="mt-2 text-xs font-bold" style={{ color: data.risk_level === 'high' ? 'var(--primary)' : 'inherit' }}>
            Niveau de risque : {data.risk_level.toUpperCase()}
          </div>
        </div>
      )}
    </div>
  );
};
