import React, { useState } from 'react';
import { Upload, Brain, AlertCircle, Ruler } from 'lucide-react';
import { api } from '../../services/api';
import { CephaloStudio } from '../../components/Analysis/CephaloStudio';
import { cn } from '../../utils/cn';

interface AnalysisResults {
  id: number;
  image_url: string;
  landmarks: Record<string, { x: number; y: number }>;
  angles: {
    SNA: number;
    SNB: number;
    ANB: number;
  };
}

export const AnalysisStudio = () => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisData, setAnalysisData] = useState<AnalysisResults | null>(null);
  const [error, setError] = useState<string | null>(null);

  // --- LOGIQUE D'UPLOAD & ANALYSE IA ---
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    setIsAnalyzing(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      // Déclenchement de l'événement pour l'animation Breath du Logo
      window.dispatchEvent(new Event('ai-generation-start'));

      const response = await api.post('/analyses/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setAnalysisData(response.data);
    } catch (err) {
      setError("Le serveur Backend ne répond pas ou l'IA a rencontré une erreur.");
    } finally {
      setIsAnalyzing(false);
      window.dispatchEvent(new Event('ai-generation-end'));
    }
  };

  return (
    <div className="flex h-full gap-6 animate-in fade-in duration-500">
      
      {/* GAUCHE : ESPACE DE TRAVAIL (CANVAS OU UPLOAD) */}
      <div className="flex-1 flex flex-col gap-4 overflow-hidden">
        {!analysisData ? (
          <div className="flex-1 flex flex-col items-center justify-center bg-slate-50 border-2 border-dashed border-slate-200 rounded-[2.5rem] p-12 text-center transition-all hover:bg-slate-100/50">
            {isAnalyzing ? (
              <div className="flex flex-col items-center gap-6">
                <div className="relative">
                  <div className="w-24 h-24 rounded-full border-4 border-slate-200 border-t-[#003380] animate-spin" />
                  <Brain className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-[#003380] animate-pulse" size={32} />
                </div>
                <div>
                  <h3 className="text-xl font-black text-[#003380] uppercase tracking-tighter">Analyse IA en cours...</h3>
                  <p className="text-slate-500 font-medium mt-2">Le modèle CEPHMark-Net identifie les 19 points anatomiques.</p>
                </div>
              </div>
            ) : (
              <>
                <div className="w-20 h-20 bg-blue-50 text-[#003380] rounded-3xl flex items-center justify-center mb-6 shadow-sm">
                  <Upload size={32} />
                </div>
                <h3 className="text-2xl font-black text-[#003380] leading-none mb-4">Téléverser une Radio</h3>
                <p className="text-slate-500 max-w-sm mb-8 font-medium">Glissez-déposez le cliché céphalométrique latéral (JPG/PNG) pour lancer l'analyse automatisée.</p>
                
                <label className="cursor-pointer bg-[#003380] hover:bg-blue-900 text-white px-8 py-4 rounded-2xl font-black transition-all shadow-xl shadow-blue-900/20 active:scale-95">
                  Sélectionner le fichier
                  <input type="file" className="hidden" accept="image/*" onChange={handleUpload} />
                </label>
              </>
            )}

            {error && (
              <div className="mt-8 flex items-center gap-3 text-red-600 bg-red-50 px-6 py-4 rounded-2xl border border-red-100 animate-bounce">
                <AlertCircle size={20} />
                <span className="font-bold text-sm">{error}</span>
              </div>
            )}
          </div>
        ) : (
          <CephaloStudio 
            analysisId={analysisData.id}
            imageUrl={analysisData.image_url}
            initialLandmarks={analysisData.landmarks}
          />
        )}
      </div>

      {/* DROITE : PANNEAU LATÉRAL DES RÉSULTATS (Angles & Diagnostics) */}
      <aside className="w-80 flex flex-col gap-4">
        
        {/* BLOC ANGLES CLINIQUES */}
        <div className="bg-white/80 backdrop-blur-xl border border-slate-200/60 rounded-[2rem] p-6 shadow-sm">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-[#003380]/5 text-[#003380] rounded-lg">
              <Ruler size={18} />
            </div>
            <h4 className="font-black text-[#003380] uppercase text-xs tracking-widest">Mesures Angulaires</h4>
          </div>

          <div className="space-y-4">
            <AngleCard label="Angle SNA" value={analysisData?.angles.SNA} normal="82° ± 2" />
            <AngleCard label="Angle SNB" value={analysisData?.angles.SNB} normal="80° ± 2" />
            <AngleCard label="Angle ANB" value={analysisData?.angles.ANB} normal="2° ± 2" highlight />
          </div>
        </div>

        {/* BLOC INFO PATIENT DYNAMIQUE */}
        <div className="bg-gradient-to-br from-[#003380] to-blue-900 rounded-[2rem] p-6 text-white shadow-xl">
          <h4 className="text-[10px] font-black text-blue-200 uppercase tracking-widest mb-4">Statut Analyse</h4>
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm font-bold">Fiabilité IA</span>
            <span className="text-sm font-black bg-white/20 px-2 py-0.5 rounded-md">98.4%</span>
          </div>
          <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
            <div className="bg-emerald-400 h-full w-[98.4%]" />
          </div>
          <p className="text-[11px] text-blue-100/70 mt-4 leading-relaxed italic">
            "Vérifiez l'emplacement des points A et B avant de valider le plan de traitement."
          </p>
        </div>

      </aside>
    </div>
  );
};

// --- COMPOSANT INTERNE : CARTE D'ANGLE ---
const AngleCard = ({ label, value, normal, highlight }: any) => (
  <div className={cn(
    "p-4 rounded-2xl border transition-all",
    highlight ? "bg-blue-50 border-blue-100" : "bg-slate-50 border-slate-100"
  )}>
    <div className="flex justify-between items-start mb-1">
      <span className="text-[10px] font-black text-slate-400 uppercase tracking-wide">{label}</span>
      <span className="text-[9px] font-bold text-slate-400">Norme : {normal}</span>
    </div>
    <div className="flex items-baseline gap-1">
      <span className={cn("text-2xl font-black", highlight ? "text-[#003380]" : "text-slate-800")}>
        {value ? value.toFixed(1) : '--.-'}
      </span>
      <span className="text-sm font-bold text-slate-400">°</span>
    </div>
  </div>
);