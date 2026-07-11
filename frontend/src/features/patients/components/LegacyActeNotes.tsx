import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../../services/api';
import { useAuthenticatedImage } from '../../../hooks/useAuthenticatedImage';
import {
  Upload,
  Save,
  Image as ImageIcon,
  Edit2,
  FileSignature,
  Receipt,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { usePatientStore } from '../../../stores/usePatientStore';

// Extrait de PatientTracking.tsx (P0-TREATMENT-JOURNEY-1) — l'éditeur de notes cliniques et
// l'upload de pièce jointe restent ancrés à `Acte.notes_cliniques`/`Acte.attachments`, qui n'ont
// pas d'équivalent dans le nouveau flux Journey (Acte écarté comme source, voir
// docs/TREATMENT_JOURNEY_DESIGN.md). Composant partagé entre PatientTracking et PatientJourney
// (section "Actes historiques") pour ne rien dupliquer.

export interface LegacyActe {
  id: number;
  libelle: string;
  montant: number;
  notes_cliniques: string | null;
  attachments: string[];
}

interface LegacyActeNotesProps {
  acte: LegacyActe;
  patientId: number;
}

function AuthImg({ url, className }: { url: string; className?: string }) {
  const src = useAuthenticatedImage(url);
  return <img src={src} alt="Pièce jointe" className={className} />;
}

export const LegacyActeNotes = ({ acte, patientId }: LegacyActeNotesProps) => {
  const queryClient = useQueryClient();
  const { setEditingDoc } = usePatientStore();
  const [isEditing, setIsEditing] = useState(false);
  const [editNotes, setEditNotes] = useState(acte.notes_cliniques || '');

  const updateNotesMutation = useMutation({
    mutationFn: async (notes: string) => {
      await api.put(`/actes/${acte.id}`, { notes_cliniques: notes });
    },
    onSuccess: () => {
      toast.success('Notes sauvegardées avec succès.');
      queryClient.invalidateQueries({ queryKey: ['actes', patientId] });
      setIsEditing(false);
    },
    onError: () => {
      toast.error('Erreur de sauvegarde.');
    },
  });

  const startEditing = () => {
    setEditNotes(acte.notes_cliniques || '');
    setIsEditing(true);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      toast.loading("Envoi de l'image en cours...", { id: `upload-${acte.id}` });
      await api.post(`/actes/${acte.id}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      queryClient.invalidateQueries({ queryKey: ['actes', patientId] });
      toast.success('Image ajoutée avec succès.', { id: `upload-${acte.id}` });
    } catch (err) {
      toast.error("Échec de l'upload.", { id: `upload-${acte.id}` });
    }
  };

  const handleGeneratePrescription = () => {
    setEditingDoc({
      type: 'ordonnance',
      clinical_data: {
        reason: acte.libelle,
        // L'IA complétera automatiquement
      },
    });
  };

  const handleGenerateInvoice = () => {
    setEditingDoc({
      type: 'honoraires',
      clinical_data: {
        items: [{ acte: acte.libelle, dent: '', prix_unitaire: acte.montant }],
      },
    });
  };

  return (
    <div>
      {/* Actions Rapides */}
      <div className="flex items-center gap-2 justify-end mb-4">
        <button
          onClick={handleGeneratePrescription}
          className="p-2 bg-slate-50 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg shadow-sm border border-slate-100 transition-colors"
          title="Générer une ordonnance"
        >
          <FileSignature size={16} />
        </button>
        <button
          onClick={handleGenerateInvoice}
          className="p-2 bg-slate-50 text-slate-500 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg shadow-sm border border-slate-100 transition-colors"
          title="Générer une note d'honoraires"
        >
          <Receipt size={16} />
        </button>
      </div>

      {/* Notes section */}
      <div className="bg-slate-50 rounded-2xl p-5 mb-4">
        {isEditing ? (
          <div className="space-y-3">
            <textarea
              className="w-full bg-white border border-slate-200 rounded-xl p-3 min-h-[100px] text-sm focus:ring-2 focus:ring-primary outline-none"
              placeholder="Saisissez vos notes cliniques (Ex: ttt canalaire, LT = 21mm, particularités...)"
              value={editNotes}
              onChange={(e) => setEditNotes(e.target.value)}
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 text-sm font-bold text-slate-500 hover:bg-slate-200 rounded-lg"
              >
                Annuler
              </button>
              <button
                onClick={() => updateNotesMutation.mutate(editNotes)}
                className="flex items-center gap-2 px-4 py-2 text-sm font-bold bg-primary text-white hover:bg-primary/90 rounded-lg shadow-sm"
              >
                <Save size={16} /> Enregistrer
              </button>
            </div>
          </div>
        ) : (
          <div className="group/note relative min-h-[60px]">
            {acte.notes_cliniques ? (
              <p className="text-slate-700 whitespace-pre-wrap text-sm leading-relaxed">
                {acte.notes_cliniques}
              </p>
            ) : (
              <p className="text-slate-400 italic text-sm">
                Aucune note clinique pour cette séance.
              </p>
            )}
            <button
              onClick={startEditing}
              className="absolute top-0 right-0 p-2 bg-white rounded-lg shadow-sm border border-slate-200 text-slate-400 hover:text-primary opacity-0 group-hover/note:opacity-100 transition-opacity"
            >
              <Edit2 size={16} />
            </button>
          </div>
        )}
      </div>

      {/* Attachments (e.g., retro-alveolaire) */}
      <div className="flex items-center gap-4 mt-4 pt-4 border-t border-slate-100">
        {acte.attachments && acte.attachments.length > 0 ? (
          <div className="flex gap-3">
            {acte.attachments.map((url, idx) => (
              <div key={idx} className="w-16 h-16 rounded-xl bg-slate-200 overflow-hidden shadow-sm">
                <AuthImg url={url} className="w-full h-full object-cover" />
              </div>
            ))}
          </div>
        ) : null}

        <div>
          <input
            type="file"
            id={`file-${acte.id}`}
            className="hidden"
            accept="image/*"
            onChange={handleFileUpload}
          />
          <label
            htmlFor={`file-${acte.id}`}
            className="flex items-center gap-2 px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-bold text-slate-500 hover:bg-slate-50 hover:text-primary cursor-pointer transition-colors"
          >
            <ImageIcon size={14} /> Joindre Radio (Rétro)
          </label>
        </div>
      </div>
    </div>
  );
};
