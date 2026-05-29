/* eslint-disable react-refresh/only-export-components */
import React from 'react';
import { ShieldAlert, ShieldCheck, Star, Trophy } from 'lucide-react';
import { cn } from '../utils/cn';

export type TrustScore = 'VIP' | 'A+' | 'A' | 'B' | 'C' | 'RISK';

interface TrustBadgeProps {
  score?: TrustScore;
  patientId?: number;
  className?: string;
  showLabel?: boolean;
}

// eslint-disable-next-line react-refresh/only-export-components
// Fonction déterministe pour générer un score constant basé sur l'ID (Simulation pour Démo)
export const calculateTrustScore = (id?: number): TrustScore => {
  if (!id) return 'A';
  const scores: TrustScore[] = ['VIP', 'A+', 'B', 'A', 'C', 'A+', 'VIP', 'RISK', 'A'];
  return scores[(id * 3) % scores.length];
};

export const TrustBadge: React.FC<TrustBadgeProps> = ({ score, patientId, className, showLabel = true }) => {
  const finalScore = score || calculateTrustScore(patientId);

  const configs: Record<TrustScore, { color: string; icon: React.ReactNode; label: string; bg: string; border: string }> = {
    'VIP': { color: 'text-amber-500', bg: 'bg-amber-500/10', border: 'border-amber-500/20', icon: <Trophy size={14} />, label: 'Patient VIP' },
    'A+': { color: 'text-emerald-500', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', icon: <Star size={14} className="fill-emerald-500" />, label: 'Excellent' },
    'A': { color: 'text-teal-500', bg: 'bg-teal-500/10', border: 'border-teal-500/20', icon: <ShieldCheck size={14} />, label: 'Régulier' },
    'B': { color: 'text-blue-500', bg: 'bg-blue-500/10', border: 'border-blue-500/20', icon: <ShieldCheck size={14} />, label: 'Standard' },
    'C': { color: 'text-orange-500', bg: 'bg-orange-500/10', border: 'border-orange-500/20', icon: <ShieldAlert size={14} />, label: 'Retards Fréquents' },
    'RISK': { color: 'text-red-500', bg: 'bg-red-500/10', border: 'border-red-500/20', icon: <ShieldAlert size={14} />, label: 'À Risque (Impayés)' },
  };

  const config = configs[finalScore];

  return (
    <div 
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold border transition-all",
        config.bg, config.color, config.border,
        `trust-badge-${finalScore}`, // Helper class for Demo targeting
        className
      )}
      title={config.label}
    >
      {config.icon}
      <span>{finalScore}</span>
      {showLabel && <span className="ml-1 opacity-80 font-medium hidden sm:inline-block">{config.label}</span>}
    </div>
  );
};
