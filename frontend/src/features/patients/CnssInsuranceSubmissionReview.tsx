import { useMemo } from 'react';
import {
  AlertCircle,
  BadgeCheck,
  FileCheck2,
  Loader2,
  LockKeyhole,
  ShieldCheck,
  X,
} from 'lucide-react';
import { cn } from '../../utils/cn';
import type {
  InsuranceAdministrativeSnapshot,
  InsuranceCareType,
  InsuranceSubmissionDraft,
} from './InsuranceSubmissionTypes';

interface CnssInsuranceSubmissionReviewProps {
  draft: InsuranceSubmissionDraft;
  busyAction?: 'validate' | 'finalize' | null;
  error?: string | null;
  onChange: (draft: InsuranceSubmissionDraft) => void;
  onValidate: () => void;
  onFinalize: () => void;
  onClose: () => void;
}

const requiredValidatedZoneFields: Array<keyof InsuranceAdministrativeSnapshot> = [
  'beneficiary_full_name',
  'beneficiary_birth_date',
  'beneficiary_national_id',
  'beneficiary_sex',
  'practitioner_full_name',
  'practitioner_inpe',
  'care_type',
];

const blockerLabel: Record<string, string> = {
  'administrative.beneficiary_full_name': 'Nom du bénéficiaire',
  'administrative.beneficiary_birth_date': 'Date de naissance',
  'administrative.beneficiary_national_id': 'CIN du bénéficiaire',
  'administrative.beneficiary_sex': 'Sexe du bénéficiaire',
  'administrative.practitioner_full_name': 'Nom du praticien',
  'administrative.practitioner_inpe': 'INPE du praticien',
  'administrative.care_type': 'Type de soins',
};

const fieldHasValue = (value: unknown): boolean => {
  if (value === null || value === undefined) return false;
  if (typeof value === 'string') return value.trim().length > 0;
  return true;
};

const fmtAmount = (value: number) => `${Number(value || 0).toLocaleString('fr-MA')} MAD`;

