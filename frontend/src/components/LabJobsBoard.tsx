import React, { useEffect, useState } from "react";

import { api } from "../services/api";
import type { Lab, LabJob } from "../types/labJob";
import { LabJobStatus } from "../types/labJob";
import {
  createLab,
  createLabJob,
  deleteLab,
  fetchLabJobs,
  fetchLabs,
  patchLabJobStatus,
} from "../services/labJobService";

const formatDistanceToNowStrict = (date: Date): string => {
  const diffMs = date.getTime() - Date.now();
  const diffDays = Math.round(diffMs / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return "aujourd'hui";
  return diffDays > 0
    ? `dans ${diffDays} jour${diffDays > 1 ? "s" : ""}`
    : `il y a ${-diffDays} jour${-diffDays > 1 ? "s" : ""}`;
};

const parseISO = (iso: string): Date => new Date(iso);

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

type StockItem = {
  id: number;
  nom: string;
  categorie: string;
};

export const LabJobsBoard: React.FC = () => {
  const [jobs, setJobs] = useState<LabJob[]>([]);
  const [labs, setLabs] = useState<Lab[]>([]);
  const [materials, setMaterials] = useState<string[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [showLabManager, setShowLabManager] = useState(false);
  const [newLabName, setNewLabName] = useState("");
  const [newLabPhone, setNewLabPhone] = useState("");
  const [labError, setLabError] = useState("");
  const [newJob, setNewJob] = useState({
    patient_id: "",
    act_id: "",
    lab_id: "",
    type: "Couronne",
    tooth_number: "",
    material: "Céramique",
    is_remake: false,
  });

  const loadJobs = async () => {
    const data = await fetchLabJobs();
    setJobs(data);
  };

  const loadCustomization = async () => {
    const [labRows, stockResponse] = await Promise.all([
      fetchLabs(),
      api.get<StockItem[]>("/stock/items"),
    ]);
    setLabs(labRows);
    setMaterials(
      stockResponse.data
        .filter(item => item.categorie === "MATERIAU")
        .map(item => item.nom)
        .filter(Boolean),
    );
  };

  const handleCreate = async () => {
    if (!newJob.patient_id || !newJob.act_id) {
      window.alert("Le patient et l'acte sont requis.");
      return;
    }
    const deadline = new Date();
    deadline.setDate(deadline.getDate() + 7);
    await createLabJob({
      patient_id: parseInt(newJob.patient_id),
      act_id: parseInt(newJob.act_id),
      lab_id: newJob.lab_id ? parseInt(newJob.lab_id) : undefined,
      type: newJob.type,
      tooth_number: newJob.tooth_number,
      material: newJob.material,
      deadline: deadline.toISOString(),
      is_remake: newJob.is_remake,
    });
    setShowModal(false);
    setNewJob({
      patient_id: "",
      act_id: "",
      lab_id: "",
      type: "Couronne",
      tooth_number: "",
      material: "Céramique",
      is_remake: false,
    });
    await loadJobs();
  };

  const handleCreateLab = async () => {
    const name = newLabName.trim();
    if (!name) return;
    setLabError("");
    try {
      await createLab({
        name,
        phone: newLabPhone.trim() || undefined,
      });
      setNewLabName("");
      setNewLabPhone("");
      await loadCustomization();
    } catch (error: any) {
      setLabError(error?.response?.data?.detail || "Impossible d’enregistrer ce laboratoire.");
    }
  };

  const handleDeleteLab = async (lab: Lab) => {
    setLabError("");
    try {
      await deleteLab(lab.id);
      if (newJob.lab_id === String(lab.id)) {
        setNewJob(current => ({ ...current, lab_id: "" }));
      }
      await loadCustomization();
    } catch (error: any) {
      setLabError(error?.response?.data?.detail || "Impossible de supprimer ce laboratoire.");
    }
  };

  useEffect(() => {
    void loadJobs();
    void loadCustomization();
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
    <div className="flex h-full w-full flex-col relative">
      <div className="flex flex-wrap justify-between gap-3 items-center mb-4 px-4 pt-4">
        <div>
          <h1 className="text-xl font-black text-slate-800 tracking-tight">Travaux prothétiques</h1>
          <p className="mt-1 text-[11px] font-medium text-slate-500">
            Laboratoires du cabinet et matériaux issus de votre stock.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setShowLabManager(true)}
            className="px-4 py-2.5 bg-white text-slate-700 border border-slate-200 rounded-xl font-bold text-xs shadow-sm hover:bg-slate-50 transition-colors"
          >
            Gérer les laboratoires
          </button>
          <button
            onClick={() => setShowModal(true)}
            className="px-5 py-2.5 bg-slate-900 text-white rounded-xl font-bold text-xs shadow-md hover:bg-slate-800 transition-colors"
          >
            + Nouvelle demande
          </button>
        </div>
      </div>

      <div className="flex space-x-4 overflow-x-auto p-4 flex-1">
        {STATUS_ORDER.map(status => (
          <div key={status} className="flex-1 min-w-[200px]">
            <h2 className="text-center font-black text-sm mb-4 text-slate-700 tracking-tight">
              {STATUS_LABELS[status]}
            </h2>
            <div className="space-y-3">
              {jobs.filter(job => job.status === status).length === 0 ? (
                <div className="p-4 rounded-xl border-2 border-dashed border-slate-200/60 bg-slate-50/50 text-center flex flex-col items-center justify-center min-h-[100px]">
                  <p className="text-xs font-bold text-slate-400 mb-1">Aucun travail</p>
                  {status === LabJobStatus.PRESCRIPTION && <p className="text-[10px] text-slate-400 leading-tight">Créez une demande depuis le dossier patient ou manuellement.</p>}
                  {status === LabJobStatus.SENT && <p className="text-[10px] text-slate-400 leading-tight">Déplacez ici les travaux envoyés au laboratoire.</p>}
                  {status === LabJobStatus.IN_PROGRESS && <p className="text-[10px] text-slate-400 leading-tight">Travaux en cours de fabrication.</p>}
                  {status === LabJobStatus.TRY_IN && <p className="text-[10px] text-slate-400 leading-tight">Travaux en cours d’essayage clinique.</p>}
                  {status === LabJobStatus.READY && <p className="text-[10px] text-slate-400 leading-tight">Travaux finalisés et prêts.</p>}
                </div>
              ) : (
                jobs
                  .filter(job => job.status === status)
                  .map(job => (
                    <div
                      key={job.id}
                      className={`p-4 rounded-2xl shadow-sm bg-white border transition-all ${isAlert(job) ? "border-red-400 shadow-red-100" : "border-slate-200/60 hover:shadow-md"}`}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div className="font-black text-slate-800 text-sm">Dent {job.tooth_number || "—"}</div>
                        <div className="text-[10px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">{job.type}</div>
                      </div>
                      <div className="text-[11px] font-semibold text-slate-500">
                        {job.material || "Matériau non renseigné"}
                      </div>
                      <div className={`text-xs font-bold mt-2 ${isAlert(job) ? "text-red-500" : "text-slate-500"}`}>
                        ⏳ {formatDistanceToNowStrict(parseISO(job.deadline))}
                      </div>
                      <select
                        className="mt-3 w-full text-xs font-bold text-slate-600 bg-slate-50 border border-slate-200 rounded-lg p-2 focus:ring-2 focus:ring-primary/20 outline-none transition-all cursor-pointer"
                        value={job.status}
                        onChange={event => void moveJob(job.id, event.target.value as LabJobStatus)}
                      >
                        {STATUS_ORDER.map(option => (
                          <option key={option} value={option}>{STATUS_LABELS[option]}</option>
                        ))}
                      </select>
                    </div>
                  ))
              )}
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-3xl p-6 shadow-xl w-full max-w-md border border-slate-200">
            <h2 className="text-lg font-black text-slate-800 mb-1 tracking-tight">Nouvelle demande labo</h2>
            <p className="mb-4 text-[11px] font-medium text-slate-500">Les listes proposées viennent uniquement de votre cabinet.</p>

            <div className="space-y-4">
              <div className="flex gap-4">
                <div className="flex-1">
                  <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">N° patient *</label>
                  <input aria-label="N° patient" type="number" className="w-full text-sm font-bold text-slate-700 bg-slate-50 border border-slate-200 rounded-xl p-3" value={newJob.patient_id} onChange={event => setNewJob({...newJob, patient_id: event.target.value})} placeholder="Ex : 1" />
                </div>
                <div className="flex-1">
                  <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">N° acte *</label>
                  <input aria-label="N° acte" type="number" className="w-full text-sm font-bold text-slate-700 bg-slate-50 border border-slate-200 rounded-xl p-3" value={newJob.act_id} onChange={event => setNewJob({...newJob, act_id: event.target.value})} placeholder="Ex : 15" />
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Laboratoire</label>
                <select
                  aria-label="Laboratoire"
                  className="w-full text-sm font-bold text-slate-700 bg-slate-50 border border-slate-200 rounded-xl p-3"
                  value={newJob.lab_id}
                  onChange={event => setNewJob({...newJob, lab_id: event.target.value})}
                >
                  <option value="">Non renseigné</option>
                  {labs.map(lab => <option key={lab.id} value={lab.id}>{lab.name}</option>)}
                </select>
              </div>

              <div className="flex gap-4">
                <div className="flex-1">
                  <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Type de travail</label>
                  <input aria-label="Type de travail" type="text" className="w-full text-sm font-bold text-slate-700 bg-slate-50 border border-slate-200 rounded-xl p-3" value={newJob.type} onChange={event => setNewJob({...newJob, type: event.target.value})} />
                </div>
                <div className="w-24">
                  <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Dent</label>
                  <input aria-label="Dent" type="text" className="w-full text-sm font-bold text-slate-700 bg-slate-50 border border-slate-200 rounded-xl p-3 text-center" value={newJob.tooth_number} onChange={event => setNewJob({...newJob, tooth_number: event.target.value})} placeholder="46" />
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Matériau</label>
                <input
                  aria-label="Matériau"
                  type="text"
                  list="cust05-materials"
                  className="w-full text-sm font-bold text-slate-700 bg-slate-50 border border-slate-200 rounded-xl p-3"
                  value={newJob.material}
                  onChange={event => setNewJob({...newJob, material: event.target.value})}
                />
                <datalist id="cust05-materials">
                  {materials.map(material => <option key={material} value={material} />)}
                </datalist>
                <p className="mt-1 text-[10px] font-medium text-slate-400">
                  Suggestions issues des matériaux enregistrés dans Stock. Saisie libre autorisée.
                </p>
              </div>

              <label className="flex items-center gap-2 cursor-pointer mt-2">
                <input type="checkbox" className="w-4 h-4 text-slate-900 rounded border-slate-300" checked={newJob.is_remake} onChange={event => setNewJob({...newJob, is_remake: event.target.checked})} />
                <span className="text-xs font-bold text-slate-700">Réfection ou réparation</span>
              </label>
            </div>

            <div className="flex justify-end gap-3 mt-8">
              <button onClick={() => setShowModal(false)} className="px-5 py-2.5 rounded-xl font-bold text-xs text-slate-500 hover:bg-slate-100">Annuler</button>
              <button onClick={() => void handleCreate()} className="px-5 py-2.5 bg-slate-900 text-white rounded-xl font-bold text-xs shadow-md hover:bg-slate-800">Créer la demande</button>
            </div>
          </div>
        </div>
      )}

      {showLabManager && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-3xl p-6 shadow-xl w-full max-w-md border border-slate-200">
            <h2 className="text-lg font-black text-slate-800 tracking-tight">Laboratoires du cabinet</h2>
            <p className="mt-1 text-[11px] font-medium text-slate-500">Ajoutez uniquement les laboratoires avec lesquels votre cabinet travaille.</p>

            <div className="mt-5 space-y-2">
              {labs.length ? labs.map(lab => (
                <div key={lab.id} className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 px-3 py-2.5">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-black text-slate-800">{lab.name}</div>
                    {lab.phone && <div className="text-[10px] font-semibold text-slate-400">{lab.phone}</div>}
                  </div>
                  <button
                    type="button"
                    onClick={() => void handleDeleteLab(lab)}
                    className="shrink-0 rounded-lg px-2.5 py-1.5 text-[10px] font-black text-rose-600 hover:bg-rose-50"
                  >
                    Supprimer
                  </button>
                </div>
              )) : (
                <div className="rounded-xl border border-dashed border-slate-200 p-4 text-center text-[11px] font-semibold text-slate-400">
                  Aucun laboratoire enregistré.
                </div>
              )}
            </div>

            <div className="mt-5 rounded-2xl bg-slate-50 p-4 space-y-3">
              <div className="text-[10px] font-black uppercase tracking-wider text-slate-500">Ajouter un laboratoire</div>
              <input
                value={newLabName}
                onChange={event => setNewLabName(event.target.value)}
                placeholder="Nom du laboratoire"
                className="w-full rounded-xl border border-slate-200 bg-white p-3 text-sm font-bold text-slate-700"
              />
              <input
                value={newLabPhone}
                onChange={event => setNewLabPhone(event.target.value)}
                placeholder="Téléphone (optionnel)"
                className="w-full rounded-xl border border-slate-200 bg-white p-3 text-sm font-bold text-slate-700"
              />
              {labError && <p role="alert" className="text-[10px] font-bold text-rose-600">{labError}</p>}
              <button
                type="button"
                onClick={() => void handleCreateLab()}
                disabled={!newLabName.trim()}
                className="w-full rounded-xl bg-slate-900 px-4 py-2.5 text-xs font-black text-white disabled:opacity-40"
              >
                Ajouter le laboratoire
              </button>
            </div>

            <div className="mt-6 flex justify-end">
              <button onClick={() => setShowLabManager(false)} className="px-5 py-2.5 rounded-xl font-bold text-xs text-slate-600 hover:bg-slate-100">
                Fermer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
