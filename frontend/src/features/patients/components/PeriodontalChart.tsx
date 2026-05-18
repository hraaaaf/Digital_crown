import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FileSpreadsheet, 
  HeartPulse, 
  Save, 
  Trash2, 
  PlusCircle, 
  AlertTriangle, 
  CheckCircle,
  Activity
} from 'lucide-react';
import { cn } from '../../../utils/cn';

interface ToothPoints {
  // Probing Depth (PD) - 6 points: Disto-buccal, Buccal, Mesio-buccal, Disto-lingual, Lingual, Mesio-lingual
  pd: [number, number, number, number, number, number];
  // Gingival Recession (GR) - 6 points
  gr: [number, number, number, number, number, number];
  // Bleeding on Probing (BOP) - 6 points
  bop: [boolean, boolean, boolean, boolean, boolean, boolean];
  // Plaque - 6 points
  plaque: [boolean, boolean, boolean, boolean, boolean, boolean];
  mobility: 0 | 1 | 2 | 3;
  furcation: 0 | 1 | 2 | 3;
}

type PerioData = Record<number, ToothPoints>;

const DEFAULT_TOOTH_DATA = (): ToothPoints => ({
  pd: [2, 2, 2, 2, 2, 2],
  gr: [0, 0, 0, 0, 0, 0],
  bop: [false, false, false, false, false, false],
  plaque: [false, false, false, false, false, false],
  mobility: 0,
  furcation: 0
});

// FDI tooth list
const MAXILLARY_TEETH = [18, 17, 16, 15, 14, 13, 12, 11, 21, 22, 23, 24, 25, 26, 27, 28];
const MANDIBULAR_TEETH = [48, 47, 46, 45, 44, 43, 42, 41, 31, 32, 33, 34, 35, 36, 37, 38];

interface PeriodontalChartProps {
  patientId: number;
}

