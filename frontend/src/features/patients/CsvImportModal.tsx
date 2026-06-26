import React, { useRef, useState } from 'react';
import { X, UploadCloud, FileText, CheckCircle, AlertTriangle, Loader2 } from 'lucide-react';
import { api } from '../../services/api';
import toast from 'react-hot-toast';
import { cn } from '../../utils/cn';

interface ImportResult {
  created: number;
  skipped_duplicates: number;
  errors: { row: number; reason: string }[];
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const CsvImportModal: React.FC<Props> = ({ isOpen, onClose, onSuccess }) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const reset = () => {
    setFile(null);
    setResult(null);
    setLoading(false);
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const handleFile = (f: File) => {
    setResult(null);
    setFile(f);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  const handleImport = async () => {
    if (!file) return;
    setLoading(true);
    try {
      const form = new FormData();
      form.append('file', file);
      const res = await api.post('/patients/import-csv', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResult(res.data);
      if (res.data.created > 0) {
        toast.success(`${res.data.created} patient(s) importé(s)`);
        onSuccess();
      }
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erreur lors de l'import");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-[2rem] shadow-2xl w-full max-w-lg animate-in fade-in zoom-in-95 duration-200">

        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary/10 rounded-xl flex items-center justify-center">
              <UploadCloud size={20} className="text-primary" />
            </div>
            <div>
              <h2 className="font-black text-slate-800">Importer des patients</h2>
              <p className="text-xs text-slate-400 font-medium">Fichier CSV — nom, prenom, date_naissance</p>
            </div>
          </div>
          <button onClick={handleClose} className="p-2 hover:bg-slate-100 rounded-xl transition-colors">
            <X size={18} className="text-slate-400" />
          </button>
        </div>

        <div className="p-6 space-y-5">

          {/* Format info */}
          <div className="bg-slate-50 rounded-2xl p-4 text-xs text-slate-500 space-y-1">
            <p className="font-black text-slate-600 mb-2">Format attendu</p>
            <p>Colonnes (l'ordre n'est pas important, séparateur auto-détecté) :</p>
            <code className="block bg-white border border-slate-200 rounded-lg px-3 py-2 text-[11px] font-mono text-slate-700 mt-1">
              nom ; prenom ; date_naissance ; telephone ; email ; assurance
            </code>
            <p className="mt-1">Date : <span className="font-mono">JJ/MM/AAAA</span> ou <span className="font-mono">AAAA-MM-JJ</span></p>
          </div>

          {/* Drop zone */}
          {!result && (
            <div
              className={cn(
                "border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all",
                dragOver ? "border-primary bg-primary/5" : "border-slate-200 hover:border-primary/50 hover:bg-slate-50"
              )}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => inputRef.current?.click()}
            >
              <input
                ref={inputRef}
                type="file"
                accept=".csv,text/csv"
                className="hidden"
                onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
              />
              {file ? (
                <div className="flex items-center justify-center gap-3">
                  <FileText size={24} className="text-primary" />
                  <div className="text-left">
                    <p className="font-black text-slate-700 text-sm">{file.name}</p>
                    <p className="text-xs text-slate-400">{(file.size / 1024).toFixed(1)} Ko</p>
                  </div>
                </div>
              ) : (
                <>
                  <UploadCloud size={32} className="mx-auto text-slate-300 mb-3" />
                  <p className="font-bold text-slate-500 text-sm">Glissez votre CSV ici ou cliquez pour choisir</p>
                </>
              )}
            </div>
          )}

          {/* Result */}
          {result && (
            <div className="space-y-3">
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-emerald-50 rounded-2xl p-4 text-center">
                  <CheckCircle size={20} className="mx-auto text-emerald-500 mb-1" />
                  <p className="text-2xl font-black text-emerald-700">{result.created}</p>
                  <p className="text-[10px] font-bold text-emerald-500 uppercase tracking-wide">Créés</p>
                </div>
                <div className="bg-amber-50 rounded-2xl p-4 text-center">
                  <AlertTriangle size={20} className="mx-auto text-amber-500 mb-1" />
                  <p className="text-2xl font-black text-amber-700">{result.skipped_duplicates}</p>
                  <p className="text-[10px] font-bold text-amber-500 uppercase tracking-wide">Doublons</p>
                </div>
                <div className="bg-rose-50 rounded-2xl p-4 text-center">
                  <X size={20} className="mx-auto text-rose-400 mb-1" />
                  <p className="text-2xl font-black text-rose-600">{result.errors.length}</p>
                  <p className="text-[10px] font-bold text-rose-400 uppercase tracking-wide">Erreurs</p>
                </div>
              </div>
              {result.errors.length > 0 && (
                <div className="bg-rose-50 rounded-2xl p-3 max-h-36 overflow-y-auto">
                  {result.errors.map((e, i) => (
                    <p key={i} className="text-xs text-rose-600 font-medium">
                      <span className="font-black">Ligne {e.row} :</span> {e.reason}
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-1">
            {result ? (
              <button
                onClick={handleClose}
                className="flex-1 py-3 bg-primary text-white font-black rounded-2xl hover:brightness-110 transition-all"
              >
                Fermer
              </button>
            ) : (
              <>
                <button onClick={handleClose} className="flex-1 py-3 border border-slate-200 text-slate-500 font-bold rounded-2xl hover:bg-slate-50 transition-all">
                  Annuler
                </button>
                <button
                  onClick={handleImport}
                  disabled={!file || loading}
                  className="flex-1 py-3 bg-primary text-white font-black rounded-2xl hover:brightness-110 transition-all disabled:opacity-40 flex items-center justify-center gap-2"
                >
                  {loading ? <Loader2 size={18} className="animate-spin" /> : <UploadCloud size={18} />}
                  {loading ? 'Import en cours…' : 'Importer'}
                </button>
              </>
            )}
          </div>

        </div>
      </div>
    </div>
  );
};
