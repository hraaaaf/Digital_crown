import React from 'react';
import { Loader2, AlertTriangle, Eye } from 'lucide-react';
import { createPortal } from 'react-dom';

interface StudioFooterProps {
  loading: boolean;
  activeTab: string;
  onGenerate: (archive: boolean, print: boolean, isPreview: boolean, force: boolean) => void;
  showPrintWarning: boolean;
  onCloseWarning: () => void;
  hasChanges: boolean;
  onSavePreference?: () => void;
  aiReport?: string | null;
  onGenerateAI?: () => void;
  loadingAi?: boolean;
  total?: number;
  sideStudioType: 'NONE' | 'PREVIEW';
  onTogglePreview: () => void;
}

export const StudioFooter: React.FC<StudioFooterProps> = ({
  activeTab,
  onGenerate,
  showPrintWarning,
  onCloseWarning,
  hasChanges,
  onSavePreference,
  aiReport,
  onGenerateAI,
  loadingAi,
  total
}) => {
  if (activeTab === 'plan') {
    return null;
  }

  if (activeTab === 'ai') {
    return (
      <div className="flex justify-end p-6 bg-slate-50/50 rounded-[2rem] border border-slate-100 mt-6">
        <button 
          onClick={onGenerateAI}
          disabled={loadingAi}
          className="px-8 py-4 bg-primary text-white rounded-2xl font-black uppercase text-[12px] tracking-widest shadow-xl shadow-primary/20 hover:-translate-y-1 transition-all active:scale-95 disabled:opacity-50"
          style={{ backgroundColor: 'var(--primary)' }}
        >
          {loadingAi ? <Loader2 className="animate-spin mr-2 inline" /> : <Eye className="mr-2 inline" />}
          {aiReport ? "Régénérer Analyse" : "Lancer Analyse IA"}
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col sm:flex-row items-center justify-center gap-8 p-3 bg-slate-50/80 backdrop-blur-xl rounded-[1.5rem] border border-slate-100 mt-2 shadow-sm relative overflow-hidden w-full shrink-0">
      
      <div className="flex items-center gap-6">
        {/* Le bouton de sauvegarde du protocole a été déplacé dans le composant de l'ordonnance lui-même pour éviter les doublons */}
        
        {(activeTab === 'devis' || activeTab === 'honoraires') && typeof total === 'number' && (
          <div className="flex items-center gap-4 px-6 border-r border-slate-200">
            <div className="flex flex-col items-center">
              <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest leading-tight">Total Document</span>
              <span className="text-xl font-black text-slate-900 tracking-tighter leading-tight">
                {total.toLocaleString('fr-FR')} <span className="text-[10px] opacity-40">MAD</span>
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Les boutons Générer / Imprimer sont désormais dans le StudioHeader */}

      {showPrintWarning && typeof document !== 'undefined' && createPortal(
        <div className="fixed inset-0 bg-white/95 backdrop-blur-sm z-[9999] flex items-center justify-center p-8 animate-in fade-in zoom-in-95 duration-300">
          <div className="flex flex-col items-center text-center max-w-sm bg-white p-8 rounded-3xl shadow-2xl border border-slate-100">
            <AlertTriangle className="text-amber-500 mb-4" size={48} />
            <h4 className="text-lg font-black text-slate-800 mb-2">Attention : Impression Directe</h4>
            <p className="text-sm text-slate-500 font-medium mb-6">Assurez-vous que votre imprimante est prête. Le document sera archivé automatiquement après l'impression.</p>
            <div className="flex gap-4">
              <button onClick={onCloseWarning} className="px-6 py-2 text-slate-400 font-bold hover:text-slate-600 transition-colors">Annuler</button>
              <button onClick={() => onGenerate(true, true, false, true)} className="px-8 py-2 bg-primary text-white rounded-xl font-black" style={{ backgroundColor: 'var(--primary)' }}>Confirmer</button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
};