export const PeriodontalChart: React.FC<PeriodontalChartProps> = ({ patientId }) => {
  const [perioData, setPerioData] = useState<PerioData>({});
  const [selectedTooth, setSelectedTooth] = useState<number | null>(null);
  const [isSaved, setIsSaved] = useState(false);

  // Load patient data
  useEffect(() => {
    const saved = localStorage.getItem(`perio_chart_data_${patientId}`);
    if (saved) {
      try {
        setPerioData(JSON.parse(saved));
      } catch (e) {
        console.error("❌ Error loading perio data:", e);
      }
    } else {
      // Initialize all teeth with default data
      const initData: PerioData = {};
      [...MAXILLARY_TEETH, ...MANDIBULAR_TEETH].forEach(t => {
        initData[t] = DEFAULT_TOOTH_DATA();
      });
      setPerioData(initData);
    }
  }, [patientId]);

  const handleSave = () => {
    localStorage.setItem(`perio_chart_data_${patientId}`, JSON.stringify(perioData));
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 3000);
  };

  const handleReset = () => {
    if (window.confirm("Êtes-vous sûr de vouloir réinitialiser l'ensemble des mesures parodontales ?")) {
      const initData: PerioData = {};
      [...MAXILLARY_TEETH, ...MANDIBULAR_TEETH].forEach(t => {
        initData[t] = DEFAULT_TOOTH_DATA();
      });
      setPerioData(initData);
      localStorage.removeItem(`perio_chart_data_${patientId}`);
    }
  };

  const updateToothData = (tooth: number, updater: (prev: ToothPoints) => ToothPoints) => {
    setPerioData(prev => ({
      ...prev,
      [tooth]: updater(prev[tooth] || DEFAULT_TOOTH_DATA())
    }));
  };



  const getPocketDepthBadge = (depth: number) => {
    if (depth <= 3) return 'bg-emerald-500';
    if (depth <= 5) return 'bg-amber-500';
    return 'bg-rose-500 animate-pulse';
  };

  // Calculate statistics
  const stats = React.useMemo(() => {
    let totalSites = 0;
    let bopSites = 0;
    let plaqueSites = 0;
    let deepPockets = 0; // >= 6mm
    let moderatePockets = 0; // 4-5mm

    Object.values(perioData).forEach(tooth => {
      tooth.pd.forEach(depth => {
        totalSites++;
        if (depth >= 6) deepPockets++;
        else if (depth >= 4) moderatePockets++;
      });
      tooth.bop.forEach(b => {
        if (b) bopSites++;
      });
      tooth.plaque.forEach(p => {
        if (p) plaqueSites++;
      });
    });

    const bopPercent = totalSites > 0 ? Math.round((bopSites / totalSites) * 100) : 0;
    const plaquePercent = totalSites > 0 ? Math.round((plaqueSites / totalSites) * 100) : 0;

    return {
      bopPercent,
      plaquePercent,
      deepPockets,
      moderatePockets,
      totalSites
    };
  }, [perioData]);

  const activeToothData = selectedTooth ? perioData[selectedTooth] : null;

  return (
    <div className="w-full flex flex-col gap-6 p-6 bg-slate-950/20 dark:bg-slate-900/40 rounded-[2.5rem] border border-slate-200/50 dark:border-slate-800/50 backdrop-blur-xl">
      
      {/* HEADER SECTION */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-200/55 dark:border-slate-800/55">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-primary/10 rounded-2xl flex items-center justify-center text-primary" style={{ color: 'var(--primary)', backgroundColor: 'rgba(var(--primary-rgb), 0.1)' }}>
            <FileSpreadsheet size={24} />
          </div>
          <div>
            <h2 className="text-lg font-black text-slate-800 dark:text-slate-100 flex items-center gap-2">
              Sondage Parodontal Graphique
              <span className="text-[10px] uppercase tracking-widest bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/20 font-black">
                Elite v2.0
              </span>
            </h2>
            <p className="text-xs text-slate-400 font-bold">Cartographie complète à 6 points de mesure (buccal & lingual).</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleReset}
            className="px-4 py-2.5 bg-slate-900/5 dark:bg-slate-800/30 text-slate-500 dark:text-slate-400 hover:text-rose-500 dark:hover:text-rose-400 border border-slate-200 dark:border-slate-800 rounded-xl text-xs font-black uppercase tracking-wider transition-all duration-300 flex items-center gap-2 active:scale-95"
          >
            <Trash2 size={14} />
            Réinitialiser
          </button>
          <button
            onClick={handleSave}
            className={cn(
              "px-5 py-2.5 rounded-xl text-xs font-black uppercase tracking-wider transition-all duration-300 flex items-center gap-2 active:scale-95 text-white shadow-lg",
              isSaved ? "bg-emerald-500 shadow-emerald-500/20" : "bg-primary hover:opacity-90"
            )}
            style={!isSaved ? { backgroundColor: 'var(--primary)' } : {}}
          >
            {isSaved ? <CheckCircle size={14} /> : <Save size={14} />}
            {isSaved ? "Enregistré" : "Enregistrer"}
          </button>
        </div>
      </div>

      {/* STATS OVERVIEW CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-card-bg border border-border-main p-4 rounded-2xl flex items-center gap-4 shadow-sm backdrop-blur-md">
          <div className="w-10 h-10 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500 flex items-center justify-center">
            <HeartPulse size={20} className="animate-pulse" />
          </div>
          <div>
            <div className="text-[10px] uppercase font-black tracking-widest text-slate-400">Saignement (BOP)</div>
            <div className="text-2xl font-black text-rose-500">{stats.bopPercent}%</div>
          </div>
        </div>

        <div className="bg-card-bg border border-border-main p-4 rounded-2xl flex items-center gap-4 shadow-sm backdrop-blur-md">
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-500 flex items-center justify-center">
            <Activity size={20} />
          </div>
          <div>
            <div className="text-[10px] uppercase font-black tracking-widest text-slate-400">Indice de Plaque</div>
            <div className="text-2xl font-black text-amber-500">{stats.plaquePercent}%</div>
          </div>
        </div>

        <div className="bg-card-bg border border-border-main p-4 rounded-2xl flex items-center gap-4 shadow-sm backdrop-blur-md">
          <div className="w-10 h-10 rounded-xl bg-rose-600/10 border border-rose-600/20 text-rose-600 flex items-center justify-center">
            <AlertTriangle size={20} />
          </div>
          <div>
            <div className="text-[10px] uppercase font-black tracking-widest text-slate-400">Poches Profondes (≥6mm)</div>
            <div className="text-2xl font-black text-rose-600">{stats.deepPockets}</div>
          </div>
        </div>

        <div className="bg-card-bg border border-border-main p-4 rounded-2xl flex items-center gap-4 shadow-sm backdrop-blur-md">
          <div className="w-10 h-10 rounded-xl bg-amber-600/10 border border-amber-600/20 text-amber-600 flex items-center justify-center">
            <PlusCircle size={20} />
          </div>
          <div>
            <div className="text-[10px] uppercase font-black tracking-widest text-slate-400">Poches Modérées (4-5mm)</div>
            <div className="text-2xl font-black text-amber-600">{stats.moderatePockets}</div>
          </div>
        </div>
      </div>

      {/* GRAPHICAL ARCHES */}
      <div className="flex flex-col gap-8 bg-slate-900/5 dark:bg-slate-900/20 p-8 rounded-3xl border border-slate-200/40 dark:border-slate-800/40">
        
        {/* MAXILLARY ARCH */}
        <div className="flex flex-col gap-3">
          <div className="text-[10px] uppercase tracking-widest font-black text-slate-400 mb-2">Arcade Maxillaire (Supérieure)</div>
          <div className="flex items-center justify-between gap-2 overflow-x-auto py-2 custom-scrollbar">
            {MAXILLARY_TEETH.map(t => {
              const tooth = perioData[t] || DEFAULT_TOOTH_DATA();
              const hasDeep = tooth.pd.some(d => d >= 6);
              const hasMod = tooth.pd.some(d => d >= 4 && d < 6);
              const maxPd = Math.max(...tooth.pd);
              
              return (
                <button
                  key={t}
                  onClick={() => setSelectedTooth(t)}
                  className={cn(
                    "flex-1 min-w-[50px] aspect-[5/8] rounded-xl border flex flex-col items-center justify-between p-2 transition-all duration-300 relative group active:scale-95 shadow-sm",
                    selectedTooth === t 
                      ? "bg-primary/10 border-primary text-primary scale-105 shadow-md shadow-primary/10" 
                      : hasDeep
                      ? "bg-rose-500/5 hover:bg-rose-500/10 border-rose-500/30 text-rose-500"
                      : hasMod
                      ? "bg-amber-500/5 hover:bg-amber-500/10 border-amber-500/30 text-amber-500"
                      : "bg-card-bg hover:bg-slate-100 dark:hover:bg-slate-800/50 border-border-main text-text-main"
                  )}
                  style={selectedTooth === t ? { borderColor: 'var(--primary)', color: 'var(--primary)' } : {}}
                >
                  <div className="text-xs font-black tracking-tight">{t}</div>
                  
                  {/* Visual Probing Depth Bars */}
                  <div className="flex gap-0.5 items-end justify-center h-8 w-full">
                    {tooth.pd.map((d, idx) => (
                      <div 
                        key={idx} 
                        className={cn("w-1 rounded-full transition-all", getPocketDepthBadge(d))}
                        style={{ height: `${Math.min(100, (d / 9) * 100)}%`, minHeight: '3px' }}
                      />
                    ))}
                  </div>

                  <div className="text-[10px] font-mono font-black">{maxPd}mm</div>
                </button>
              );
            })}
          </div>
        </div>

        {/* MANDIBULAR ARCH */}
        <div className="flex flex-col gap-3">
          <div className="text-[10px] uppercase tracking-widest font-black text-slate-400 mb-2">Arcade Mandibulaire (Inférieure)</div>
          <div className="flex items-center justify-between gap-2 overflow-x-auto py-2 custom-scrollbar">
            {MANDIBULAR_TEETH.map(t => {
              const tooth = perioData[t] || DEFAULT_TOOTH_DATA();
              const hasDeep = tooth.pd.some(d => d >= 6);
              const hasMod = tooth.pd.some(d => d >= 4 && d < 6);
              const maxPd = Math.max(...tooth.pd);
              
              return (
                <button
                  key={t}
                  onClick={() => setSelectedTooth(t)}
                  className={cn(
                    "flex-1 min-w-[50px] aspect-[5/8] rounded-xl border flex flex-col items-center justify-between p-2 transition-all duration-300 relative group active:scale-95 shadow-sm",
                    selectedTooth === t 
                      ? "bg-primary/10 border-primary text-primary scale-105 shadow-md shadow-primary/10" 
                      : hasDeep
                      ? "bg-rose-500/5 hover:bg-rose-500/10 border-rose-500/30 text-rose-500"
                      : hasMod
                      ? "bg-amber-500/5 hover:bg-amber-500/10 border-amber-500/30 text-amber-500"
                      : "bg-card-bg hover:bg-slate-100 dark:hover:bg-slate-800/50 border-border-main text-text-main"
                  )}
                  style={selectedTooth === t ? { borderColor: 'var(--primary)', color: 'var(--primary)' } : {}}
                >
                  <div className="text-xs font-black tracking-tight">{t}</div>
                  
                  {/* Visual Probing Depth Bars */}
                  <div className="flex gap-0.5 items-end justify-center h-8 w-full">
                    {tooth.pd.map((d, idx) => (
                      <div 
                        key={idx} 
                        className={cn("w-1 rounded-full transition-all", getPocketDepthBadge(d))}
                        style={{ height: `${Math.min(100, (d / 9) * 100)}%`, minHeight: '3px' }}
                      />
                    ))}
                  </div>

                  <div className="text-[10px] font-mono font-black">{maxPd}mm</div>
                </button>
              );
            })}
          </div>
        </div>

      </div>

      {/* INTERACTIVE TOOTH EDITION PANEL */}
      <AnimatePresence mode="wait">
        {selectedTooth && activeToothData && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="bg-card-bg border border-border-main rounded-[2rem] p-6 shadow-xl flex flex-col gap-6"
          >
            <div className="flex items-center justify-between border-b border-border-main pb-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-primary/15 flex items-center justify-center font-black text-sm text-primary" style={{ color: 'var(--primary)', backgroundColor: 'rgba(var(--primary-rgb), 0.15)' }}>
                  {selectedTooth}
                </div>
                <div>
                  <h3 className="text-sm font-black text-slate-800 dark:text-slate-100">
                    Configuration Détaillée de la Dent {selectedTooth}
                  </h3>
                  <p className="text-[11px] text-slate-400 font-bold">Entrez les profondeurs de poches, récessions et saignements sur 6 points.</p>
                </div>
              </div>
              <button 
                onClick={() => setSelectedTooth(null)}
                className="text-xs font-black text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 uppercase tracking-widest transition-colors"
              >
                Fermer
              </button>
            </div>

            {/* 6-POINTS GRID */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* FACE VESTIBULAIRE (BUCCAL) */}
              <div className="flex flex-col gap-4 p-5 rounded-2xl bg-slate-900/5 dark:bg-slate-800/20 border border-slate-200/30 dark:border-slate-800/30">
                <div className="text-xs font-black uppercase tracking-wider text-slate-500 dark:text-slate-400 pb-2 border-b border-slate-200/50 dark:border-slate-800/50">
                  Face Vestibulaire (Buccal)
                </div>
                
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div>
                    <div className="text-[9px] uppercase tracking-widest font-black text-slate-400 mb-1">Disto-Vestibulaire</div>
                    <PointControl 
                      pd={activeToothData.pd[0]}
                      gr={activeToothData.gr[0]}
                      bop={activeToothData.bop[0]}
                      plaque={activeToothData.plaque[0]}
                      onChange={(field, val) => updateToothData(selectedTooth, prev => {
                        const copy = { ...prev };
                        if (field === 'pd') copy.pd[0] = val as number;
                        if (field === 'gr') copy.gr[0] = val as number;
                        if (field === 'bop') copy.bop[0] = val as boolean;
                        if (field === 'plaque') copy.plaque[0] = val as boolean;
                        return copy;
                      })}
                    />
                  </div>

                  <div>
                    <div className="text-[9px] uppercase tracking-widest font-black text-slate-400 mb-1">Médio-Vestibulaire</div>
                    <PointControl 
                      pd={activeToothData.pd[1]}
                      gr={activeToothData.gr[1]}
                      bop={activeToothData.bop[1]}
                      plaque={activeToothData.plaque[1]}
                      onChange={(field, val) => updateToothData(selectedTooth, prev => {
                        const copy = { ...prev };
                        if (field === 'pd') copy.pd[1] = val as number;
                        if (field === 'gr') copy.gr[1] = val as number;
                        if (field === 'bop') copy.bop[1] = val as boolean;
                        if (field === 'plaque') copy.plaque[1] = val as boolean;
                        return copy;
                      })}
                    />
                  </div>

                  <div>
                    <div className="text-[9px] uppercase tracking-widest font-black text-slate-400 mb-1">Mésio-Vestibulaire</div>
                    <PointControl 
                      pd={activeToothData.pd[2]}
                      gr={activeToothData.gr[2]}
                      bop={activeToothData.bop[2]}
                      plaque={activeToothData.plaque[2]}
                      onChange={(field, val) => updateToothData(selectedTooth, prev => {
                        const copy = { ...prev };
                        if (field === 'pd') copy.pd[2] = val as number;
                        if (field === 'gr') copy.gr[2] = val as number;
                        if (field === 'bop') copy.bop[2] = val as boolean;
                        if (field === 'plaque') copy.plaque[2] = val as boolean;
                        return copy;
                      })}
                    />
                  </div>
                </div>
              </div>

              {/* FACE LINGUALE / PALATINE */}
              <div className="flex flex-col gap-4 p-5 rounded-2xl bg-slate-900/5 dark:bg-slate-800/20 border border-slate-200/30 dark:border-slate-800/30">
                <div className="text-xs font-black uppercase tracking-wider text-slate-500 dark:text-slate-400 pb-2 border-b border-slate-200/50 dark:border-slate-800/50">
                  Face Linguale / Palatine
                </div>
                
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div>
                    <div className="text-[9px] uppercase tracking-widest font-black text-slate-400 mb-1">Disto-Lingual</div>
                    <PointControl 
                      pd={activeToothData.pd[3]}
                      gr={activeToothData.gr[3]}
                      bop={activeToothData.bop[3]}
                      plaque={activeToothData.plaque[3]}
                      onChange={(field, val) => updateToothData(selectedTooth, prev => {
                        const copy = { ...prev };
                        if (field === 'pd') copy.pd[3] = val as number;
                        if (field === 'gr') copy.gr[3] = val as number;
                        if (field === 'bop') copy.bop[3] = val as boolean;
                        if (field === 'plaque') copy.plaque[3] = val as boolean;
                        return copy;
                      })}
                    />
                  </div>

                  <div>
                    <div className="text-[9px] uppercase tracking-widest font-black text-slate-400 mb-1">Médio-Lingual</div>
                    <PointControl 
                      pd={activeToothData.pd[4]}
                      gr={activeToothData.gr[4]}
                      bop={activeToothData.bop[4]}
                      plaque={activeToothData.plaque[4]}
                      onChange={(field, val) => updateToothData(selectedTooth, prev => {
                        const copy = { ...prev };
                        if (field === 'pd') copy.pd[4] = val as number;
                        if (field === 'gr') copy.gr[4] = val as number;
                        if (field === 'bop') copy.bop[4] = val as boolean;
                        if (field === 'plaque') copy.plaque[4] = val as boolean;
                        return copy;
                      })}
                    />
                  </div>

                  <div>
                    <div className="text-[9px] uppercase tracking-widest font-black text-slate-400 mb-1">Mésio-Lingual</div>
                    <PointControl 
                      pd={activeToothData.pd[5]}
                      gr={activeToothData.gr[5]}
                      bop={activeToothData.bop[5]}
                      plaque={activeToothData.plaque[5]}
                      onChange={(field, val) => updateToothData(selectedTooth, prev => {
                        const copy = { ...prev };
                        if (field === 'pd') copy.pd[5] = val as number;
                        if (field === 'gr') copy.gr[5] = val as number;
                        if (field === 'bop') copy.bop[5] = val as boolean;
                        if (field === 'plaque') copy.plaque[5] = val as boolean;
                        return copy;
                      })}
                    />
                  </div>
                </div>
              </div>

            </div>

            {/* ADDITIONAL CLINICAL PARAMETERS */}
            <div className="grid grid-cols-2 gap-4 border-t border-border-main pt-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest">Mobilité Dentaire</span>
                <div className="flex gap-1.5">
                  {([0, 1, 2, 3] as const).map(g => (
                    <button
                      key={g}
                      onClick={() => updateToothData(selectedTooth, prev => ({ ...prev, mobility: g }))}
                      className={cn(
                        "w-8 h-8 rounded-lg font-black text-xs transition-all border flex items-center justify-center",
                        activeToothData.mobility === g 
                          ? "bg-primary text-white border-primary" 
                          : "bg-slate-900/5 hover:bg-slate-100 dark:bg-slate-800/30 border-border-main text-slate-500"
                      )}
                      style={activeToothData.mobility === g ? { backgroundColor: 'var(--primary)', borderColor: 'var(--primary)' } : {}}
                    >
                      {g}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-xs font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest">Atteinte de Furcation</span>
                <div className="flex gap-1.5">
                  {([0, 1, 2, 3] as const).map(f => (
                    <button
                      key={f}
                      onClick={() => updateToothData(selectedTooth, prev => ({ ...prev, furcation: f }))}
                      className={cn(
                        "w-8 h-8 rounded-lg font-black text-xs transition-all border flex items-center justify-center",
                        activeToothData.furcation === f 
                          ? "bg-primary text-white border-primary" 
                          : "bg-slate-900/5 hover:bg-slate-100 dark:bg-slate-800/30 border-border-main text-slate-500"
                      )}
                      style={activeToothData.furcation === f ? { backgroundColor: 'var(--primary)', borderColor: 'var(--primary)' } : {}}
                    >
                      {f === 0 ? '0' : `F${f}`}
                    </button>
                  ))}
                </div>
              </div>
            </div>

          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
};

interface PointControlProps {
  pd: number;
  gr: number;
  bop: boolean;
  plaque: boolean;
  onChange: (field: 'pd' | 'gr' | 'bop' | 'plaque', val: number | boolean) => void;
}

const PointControl: React.FC<PointControlProps> = ({ pd, gr, bop, plaque, onChange }) => {
  return (
    <div className="flex flex-col gap-2 p-3 bg-card-bg border border-border-main rounded-xl items-center shadow-sm">
      
      {/* Probing Depth (PD) */}
      <div className="flex flex-col items-center">
        <span className="text-[8px] uppercase tracking-widest font-black text-slate-400">Poche (PD)</span>
        <div className="flex items-center gap-1.5 mt-0.5">
          <button 
            onClick={() => onChange('pd', Math.max(1, pd - 1))}
            className="w-5 h-5 rounded bg-slate-900/5 hover:bg-slate-100 dark:bg-slate-800 dark:hover:bg-slate-700 font-bold text-xs flex items-center justify-center text-text-main"
          >-</button>
          <span className={cn("text-xs font-mono font-black w-6 text-center rounded py-0.5", 
            pd <= 3 ? "text-emerald-500 bg-emerald-500/10" : 
            pd <= 5 ? "text-amber-500 bg-amber-500/10" : 
            "text-rose-500 bg-rose-500/10"
          )}>{pd}</span>
          <button 
            onClick={() => onChange('pd', Math.min(9, pd + 1))}
            className="w-5 h-5 rounded bg-slate-900/5 hover:bg-slate-100 dark:bg-slate-800 dark:hover:bg-slate-700 font-bold text-xs flex items-center justify-center text-text-main"
          >+</button>
        </div>
      </div>

      {/* Gingival Recession (GR) */}
      <div className="flex flex-col items-center">
        <span className="text-[8px] uppercase tracking-widest font-black text-slate-400">Recession (GR)</span>
        <div className="flex items-center gap-1.5 mt-0.5">
          <button 
            onClick={() => onChange('gr', Math.max(0, gr - 1))}
            className="w-5 h-5 rounded bg-slate-900/5 hover:bg-slate-100 dark:bg-slate-800 dark:hover:bg-slate-700 font-bold text-xs flex items-center justify-center text-text-main"
          >-</button>
          <span className="text-xs font-mono font-black w-6 text-center text-slate-700 dark:text-slate-200">{gr}</span>
          <button 
            onClick={() => onChange('gr', Math.min(9, gr + 1))}
            className="w-5 h-5 rounded bg-slate-900/5 hover:bg-slate-100 dark:bg-slate-800 dark:hover:bg-slate-700 font-bold text-xs flex items-center justify-center text-text-main"
          >+</button>
        </div>
      </div>

      {/* BOP & Plaque buttons */}
      <div className="flex gap-2 border-t border-slate-100 dark:border-slate-800 w-full pt-2 mt-1 justify-center">
        <button
          onClick={() => onChange('bop', !bop)}
          className={cn(
            "px-2 py-1 rounded text-[8px] uppercase font-black tracking-widest border transition-all",
            bop 
              ? "bg-rose-500/15 border-rose-500/30 text-rose-500" 
              : "bg-slate-900/5 border-border-main text-slate-400 hover:text-slate-600"
          )}
        >
          BOP
        </button>

        <button
          onClick={() => onChange('plaque', !plaque)}
          className={cn(
            "px-2 py-1 rounded text-[8px] uppercase font-black tracking-widest border transition-all",
            plaque 
              ? "bg-amber-500/15 border-amber-500/30 text-amber-500" 
              : "bg-slate-900/5 border-border-main text-slate-400 hover:text-slate-600"
          )}
        >
          PLQ
        </button>
      </div>

    </div>
  );
};
