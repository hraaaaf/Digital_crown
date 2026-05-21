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
    <div className={cn('bg-white/70 backdrop-blur-xl border border-white/50 p-6 rounded-2xl shadow-md') }>
      <h3 className="text-primary font-black text-lg mb-2" style={{ color: 'var(--primary)' }}>
        {patientName} – Résumé Clinique
      </h3>
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
  );
};
