/**
 * Odontogram.tsx
 * Contrôleur parent unifié utilisant TreatmentSelector pour l'intelligence clinique
 */
import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Stethoscope, Save, RotateCcw, FileText, AlertCircle, X, User, Baby, Zap, Check } from 'lucide-react';
import { cn } from '../../utils/cn';
import { OdontogramSVG } from './OdontogramSVG';
import { TreatmentSelector } from './TreatmentSelector';
import type { 
  ToothSurfaceState,
  SurfaceState,
  SelectedSurfaceData,
  OdontogramType,
  ToothSurface
} from './types';
import { 
  DEFAULT_SURFACE_STATE,
  SURFACE_LABELS,
  TREATMENTS_BY_CATEGORY,
  ALL_TEETH_FDI,
  ALL_TEETH_PEDRIATIC
} from './types';

// ============================================================================
// TYPES
// ============================================================================

interface OdontogramProps {
  patientId: number;
  scope?: 'UNITAIRE' | 'MULTIDENTS' | 'GLOBAL';
  mode?: 'VIEW' | 'EDIT_STATUS' | 'PLAN_TREATMENT' | 'SELECT_FOR_DOCUMENT';
  initialData?: Record<number, ToothSurfaceState>;
  initialStatus?: Record<number, any>;
  defaultType?: OdontogramType;
  onChange?: (selectedSurfaces: SelectedSurfaceData[]) => void;
  onSave?: (data: SelectedSurfaceData[]) => Promise<void>;
  readOnly?: boolean;
  showLegend?: boolean;
  compact?: boolean;
  className?: string;
  naked?: boolean;
  embeddedSelector?: boolean;
}

// ============================================================================
// COMPOSANT PRINCIPAL
// ============================================================================

const createDefaultTeethSurfaces = (type: OdontogramType): Record<number, ToothSurfaceState> => {
  const teeth: Record<number, ToothSurfaceState> = {};
  const toothList = type === 'ADULT' ? ALL_TEETH_FDI : ALL_TEETH_PEDRIATIC;
  toothList.forEach(num => {
    teeth[num] = { ...DEFAULT_SURFACE_STATE };
  });
  return teeth;
};

const STATUS_LEGEND = [
  { state: 'HEALTHY', label: 'Sain', color: 'bg-white border-slate-300' },
  { state: 'CARIES', label: 'Carie', color: 'bg-red-500' },
  { state: 'FILLING_COMPOSITE', label: 'Composite', color: 'bg-sky-500' },
  { state: 'FILLING_AMALGAM', label: 'Amalgame', color: 'bg-slate-400' },
  { state: 'CROWN', label: 'Couronne', color: 'bg-amber-200 border-amber-400' },
  { state: 'ROOT_CANAL', label: 'Dévitalisé', color: 'bg-slate-200' },
  { state: 'IMPLANT', label: 'Implant', color: 'bg-slate-400' },
];