export const CnssInsuranceSubmissionReview = ({
  draft,
  busyAction = null,
  error = null,
  onChange,
  onValidate,
  onFinalize,
  onClose,
}: CnssInsuranceSubmissionReviewProps) => {
  const admin = draft.administrative;
  const allMappingsExact = draft.lines.every(line => line.mapping_status === 'EXACT');

  const visibleBlockers = useMemo(() => {
    const unresolved = draft.unresolved_fields.filter(key => {
      if (!key.startsWith('administrative.')) return true;
      const field = key.replace('administrative.', '') as keyof InsuranceAdministrativeSnapshot;
      return !fieldHasValue(admin[field]);
    });
    for (const field of requiredValidatedZoneFields) {
      if (!fieldHasValue(admin[field])) {
        const key = `administrative.${field}`;
        if (!unresolved.includes(key)) unresolved.push(key);
      }
    }
    return unresolved;
  }, [admin, draft.unresolved_fields]);

  const updateAdmin = <K extends keyof InsuranceAdministrativeSnapshot>(
    field: K,
    value: InsuranceAdministrativeSnapshot[K],
  ) => {
    onChange({
      ...draft,
      administrative: {
        ...draft.administrative,
        [field]: value,
      },
      status: draft.status === 'VALIDATED' ? 'INCOMPLETE' : draft.status,
      validated_at: draft.status === 'VALIDATED' ? null : draft.validated_at,
      validated_by_practitioner_id: draft.status === 'VALIDATED' ? null : draft.validated_by_practitioner_id,
    });
  };

  const canValidate = draft.status !== 'VALIDATED' && visibleBlockers.length === 0 && allMappingsExact && !busyAction;
  const canFinalize = draft.status === 'VALIDATED' && !busyAction;

  return (
    <div
      data-insurance-review="cnss"
      className="fixed inset-0 z-[120] bg-slate-950/35 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="cnss-review-title"
    >
      <div className="w-full sm:max-w-5xl max-h-[96dvh] sm:max-h-[92vh] overflow-hidden rounded-t-[2rem] sm:rounded-[2rem] bg-white shadow-2xl border border-slate-200 flex flex-col">
        <header className="shrink-0 px-5 sm:px-7 py-5 border-b border-slate-100 bg-gradient-to-r from-white to-primary/5 flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-primary text-[10px] sm:text-xs font-black uppercase tracking-[0.18em]">
              <ShieldCheck size={16} /> CNSS · Feuille de soins dentaires
            </div>
            <h2 id="cnss-review-title" className="mt-1 text-xl sm:text-2xl font-black text-slate-900">Revue avant validation praticien</h2>
            <p className="mt-1 text-xs sm:text-sm text-slate-500 font-medium">Source Honoraires #{draft.honoraires_document_id} · données cliniques verrouillées</p>
          </div>
          <button type="button" aria-label="Fermer la revue CNSS" onClick={onClose} className="min-w-11 min-h-11 rounded-xl border border-slate-200 bg-white inline-flex items-center justify-center text-slate-500 hover:bg-slate-50">
            <X size={19} />
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-4 sm:px-7 py-5 space-y-5">
          <section className="rounded-2xl border border-slate-200 overflow-hidden" data-cnss-section="source">
            <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between gap-3">
              <div>
                <h3 className="font-black text-slate-800 text-sm">1. Source Honoraires vérifiée</h3>
                <p className="text-[11px] text-slate-500 mt-0.5">Lecture seule. Les actes, dents, montants et mappings NGAP viennent du serveur.</p>
              </div>
              <LockKeyhole size={18} className="text-slate-400 shrink-0" />
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[680px] text-xs">
                <thead className="bg-white text-slate-400 uppercase tracking-wider text-[9px]">
                  <tr>
                    <th className="text-left px-4 py-3">Date</th>
                    <th className="text-left px-4 py-3">Acte</th>
                    <th className="text-left px-4 py-3">Dent(s)</th>
                    <th className="text-left px-4 py-3">NGAP</th>
                    <th className="text-left px-4 py-3">Coef.</th>
                    <th className="text-right px-4 py-3">Montant</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {draft.lines.map((line, index) => (
                    <tr key={`${line.source.source_line_uid || line.source.honoraires_line_index}-${index}`}>
                      <td className="px-4 py-3 font-semibold text-slate-600 whitespace-nowrap">{line.service_date}</td>
                      <td className="px-4 py-3 font-bold text-slate-800">{line.label}</td>
                      <td className="px-4 py-3 font-semibold text-slate-600">{line.teeth.join(', ') || '—'}</td>
                      <td className="px-4 py-3">
                        <span className={cn('inline-flex items-center px-2 py-1 rounded-lg font-black', line.mapping_status === 'EXACT' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700')}>
                          {line.ngap_code || line.mapping_status}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-semibold text-slate-600">{line.ngap_coefficient ?? '—'}</td>
                      <td className="px-4 py-3 text-right font-black text-slate-800 whitespace-nowrap">{fmtAmount(line.amount_mad)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="rounded-2xl border border-primary/20 bg-primary/[0.025] p-4 sm:p-5" data-cnss-section="administrative">
            <div className="mb-4">
              <h3 className="font-black text-slate-800 text-sm">2. Données administratives CNSS</h3>
              <p className="text-[11px] text-slate-500 mt-1">Digital Crown remplit uniquement la zone praticien/bénéficiaire validée. La partie supérieure réservée à l’assuré reste volontairement vierge.</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <label className="space-y-1.5">
                <span className="text-[10px] uppercase tracking-wider font-black text-slate-500">Bénéficiaire</span>
                <input data-cnss-field="beneficiary_full_name" value={admin.beneficiary_full_name || ''} onChange={e => updateAdmin('beneficiary_full_name', e.target.value || null)} className="w-full min-h-11 px-3 rounded-xl border border-slate-200 bg-white text-sm font-bold outline-none focus:ring-2 focus:ring-primary/20" />
              </label>
              <label className="space-y-1.5">
                <span className="text-[10px] uppercase tracking-wider font-black text-slate-500">Date de naissance</span>
                <input data-cnss-field="beneficiary_birth_date" type="date" value={admin.beneficiary_birth_date || ''} onChange={e => updateAdmin('beneficiary_birth_date', e.target.value || null)} className="w-full min-h-11 px-3 rounded-xl border border-slate-200 bg-white text-sm font-bold outline-none focus:ring-2 focus:ring-primary/20" />
              </label>
              <label className="space-y-1.5">
                <span className="text-[10px] uppercase tracking-wider font-black text-slate-500">CIN bénéficiaire</span>
                <input data-cnss-field="beneficiary_national_id" value={admin.beneficiary_national_id || ''} onChange={e => updateAdmin('beneficiary_national_id', e.target.value.toUpperCase() || null)} className="w-full min-h-11 px-3 rounded-xl border border-slate-200 bg-white text-sm font-bold outline-none focus:ring-2 focus:ring-primary/20" />
              </label>
              <label className="space-y-1.5">
                <span className="text-[10px] uppercase tracking-wider font-black text-slate-500">Sexe</span>
                <select data-cnss-field="beneficiary_sex" value={admin.beneficiary_sex || ''} onChange={e => updateAdmin('beneficiary_sex', e.target.value || null)} className="w-full min-h-11 px-3 rounded-xl border border-slate-200 bg-white text-sm font-bold outline-none focus:ring-2 focus:ring-primary/20">
                  <option value="">À renseigner</option><option value="M">M</option><option value="F">F</option>
                </select>
              </label>
              <label className="space-y-1.5">
                <span className="text-[10px] uppercase tracking-wider font-black text-slate-500">Praticien</span>
                <input data-cnss-field="practitioner_full_name" value={admin.practitioner_full_name || ''} onChange={e => updateAdmin('practitioner_full_name', e.target.value || null)} className="w-full min-h-11 px-3 rounded-xl border border-slate-200 bg-white text-sm font-bold outline-none focus:ring-2 focus:ring-primary/20" />
              </label>
              <label className="space-y-1.5">
                <span className="text-[10px] uppercase tracking-wider font-black text-slate-500">INPE</span>
                <input data-cnss-field="practitioner_inpe" value={admin.practitioner_inpe || ''} onChange={e => updateAdmin('practitioner_inpe', e.target.value || null)} className="w-full min-h-11 px-3 rounded-xl border border-slate-200 bg-white text-sm font-bold outline-none focus:ring-2 focus:ring-primary/20" />
              </label>
              <label className="space-y-1.5">
                <span className="text-[10px] uppercase tracking-wider font-black text-slate-500">Type de soins</span>
                <select data-cnss-field="care_type" value={admin.care_type || ''} onChange={e => updateAdmin('care_type', (e.target.value || null) as InsuranceCareType | null)} className="w-full min-h-11 px-3 rounded-xl border border-slate-200 bg-white text-sm font-bold outline-none focus:ring-2 focus:ring-primary/20">
                  <option value="">À renseigner</option>
                  <option value="SOINS">Soins</option>
                  <option value="PROTHESE">Prothèse</option>
                  <option value="ORTHODONTIE_FACIALE">Orthodontie faciale</option>
                  <option value="AUTRES">Autres</option>
                </select>
              </label>
              <label className="space-y-1.5">
                <span className="text-[10px] uppercase tracking-wider font-black text-slate-500">N° entente préalable · optionnel</span>
                <input data-cnss-field="prior_approval_number" value={admin.prior_approval_number || ''} onChange={e => updateAdmin('prior_approval_number', e.target.value || null)} className="w-full min-h-11 px-3 rounded-xl border border-slate-200 bg-white text-sm font-bold outline-none focus:ring-2 focus:ring-primary/20" />
              </label>
              <label className="space-y-1.5">
                <span className="text-[10px] uppercase tracking-wider font-black text-slate-500">Date accident · optionnel</span>
                <input data-cnss-field="accident_date" type="date" value={admin.accident_date || ''} onChange={e => updateAdmin('accident_date', e.target.value || null)} className="w-full min-h-11 px-3 rounded-xl border border-slate-200 bg-white text-sm font-bold outline-none focus:ring-2 focus:ring-primary/20" />
              </label>
              <label className="space-y-1.5 sm:col-span-2">
                <span className="text-[10px] uppercase tracking-wider font-black text-slate-500">Circonstances accident · optionnel</span>
                <input data-cnss-field="accident_circumstances" value={admin.accident_circumstances || ''} onChange={e => updateAdmin('accident_circumstances', e.target.value || null)} className="w-full min-h-11 px-3 rounded-xl border border-slate-200 bg-white text-sm font-bold outline-none focus:ring-2 focus:ring-primary/20" />
              </label>
            </div>

            {visibleBlockers.length > 0 && (
              <div data-cnss-blockers className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-3.5 py-3 text-amber-800">
                <div className="flex items-center gap-2 font-black text-xs"><AlertCircle size={16} /> À compléter avant validation</div>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {visibleBlockers.map(key => <span key={key} className="px-2 py-1 rounded-lg bg-white/80 border border-amber-200 text-[10px] font-bold">{blockerLabel[key] || key}</span>)}
                </div>
              </div>
            )}
          </section>

          <section className="rounded-2xl border border-slate-200 p-4 sm:p-5" data-cnss-section="actions">
            <h3 className="font-black text-slate-800 text-sm">3. Actions contrôlées</h3>
            <p className="text-[11px] text-slate-500 mt-1">La validation lie le dossier à votre identité applicative. Digital Crown n’appose automatiquement ni signature manuscrite, ni cachet, ni décision CNSS.</p>
            {error && <div className="mt-3 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2.5 text-xs font-bold text-rose-700">{error}</div>}
            <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button data-cnss-action="validate" type="button" disabled={!canValidate} onClick={onValidate} className="min-h-[48px] rounded-xl bg-slate-900 text-white font-black text-xs uppercase tracking-wider inline-flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed">
                {busyAction === 'validate' ? <Loader2 size={17} className="animate-spin" /> : draft.status === 'VALIDATED' ? <BadgeCheck size={17} /> : <ShieldCheck size={17} />}
                {draft.status === 'VALIDATED' ? 'Validé par le praticien' : 'Valider avec mon identité'}
              </button>
              <button data-cnss-action="finalize" type="button" disabled={!canFinalize} onClick={onFinalize} className="min-h-[48px] rounded-xl bg-gradient-to-r from-primary to-secondary text-white font-black text-xs uppercase tracking-wider inline-flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed">
                {busyAction === 'finalize' ? <Loader2 size={17} className="animate-spin" /> : <FileCheck2 size={17} />}
                Générer et archiver le PDF
              </button>
            </div>
            {!allMappingsExact && <p className="mt-3 text-[11px] font-bold text-amber-700">Le serveur signale au moins un mapping NGAP non exact. La validation reste bloquée.</p>}
          </section>
        </div>
      </div>
    </div>
  );
};
