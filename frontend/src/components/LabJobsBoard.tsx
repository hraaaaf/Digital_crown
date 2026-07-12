import React, { useEffect, useState } from "react";

// Simple date utilities (replacing date-fns)
const formatDistanceToNowStrict = (date: Date): string => {
  const diffMs = date.getTime() - Date.now();
  const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return 'aujourd\'hui';
  return diffDays > 0 ? `dans ${diffDays} jour${diffDays > 1 ? 's' : ''}` : `il y a ${-diffDays} jour${-diffDays > 1 ? 's' : ''}`;
};
const parseISO = (iso: string): Date => new Date(iso);

import type { LabJob } from "../types/labJob";
import { LabJobStatus } from "../types/labJob";
import { fetchLabJobs, patchLabJobStatus, createLabJob } from "../services/labJobService";

/**
 * Minimal Kanban board for LabJob management.
 * Columns represent active statuses. Cards display tooth number, type, and a countdown.
 * If a job is late (is_late flag) or its deadline is <24h away, the border turns red.
 */
const STATUS_ORDER: LabJobStatus[] = [
  LabJobStatus.PRESCRIPTION,
  LabJobStatus.SENT,
  LabJobStatus.IN_PROGRESS,
  LabJobStatus.TRY_IN,
  LabJobStatus.READY,
];

const STATUS_LABELS: Record<LabJobStatus, string> = {
  [LabJobStatus.PRESCRIPTION]: "Prescription",
  [LabJobStatus.SENT]: "Envoyé au labo",
  [LabJobStatus.IN_PROGRESS]: "En fabrication",
  [LabJobStatus.TRY_IN]: "Essayage",
  [LabJobStatus.READY]: "Prêt / Terminé",
  [LabJobStatus.DELIVERED]: "Livré",
};

