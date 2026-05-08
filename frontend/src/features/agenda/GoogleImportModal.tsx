import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, UploadCloud, Calendar, FileText, CheckCircle2, AlertCircle } from 'lucide-react';
import { api } from '../../services/api';
import { parseIcsContent } from '../../utils/icsParser';
import type { ParsedEvent } from '../../utils/icsParser';

interface GoogleImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const GoogleImportModal: React.FC<GoogleImportModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [events, setEvents] = useState<ParsedEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState<1 | 2>(1); // 1: Upload, 2: Preview
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;
    
    setError('');
    
    try {
      const text = await selectedFile.text();
      const parsed = parseIcsContent(text);
      if (parsed.length === 0) {
        setError('Aucun rendez-vous valide trouvé dans ce fichier.');
      } else {
        setEvents(parsed);
        setStep(2);
      }
    } catch (err) {
      setError('Erreur lors de la lecture du fichier. Assurez-vous qu\'il s\'agit d\'un fichier .ics valide.');
    }
  };

  const handleImport = async () => {
    setLoading(true);
    setError('');
    
    try {
      // Map aux champs attendus par le backend
      const payload = {
        appointments: events.map(ev => ({
          patient_name: ev.patient_name.substring(0, 50), // Sécruité longueur
          datetime_start: ev.datetime_start,
          duration_minutes: ev.duration_minutes,
          notes: ev.notes || 'Importé depuis Google Agenda',
          status: 'PRÉVU'
        }))
      };

      await api.post('/appointments/bulk', payload);
      onSuccess();
      onClose();
      // Reset
      setTimeout(() => {
        setStep(1);
        setEvents([]);
      }, 500);
    } catch (err) {
      console.error(err);
      setError('Erreur lors de l\'importation des rendez-vous.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
        />

        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="relative w-full max-w-3xl bg-white rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-slate-100 bg-slate-50/50">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-primary/10 text-primary rounded-xl">
                <Calendar size={24} />
              </div>
              <div>
                <h2 className="text-xl font-bold text-slate-800">Import Google Agenda</h2>
                <p className="text-sm text-slate-500">Importez vos rendez-vous via un fichier .ics</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full transition-colors"
            >
              <X size={20} />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto">
            {error && (
              <div className="mb-6 flex items-start gap-3 p-4 bg-red-50 text-red-600 rounded-xl">
                <AlertCircle size={20} className="shrink-0 mt-0.5" />
                <p className="text-sm font-medium">{error}</p>
              </div>
            )}

            {step === 1 && (
              <div 
                className="border-2 border-dashed border-slate-200 rounded-2xl p-12 text-center hover:border-primary hover:bg-primary/5 transition-colors cursor-pointer group"
                onClick={() => fileInputRef.current?.click()}
              >
                <div className="w-16 h-16 bg-primary/10 text-primary rounded-full flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                  <UploadCloud size={32} />
                </div>
                <h3 className="text-lg font-bold text-slate-700 mb-2">Sélectionnez un fichier .ics</h3>
                <p className="text-slate-500 text-sm max-w-sm mx-auto">
                  Exportez votre calendrier depuis Google Agenda (Paramètres &gt; Exporter) et sélectionnez le fichier .ics.
                </p>
                <input 
                  type="file" 
                  accept=".ics" 
                  className="hidden" 
                  ref={fileInputRef}
                  onChange={handleFileChange}
                />
              </div>
            )}

            {step === 2 && (
              <div className="space-y-6">
                <div className="flex items-center justify-between bg-primary/5 p-4 rounded-xl border border-primary/20">
                  <div className="flex items-center gap-3">
                    <CheckCircle2 className="text-primary" size={24} />
                    <div>
                      <p className="font-bold text-primary">{events.length} rendez-vous trouvés</p>
                      <p className="text-xs text-primary/80">Prêts à être importés dans votre agenda Digital Crown.</p>
                    </div>
                  </div>
                  <button 
                    onClick={() => { setStep(1); setEvents([]); }}
                    className="text-sm text-primary hover:brightness-110 font-medium"
                  >
                    Changer de fichier
                  </button>
                </div>

                <div className="border border-slate-200 rounded-xl overflow-hidden max-h-[400px] overflow-y-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-slate-50 sticky top-0 border-b border-slate-200">
                      <tr>
                        <th className="p-3 font-semibold text-slate-600">Patient / Titre</th>
                        <th className="p-3 font-semibold text-slate-600">Date & Heure</th>
                        <th className="p-3 font-semibold text-slate-600">Durée</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {events.slice(0, 50).map((ev, idx) => {
                        const date = new Date(ev.datetime_start);
                        return (
                          <tr key={idx} className="hover:bg-slate-50">
                            <td className="p-3 font-medium text-slate-800">{ev.patient_name}</td>
                            <td className="p-3 text-slate-600">
                              {date.toLocaleDateString('fr-FR')} à {date.toLocaleTimeString('fr-FR', {hour: '2-digit', minute:'2-digit'})}
                            </td>
                            <td className="p-3 text-slate-600">
                              {ev.duration_minutes} min
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                  {events.length > 50 && (
                    <div className="p-3 text-center text-sm text-slate-500 bg-slate-50 border-t border-slate-200">
                      Et {events.length - 50} autres événements non affichés...
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-6 border-t border-slate-100 bg-slate-50/50 flex justify-end gap-3">
            <button
              onClick={onClose}
              className="px-5 py-2.5 text-slate-600 font-medium hover:bg-slate-200/50 rounded-xl transition-colors"
            >
              Annuler
            </button>
            <button
              onClick={handleImport}
              disabled={step === 1 || loading}
              className="px-6 py-2.5 bg-primary text-white font-bold rounded-xl shadow-lg shadow-primary/20 hover:brightness-110 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              ) : (
                <FileText size={18} />
              )}
              {loading ? 'Importation...' : 'Confirmer l\'import'}
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
