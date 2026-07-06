/**
 * RVG Upload Modal — Tailwind version (no MUI dependency)
 * Allows users to upload intra-oral X-ray images with metadata.
 */
import React, { useState } from 'react';
import { X } from 'lucide-react';
import rvgService from '../../../services/rvgService';
import type { RVGUploadRequest, RVGDocument } from '../../../services/rvgService';

interface RvgUploadModalProps {
  open: boolean;
  patientId: number;
  onClose: () => void;
  onSuccess: (doc: RVGDocument) => void;
  onError?: (error: any) => void;
}

const RADIO_TYPES = [
  { value: 'rvg', label: 'RVG' },
  { value: 'periapical', label: 'Périapicale' },
  { value: 'bitewing', label: 'Bitewing' },
  { value: 'occlusal', label: 'Occlusale' },
  { value: 'other', label: 'Autre intra-orale' },
];

export const RvgUploadModal: React.FC<RvgUploadModalProps> = ({
  open,
  patientId,
  onClose,
  onSuccess,
  onError,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [radioType, setRadioType] = useState('rvg');
  const [toothNumber, setToothNumber] = useState('');
  const [sector, setSector] = useState('');
  const [acquisitionDate, setAcquisitionDate] = useState('');
  const [note, setNote] = useState('');
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);

      if (selectedFile.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (event) => {
          setPreview(event.target?.result as string);
        };
        reader.readAsDataURL(selectedFile);
      }
    }
  };

  const handleSubmit = async () => {
    if (!file) {
      setError('Veuillez sélectionner un fichier.');
      return;
    }

    setLoading(true);
    setProgress(0);

    try {
      const request: RVGUploadRequest = {
        file,
        radio_type: radioType as any,
        tooth_number: toothNumber || undefined,
        sector: sector || undefined,
        acquisition_date: acquisitionDate || undefined,
        note: note || undefined,
      };

      const progressInterval = setInterval(() => {
        setProgress((p) => Math.min(p + 10, 90));
      }, 100);

      const doc = await rvgService.uploadRVG(patientId, request);

      clearInterval(progressInterval);
      setProgress(100);

      setFile(null);
      setRadioType('rvg');
      setToothNumber('');
      setSector('');
      setAcquisitionDate('');
      setNote('');
      setPreview(null);
      setError(null);

      onSuccess(doc);
      setTimeout(() => onClose(), 500);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors du téléchargement.');
      if (onError) onError(err);
    } finally {
      setLoading(false);
      setProgress(0);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setFile(null);
      setError(null);
      setPreview(null);
      onClose();
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center p-6 border-b sticky top-0 bg-white">
          <h2 className="text-xl font-bold">Ajouter une radio RVG</h2>
          <button
            onClick={handleClose}
            disabled={loading}
            className="p-2 hover:bg-gray-100 rounded-lg disabled:opacity-50"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-100 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* File Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Fichier image ou PDF
            </label>
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp,application/pdf"
              onChange={handleFileChange}
              disabled={loading}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
            <p className="text-xs text-gray-500 mt-1">
              Formats acceptés : JPEG, PNG, WebP, PDF (max 10 MB)
            </p>
          </div>

          {/* Preview */}
          {preview && (
            <div className="text-center">
              <img
                src={preview}
                alt="Aperçu"
                className="max-w-full max-h-48 mx-auto rounded-lg"
              />
            </div>
          )}

          {/* Radio Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Type de radio
            </label>
            <select
              value={radioType}
              onChange={(e) => setRadioType(e.target.value)}
              disabled={loading}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              {RADIO_TYPES.map((rt) => (
                <option key={rt.value} value={rt.value}>
                  {rt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Tooth Number */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Dent concernée (optionnel)
            </label>
            <input
              type="text"
              value={toothNumber}
              onChange={(e) => setToothNumber(e.target.value)}
              disabled={loading}
              placeholder="ex: 16, 27, 38"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>

          {/* Sector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Secteur (optionnel)
            </label>
            <input
              type="text"
              value={sector}
              onChange={(e) => setSector(e.target.value)}
              disabled={loading}
              placeholder="ex: UR, LL"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>

          {/* Acquisition Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Date de prise (optionnel)
            </label>
            <input
              type="date"
              value={acquisitionDate}
              onChange={(e) => setAcquisitionDate(e.target.value)}
              disabled={loading}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>

          {/* Note */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Note (optionnel)
            </label>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              disabled={loading}
              rows={3}
              placeholder="Observations cliniques..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
          </div>

          {/* Progress */}
          {loading && progress > 0 && (
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
          )}
        </div>

        <div className="border-t p-6 flex gap-3 bg-gray-50 sticky bottom-0">
          <button
            onClick={handleClose}
            disabled={loading}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg font-medium hover:bg-gray-100 disabled:opacity-50 transition-colors"
          >
            Annuler
          </button>
          <button
            onClick={handleSubmit}
            disabled={!file || loading}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? `Téléchargement... ${progress}%` : 'Enregistrer'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default RvgUploadModal;
