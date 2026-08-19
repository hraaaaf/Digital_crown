import React, { useCallback, useEffect, useState } from 'react';
import { AlertCircle, ImagePlus, Loader2, RefreshCw } from 'lucide-react';
import rvgService, { type RVGDocument } from '../../../services/rvgService';
import { RvgCard } from './RvgCard';
import { RvgUploadModal } from './RvgUploadModal';

interface PatientRvgPanelProps {
  patientId: number;
}

export const PatientRvgPanel: React.FC<PatientRvgPanelProps> = ({ patientId }) => {
  const [documents, setDocuments] = useState<RVGDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const rows = await rvgService.listRVG(patientId);
      setDocuments(rows);
    } catch (err) {
      console.error('Impossible de charger les RVG:', err);
      setDocuments([]);
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    void load();
  }, [load, reloadKey]);

  if (loading) {
    return (
      <div className="min-h-[320px] flex flex-col items-center justify-center gap-3 text-slate-500">
        <Loader2 className="animate-spin" size={28} />
        <p className="text-sm font-semibold">Chargement des radios intra-orales…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-[320px] flex flex-col items-center justify-center gap-4 px-6 text-center">
        <AlertCircle size={38} className="text-rose-500" />
        <div>
          <h3 className="font-black text-slate-800">Impossible de charger les RVG</h3>
          <p className="text-sm text-slate-500 mt-1">Aucun état vide n'est déduit tant que le backend ne répond pas.</p>
        </div>
        <button
          type="button"
          onClick={() => setReloadKey(key => key + 1)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#003380] text-white text-xs font-black uppercase tracking-widest"
        >
          <RefreshCw size={15} /> Réessayer
        </button>
      </div>
    );
  }

  return (
    <section className="space-y-5 min-w-0" aria-label="Radios RVG et intra-orales">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="font-black text-slate-800 text-lg">Radios intra-orales</h2>
          <p className="text-sm text-slate-500 mt-1">
            RVG, périapicales, bitewings et occlusales archivées dans le dossier Patient.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setUploadOpen(true)}
          className="inline-flex shrink-0 items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-[#003380] text-white text-xs font-black uppercase tracking-widest"
        >
          <ImagePlus size={16} /> Ajouter une RVG
        </button>
      </div>

      {documents.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50/70 py-16 px-6 text-center">
          <p className="font-black text-slate-700">Aucune radio intra-orale enregistrée</p>
          <p className="text-sm text-slate-500 mt-1">Cet état vide provient d'une lecture backend réussie.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {documents.map(doc => (
            <RvgCard
              key={doc.id}
              doc={doc}
              canDelete
              canDownload
              onDelete={docId => setDocuments(current => current.filter(item => item.id !== docId))}
            />
          ))}
        </div>
      )}

      <RvgUploadModal
        open={uploadOpen}
        patientId={patientId}
        onClose={() => setUploadOpen(false)}
        onSuccess={doc => setDocuments(current => [doc, ...current.filter(item => item.id !== doc.id)])}
        onError={err => console.error('Erreur upload RVG:', err)}
      />
    </section>
  );
};

export default PatientRvgPanel;
