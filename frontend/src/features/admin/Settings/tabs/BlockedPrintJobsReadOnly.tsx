import { useCallback, useEffect, useState } from 'react';
import { AlertTriangle, RefreshCw, ShieldCheck } from 'lucide-react';
import { api } from '../../../../services/api';

type BlockedJob = {
  reference: string;
  status: 'uncertain';
  updatedAt: string;
  investigations: number;
};
type BlockedJobsResponse = {
  status: 'review_only';
  printingAvailable: false;
  retrySupported: false;
  total: number;
  jobs: BlockedJob[];
};

/**
 * LOT04.8-C owner Cabinet monitoring. READ ONLY, never Station-facing.
 * No print retry, printer selection, document link, patient identity, PDF,
 * completed indicator or mutating network request.
 */
export function BlockedPrintJobsReadOnly({ ownerVerified }: { ownerVerified: boolean }) {
  const [data, setData] = useState<BlockedJobsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);

  const refresh = useCallback(async () => {
    if (!ownerVerified) return;
    setLoading(true);
    setFailed(false);
    try {
      const result = await api.get<BlockedJobsResponse>('/admin/station-print-config/blocked-jobs');
      if (
        result.data.status !== 'review_only'
        || result.data.printingAvailable !== false
        || result.data.retrySupported !== false
        || !Array.isArray(result.data.jobs)
      ) {
        throw new Error('UNEXPECTED_PRINT_MONITOR_CONTRACT');
      }
      setData(result.data);
    } catch {
      setFailed(true);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [ownerVerified]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  if (!ownerVerified) return null;

  return (
    <section data-testid="blocked-print-jobs-read-only" aria-label="Impressions bloquées"
      className="w-full min-w-0 overflow-hidden rounded-2xl border border-amber-200 bg-amber-50/50 p-4 sm:p-6">
      <div className="flex min-w-0 flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 items-start gap-3">
          <ShieldCheck className="mt-0.5 shrink-0 text-amber-700" size={22} />
          <div className="min-w-0">
            <h3 className="text-lg font-black text-slate-900">Impressions à vérifier</h3>
            <p className="mt-1 text-sm leading-relaxed text-slate-700">
              Suivi réservé au propriétaire du Cabinet. Une impression incertaine exige une vérification humaine.
              Aucune relance n’est possible depuis cet écran.
            </p>
          </div>
        </div>
        <button type="button" onClick={() => void refresh()} disabled={loading}
          className="inline-flex w-full shrink-0 items-center justify-center gap-2 rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-bold text-slate-800 disabled:opacity-50 sm:w-auto">
          <RefreshCw size={16} aria-hidden="true" />
          Actualiser les états
        </button>
      </div>
      <div role="status" aria-live="polite" className="mt-4 text-sm text-slate-700">
        {loading ? 'Lecture des états…' : failed
          ? 'États indisponibles. Aucun résultat précédent n’est affiché.'
          : data && data.total === 0 ? 'Aucune impression bloquée répertoriée.'
          : data ? `${data.total} impression(s) à vérifier, ${data.jobs.length} affichée(s).`
          : 'Aucun état chargé.'}
      </div>
      {data && data.jobs.length > 0 && (
        <ul className="mt-4 grid min-w-0 grid-cols-1 gap-3 lg:grid-cols-2">
          {data.jobs.map((job) => (
            <li key={job.reference}
              className="min-w-0 rounded-xl border border-amber-200 bg-white p-4"
              data-print-job-status="uncertain">
              <div className="flex min-w-0 items-center gap-2">
                <AlertTriangle size={17} className="shrink-0 text-amber-700" aria-hidden="true" />
                <strong className="break-all text-sm text-slate-900">Réf. {job.reference}</strong>
              </div>
              <p className="mt-2 text-sm font-semibold text-amber-800">À vérifier — ne pas réimprimer</p>
              <p className="mt-1 break-words text-xs text-slate-600">
                Dernier changement : {new Date(job.updatedAt).toLocaleString()}
              </p>
              <p className="mt-1 text-xs text-slate-600">
                Constat(s) d’investigation : {job.investigations}
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
