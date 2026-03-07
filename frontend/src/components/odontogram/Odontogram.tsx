/**
 * Odontogram.tsx
 * Contrôleur parent avec sélection "Direct-to-Surface" et support Adulte/Pédiatrique
 * Menu flottant (Popover) ultra-rapide au clic
 */
import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Stethoscope, Save, RotateCcw, FileText, AlertCircle, X, Check, Clock, User, Baby } from 'lucide-react';
import { OdontogramSVG } from './OdontogramSVG';
import type { 
  ToothTreatment, 
  ToothSurfaceState,
  SurfaceState,
  SelectedSurfaceData,
  OdontogramType
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
}

interface SurfacePopoverProps {
  toothNumber: number;
  surface: 'M' | 'D' | 'O' | 'V' | 'P';
  position: { x: number; y: number };
  currentTreatments: ToothTreatment[];
  currentPrice: number;
  onConfirm: (treatments: ToothTreatment[], price: number, surfaceState: SurfaceState) => void;
  onCancel: () => void;
}

// ============================================================================
// POPOVER Flottant de sélection rapide
// ============================================================================

const CATEGORY_COLORS: Record<string, { bg: string; border: string; text: string; dot: string }> = {
  CONSERVATRICE: { bg: 'bg-sky-50', border: 'border-sky-200', text: 'text-sky-700', dot: 'bg-sky-500' },
  ENDODONTIE: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', dot: 'bg-red-500' },
  CHIRURGIE: { bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-700', dot: 'bg-purple-500' },
  PROTHESE: { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-700', dot: 'bg-amber-500' },
  PREVENTION: { bg: 'bg-emerald-50', border: 'border-emerald-200', text: 'text-emerald-700', dot: 'bg-emerald-500' },
  PARODONTOLOGIE: { bg: 'bg-pink-50', border: 'border-pink-200', text: 'text-pink-700', dot: 'bg-pink-500' },
  ESTHETIQUE: { bg: 'bg-cyan-50', border: 'border-cyan-200', text: 'text-cyan-700', dot: 'bg-cyan-500' },
};

const CATEGORY_LABELS: Record<string, string> = {
  CONSERVATRICE: 'Conservatrice',
  ENDODONTIE: 'Endodontie',
  CHIRURGIE: 'Chirurgie',
  PROTHESE: 'Prothèse',
  PREVENTION: 'Prévention',
  PARODONTOLOGIE: 'Parodontologie',
  ESTHETIQUE: 'Esthétique',
};

// Mapping traitement vers état de surface
const getSurfaceStateFromTreatment = (treatment: ToothTreatment): SurfaceState => {
  switch (treatment.category) {
    case 'CONSERVATRICE':
      if (treatment.name.includes('Amalgame')) return 'FILLING_AMALGAM';
      if (treatment.name.includes('Composite')) return 'FILLING_COMPOSITE';
      if (treatment.name.includes('Or')) return 'FILLING_GOLD';
      return 'FILLING_COMPOSITE';
    case 'ENDODONTIE':
      return 'ROOT_CANAL';
    case 'PROTHESE':
      if (treatment.name.includes('Couronne')) return 'CROWN';
      if (treatment.name.includes('Inlay')) return 'INLAY';
      if (treatment.name.includes('Onlay')) return 'ONLAY';
      return 'CROWN';
    case 'CHIRURGIE':
      if (treatment.name.includes('Extraction')) return 'ABSENT';
      if (treatment.name.includes('Implant')) return 'IMPLANT';
      return 'SELECTED';
    case 'PREVENTION':
      if (treatment.name.includes('Sceau')) return 'SEALANT';
      return 'HEALTHY';
    default:
      return 'SELECTED';
  }
};

const SurfacePopover: React.FC<SurfacePopoverProps> = ({
  toothNumber,
  surface,
  position,
  currentTreatments,
  currentPrice,
  onConfirm,
  onCancel,
}) => {
  const [selectedTreatments, setSelectedTreatments] = useState<ToothTreatment[]>(currentTreatments);
  const [price, setPrice] = useState<number>(currentPrice);
  const [activeCategory, setActiveCategory] = useState<string>('CONSERVATRICE');

  const surfaceLabel = SURFACE_LABELS[surface] || surface;

  // Ajuster la position pour ne pas dépasser de l'écran
  const adjustedPosition = useMemo(() => {
    const popoverWidth = 360;
    const popoverHeight = 400;
    let { x, y } = position;
    
    if (x + popoverWidth > window.innerWidth - 20) {
      x = window.innerWidth - popoverWidth - 20;
    }
    if (x < 20) x = 20;
    
    if (y + popoverHeight > window.innerHeight - 20) {
      y = y - popoverHeight - 20;
    }
    if (y < 20) y = 20;
    
    return { x, y };
  }, [position]);

  const toggleTreatment = (template: Omit<ToothTreatment, 'price'>) => {
    const exists = selectedTreatments.find(t => t.id === template.id);
    if (exists) {
      setSelectedTreatments(prev => prev.filter(t => t.id !== template.id));
    } else {
      const newTreatment: ToothTreatment = { ...template, price };
      setSelectedTreatments(prev => [...prev, newTreatment]);
    }
  };

  const handleConfirm = () => {
    const mainTreatment = selectedTreatments[0];
    const surfaceState = mainTreatment ? getSurfaceStateFromTreatment(mainTreatment) : 'SELECTED';
    onConfirm(selectedTreatments, price, surfaceState);
  };

  // EJECTION DOM via createPortal pour briser le CSS Containing Block
  return createPortal(
    <motion.div
      initial={{ opacity: 0, scale: 0.9, y: 10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9, y: 10 }}
      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
      className="fixed z-[9999] bg-white rounded-2xl shadow-2xl border border-gray-200 overflow-hidden"
      style={{ 
        left: adjustedPosition.x, 
        top: adjustedPosition.y,
        width: '360px',
        maxHeight: '450px'
      }}
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-700 to-slate-800 px-4 py-3 text-white flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center text-lg font-bold">
            {toothNumber}
          </div>
          <div>
            <h3 className="font-bold text-sm">Dent {toothNumber}</h3>
            <p className="text-xs text-slate-300">Face {surfaceLabel} ({surface})</p>
          </div>
        </div>
        <button 
          onClick={onCancel}
          className="p-1.5 hover:bg-white/20 rounded-lg transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <div className="p-4 max-h-[350px] overflow-y-auto">
        {/* Catégories */}
        <div className="flex gap-1.5 mb-3 overflow-x-auto pb-2 scrollbar-thin">
          {Object.keys(TREATMENTS_BY_CATEGORY).map(category => (
            <button
              key={category}
              onClick={() => setActiveCategory(category)}
              className={`px-2.5 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
                activeCategory === category
                  ? `${CATEGORY_COLORS[category].bg} ${CATEGORY_COLORS[category].text} ring-1 ring-offset-1 ${CATEGORY_COLORS[category].border.replace('border', 'ring')}`
                  : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
              }`}
            >
              {CATEGORY_LABELS[category]}
            </button>
          ))}
        </div>

        {/* Traitements rapides */}
        <div className="space-y-1.5 mb-4">
          {TREATMENTS_BY_CATEGORY[activeCategory]?.slice(0, 6).map(template => {
            const isSelected = selectedTreatments.find(t => t.id === template.id);
            const colors = CATEGORY_COLORS[template.category];
            
            return (
              <button
                key={template.id}
                onClick={() => toggleTreatment(template)}
                className={`w-full flex items-center gap-2 px-3 py-2 rounded-xl text-left text-sm transition-all ${
                  isSelected
                    ? `${colors.bg} ${colors.text} ring-1 ${colors.border}`
                    : 'bg-gray-50 text-gray-700 hover:bg-gray-100'
                }`}
              >
                <div className={`w-4 h-4 rounded-full flex items-center justify-center ${
                  isSelected ? colors.dot : 'bg-gray-300'
                }`}>
                  {isSelected && <Check className="w-2.5 h-2.5 text-white" />}
                </div>
                <span className="flex-1 font-medium">{template.name}</span>
                {template.duration && (
                  <span className="text-xs text-gray-400 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {template.duration}min
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Prix */}
        {selectedTreatments.length > 0 && (
          <div className="border-t border-gray-100 pt-3 mb-3">
            <label className="text-xs font-semibold text-gray-500 mb-1.5 block">Prix (MAD)</label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                value={price || ''}
                onChange={(e) => setPrice(Number(e.target.value))}
                placeholder="0"
                className="flex-1 px-3 py-2 bg-gray-50 border border-gray-200 rounded-xl text-right font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                autoFocus
              />
              <span className="text-gray-500 font-medium text-sm">MAD</span>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          <button
            onClick={onCancel}
            className="flex-1 py-2.5 bg-gray-100 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-200 transition-colors"
          >
            Annuler
          </button>
          <button
            onClick={handleConfirm}
            disabled={selectedTreatments.length === 0}
            className="flex-1 py-2.5 bg-slate-700 text-white rounded-xl text-sm font-medium hover:bg-slate-800 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            <Check className="w-4 h-4" />
            Valider
          </button>
        </div>
      </div>
    </motion.div>,
    document.body
  );
};

// ============================================================================
// COMPOSANT PRINCIPAL
// ============================================================================

// État initial par défaut
const createDefaultTeethSurfaces = (type: OdontogramType): Record<number, ToothSurfaceState> => {
  const teeth: Record<number, ToothSurfaceState> = {};
  const toothList = type === 'ADULT' ? ALL_TEETH_FDI : ALL_TEETH_PEDRIATIC;
  toothList.forEach(num => {
    teeth[num] = { ...DEFAULT_SURFACE_STATE };
  });
  return teeth;
};



// Légende mise à jour
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
  initialStatus,
  defaultType = 'ADULT',
  onChange,
  onSave,
  readOnly = false,
  showLegend = true,
  compact = false,
  className = '',
}) => {
  const [odontogramType, setOdontogramType] = useState<OdontogramType>(defaultType);
  const [teethSurfaces, setTeethSurfaces] = useState<Record<number, ToothSurfaceState>>(
    initialData || createDefaultTeethSurfaces(defaultType)
  );

  const [selectedSurfaces, setSelectedSurfaces] = useState<SelectedSurfaceData[]>([]);
  const [activeTooth, setActiveTooth] = useState<number | null>(null);
  const [activeSurface, setActiveSurface] = useState<'M' | 'D' | 'O' | 'V' | 'P' | null>(null);
  const [popoverPosition, setPopoverPosition] = useState<{ x: number; y: number } | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Réinitialiser quand on change de type
  const handleTypeChange = useCallback((newType: OdontogramType) => {
    setOdontogramType(newType);
    setTeethSurfaces(initialData || createDefaultTeethSurfaces(newType));
    setSelectedSurfaces([]);
    setActiveTooth(null);
    setActiveSurface(null);
    setPopoverPosition(null);
  }, [initialData, initialStatus]);

  const handleReset = useCallback(() => {
    setSelectedSurfaces([]);
    setTeethSurfaces(initialData || createDefaultTeethSurfaces(odontogramType));
    setActiveTooth(null);
    setActiveSurface(null);
    setPopoverPosition(null);
    setSaveError(null);
  }, [initialData, initialStatus, odontogramType]);

  // Gestion du clic sur une surface
  const handleSurfaceClick = useCallback((
    toothNumber: number, 
    surface: 'M' | 'D' | 'O' | 'V' | 'P',
    event: React.MouseEvent
  ) => {
    if (readOnly) return;

    if (mode === 'SELECT_FOR_DOCUMENT') {
      setActiveTooth(toothNumber);
      setActiveSurface(surface);
      
      const rect = (event.target as Element).getBoundingClientRect();
      setPopoverPosition({
        x: rect.left + rect.width / 2,
        y: rect.top + rect.height / 2
      });
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

  // Confirmation depuis le popover
  const handleConfirmPopover = useCallback((
    treatments: ToothTreatment[],
    price: number,
    surfaceState: SurfaceState
  ) => {
    if (!activeTooth || !activeSurface) return;

    // Mettre à jour l'état de la surface
    setTeethSurfaces(prev => ({
      ...prev,
      [activeTooth]: {
        ...prev[activeTooth],
        [activeSurface]: surfaceState
      }
    }));

    // Ajouter aux sélections
    const newData: SelectedSurfaceData = {
      toothNumber: activeTooth,
      surface: activeSurface,
      treatments: treatments.map(t => ({ ...t, price })),
    };

    setSelectedSurfaces(prev => {
      const existingIndex = prev.findIndex(
        s => s.toothNumber === activeTooth && s.surface === activeSurface
      );
      if (existingIndex >= 0) {
        const updated = [...prev];
        updated[existingIndex] = newData;
        return updated;
      }
      return [...prev, newData];
    });

    setPopoverPosition(null);
    setActiveTooth(null);
    setActiveSurface(null);
  }, [activeTooth, activeSurface]);

  const handleCancelPopover = useCallback(() => {
    setPopoverPosition(null);
    setActiveTooth(null);
    setActiveSurface(null);
  }, []);

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

  const currentPopoverData = useMemo(() => {
    if (!activeTooth || !activeSurface) return null;
    const existing = selectedSurfaces.find(
      s => s.toothNumber === activeTooth && s.surface === activeSurface
    );
    return {
      treatments: existing?.treatments || [],
      price: existing?.treatments[0]?.price || 0
    };
  }, [activeTooth, activeSurface, selectedSurfaces]);

  // Les noms des dents sont gérés dans le composant SVG

  return (
    <div className={`bg-white rounded-3xl shadow-lg border border-gray-100 overflow-hidden ${className}`}>
      {/* Header avec Toggle Adulte/Enfant */}
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
          {/* Toggle Adulte / Enfant */}
          <div className="flex bg-gray-200 rounded-xl p-1">
            <button
              onClick={() => handleTypeChange('ADULT')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                odontogramType === 'ADULT'
                  ? 'bg-white text-slate-700 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <User className="w-4 h-4" />
              Adulte
            </button>
            <button
              onClick={() => handleTypeChange('PEDIATRIC')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                odontogramType === 'PEDIATRIC'
                  ? 'bg-white text-slate-700 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <Baby className="w-4 h-4" />
              Enfant
            </button>
          </div>
          
          {!readOnly && (
            <div className="flex items-center gap-2">
              <button
                onClick={handleReset}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                title="Réinitialiser"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
              {onSave && (
                <button
                  onClick={handleSave}
                  disabled={isSaving || selectedSurfaces.length === 0}
                  className="flex items-center gap-2 px-4 py-2 bg-slate-700 text-white rounded-xl font-medium hover:bg-slate-800 disabled:opacity-50 transition-all"
                >
                  {isSaving ? (
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <Save className="w-4 h-4" />
                  )}
                  Sauvegarder
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Error */}
      <AnimatePresence>
        {saveError && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="px-6 py-3 bg-red-50 border-b border-red-100"
          >
            <div className="flex items-center gap-2 text-red-600 text-sm">
              <AlertCircle className="w-4 h-4" />
              {saveError}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Content */}
      <div className={`p-6 ${compact ? 'p-4' : ''}`}>
        <OdontogramSVG
          type={odontogramType}
          teethSurfaces={teethSurfaces}
          selectedTooth={activeTooth}
          selectedSurface={activeSurface}
          onSurfaceClick={handleSurfaceClick}
          showNumbers={!compact}
          readOnly={readOnly}
        />

        {/* Récapitulatif des sélections */}
        {selectedSurfaces.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mt-6 p-4 bg-gray-50 rounded-2xl"
          >
            <h4 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Surfaces sélectionnées ({selectedSurfaces.length})
            </h4>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {selectedSurfaces.map((surfaceData, idx) => (
                <div
                  key={`${surfaceData.toothNumber}-${surfaceData.surface}-${idx}`}
                  className="flex items-center justify-between p-3 bg-white rounded-xl border border-gray-100"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1.5">
                      <span className="w-8 h-8 bg-slate-100 text-slate-700 rounded-lg flex items-center justify-center font-bold text-sm">
                        {surfaceData.toothNumber}
                      </span>
                      <span className="px-2 py-1 bg-slate-50 text-slate-600 rounded text-xs font-medium">
                        {SURFACE_LABELS[surfaceData.surface] || surfaceData.surface}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {surfaceData.treatments.map(t => t.name).join(', ')}
                      </p>
                    </div>
                  </div>
                  <span className="font-bold text-gray-900">
                    {surfaceData.treatments.reduce((sum, t) => sum + (t.price || 0), 0)} MAD
                  </span>
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
                  <div className={`w-4 h-4 rounded ${color} border`} />
                  <span className="text-xs text-gray-600">{label}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Popover flottant */}
      <AnimatePresence>
        {popoverPosition && activeTooth && activeSurface && (
          <SurfacePopover
            toothNumber={activeTooth}
            surface={activeSurface}
            position={popoverPosition}
            currentTreatments={currentPopoverData?.treatments || []}
            currentPrice={currentPopoverData?.price || 0}
            onConfirm={handleConfirmPopover}
            onCancel={handleCancelPopover}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default Odontogram;