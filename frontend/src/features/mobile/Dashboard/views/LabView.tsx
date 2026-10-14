import { LabJobStatus } from '../../../../types/labJob';
import type { LabJob } from '../../../../types/labJob';

const STATUS_LABELS: Record<LabJobStatus, string> = {
  [LabJobStatus.PRESCRIPTION]: 'Brouillon',
  [LabJobStatus.SENT]: 'Transmis',
  [LabJobStatus.IN_PROGRESS]: 'En fabrication',
  [LabJobStatus.TRY_IN]: 'Essayage',
  [LabJobStatus.READY]: 'Prêt',
  [LabJobStatus.DELIVERED]: 'Livré',
};

export function LabView({
  labJobs,
  handleWhatsAppSend,
  isOnline = true,
}: {
  labJobs: LabJob[];
  handleWhatsAppSend: (job: LabJob) => void;
  isOnline?: boolean;
}) {
  const sorted = labJobs.slice().sort((a, b) => a.deadline.localeCompare(b.deadline) || a.id - b.id);
  const pending = sorted.filter(job => job.status !== LabJobStatus.DELIVERED).length;
  return (
    <section data-mobile-lab className="space-y-3 pb-8">
      <div className="rounded-[22px] border border-border-main bg-card p-4 shadow-sm">
        <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-primary">Laboratoire</p>
        <h2 className="mt-1 text-[21px] font-bold text-text-main">Suivi des envois</h2>
        <p className="mt-2 text-[12px] font-medium text-text-muted">{pending} travail{pending > 1 ? 'x' : ''} en cours · statut confirmé par le cabinet</p>
        <p className="mt-1 text-[12px] font-medium text-text-muted">La préparation d’un message ne confirme jamais sa réception par le laboratoire.</p>
      </div>
      {sorted.length === 0 && <div className="rounded-[20px] border border-glass-border bg-card p-6 text-center text-[11px] font-bold text-text-muted">Aucun travail Labo à afficher.</div>}
      {sorted.map(job => (
        <article key={job.id} className="rounded-[24px] border border-glass-border bg-card p-4 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="text-[13px] font-semibold text-text-main">{job.type} {job.tooth_number ? `· dent ${job.tooth_number}` : ''}</p>
              <p className="mt-1 text-[11px] font-medium text-text-muted">Échéance : {new Date(job.deadline).toLocaleDateString('fr-FR')}</p>
            </div>
            <span className="rounded-full border border-primary/20 bg-primary/5 px-2.5 py-1 text-[11px] font-semibold text-primary">
              {STATUS_LABELS[job.status] ?? 'Statut à vérifier'}
            </span>
          </div>
          {job.status === LabJobStatus.PRESCRIPTION && (
            <button
              type="button"
              disabled={!isOnline}
              onClick={() => handleWhatsAppSend(job)}
              className="mt-3 min-h-11 w-full rounded-[14px] border border-primary/20 bg-primary/10 px-4 text-[12px] font-semibold text-primary disabled:opacity-40"
            >
              Copier le brouillon
            </button>
          )}
        </article>
      ))}
    </section>
  );
}
