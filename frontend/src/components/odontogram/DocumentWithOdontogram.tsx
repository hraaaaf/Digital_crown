/**
 * DocumentWithOdontogram.tsx
 * Exemple d'intégration de l'odontogramme dans un formulaire de devis/note d'honoraires
 */
import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { FileText, Save, Printer, ChevronDown, ChevronUp, Calculator } from 'lucide-react';
import { Odontogram } from './Odontogram';
import type { SelectedSurfaceData } from './types';

interface DocumentLine {
  id: string;
  code: string;
  description: string;
  quantity: number;
  unitPrice: number;
  total: number;
  toothNumbers?: number[];
}

interface DocumentWithOdontogramProps {
  patientId: number;
  patientName: string;
  documentType: 'DEVIS' | 'NOTE_HONORAIRES';
  onSave: (data: {
    lines: DocumentLine[];
    total: number;
    teeth: SelectedSurfaceData[];
  }) => Promise<void>;
  onPrint: () => void;
}

export const DocumentWithOdontogram: React.FC<DocumentWithOdontogramProps> = ({
  patientId,
  patientName,
  documentType,
  onSave,
  onPrint,
}) => {
  const [lines, setLines] = useState<DocumentLine[]>([]);
  const [selectedTeeth, setSelectedTeeth] = useState<SelectedSurfaceData[]>([]);
  const [showOdontogram, setShowOdontogram] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  // Convertir les dents sélectionnées en lignes de document
  const handleTeethChange = (teeth: SelectedSurfaceData[]) => {
    setSelectedTeeth(teeth);
    
    // Générer automatiquement les lignes du document
    const newLines: DocumentLine[] = [];
    
    teeth.forEach((tooth) => {
      tooth.treatments.forEach((treatment) => {
        newLines.push({
          id: `${tooth.toothNumber}-${treatment.id}`,
          code: treatment.code || '',
          description: `${treatment.name} - Dent ${tooth.toothNumber}${
            tooth.surface ? ` (${tooth.surface})` : ''
          }`,
          quantity: 1,
          unitPrice: treatment.price,
          total: treatment.price,
          toothNumbers: [tooth.toothNumber as number],
        });
      });
    });
    
    setLines(newLines);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSave({
        lines,
        total: lines.reduce((sum, l) => sum + l.total, 0),
        teeth: selectedTeeth,
      });
    } finally {
      setIsSaving(false);
    }
  };

  const documentTitle = documentType === 'DEVIS' ? 'Devis' : 'Note d\'honoraires';
  const totalAmount = lines.reduce((sum, l) => sum + l.total, 0);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6 mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-gradient-to-br from-blue-600 to-blue-800 rounded-2xl flex items-center justify-center text-white">
                <FileText className="w-7 h-7" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{documentTitle}</h1>
                <p className="text-gray-500">{patientName}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <button
                onClick={handleSave}
                disabled={isSaving || lines.length === 0}
                className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 disabled:opacity-50 transition-all"
              >
                {isSaving ? (
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <Save className="w-5 h-5" />
                )}
                Enregistrer
              </button>
              <button
                onClick={onPrint}
                disabled={lines.length === 0}
                className="flex items-center gap-2 px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-semibold hover:bg-gray-200 disabled:opacity-50 transition-all"
              >
                <Printer className="w-5 h-5" />
                Imprimer
              </button>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Colonne gauche: Odontogramme */}
          <div>
            <button
              onClick={() => setShowOdontogram(!showOdontogram)}
              className="w-full flex items-center justify-between p-4 bg-white rounded-2xl shadow-sm border border-gray-100 mb-4 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
                  <Calculator className="w-5 h-5 text-blue-600" />
                </div>
                <div className="text-left">
                  <h2 className="font-bold text-gray-900">Sélection des dents</h2>
                  <p className="text-sm text-gray-500">
                    {selectedTeeth.length} dent{selectedTeeth.length > 1 ? 's' : ''} sélectionnée
                    {selectedTeeth.length > 1 ? 's' : ''} • {lines.length} acte{lines.length > 1 ? 's' : ''}
                  </p>
                </div>
              </div>
              {showOdontogram ? (
                <ChevronUp className="w-5 h-5 text-gray-400" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-400" />
              )}
            </button>

            {showOdontogram && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
              >
                <Odontogram
                  patientId={patientId}
                  mode="SELECT_FOR_DOCUMENT"
                  onChange={handleTeethChange}
                  showLegend={true}
                />
              </motion.div>
            )}
          </div>

          {/* Colonne droite: Détail du document */}
          <div className="space-y-6">
            {/* Récapitulatif des actes */}
            <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
              <div className="p-6 border-b border-gray-100">
                <h2 className="font-bold text-gray-900">Détail des actes</h2>
              </div>
              
              {lines.length === 0 ? (
                <div className="p-12 text-center text-gray-400">
                  <p>Sélectionnez des dents sur l'odontogramme</p>
                  <p className="text-sm mt-2">pour ajouter des actes automatiquement</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-100">
                  {lines.map((line) => (
                    <div key={line.id} className="p-4 hover:bg-gray-50 transition-colors">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-bold rounded-lg">
                              {line.code}
                            </span>
                            {line.toothNumbers && (
                              <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-lg">
                                Dent {line.toothNumbers.join(', ')}
                              </span>
                            )}
                          </div>
                          <p className="mt-2 text-gray-900">{line.description}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-gray-900">{line.total} €</p>
                          <p className="text-sm text-gray-500">{line.unitPrice} € x {line.quantity}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              {/* Total */}
              <div className="p-6 bg-gray-50 border-t border-gray-100">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Total</span>
                  <span className="text-3xl font-bold text-blue-600">{totalAmount.toFixed(2)} €</span>
                </div>
              </div>
            </div>

            {/* Informations complémentaires */}
            <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-6">
              <h3 className="font-bold text-gray-900 mb-4">Informations</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Date du document
                  </label>
                  <input
                    type="date"
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    defaultValue={new Date().toISOString().split('T')[0]}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Commentaires
                  </label>
                  <textarea
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                    rows={3}
                    placeholder="Observations particulières..."
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentWithOdontogram;
