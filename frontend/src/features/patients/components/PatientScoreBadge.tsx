import { useEffect, useState } from 'react';
import { Shield, ShieldAlert, ShieldCheck, Award, Loader2 } from 'lucide-react';
import { api } from '../../../services/api';
import { cn } from '../../../utils/cn';

interface PatientScoreData {
  score: number;
  grade: 'PLATINUM' | 'GOLD' | 'SILVER' | 'BRONZE';
  details: {
    assiduite_score: number;
    solvabilite_score: number;
    rdv_honores: number;
    rdv_annules: number;
    total_facture: number;
    total_encaisse: number;
  };
}

interface PatientScoreBadgeProps {
  patientId: number;
  className?: string;
}

export const PatientScoreBadge = ({ patientId, className }: PatientScoreBadgeProps) => {
  const [data, setData] = useState<PatientScoreData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchScore = async () => {
      try {
        const response = await api.get(`/patients/${patientId}/score`);
        setData(response.data);
      } catch (error) {
        console.error("Erreur récupération score patient", error);
      } finally {
        setLoading(false);
      }
    };
    fetchScore();
  }, [patientId]);

  if (loading) {
    return (
      <div className={cn("w-8 h-8 rounded-xl bg-slate-100 flex items-center justify-center", className)}>
        <Loader2 size={14} className="animate-spin text-slate-300" />
      </div>
    );
  }

  if (!data) return null;

  // Configuration par grade
  const gradeConfig = {
    PLATINUM: {
      icon: <Award size={16} />,
      bg: "bg-slate-900",
      text: "text-white",
      border: "border-slate-800",
      shadow: "shadow-lg shadow-slate-900/20",
      label: "VIP Platinum"
    },
    GOLD: {
      icon: <ShieldCheck size={16} />,
      bg: "bg-amber-100",
      text: "text-amber-700",
      border: "border-amber-200",
      shadow: "shadow-md shadow-amber-500/10",
      label: "Gold"
    },
    SILVER: {
      icon: <Shield size={16} />,
      bg: "bg-slate-100",
      text: "text-slate-600",
      border: "border-slate-200",
      shadow: "shadow-sm",
      label: "Silver"
    },
    BRONZE: {
      icon: <ShieldAlert size={16} />,
      bg: "bg-rose-100",
      text: "text-rose-700",
      border: "border-rose-200",
      shadow: "shadow-md shadow-rose-500/10",
      label: "Risque (Bronze)"
    }
  };

  const config = gradeConfig[data.grade];

  return (
    <div className={cn("relative group cursor-help", className)}>
      <div className={cn(
        "flex items-center justify-center w-8 h-8 rounded-xl border transition-all",
        config.bg, config.text, config.border, config.shadow
      )}>
        {config.icon}
      </div>

      {/* Tooltip Hover (Ghost Elite Style) */}
      <div className="absolute left-1/2 -translate-x-1/2 top-full mt-2 w-64 p-4 bg-white/95 backdrop-blur-xl border border-slate-200/60 rounded-2xl shadow-[0_20px_40px_-15px_rgba(0,0,0,0.15)] opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 pointer-events-none">
        
        {/* Triangle pointer */}
        <div className="absolute left-1/2 -translate-x-1/2 -top-2 border-8 border-transparent border-b-white/95" />

        <div className="flex items-center gap-2 mb-3">
          <div className={cn("p-1.5 rounded-lg", config.bg, config.text)}>
            {config.icon}
          </div>
          <div>
            <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Fiabilité Patient</p>
            <p className={cn("text-xs font-black uppercase tracking-wide", config.text)}>{config.label} ({data.score}/100)</p>
          </div>
        </div>

        <div className="space-y-3 pt-3 border-t border-slate-100">
          <div>
            <div className="flex justify-between text-[11px] font-bold mb-1">
              <span className="text-slate-500">Assiduité RDV (60%)</span>
              <span className={data.details.assiduite_score < 50 ? 'text-rose-500' : 'text-emerald-500'}>
                {data.details.assiduite_score}/100
              </span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
              <div 
                className={cn("h-full rounded-full", data.details.assiduite_score < 50 ? 'bg-rose-500' : 'bg-emerald-500')} 
                style={{ width: `${data.details.assiduite_score}%` }}
              />
            </div>
            <p className="text-[9px] text-slate-400 mt-1 font-medium">{data.details.rdv_honores} honorés • {data.details.rdv_annules} no-shows</p>
          </div>

          <div>
            <div className="flex justify-between text-[11px] font-bold mb-1">
              <span className="text-slate-500">Solvabilité (40%)</span>
              <span className={data.details.solvabilite_score < 50 ? 'text-rose-500' : 'text-emerald-500'}>
                {data.details.solvabilite_score}/100
              </span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
              <div 
                className={cn("h-full rounded-full", data.details.solvabilite_score < 50 ? 'bg-rose-500' : 'bg-emerald-500')} 
                style={{ width: `${data.details.solvabilite_score}%` }}
              />
            </div>
            <p className="text-[9px] text-slate-400 mt-1 font-medium">{data.details.total_encaisse} MAD encaissés sur {data.details.total_facture} MAD</p>
          </div>
        </div>
      </div>
    </div>
  );
};
