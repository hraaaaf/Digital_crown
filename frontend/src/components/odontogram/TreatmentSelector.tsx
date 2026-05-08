/**
 * TreatmentSelector.tsx
 * Modal de sélection des traitements - Prix libre en MAD
 */
import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { X, Check, Clock, Zap, Stethoscope } from 'lucide-react';
import type { ToothNumberFDI, ToothTreatment, ToothSurface } from './types';
import { TREATMENT_TEMPLATES, TREATMENTS_BY_CATEGORY, TOOTH_NAMES } from './types';

interface TreatmentSelectorProps {
  toothNumber: ToothNumberFDI;
  currentTreatments: ToothTreatment[];
  onConfirm: (treatments: ToothTreatment[], surfaces: ToothSurface[], notes: string) => void;
  onCancel: () => void;
}

const CATEGORY_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  CONSERVATRICE: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700' },
  ENDODONTIE: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700' },
  CHIRURGIE: { bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-700' },
  PROTHESE: { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-700' },
  PREVENTION: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-700' },
  PARODONTOLOGIE: { bg: 'bg-pink-50', border: 'border-pink-200', text: 'text-pink-700' },
  ESTHETIQUE: { bg: 'bg-cyan-50', border: 'border-cyan-200', text: 'text-cyan-700' },
  ORTHODONTIE: { bg: 'bg-indigo-50', border: 'border-indigo-200', text: 'text-indigo-700' },
};

const CATEGORY_LABELS: Record<string, string> = {
  CONSERVATRICE: 'Conservatrice',
  ENDODONTIE: 'Endodontie',
  CHIRURGIE: 'Chirurgie',
  PROTHESE: 'Prothèse',
  PREVENTION: 'Prévention',
  PARODONTOLOGIE: 'Parodontologie',
  ESTHETIQUE: 'Esthétique',
  ORTHODONTIE: 'Orthodontie',
};

const SURFACES: { code: ToothSurface; label: string }[] = [
  { code: 'M', label: 'Mésiale' },
  { code: 'O', label: 'Occlusale' },
  { code: 'D', label: 'Distale' },
  { code: 'B', label: 'Buccale' },
  { code: 'L', label: 'Linguale' },
  { code: 'MOD', label: 'MOD (3 sfc)' },
  { code: 'MO', label: 'MO' },
  { code: 'DO', label: 'DO' },
];

export const TreatmentSelector: React.FC<TreatmentSelectorProps> = ({
  toothNumber,
  currentTreatments,
  onConfirm,
  onCancel,
}) => {
  const [selectedTreatments, setSelectedTreatments] = useState<ToothTreatment[]>(currentTreatments);
  const [treatmentPrices, setTreatmentPrices] = useState<Record<string, number>>({});
  const [selectedSurfaces, setSelectedSurfaces] = useState<ToothSurface[]>([]);
  const [activeCategory, setActiveCategory] = useState<string>('CONSERVATRICE');
  const [notes, setNotes] = useState('');

  const toothName = TOOTH_NAMES[toothNumber];
  const quadrant = Math.floor(toothNumber / 10);
  const isMolar = [6, 7, 8].includes(toothNumber % 10);
  const isAnterior = [1, 2, 3].includes(toothNumber % 10);

  // Suggestions intelligentes unitaires (v4.8)
  const suggestedTreatments = useMemo(() => {
    const unitaireTemplates = TREATMENT_TEMPLATES.filter(t => t.scope === 'UNITAIRE');
    
    if (isAnterior) {
      return unitaireTemplates.filter(t => 
        t.category === 'ESTHETIQUE' || 
        t.id.startsWith('comp-') ||
        t.id === 'endo-mono'
      );
    } else if (isMolar) {
      return unitaireTemplates.filter(t =>
        t.id.includes('ext') ||
        t.id.startsWith('prost-') ||
        t.id.startsWith('endo-pluri')
      );
    }
    return unitaireTemplates.filter(t => 
      ['comp-1', 'comp-2', 'endo-mono'].includes(t.id)
    );
  }, [isAnterior, isMolar]);

  const toggleTreatment = (template: Omit<ToothTreatment, 'price'>) => {
    const exists = selectedTreatments.find(t => t.id === template.id);
    if (exists) {
      setSelectedTreatments(prev => prev.filter(t => t.id !== template.id));
    } else {
      // Ajouter avec prix 0 (à remplir par l'utilisateur)
      const newTreatment: ToothTreatment = {
        ...template,
        price: treatmentPrices[template.id] || 0,
      };
      setSelectedTreatments(prev => [...prev, newTreatment]);
      if (template.suggestedSurfaces && selectedSurfaces.length === 0) {
        setSelectedSurfaces(template.suggestedSurfaces);
      }
    }
  };

  const updateTreatmentPrice = (id: string, price: number) => {
    setTreatmentPrices(prev => ({ ...prev, [id]: price }));
    setSelectedTreatments(prev =>
      prev.map(t => t.id === id ? { ...t, price } : t)
    );
  };

  const toggleSurface = (surface: ToothSurface) => {
    setSelectedSurfaces(prev =>
      prev.includes(surface)
        ? prev.filter(s => s !== surface)
        : [...prev, surface]
    );
  };

  const totalPrice = selectedTreatments.reduce((sum, t) => sum + (t.price || 0), 0);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        className="bg-white rounded-3xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-hidden flex flex-col"
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-800 px-8 py-6 text-white flex items-center justify-between shrink-0">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center text-2xl font-bold backdrop-blur">
              {toothNumber}
            </div>
            <div>
              <h2 className="text-2xl font-black tracking-tight">{toothName}</h2>
              <p className="text-blue-100 text-[10px] font-black uppercase tracking-widest opacity-70">Quadrant {quadrant} • Saisissez les prix en MAD</p>
            </div>
          </div>
          <button onClick={onCancel} className="p-2 hover:bg-white/20 rounded-xl transition-colors">
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden flex">
          {/* Left: Categories & Treatments */}
          <div className="flex-1 overflow-y-auto p-6 border-r border-gray-100">
            {/* Suggestions */}
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                <Zap className="w-4 h-4" />
                Suggestions
              </h3>
              <div className="flex flex-wrap gap-2">
                {suggestedTreatments.slice(0, 5).map(template => (
                  <button
                    key={template.id}
                    onClick={() => toggleTreatment(template)}
                    className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                      selectedTreatments.find(t => t.id === template.id)
                        ? 'bg-blue-600 text-white shadow-lg'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {template.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Category tabs (Filtered for unitaire scope) */}
            <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
              {Object.keys(TREATMENTS_BY_CATEGORY).filter(cat => 
                TREATMENTS_BY_CATEGORY[cat].some(t => t.scope === 'UNITAIRE')
              ).map(category => (
                <button
                  key={category}
                  onClick={() => setActiveCategory(category)}
                  className={`px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
                    activeCategory === category
                      ? `${CATEGORY_COLORS[category].bg} ${CATEGORY_COLORS[category].text} ring-2 ring-offset-1 ${CATEGORY_COLORS[category].border.replace('border', 'ring')}`
                      : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  {CATEGORY_LABELS[category]}
                </button>
              ))}
            </div>

            {/* Treatments list with price input (Filtered for unitaire scope) */}
            <div className="space-y-3">
              {TREATMENTS_BY_CATEGORY[activeCategory]
                ?.filter(t => t.scope === 'UNITAIRE')
                ?.map(template => {
                const isSelected = selectedTreatments.find(t => t.id === template.id);
                const currentPrice = treatmentPrices[template.id] || 0;
                const colors = CATEGORY_COLORS[template.category];
                
                return (
                  <motion.div
                    key={template.id}
                    className={`p-4 rounded-2xl border-2 transition-all ${
                      isSelected
                        ? `${colors.bg} ${colors.border} shadow-md`
                        : 'bg-white border-gray-100 hover:border-gray-200'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 flex-1">
                        <button
                          onClick={() => toggleTreatment(template)}
                          className={`w-6 h-6 rounded-full flex items-center justify-center transition-all ${
                            isSelected ? 'bg-blue-600 text-white' : 'bg-gray-200'
                          }`}
                        >
                          {isSelected && <Check className="w-4 h-4" />}
                        </button>
                        <div className="flex-1">
                          <h4 className="font-semibold text-gray-900">{template.name}</h4>
                          <div className="flex items-center gap-4 mt-1 text-xs text-gray-500">
                            {template.duration && (
                              <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {template.duration} min
                              </span>
                            )}
                            {template.anesthesia && (
                              <span className="text-orange-600 flex items-center gap-1">
                                <Stethoscope className="w-3 h-3" />
                                Anesthésie
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      {/* Price input */}
                      {isSelected && (
                        <div className="flex items-center gap-2">
                          <input
                            type="number"
                            value={currentPrice || ''}
                            onChange={(e) => updateTreatmentPrice(template.id, Number(e.target.value))}
                            placeholder="0"
                            className="w-28 px-3 py-2 border-2 border-slate-200 rounded-xl text-right font-mono text-base font-black text-slate-950 bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all shadow-inner"
                            autoFocus
                          />
                          <span className="text-gray-500 font-medium">MAD</span>
                        </div>
                      )}
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>

          {/* Right: Surfaces & Summary */}
          <div className="w-80 bg-gray-50 p-6 flex flex-col">
            {/* Surfaces */}
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Surfaces</h3>
              <div className="grid grid-cols-2 gap-2">
                {SURFACES.map(({ code, label }) => (
                  <button
                    key={code}
                    onClick={() => toggleSurface(code)}
                    className={`p-3 rounded-xl text-sm font-medium transition-all ${
                      selectedSurfaces.includes(code)
                        ? 'bg-blue-600 text-white shadow-md'
                        : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
                    }`}
                  >
                    <span className="font-bold">{code}</span>
                    <span className="ml-1 text-xs opacity-80">{label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Notes */}
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Notes</h3>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Observations..."
                className="w-full p-3 rounded-xl border border-gray-200 resize-none focus:ring-2 focus:ring-blue-500"
                rows={3}
              />
            </div>

            {/* Summary */}
            <div className="mt-auto">
              <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Récapitulatif</h3>
                
                {selectedTreatments.length === 0 ? (
                  <p className="text-sm text-gray-400 italic">Aucun traitement sélectionné</p>
                ) : (
                  <div className="space-y-2 mb-4 max-h-32 overflow-y-auto">
                    {selectedTreatments.map(t => (
                      <div key={t.id} className="flex justify-between text-sm">
                        <span className="text-gray-600 truncate flex-1">{t.name}</span>
                        <span className="font-medium text-gray-900 ml-2">
                          {t.price > 0 ? `${t.price} MAD` : '-'}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
                
                <div className="border-t border-gray-100 pt-3 mt-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Total</span>
                    <span className="text-2xl font-bold text-blue-600">
                      {totalPrice > 0 ? `${totalPrice} MAD` : '-'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="mt-4 space-y-2">
                <button
                  onClick={() => onConfirm(selectedTreatments, selectedSurfaces, notes)}
                  disabled={selectedTreatments.length === 0}
                  className="w-full py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 disabled:bg-gray-300 transition-all flex items-center justify-center gap-2"
                >
                  <Check className="w-5 h-5" />
                  Confirmer
                </button>
                <button
                  onClick={onCancel}
                  className="w-full py-3 bg-white text-gray-600 rounded-xl font-medium hover:bg-gray-100 border border-gray-200 transition-all"
                >
                  Annuler
                </button>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default TreatmentSelector;
