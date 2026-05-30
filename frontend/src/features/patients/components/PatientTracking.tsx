import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../../services/api';
import { cn } from '../../../utils/cn';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import { 
  Calendar, 
  Stethoscope, 
  Banknote, 
  CheckCircle2, 
  Clock, 
  Upload, 
  Plus, 
  Save, 
  FileText,
  Image as ImageIcon,
  Edit2,
  FileSignature,
  Receipt,
  Activity,
  Target
} from 'lucide-react';
import toast from 'react-hot-toast';
import { EliteGhostLoader } from '../../../../components/EliteGhostLoader';
import { usePatientStore } from '../../../../stores/usePatientStore';

interface Acte {
  id: number;
  type_acte: string;
  libelle: string;
  montant: number;
  date_debut: string;
  statut_paiement: string;
  notes_cliniques: string | null;
  attachments: string[];
}

interface Appointment {
  id: number;
  datetime_start: string;
  motif: string;
  status: string;
}

interface PatientTrackingProps {
  patientId: number;
}

export const PatientTracking = ({ patientId }: PatientTrackingProps) => {
  const queryClient = useQueryClient();
  const { setEditingDoc } = usePatientStore();
  const [editingActeId, setEditingActeId] = useState<number | null>(null);
  const [editNotes, setEditNotes] = useState('');

  // 1. Fetch Actes
  const { data: actes = [], isLoading: loadingActes } = useQuery({
    queryKey: ['actes', patientId],
    queryFn: async () => {
      const res = await api.get(`/actes/patient/${patientId}`);
      return res.data as Acte[];
    }
  });

  // 2. Fetch Appointments
  const { data: appointments = [], isLoading: loadingAppts } = useQuery({
    queryKey: ['appointments', patientId],
    queryFn: async () => {
      const res = await api.get(`/appointments/patient/${patientId}`);
      return res.data as Appointment[];
    }
  });

  // 3. Fetch Treatment Plan
  const { data: treatmentPlan } = useQuery({
    queryKey: ['treatmentPlan', patientId],
    queryFn: async () => {
      const res = await api.get(`/intelligence/patient/${patientId}/treatment-plan`);
      return res.data;
    },
    retry: 0
  });

  // 4. Fetch Cephalo Analyses
  const { data: cephaloAnalyses = [] } = useQuery({
    queryKey: ['cephaloAnalyses', patientId],
    queryFn: async () => {
      const res = await api.get(`/patients/${patientId}/analyses`);
      return res.data;
    },
    retry: 0
  });

  // Compute stats with useMemo
  const { totalFacture, totalEncaisse } = useMemo(() => {
    let fact = 0;
    let encaiss = 0;
    actes.forEach((a: Acte) => {
      fact += a.montant;
      if (a.statut_paiement === 'PAYE') {
        encaiss += a.montant;
      } else if (a.statut_paiement === 'PARTIEL') {
        encaiss += a.montant * 0.5; // Heuristic
      }
    });
    return { totalFacture: fact, totalEncaisse: encaiss };
  }, [actes]);

  const loading = loadingActes || loadingAppts;

  const updateNotesMutation = useMutation({
    mutationFn: async ({ acteId, notes }: { acteId: number, notes: string }) => {
      await api.put(`/actes/${acteId}`, { notes_cliniques: notes });
    },
    onSuccess: () => {
      toast.success("Notes sauvegardées avec succès.");
      queryClient.invalidateQueries({ queryKey: ['actes', patientId] });
      setEditingActeId(null);
    },
    onError: () => {
      toast.error("Erreur de sauvegarde.");
    }
  });

  const handleSaveNotes = (acteId: number) => {
    updateNotesMutation.mutate({ acteId, notes: editNotes });
  };

  const startEditing = (acte: Acte) => {
    setEditNotes(acte.notes_cliniques || '');
    setEditingActeId(acte.id);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>, acte: Acte) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    
    try {
      toast.loading("Envoi de l'image en cours...", { id: `upload-${acte.id}` });
      await api.post(`/actes/${acte.id}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      queryClient.invalidateQueries({ queryKey: ['actes', patientId] });
      toast.success("Image ajoutée avec succès.", { id: `upload-${acte.id}` });
    } catch (err) {
      toast.error("Échec de l'upload.", { id: `upload-${acte.id}` });
    }
  };

  const handleGeneratePrescription = (acte: Acte) => {
    setEditingDoc({
      type: 'ordonnance',
      clinical_data: { 
        reason: acte.libelle, 
        // L'IA complétera automatiquement
      }
    });
  };

  const handleGenerateInvoice = (acte: Acte) => {
    setEditingDoc({
      type: 'honoraires',
      clinical_data: {
        items: [{ acte: acte.libelle, dent: '', prix_unitaire: acte.montant }]
      }
    });
  };

  if (loading) {
    return <EliteGhostLoader text="Chargement du suivi clinique..." />;
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Dashboard Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-card-bg p-6 rounded-[2rem] border border-border-main shadow-sm flex flex-col justify-center">
          <div className="flex items-center gap-3 text-text-muted font-bold text-sm uppercase tracking-widest mb-2">
            <Stethoscope size={18} />
            Total Séances
          </div>
          <div className="text-4xl font-black" style={{ color: 'var(--primary)' }}>
            {actes.length}
          </div>
        </div>

        <div className="bg-card-bg p-6 rounded-[2rem] border border-border-main shadow-sm flex flex-col justify-center">
          <div className="flex items-center gap-3 text-text-muted font-bold text-sm uppercase tracking-widest mb-2">
            <Banknote size={18} />
            Total Facturé
          </div>
          <div className="text-4xl font-black text-slate-800">
            {totalFacture.toLocaleString('fr-MA')} MAD
          </div>
        </div>

        <div className="bg-card-bg p-6 rounded-[2rem] border border-border-main shadow-sm flex flex-col justify-center">
          <div className="flex items-center gap-3 text-emerald-500 font-bold text-sm uppercase tracking-widest mb-2">
            <CheckCircle2 size={18} />
            Restant à Encaisser
          </div>
          <div className="text-4xl font-black text-emerald-600">
            {Math.max(0, totalFacture - totalEncaisse).toLocaleString('fr-MA')} MAD
          </div>
        </div>
      </div>

      {/* Upcoming Appointments Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {appointments.filter(a => new Date(a.datetime_start) >= new Date() && a.status !== 'ANNULE').length > 0 && (
          <div className="bg-amber-50 rounded-[2rem] border border-amber-200 p-6 shadow-sm flex flex-col justify-center">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 bg-amber-100 text-amber-600 rounded-full flex items-center justify-center shadow-inner">
                <Clock size={24} />
              </div>
              <div>
                <h3 className="font-black text-amber-900 text-lg">Prochains Rendez-vous</h3>
                <p className="text-amber-700/80 text-sm font-bold">À valider après la visite.</p>
              </div>
            </div>
            <div className="flex gap-4 overflow-x-auto pb-2">
              {appointments
                .filter(a => new Date(a.datetime_start) >= new Date() && a.status !== 'ANNULE')
                .slice(0, 2)
                .map(appt => (
                  <div key={appt.id} className="bg-white px-5 py-3 rounded-2xl border border-amber-100 shadow-sm min-w-[200px]">
                    <div className="text-xs font-black text-amber-500 uppercase tracking-widest mb-1">
                      {format(new Date(appt.datetime_start), "d MMM yyyy", { locale: fr })}
                    </div>
                    <div className="font-bold text-slate-800 text-sm">{appt.motif}</div>
                    <button 
                      onClick={() => toast.error("La création d'acte depuis un rdv nécessitera une action validée dans le menu!")}
                      className="mt-2 text-xs text-primary font-bold hover:underline"
                    >
                      Transformer en séance →
                    </button>
                  </div>
              ))}
            </div>
          </div>
        )}

        {/* Céphalo & Plan de Traitement Widget */}
        {(treatmentPlan || cephaloAnalyses.length > 0) && (
          <div className="bg-blue-50/50 rounded-[2rem] border border-blue-100 p-6 shadow-sm flex flex-col justify-center space-y-4">
            {treatmentPlan && treatmentPlan.phases && (
              <div className="flex items-center justify-between p-4 bg-white rounded-2xl border border-blue-100 shadow-sm">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center">
                    <Target size={20} />
                  </div>
                  <div>
                    <h4 className="font-black text-slate-800 text-sm">Plan de Traitement</h4>
                    <p className="text-xs text-slate-500 font-bold">Progression Active</p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-blue-600 font-black text-lg">Actif</span>
                  <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Voir Odontogramme</p>
                </div>
              </div>
            )}
            {cephaloAnalyses.length > 0 && (
              <div className="flex items-center justify-between p-4 bg-white rounded-2xl border border-indigo-100 shadow-sm">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center">
                    <Activity size={20} />
                  </div>
                  <div>
                    <h4 className="font-black text-slate-800 text-sm">Céphalométrie (IA)</h4>
                    <p className="text-xs text-slate-500 font-bold">{cephaloAnalyses.length} analyse(s) enregistrée(s)</p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-indigo-600 font-black text-sm">{format(new Date(cephaloAnalyses[0].created_at || new Date()), "d MMM yyyy", { locale: fr })}</span>
                  <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Dernier tracé</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Timeline / List of Acts */}
      <div className="bg-card-bg rounded-[2.5rem] border border-border-main shadow-elite overflow-hidden">
        <div className="p-8 border-b border-border-main flex items-center justify-between">
          <h2 className="text-2xl font-black flex items-center gap-3">
            <FileText className="text-primary" /> Fiche de Suivi (Séances)
          </h2>
          <button className="flex items-center gap-2 px-4 py-2 bg-primary/10 text-primary rounded-xl font-bold hover:bg-primary/20 transition-all text-sm">
            <Plus size={16} /> Ajouter une note manuelle
          </button>
        </div>

        <div className="p-8 space-y-6">
          {actes.length === 0 ? (
            <div className="text-center py-10 text-text-muted font-bold">
              Aucun acte ou séance enregistré pour ce patient.
            </div>
          ) : (
            actes.map((acte) => (
              <div key={acte.id} className="group flex gap-6">
                {/* Timeline Line */}
                <div className="flex flex-col items-center">
                  <div className="w-12 h-12 rounded-full bg-slate-100 border-4 border-white shadow-sm flex items-center justify-center text-primary z-10">
                    <Calendar size={18} />
                  </div>
                  <div className="w-px h-full bg-slate-200 mt-2 group-last:hidden"></div>
                </div>

                {/* Content Card */}
                <div className="flex-1 bg-white border border-slate-100 rounded-3xl p-6 shadow-sm hover:shadow-md transition-all">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-xl font-black text-slate-800 mb-1">
                        {acte.libelle}
                      </h3>
                      <div className="flex items-center gap-4 text-sm font-bold text-slate-500">
                        <span className="flex items-center gap-1">
                          <Clock size={14} />
                          {format(new Date(acte.date_debut), "EEEE d MMMM yyyy 'à' HH:mm", { locale: fr })}
                        </span>
                        <span className={cn(
                          "px-2 py-0.5 rounded-md text-[10px] uppercase tracking-widest",
                          acte.statut_paiement === 'PAYE' ? "bg-emerald-100 text-emerald-600" :
                          acte.statut_paiement === 'PARTIEL' ? "bg-amber-100 text-amber-600" :
                          "bg-red-100 text-red-600"
                        )}>
                          {acte.statut_paiement}
                        </span>
                        <span className="text-primary">{acte.montant} MAD</span>
                      </div>
                    </div>
                    
                    {/* Actions Rapides */}
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={() => handleGeneratePrescription(acte)}
                        className="p-2 bg-slate-50 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg shadow-sm border border-slate-100 transition-colors"
                        title="Générer une ordonnance"
                      >
                        <FileSignature size={16} />
                      </button>
                      <button 
                        onClick={() => handleGenerateInvoice(acte)}
                        className="p-2 bg-slate-50 text-slate-500 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg shadow-sm border border-slate-100 transition-colors"
                        title="Générer une note d'honoraires"
                      >
                        <Receipt size={16} />
                      </button>
                    </div>
                  </div>

                  {/* Notes section */}
                  <div className="bg-slate-50 rounded-2xl p-5 mb-4">
                    {editingActeId === acte.id ? (
                      <div className="space-y-3">
                        <textarea
                          className="w-full bg-white border border-slate-200 rounded-xl p-3 min-h-[100px] text-sm focus:ring-2 focus:ring-primary outline-none"
                          placeholder="Saisissez vos notes cliniques (Ex: ttt canalaire, LT = 21mm, particularités...)"
                          value={editNotes}
                          onChange={(e) => setEditNotes(e.target.value)}
                        />
                        <div className="flex justify-end gap-2">
                          <button 
                            onClick={() => setEditingActeId(null)}
                            className="px-4 py-2 text-sm font-bold text-slate-500 hover:bg-slate-200 rounded-lg"
                          >
                            Annuler
                          </button>
                          <button 
                            onClick={() => handleSaveNotes(acte.id)}
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
                          onClick={() => startEditing(acte)}
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
                            <img src={url} alt="Attachment" className="w-full h-full object-cover" />
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
                        onChange={(e) => handleFileUpload(e, acte)}
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
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
