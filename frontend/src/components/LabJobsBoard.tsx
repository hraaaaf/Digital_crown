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
import { fetchLabJobs, patchLabJobStatus } from "../services/labJobService";

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
    <div className="flex space-x-4 overflow-x-auto p-4">
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
  );
};
