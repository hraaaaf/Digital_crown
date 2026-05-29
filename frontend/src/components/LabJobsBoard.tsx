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
          <h2 className="text-center font-bold mb-2">{status}</h2>
          <div className="space-y-2">
            {jobs
              .filter((j) => j.status === status)
              .map((job) => (
                <div
                  key={job.id}
                  className={`p-3 rounded shadow-sm bg-white border ${isAlert(job) ? "border-red-500" : "border-gray-200"}`}
                >
                  <div className="font-medium">{job.tooth_number || "—"}</div>
                  <div className="text-sm text-gray-600">{job.type}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {formatDistanceToNowStrict(parseISO(job.deadline))}
                  </div>
                  <select
                    className="mt-2 w-full text-sm"
                    value={job.status}
                    onChange={(e) => moveJob(job.id, e.target.value as LabJobStatus)}
                  >
                    {STATUS_ORDER.map((opt) => (
                      <option key={opt} value={opt}>
                        {opt}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
          </div>
        </div>
      ))}
    </div>
  );
};
