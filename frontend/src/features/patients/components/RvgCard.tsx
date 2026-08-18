/**
 * RVG Card Component — Tailwind version (no MUI dependency)
 * Displays a single RVG document with metadata and action buttons.
 */
import React, { useState } from 'react';
import { Trash2, Download, ExternalLink } from 'lucide-react';
import type { RVGDocument } from '../../../services/rvgService';
import rvgService from '../../../services/rvgService';
import { useAuthenticatedImage } from '../../../hooks/useAuthenticatedImage';

interface RvgCardProps {
  doc: RVGDocument;
  onDelete?: (docId: number) => void;
  canDelete?: boolean;
  canDownload?: boolean;
}

export const RvgCard: React.FC<RvgCardProps> = ({
  doc,
  onDelete,
  canDelete = false,
  canDownload = true,
}) => {
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [opening, setOpening] = useState(false);
  const thumbnailUrl = useAuthenticatedImage(`/api/documents/${doc.id}/download`);

  const handleOpenFile = async () => {
    setOpening(true);
    try {
      const blob = await rvgService.fetchRVGBlob(doc.id);
      const objectUrl = URL.createObjectURL(blob);
      const opened = window.open(objectUrl, '_blank', 'noopener,noreferrer');
      if (!opened) URL.revokeObjectURL(objectUrl);
      else window.setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
    } catch (err) {
      console.error('Error opening file:', err);
    } finally {
      setOpening(false);
    }
  };

  const handleDownload = async () => {
    try {
      const blob = await rvgService.fetchRVGBlob(doc.id);
      const objectUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = objectUrl;
      a.download = doc.original_filename || `rvg_${doc.id}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(objectUrl);
    } catch (err) {
      console.error('Error downloading file:', err);
    }
  };

  const handleDeleteConfirm = async () => {
    if (onDelete) {
      try {
        await rvgService.deleteRVG(doc.id);
        onDelete(doc.id);
      } catch (err) {
        console.error('Error deleting RVG:', err);
      }
    }
    setDeleteConfirmOpen(false);
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString('fr-FR');
    } catch {
      return dateStr;
    }
  };

  const radioTypeLabels: Record<string, string> = {
    rvg: 'RVG',
    periapical: 'Périapicale',
    bitewing: 'Bitewing',
    occlusal: 'Occlusale',
    other: 'Autre',
  };
  const radioTypeLabel = (doc.clinical_data?.radio_type && radioTypeLabels[doc.clinical_data.radio_type]) || doc.clinical_data?.radio_type || 'Radio';

  return (
    <>
      <div className="border rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow bg-white flex flex-col h-full">
        {/* Thumbnail */}
        <div className="h-48 bg-gray-100 overflow-hidden flex items-center justify-center">
          {doc.original_filename?.toLowerCase().endsWith('.pdf') ? (
            <div className="flex flex-col items-center justify-center text-gray-500">
              <span className="text-3xl mb-2">📄</span>
              <p className="text-sm font-semibold truncate px-2">{doc.original_filename}</p>
            </div>
          ) : (
            <img
              src={thumbnailUrl}
              alt={`${radioTypeLabel} - ${doc.original_filename}`}
              className="w-full h-full object-cover"
              onError={(e) => {
                (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22100%22%3E%3Crect fill=%22%23f3f4f6%22 width=%22100%22 height=%22100%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-family=%22system-ui%22 font-size=%2212%22 fill=%22%239ca3af%22%3EImage%3C/text%3E%3C/svg%3E';
              }}
            />
          )}
        </div>

        {/* Metadata */}
        <div className="p-4 flex-1">
          <div className="mb-2 flex flex-wrap gap-1">
            <span className="inline-block px-2 py-1 bg-blue-100 text-blue-700 text-xs font-semibold rounded">
              {radioTypeLabel}
            </span>
            {doc.clinical_data?.tooth_number && (
              <span className="inline-block px-2 py-1 bg-gray-100 text-gray-700 text-xs font-semibold rounded">
                Dent {doc.clinical_data.tooth_number}
              </span>
            )}
            {doc.clinical_data?.sector && (
              <span className="inline-block px-2 py-1 bg-gray-100 text-gray-700 text-xs font-semibold rounded">
                Secteur {doc.clinical_data.sector}
              </span>
            )}
          </div>

          {doc.clinical_data?.acquisition_date && (
            <p className="text-xs text-gray-500 mb-2">
              Prise le : {formatDate(doc.clinical_data.acquisition_date)}
            </p>
          )}

          {doc.clinical_data?.note && (
            <p className="text-sm text-gray-700 mb-2 line-clamp-2">
              {doc.clinical_data.note}
            </p>
          )}

          <p className="text-xs text-gray-500">
            Ajoutée le {formatDate(doc.created_at)}
          </p>
        </div>

        {/* Actions */}
        <div className="p-3 border-t border-gray-100 flex gap-2 bg-gray-50">
          <button
            onClick={handleOpenFile}
            disabled={opening}
            className="flex-1 flex items-center justify-center gap-1 px-3 py-2 text-sm font-medium bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
          >
            <ExternalLink size={14} />
            Ouvrir
          </button>
          {canDownload && (
            <button
              onClick={handleDownload}
              className="flex-1 flex items-center justify-center gap-1 px-3 py-2 text-sm font-medium bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Download size={14} />
              Télécharger
            </button>
          )}
          {canDelete && (
            <button
              onClick={() => setDeleteConfirmOpen(true)}
              className="flex-1 flex items-center justify-center gap-1 px-3 py-2 text-sm font-medium bg-white border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors"
            >
              <Trash2 size={14} />
              Supprimer
            </button>
          )}
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      {deleteConfirmOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-sm w-full p-6">
            <h2 className="text-lg font-bold mb-4">Confirmer la suppression</h2>
            <p className="text-gray-600 mb-6">
              Êtes-vous sûr de vouloir supprimer cette radio ?
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setDeleteConfirmOpen(false)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg font-medium hover:bg-gray-50 transition-colors"
              >
                Annuler
              </button>
              <button
                onClick={handleDeleteConfirm}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors"
              >
                Supprimer
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default RvgCard;