export const LabJobsBoard: React.FC = () => {
  const [jobs, setJobs] = useState<LabJob[]>([]);

  const loadJobs = async () => {
    const data = await fetchLabJobs();
    setJobs(data);
  };

  const [showModal, setShowModal] = useState(false);
  const [newJob, setNewJob] = useState({ patient_id: "", act_id: "", type: "Couronne", tooth_number: "", material: "Céramique", is_remake: false });

  const handleCreate = async () => {
    if (!newJob.patient_id || !newJob.act_id) return alert("L'ID du patient et de l'acte sont requis.");
    const deadline = new Date();
    deadline.setDate(deadline.getDate() + 7);
    await createLabJob({
      patient_id: parseInt(newJob.patient_id),
      act_id: parseInt(newJob.act_id),
      type: newJob.type,
      tooth_number: newJob.tooth_number,
      material: newJob.material,
      deadline: deadline.toISOString(),
      is_remake: newJob.is_remake
    });
    setShowModal(false);
    setNewJob({ patient_id: "", act_id: "", type: "Couronne", tooth_number: "", material: "Céramique", is_remake: false });
    await loadJobs();
  };


  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadJobs();
    const interval = setInterval(loadJobs, 30000);
    return () => clearInterval(interval);
  }, []);

  const moveJob = async (jobId: number, newStatus: LabJobStatus) => {
    await patchLabJobStatus(jobId, { status: newStatus });
    await loadJobs();
  };

  const isAlert = (job: LabJob) => {
    const now = new Date();
    const deadline = parseISO(job.deadline);
    const diffHours = (deadline.getTime() - now.getTime()) / 3600000;
    return job.is_late || diffHours < 24;
  };

  return (
    <div className="flex flex-col h-full w-full relative">
      <div className="mx-4 mt-4 px-4 py-2.5 bg-amber-50 border border-amber-200 rounded-xl text-xs font-bold text-amber-700 flex items-center gap-2">
        <span className="text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-600 border border-amber-500/20">Bientôt</span>
        Module en cours de finalisation — bientôt disponible dans sa version complète. Vous pouvez déjà l'utiliser normalement.
      </div>
      <div className="flex justify-between items-center mb-4 px-4 pt-4">
        <h1 className="text-xl font-black text-slate-800 tracking-tight">Travaux Prothétiques</h1>
        <button 
          onClick={() => setShowModal(true)} 
          className="px-5 py-2.5 bg-slate-900 text-white rounded-xl font-bold text-xs shadow-md hover:bg-slate-800 transition-colors flex items-center gap-2"
        >
          <span>+ Nouvelle Demande Manuelle</span>
        </button>
      </div>

      {/* Kanban Board */}
      <div className="flex space-x-4 overflow-x-auto p-4 flex-1">
      {STATUS_ORDER.map((status) => (
        <div key={status} className="flex-1 min-w-[200px]">
          <h2 className="text-center font-black text-sm mb-4 text-slate-700 tracking-tight">{STATUS_LABELS[status]}</h2>
          <div className="space-y-3">
            {jobs.filter((j) => j.status === status).length === 0 ? (
              <div className="p-4 rounded-xl border-2 border-dashed border-slate-200/60 bg-slate-50/50 text-center flex flex-col items-center justify-center min-h-[100px]">
                <p className="text-xs font-bold text-slate-400 mb-1">Aucun travail</p>
                {status === LabJobStatus.PRESCRIPTION && <p className="text-[10px] text-slate-400 leading-tight">Créez une prescription depuis le dossier patient pour commencer.</p>}
                {status === LabJobStatus.SENT && <p className="text-[10px] text-slate-400 leading-tight">Déplacez une prescription ici lorsqu'elle est envoyée au laboratoire.</p>}
                {status === LabJobStatus.IN_PROGRESS && <p className="text-[10px] text-slate-400 leading-tight">En attente de réception du laboratoire.</p>}
                {status === LabJobStatus.TRY_IN && <p className="text-[10px] text-slate-400 leading-tight">Travaux en cours d'essayage clinique.</p>}
                {status === LabJobStatus.READY && <p className="text-[10px] text-slate-400 leading-tight">Travaux finalisés et prêts à être posés.</p>}
              </div>
            ) : (
              jobs
                .filter((j) => j.status === status)
                .map((job) => (
                  <div
                    key={job.id}
                    className={`p-4 rounded-2xl shadow-sm bg-white border transition-all ${isAlert(job) ? "border-red-400 shadow-red-100" : "border-slate-200/60 hover:shadow-md"}`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="font-black text-slate-800 text-sm">Dent {job.tooth_number || "—"}</div>
                      <div className="text-[10px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">{job.type}</div>
                    </div>
                    <div className={`text-xs font-bold mt-2 ${isAlert(job) ? "text-red-500" : "text-slate-500"}`}>
                      ⏳ {formatDistanceToNowStrict(parseISO(job.deadline))}
                    </div>
                    <select
                      className="mt-3 w-full text-xs font-bold text-slate-600 bg-slate-50 border border-slate-200 rounded-lg p-2 focus:ring-2 focus:ring-primary/20 outline-none transition-all cursor-pointer"
                      value={job.status}
                      onChange={(e) => moveJob(job.id, e.target.value as LabJobStatus)}
                    >
                      {STATUS_ORDER.map((opt) => (
                        <option key={opt} value={opt}>
                          {STATUS_LABELS[opt]}
                        </option>
                      ))}
                    </select>
                  </div>
                ))
            )}
          </div>
        </div>
      ))}
    </div>

      {/* Modale de création manuelle */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-3xl p-6 shadow-xl w-full max-w-md border border-slate-200">
            <h2 className="text-lg font-black text-slate-800 mb-4 tracking-tight">Demande Labo Manuelle</h2>
            
            <div className="space-y-4">
              <div className="flex gap-4">
                <div className="flex-1">
                  <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Patient ID (Requis)</label>
                  <input type="number" className="w-full text-sm font-bold text-slate-700 bg-slate-50 border border-slate-200 rounded-xl p-3 focus:ring-2 focus:ring-primary/20 outline-none transition-all" value={newJob.patient_id} onChange={e => setNewJob({...newJob, patient_id: e.target.value})} placeholder="Ex: 1" />
                </div>
                <div className="flex-1">
                  <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Acte ID (Requis)</label>
                  <input type="number" className="w-full text-sm font-bold text-slate-700 bg-slate-50 border border-slate-200 rounded-xl p-3 focus:ring-2 focus:ring-primary/20 outline-none transition-all" value={newJob.act_id} onChange={e => setNewJob({...newJob, act_id: e.target.value})} placeholder="Ex: 15" />
                </div>
              </div>

              <div className="flex gap-4">
                <div className="flex-1">
                  <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Type de prothèse</label>
                  <input type="text" className="w-full text-sm font-bold text-slate-700 bg-slate-50 border border-slate-200 rounded-xl p-3 focus:ring-2 focus:ring-primary/20 outline-none transition-all" value={newJob.type} onChange={e => setNewJob({...newJob, type: e.target.value})} />
                </div>
                <div className="w-24">
                  <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Dent</label>
                  <input type="text" className="w-full text-sm font-bold text-slate-700 bg-slate-50 border border-slate-200 rounded-xl p-3 text-center focus:ring-2 focus:ring-primary/20 outline-none transition-all" value={newJob.tooth_number} onChange={e => setNewJob({...newJob, tooth_number: e.target.value})} placeholder="Ex: 46" />
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Matériau</label>
                <input type="text" className="w-full text-sm font-bold text-slate-700 bg-slate-50 border border-slate-200 rounded-xl p-3 focus:ring-2 focus:ring-primary/20 outline-none transition-all" value={newJob.material} onChange={e => setNewJob({...newJob, material: e.target.value})} />
              </div>

              <label className="flex items-center gap-2 cursor-pointer mt-2">
                <input type="checkbox" className="w-4 h-4 text-slate-900 rounded border-slate-300 focus:ring-slate-900" checked={newJob.is_remake} onChange={e => setNewJob({...newJob, is_remake: e.target.checked})} />
                <span className="text-xs font-bold text-slate-700">Ceci est une réfection (Refonte / Réparation)</span>
              </label>
            </div>

            <div className="flex justify-end gap-3 mt-8">
              <button onClick={() => setShowModal(false)} className="px-5 py-2.5 rounded-xl font-bold text-xs text-slate-500 hover:bg-slate-100 transition-colors">Annuler</button>
              <button onClick={handleCreate} className="px-5 py-2.5 bg-slate-900 text-white rounded-xl font-bold text-xs shadow-md hover:bg-slate-800 transition-colors">Créer la demande</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

};
