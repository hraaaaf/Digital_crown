import { LabJobStatus } from '../../../../types/labJob';
import type { LabJob } from '../../../../types/labJob';

export function LabView({
  labJobs,
  handleWhatsAppSend
}: {
  labJobs: LabJob[];
  handleWhatsAppSend: (job: LabJob) => void;
}) {
  return (
    <div className="space-y-4">
      {labJobs.filter(job => job.status === 'PRESCRIPTION').map(job => (
        <div key={job.id} className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[24px] p-5 shadow-elite flex items-center justify-between">
          <div>
            <p className="font-black text-text-main">{job.type} ({job.tooth_number})</p>
            <p className="text-[10px] text-text-muted">Échéance: {new Date(job.deadline).toLocaleDateString()}</p>
          </div>
          <button onClick={() => handleWhatsAppSend(job)} className="bg-primary/10 text-primary text-[10px] font-black px-4 py-2 rounded-lg">
            Envoyer
          </button>
        </div>
      ))}
    </div>
  );
}
