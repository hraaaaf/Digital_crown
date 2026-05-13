import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ShieldAlert, 
  Activity, 
  Wrench, 
  Crown, 
  ClipboardCheck, 
  ChevronDown, 
  ChevronUp,
  FileText,
  Plus,
  Brain
} from 'lucide-react';
import { cn } from '../../../utils/cn';
import { useEliteStore } from '../../../stores/useEliteStore';

interface PhaseProps {
  title: string;
  icon: React.ElementType;
  items: any[];
  isOpen: boolean;
  onToggle: () => void;
  color: string;
  selectedIds: string[];
  onToggleSelect: (id: string) => void;
  onUpdateLabel: (id: string, label: string) => void;
  onDropAct: (actId: string, targetPhase: string) => void;
  phaseKey: string;
}

const PhaseCard: React.FC<PhaseProps> = ({ title, icon: Icon, items, isOpen, onToggle, color, selectedIds, onToggleSelect, onUpdateLabel, onDropAct, phaseKey }) => {
  if (items.length === 0) return null;

  return (
    <div 
      onDragOver={(e: React.DragEvent) => {
        e.preventDefault();
        e.currentTarget.classList.add('ring-2', 'ring-primary/20', 'bg-primary/5');
      }}
      onDragLeave={(e: React.DragEvent) => {
        e.currentTarget.classList.remove('ring-2', 'ring-primary/20', 'bg-primary/5');
      }}
      onDrop={(e: React.DragEvent) => {
        e.preventDefault();
        e.currentTarget.classList.remove('ring-2', 'ring-primary/20', 'bg-primary/5');
        const actId = e.dataTransfer.getData('actId');
        if (actId) onDropAct(actId, phaseKey);
      }}
      className={cn(
        "mb-4 rounded-3xl border transition-all duration-500 overflow-hidden",
        isOpen ? "bg-white shadow-xl border-slate-200" : "bg-slate-50/50 border-transparent hover:bg-white hover:border-slate-100"
      )}
    >
      <button 
        onClick={onToggle}
        className="w-full px-8 py-5 flex items-center justify-between group"
      >
        <div className="flex items-center gap-4">
          <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center text-white shadow-lg", color)}>
            <Icon size={20} />
          </div>
          <div className="text-left">
            <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 leading-none mb-1">Phase</h4>
            <span className="text-sm font-black text-slate-800">{title}</span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="px-3 py-1 bg-slate-200/50 rounded-full text-[9px] font-black text-slate-500">
            {items.length} ACTE(S)
          </span>
          {isOpen ? <ChevronUp size={18} className="text-slate-300" /> : <ChevronDown size={18} className="text-slate-300" />}
        </div>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="px-8 pb-8"
          >
            <div className="space-y-3 pt-4 border-t border-slate-50">
              {items.map((item, idx) => (
                <div 
                  key={item.id}
                  draggable
                  onDragStart={(e: React.DragEvent) => {
                    e.dataTransfer.setData('actId', item.id);
                    e.dataTransfer.effectAllowed = 'move';
                  }}
                  className={cn(
                    "p-4 rounded-2xl border flex items-center justify-between group/item transition-all cursor-grab active:cursor-grabbing",
                    selectedIds.includes(item.id) 
                      ? "bg-white border-slate-200 shadow-sm" 
                      : "bg-slate-50/50 border-transparent opacity-60 grayscale"
                  )}
                >
                  <motion.div 
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: idx * 0.05 }}
                    className="flex items-center gap-4 flex-1"
                  >
                    <button 
                      onClick={() => onToggleSelect(item.id)}
                      className={cn(
                        "w-5 h-5 rounded-md border flex items-center justify-center transition-all",
                        selectedIds.includes(item.id) ? "bg-primary border-primary text-white" : "bg-white border-slate-300"
                      )}
                    >
                      {selectedIds.includes(item.id) && <Plus size={12} className="rotate-45" />}
                    </button>
                    <div className="w-8 h-8 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-center text-[10px] font-black text-slate-400">
                      {item.fdi}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-[10px] font-black text-primary uppercase tracking-wider">{item.diagnosis}</span>
                      </div>
                      <input 
                        type="text" 
                        value={item.suggested_act}
                        onChange={(e) => onUpdateLabel(item.id, e.target.value)}
                        className="w-full bg-transparent text-xs font-bold text-slate-700 focus:outline-none focus:text-primary transition-colors"
                      />
                    </div>
                  </motion.div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export const TreatmentPlanStudio: React.FC<{ patientId: number; onConvertToQuote?: (acts: any[]) => void }> = ({ patientId, onConvertToQuote }) => {
  const { treatmentPlan, fetchTreatmentPlan, isLoading } = useEliteStore();
  const [openPhases, setOpenPhases] = useState<string[]>(["URGENCE", "INITIALE"]);

  useEffect(() => {
    fetchTreatmentPlan(patientId);
  }, [patientId, fetchTreatmentPlan]);

  const [localPhases, setLocalPhases] = useState<any>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  useEffect(() => {
    if (treatmentPlan && !treatmentPlan.error) {
      setLocalPhases(treatmentPlan.phases);
      const allIds = Object.values(treatmentPlan.phases).flat().map((a: any) => a.id);
      setSelectedIds(allIds);
    }
  }, [treatmentPlan]);

  const handleConvertToQuote = () => {
    if (!localPhases || !onConvertToQuote) return;
    const selectedActs = Object.values(localPhases).flat().filter((a: any) => selectedIds.includes(a.id));
    onConvertToQuote(selectedActs);
  };

  const toggleSelect = (id: string) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]);
  };

  const updateActLabel = (phaseKey: string, id: string, newLabel: string) => {
    setLocalPhases((prev: any) => ({
      ...prev,
      [phaseKey]: prev[phaseKey].map((a: any) => a.id === id ? { ...a, suggested_act: newLabel } : a)
    }));
  };

  const moveAct = (actId: string, targetPhase: string) => {
    setLocalPhases((prev: any) => {
      // Trouver l'acte et sa phase d'origine
      let actToMove: any = null;
      let sourcePhase: string = '';
      
      for (const [phase, acts] of Object.entries(prev)) {
        const act = (acts as any[]).find(a => a.id === actId);
        if (act) {
          actToMove = act;
          sourcePhase = phase;
          break;
        }
      }

      if (!actToMove || sourcePhase === targetPhase) return prev;

      // Créer la nouvelle structure
      return {
        ...prev,
        [sourcePhase]: (prev[sourcePhase] as any[]).filter(a => a.id !== actId),
        [targetPhase]: [...(prev[targetPhase] as any[]), actToMove]
      };
    });
  };

  const togglePhase = (phase: string) => {
    setOpenPhases(prev => 
      prev.includes(phase) ? prev.filter(p => p !== phase) : [...prev, phase]
    );
  };

  if (isLoading) {
    return (
      <div className="p-20 flex flex-col items-center justify-center">
        <Brain size={40} className="text-primary animate-pulse mb-4" />
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Séquençage clinique en cours...</p>
      </div>
    );
  }

  if (!localPhases) {
    return (
      <div className="p-12 text-center bg-slate-50 rounded-3xl border border-dashed border-slate-200">
        <FileText size={40} className="text-slate-300 mx-auto mb-4" />
        <p className="text-xs font-bold text-slate-500">Aucun plan de traitement généré.</p>
        <button 
          onClick={() => fetchTreatmentPlan(patientId)}
          className="mt-4 px-6 py-2 bg-primary text-white rounded-xl text-[10px] font-black uppercase"
        >
          Générer maintenant
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-1000">
      <div className="flex items-center justify-between bg-white/60 p-6 rounded-[2rem] border border-white/80 backdrop-blur-xl shadow-lg shadow-slate-200/50">
        <div>
          <h3 className="text-lg font-black text-slate-800 leading-none mb-2">Stratégie Thérapeutique</h3>
          <p className="text-xs font-bold text-slate-400 italic">"{treatmentPlan.summary}"</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right mr-4">
             <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Sélection</p>
             <p className="text-sm font-black text-primary">{selectedIds.length} acte(s)</p>
          </div>
          <button 
            onClick={handleConvertToQuote}
            disabled={selectedIds.length === 0}
            className="px-8 py-3 bg-slate-900 text-white rounded-2xl text-[10px] font-black uppercase tracking-widest shadow-xl shadow-slate-900/20 hover:scale-[1.02] active:scale-95 disabled:opacity-30 disabled:grayscale transition-all flex items-center gap-3"
          >
            <Plus size={16} /> Générer le Devis ({selectedIds.length})
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {Object.entries(localPhases).map(([key, acts]: [string, any]) => (
          <PhaseCard 
            key={key}
            title={key === "URGENCE" ? "Phase d'Urgence" : 
                   key === "INITIALE" ? "Préparation & Assainissement" : 
                   key === "CONSERVATRICE" ? "Soins Conservateurs" : 
                   key === "REHABILITATION" ? "Réhabilitation & Prothèse" : "Maintenance"} 
            icon={key === "URGENCE" ? ShieldAlert : 
                  key === "INITIALE" ? Activity : 
                  key === "CONSERVATRICE" ? Wrench : 
                  key === "REHABILITATION" ? Crown : ClipboardCheck}
            items={acts}
            isOpen={openPhases.includes(key)}
            onToggle={() => togglePhase(key)}
            color={key === "URGENCE" ? "bg-red-500" : 
                   key === "INITIALE" ? "bg-amber-500" : 
                   key === "CONSERVATRICE" ? "bg-blue-500" : 
                   key === "REHABILITATION" ? "bg-indigo-500" : "bg-emerald-500"}
            selectedIds={selectedIds}
            onToggleSelect={toggleSelect}
            onUpdateLabel={(id, val) => updateActLabel(key, id, val)}
            onDropAct={moveAct}
            phaseKey={key}
          />
        ))}
      </div>
    </div>
  );
};
