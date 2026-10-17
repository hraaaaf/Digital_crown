import { AlertTriangle, FilePenLine, Info } from 'lucide-react';

export interface PatientClinicalAdvice {
  title: string;
  message: string;
  action?: string;
}

/**
 * Same source-first clinical context on dossier, imaging and G1 MultiView.
 * A missing medical history is UNKNOWN, never "no known history".
 * NBA.action comes from free text, not a trusted route or executable command.
 * Parent protected patient route owns permissions and patient identity.
 */
export function PatientClinicalContextNotice({
  medicalHistory,
  advice,
  onEdit,
}: {
  medicalHistory?: string | null;
  advice?: PatientClinicalAdvice | null;
  onEdit: () => void;
}) {
  const historyMissing = !medicalHistory?.trim();
  const hasAdvice = Boolean(advice?.title?.trim() || advice?.message?.trim() || advice?.action?.trim());
  // The same backend fact is already represented by the missing-history status.
  const repeatsMissingHistory = historyMissing && advice?.message?.trim().toLocaleLowerCase('fr-FR') === 'antécédents médicaux non renseignés';
  if (!historyMissing && !hasAdvice) return null;

  return (
    <section data-testid="patient-clinical-context" aria-label="Contexte clinique du dossier" className="min-w-0 space-y-2">
      {historyMissing && (
        <div
          role="status"
          aria-label="Antécédents médicaux non renseignés"
          className="flex min-w-0 flex-wrap items-center gap-3 rounded-elite-sm border border-warning-border bg-warning-surface px-4 py-3 text-text-main"
        >
          <AlertTriangle size={19} className="shrink-0 text-warning" aria-hidden="true" />
          <div className="min-w-0 flex-1">
            <h3 className="text-sm font-bold">Antécédents médicaux non renseignés</h3>
            <p className="mt-1 text-sm leading-relaxed">
              Aucune information d’antécédents n’est enregistrée. Cela ne confirme pas leur absence.
            </p>
          </div>
          <button
            type="button"
            onClick={onEdit}
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-bold text-on-primary focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
            aria-label="Compléter les antécédents dans la fiche patient"
          >
            <FilePenLine size={16} aria-hidden="true" />
            Compléter le dossier
          </button>
        </div>
      )}
      {hasAdvice && advice && (
        <aside
          data-v15-07-g1-inline-nba
          role="note"
          aria-label="Conseil clinique du dossier"
          className="flex min-w-0 items-start gap-3 rounded-elite-sm border border-border-main bg-card-bg px-4 py-3 text-text-main"
        >
          <Info size={19} className="mt-0.5 shrink-0 text-text-main" aria-hidden="true" />
          <div className="min-w-0 space-y-1">
            <h3 className="text-sm font-bold">Conseil clinique</h3>
            {advice.title?.trim() && <p className="text-sm font-semibold break-words">{advice.title}</p>}
            {advice.message?.trim() && !repeatsMissingHistory && <p className="text-sm leading-relaxed break-words">{advice.message}</p>}
            {advice.action?.trim() && (
              <p className="text-sm leading-relaxed break-words">
                <span className="font-bold">Action conseillée (non exécutée) : </span>
                {advice.action}
              </p>
            )}
          </div>
        </aside>
      )}
    </section>
  );
}