export const Odontogram: React.FC<OdontogramProps> = ({
  patientId: _patientId,
  mode = 'SELECT_FOR_DOCUMENT',
  initialData,
  initialStatus: _initialStatus,
  defaultType = 'ADULT',
  onChange,
  onSave,
  readOnly = false,
  showLegend = true,
  compact = false,
  className = '',
  naked = false,
  embeddedSelector = false,
}) => {
  const [odontogramType, setOdontogramType] = useState<OdontogramType>(defaultType);
  const [teethSurfaces, setTeethSurfaces] = useState<Record<number, ToothSurfaceState>>(
    initialData || createDefaultTeethSurfaces(defaultType)
  );

  const [selectedSurfaces, setSelectedSurfaces] = useState<SelectedSurfaceData[]>([]);
  const [activeTooth, setActiveTooth] = useState<number | null>(null);
  const [showGlobalSelector, setShowGlobalSelector] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Synchronisation avec la prop defaultType (v4.9)
  useEffect(() => {
    if (defaultType !== odontogramType) {
      setOdontogramType(defaultType);
      setTeethSurfaces(initialData || createDefaultTeethSurfaces(defaultType));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [defaultType]);

  const handleTypeChange = useCallback((newType: OdontogramType) => {
    setOdontogramType(newType);
    setTeethSurfaces(initialData || createDefaultTeethSurfaces(newType));
    setSelectedSurfaces([]);
    setActiveTooth(null);
  }, [initialData]);

  const handleReset = useCallback(() => {
    setSelectedSurfaces([]);
    setTeethSurfaces(initialData || createDefaultTeethSurfaces(odontogramType));
    setActiveTooth(null);
    setSaveError(null);
  }, [initialData, odontogramType]);

  const handleSurfaceClick = useCallback((
    toothNumber: number, 
    surface: 'M' | 'D' | 'O' | 'V' | 'P',
    _event: React.MouseEvent
  ) => {
    if (readOnly) return;

    if (mode === 'SELECT_FOR_DOCUMENT') {
      setActiveTooth(toothNumber);
    } else if (mode === 'EDIT_STATUS') {
      const currentState = teethSurfaces[toothNumber][surface];
      const stateOrder: SurfaceState[] = [
        'HEALTHY', 'CARIES', 'FILLING_COMPOSITE', 'FILLING_AMALGAM', 'CROWN'
      ];
      const currentIndex = stateOrder.indexOf(currentState);
      const nextState = stateOrder[(currentIndex + 1) % stateOrder.length];
      
      setTeethSurfaces(prev => ({
        ...prev,
        [toothNumber]: {
          ...prev[toothNumber],
          [surface]: nextState
        }
      }));
    }
  }, [readOnly, mode, teethSurfaces]);

  useEffect(() => {
    onChange?.(selectedSurfaces);
  }, [selectedSurfaces, onChange]);

  const handleSave = useCallback(async () => {
    if (!onSave) return;
    setIsSaving(true);
    setSaveError(null);
    try {
      await onSave(selectedSurfaces);
    } catch (err) {
      setSaveError('Erreur lors de la sauvegarde');
    } finally {
      setIsSaving(false);
    }
  }, [onSave, selectedSurfaces]);

  const totals = useMemo(() => {
    return selectedSurfaces.reduce((acc, surface) => {
      const surfaceTotal = surface.treatments.reduce((sum, t) => sum + (t.price || 0), 0);
      return { count: acc.count + surface.treatments.length, price: acc.price + surfaceTotal };
    }, { count: 0, price: 0 });
  }, [selectedSurfaces]);

  return (
    <div className={cn(
      "overflow-hidden transition-all duration-500",
      naked ? "bg-transparent shadow-none border-none" : "bg-white rounded-3xl shadow-lg border border-gray-100",
      className
    )}>
      {/* Header avec Toggle Adulte/Enfant */}
      {!naked && (
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-gray-50/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-slate-100 rounded-xl flex items-center justify-center">
              <Stethoscope className="w-5 h-5 text-slate-600" />
            </div>
            <div>
              <h3 className="font-bold text-gray-900">Odontogramme FDI</h3>
              <p className="text-xs text-gray-500">
                {odontogramType === 'ADULT' ? '32 dents' : '20 dents'} • Cliquez sur une face
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="flex bg-gray-200 rounded-xl p-1">
              <button
                onClick={() => handleTypeChange('ADULT')}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all",
                  odontogramType === 'ADULT' ? 'bg-white text-slate-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                )}
              >
                <User className="w-4 h-4" /> Adulte
              </button>
              <button
                onClick={() => handleTypeChange('PEDIATRIC')}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all",
                  odontogramType === 'PEDIATRIC' ? 'bg-white text-slate-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                )}
              >
                <Baby className="w-4 h-4" /> Enfant
              </button>
            </div>
            
            {!readOnly && (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowGlobalSelector(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-indigo-50 text-indigo-700 border border-indigo-100 rounded-xl font-medium hover:bg-indigo-100 transition-all"
                >
                  <Zap className="w-4 h-4" /> Actes Globaux
                </button>
                <button
                  onClick={handleReset}
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <RotateCcw className="w-4 h-4" />
                </button>
                {onSave && (
                  <button
                    onClick={handleSave}
                    disabled={isSaving || selectedSurfaces.length === 0}
                    className="flex items-center gap-2 px-4 py-2 bg-slate-700 text-white rounded-xl font-medium hover:bg-slate-800 disabled:opacity-50 transition-all"
                  >
                    {isSaving ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Save className="w-4 h-4" />}
                    Sauvegarder
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Error */}
      <AnimatePresence>
        {saveError && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="px-6 py-3 bg-red-50 border-b border-red-100">
            <div className="flex items-center gap-2 text-red-600 text-sm">
              <AlertCircle className="w-4 h-4" /> {saveError}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Content */}
      <div className={cn(
        "relative transition-all duration-500",
        activeTooth && embeddedSelector ? "opacity-0 scale-90 pointer-events-none" : "opacity-100 scale-100",
        compact && "p-4"
      )}>
        <OdontogramSVG
          type={odontogramType}
          teethSurfaces={teethSurfaces}
          selectedTooth={activeTooth}
          selectedSurface={null}
          onSurfaceClick={handleSurfaceClick}
          showNumbers={!compact}
          readOnly={readOnly}
        />

        {/* Récapitulatif des sélections */}
        {selectedSurfaces.length > 0 && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="mt-6 p-4 bg-gray-50 rounded-2xl">
            <h4 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <FileText className="w-4 h-4" /> Surfaces sélectionnées ({selectedSurfaces.length})
            </h4>
            <div className="space-y-2 max-h-48 overflow-y-auto custom-scrollbar">
              {selectedSurfaces.map((surfaceData, idx) => (
                <div key={`${surfaceData.toothNumber}-${surfaceData.surface}-${idx}`} className="flex items-center justify-between p-3 bg-white rounded-xl border border-gray-100">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1.5">
                      <span className="w-8 h-8 bg-slate-100 text-slate-700 rounded-lg flex items-center justify-center font-bold text-sm">{surfaceData.toothNumber}</span>
                      <span className="px-2 py-1 bg-slate-50 text-slate-600 rounded text-xs font-medium">{SURFACE_LABELS[surfaceData.surface as ToothSurface] || surfaceData.surface}</span>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">{surfaceData.treatments.map(t => t.name).join(', ')}</p>
                    </div>
                  </div>
                  <span className="font-bold text-gray-900">{surfaceData.treatments.reduce((sum, t) => sum + (t.price || 0), 0)} MAD</span>
                </div>
              ))}
            </div>
            <div className="mt-4 pt-4 border-t border-gray-200 flex items-center justify-between">
              <span className="text-gray-600">Total</span>
              <span className="text-2xl font-bold text-slate-700">{totals.price} MAD</span>
            </div>
          </motion.div>
        )}

        {/* Légende */}
        {showLegend && !compact && (
          <div className="mt-6 pt-6 border-t border-gray-100">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Légende</h4>
            <div className="flex flex-wrap gap-2">
              {STATUS_LEGEND.map(({ state, label, color }) => (
                <div key={state} className="flex items-center gap-2 px-3 py-1.5 bg-gray-50 rounded-lg">
                  <div className={cn("w-4 h-4 rounded border", color)} />
                  <span className="text-xs text-gray-600">{label}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Elite TreatmentSelector Integration (v4.9) */}
      <AnimatePresence>
        {activeTooth && (
          <div className={cn(
            embeddedSelector ? "absolute inset-0 z-50 bg-slate-900 rounded-[2.5rem] overflow-hidden" : ""
          )}>
            <TreatmentSelector
              toothNumber={activeTooth as any}
              currentTreatments={selectedSurfaces.filter(s => s.toothNumber === activeTooth).flatMap(s => s.treatments)}
              embedded={embeddedSelector}
              onConfirm={(treatments, surfaces, _notes) => {
                const newSelections: SelectedSurfaceData[] = surfaces.length > 0 
                  ? surfaces.map(surf => ({ toothNumber: activeTooth, surface: surf, treatments }))
                  : [{ toothNumber: activeTooth, surface: 'ALL', treatments }];

                setSelectedSurfaces(prev => {
                  const others = prev.filter(s => s.toothNumber !== activeTooth);
                  return [...others, ...newSelections];
                });

                // Update visual state (optional: map first treatment to status)
                if (treatments.length > 0) {
                  const mainCat = treatments[0].category;
                  let status: SurfaceState = 'SELECTED';
                  if (mainCat === 'CONSERVATRICE') status = 'FILLING_COMPOSITE';
                  if (mainCat === 'CHIRURGIE') status = 'ABSENT';
                  if (mainCat === 'PROTHESE') status = 'CROWN';
                  
                  setTeethSurfaces(prev => ({
                    ...prev,
                    [activeTooth]: surfaces.reduce((acc, surf) => ({ ...acc, [surf]: status }), { ...prev[activeTooth] })
                  }));
                }

                setActiveTooth(null);
              }}
              onCancel={() => setActiveTooth(null)}
            />
          </div>
        )}
      </AnimatePresence>

      {/* Modal Actes Globaux */}
      <AnimatePresence>
        {showGlobalSelector && (
          <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
            <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }} className="bg-white rounded-3xl shadow-2xl w-full max-w-2xl overflow-hidden">
              <div className="bg-gradient-to-r from-indigo-600 to-violet-700 px-6 py-4 text-white flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Zap className="w-5 h-5" />
                  <div><h3 className="font-bold">Actes Globaux</h3><p className="text-xs text-indigo-100">Ortho, Prothèse amovible...</p></div>
                </div>
                <button onClick={() => setShowGlobalSelector(false)} className="p-2 hover:bg-white/20 rounded-xl transition-colors"><X className="w-5 h-5" /></button>
              </div>
              <div className="p-6 max-h-[70vh] overflow-y-auto">
                {Object.keys(TREATMENTS_BY_CATEGORY).filter(cat => TREATMENTS_BY_CATEGORY[cat].some(t => t.scope !== 'UNITAIRE')).map(category => (
                  <div key={category} className="mb-6">
                    <h4 className="text-sm font-bold text-slate-500 uppercase tracking-widest mb-3 flex items-center gap-2">{category}</h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {TREATMENTS_BY_CATEGORY[category].filter(t => t.scope !== 'UNITAIRE').map(template => (
                        <button key={template.id} onClick={() => {
                          setSelectedSurfaces(prev => [...prev, { toothNumber: 0, surface: 'ALL', treatments: [{ ...template, price: 0 }] }]);
                          setShowGlobalSelector(false);
                        }} className="flex items-center gap-3 p-3 bg-slate-50 hover:bg-slate-100 rounded-2xl text-left transition-all border border-transparent hover:border-slate-200">
                          <Check className="w-5 h-5 opacity-20 text-indigo-600" />
                          <span className="font-semibold text-slate-700 text-sm">{template.name}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
              <div className="p-4 bg-slate-50 border-t border-slate-100 flex justify-end">
                <button onClick={() => setShowGlobalSelector(false)} className="px-6 py-2.5 bg-slate-700 text-white rounded-xl font-bold hover:bg-slate-800 transition-all">Fermer</button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Odontogram;
