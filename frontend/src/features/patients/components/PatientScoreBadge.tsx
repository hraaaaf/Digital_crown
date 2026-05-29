import { useEffect, useState, useRef } from 'react';
import { Crown, Gem, ShieldCheck, AlertCircle, Loader2, RefreshCcw } from 'lucide-react';
import { api } from '../../../services/api';
import { cn } from '../../../utils/cn';

interface PatientScoreData {
  score: number;
  grade: 'PLATINUM' | 'GOLD' | 'SILVER' | 'BRONZE';
  is_manual: boolean;
  comment?: string;
  details: {
    assiduite_score: number;
    solvabilite_score: number;
    rdv_honores?: number;
    rdv_annules?: number;
    total_facture?: number;
    total_encaisse?: number;
  };
}

interface PatientScoreBadgeProps {
  patientId: number;
  className?: string;
  onUpdate?: () => void;
}

export const PatientScoreBadge = ({ patientId, className, onUpdate }: PatientScoreBadgeProps) => {
  const [data, setData] = useState<PatientScoreData | null>(null);
  const [loading, setLoading] = useState(true);
  const [showMenu, setShowMenu] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const fetchScore = async () => {
    if (!patientId) return;
    try {
      const response = await api.get(`/patients/${patientId}/score`);
      setData(response.data);
    } catch (error) {
      console.error("Erreur récupération score patient", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScore();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [patientId]);

  const handleUpdateGrade = async (newGrade: string | null) => {
    setIsUpdating(true);
    try {
      await api.patch(`/patients/${patientId}/grade`, { 
        grade: newGrade,
        comment: newGrade ? `Modifié manuellement par le praticien.` : null
      });
      await fetchScore();
      onUpdate?.();
      setShowMenu(false);
    } catch (error) {
      console.error("Erreur mise à jour grade", error);
    } finally {
      setIsUpdating(false);
    }
  };

  // Fermeture au clic extérieur
  useEffect(() => {
    if (!showMenu) return;
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showMenu]);

  if (loading) {
    return (
      <div className={cn("w-8 h-8 rounded-xl bg-slate-100 flex items-center justify-center", className)}>
        <Loader2 size={14} className="animate-spin text-slate-300" />
      </div>
    );
  }

  if (!data) return null;

  const gradeConfig = {
    PLATINUM: {
      icon: <Crown size={14} strokeWidth={3} />,
      bg: "bg-slate-950",
      text: "text-slate-50",
      border: "border-slate-800",
      shadow: "shadow-[0_0_15px_-3px_rgba(0,0,0,0.4)]",
      label: "Platinum Elite",
      desc: "Patient VIP. Excellence clinique et administrative."
    },
    GOLD: {
      icon: <Gem size={14} strokeWidth={2.5} />,
      bg: "bg-[#FFF9E6]",
      text: "text-[#B48A05]",
      border: "border-[#F3E2B4]",
      shadow: "shadow-sm",
      label: "Gold Status",
      desc: "Haut niveau de fiabilité. Engagement exemplaire."
    },
    SILVER: {
      icon: <ShieldCheck size={14} strokeWidth={2.5} />,
      bg: "bg-slate-50",
      text: "text-slate-500",
      border: "border-slate-200",
      shadow: "shadow-none",
      label: "Silver",
      desc: "Patient standard. Suivi régulier et conforme."
    },
    BRONZE: {
      icon: <AlertCircle size={14} strokeWidth={2.5} />,
      bg: "bg-rose-50",
      text: "text-rose-600",
      border: "border-rose-100",
      shadow: "shadow-none",
      label: "Bronze (Vigilance)",
      desc: "Attention requise : Historique d'absences ou retards."
    }
  };

  const config = (data.grade && gradeConfig[data.grade]) || gradeConfig.SILVER;

  return (
    <div className={cn("relative", className)}>
      <div 
        onClick={(e) => {
          e.stopPropagation();
          setShowMenu(!showMenu);
        }}
        className={cn(
          "flex items-center justify-center w-8 h-8 rounded-xl border transition-all cursor-pointer hover:scale-110 active:scale-95 group",
          config.bg, config.text, config.border, config.shadow,
          data.is_manual && "ring-2 ring-offset-2 ring-slate-400"
        )}
      >
        {config.icon}
        {data.is_manual && (
          <div className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-blue-500 border-2 border-white rounded-full" />
        )}
      </div>

      {showMenu && (
        <div 
          ref={menuRef}
          onClick={(e) => e.stopPropagation()}
          className="absolute right-0 top-full mt-3 w-72 bg-white rounded-[2rem] shadow-[0_25px_50px_-12px_rgba(0,0,0,0.25)] border border-slate-100 p-4 z-[9999] animate-in fade-in zoom-in-95 duration-200 origin-top-right"
        >
          <h4 className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-4 px-2">Modifier le Badge Patient</h4>
          
          <div className="space-y-2">
            {(Object.keys(gradeConfig) as Array<keyof typeof gradeConfig>).map((g) => (
              <button
                key={g}
                disabled={isUpdating}
                onClick={() => handleUpdateGrade(g)}
                className={cn(
                  "w-full flex items-center gap-3 p-3 rounded-2xl transition-all text-left group/item",
                  data.grade === g ? "bg-slate-50 ring-1 ring-slate-100" : "hover:bg-slate-50"
                )}
              >
                <div className={cn("p-2 rounded-xl transition-transform group-hover/item:scale-110", gradeConfig[g].bg, gradeConfig[g].text)}>
                  {gradeConfig[g].icon}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-black text-slate-800">{gradeConfig[g].label}</span>
                    {data.grade === g && <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />}
                  </div>
                  <p className="text-[10px] font-bold text-slate-400 leading-tight mt-0.5">{gradeConfig[g].desc}</p>
                </div>
              </button>
            ))}
          </div>

          <div className="mt-4 pt-4 border-t border-slate-50 flex flex-col gap-2">
            {data.is_manual && (
              <button
                disabled={isUpdating}
                onClick={() => handleUpdateGrade(null)}
                className="w-full py-3 rounded-xl text-[10px] font-black uppercase tracking-widest text-blue-500 hover:bg-blue-50 transition-all flex items-center justify-center gap-2"
              >
                <RefreshCcw size={12} />
                Réinitialiser en auto
              </button>
            )}
            <button
              onClick={() => setShowMenu(false)}
              className="w-full py-3 rounded-xl text-[10px] font-black uppercase tracking-widest text-slate-400 hover:bg-slate-50 transition-all"
            >
              Fermer
            </button>
          </div>
        </div>
      )}

    </div>
  );
};
