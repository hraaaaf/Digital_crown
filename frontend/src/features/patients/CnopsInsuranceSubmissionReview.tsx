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
  InsuranceRequestNature,
  InsuranceSubmissionDraft,
} from './InsuranceSubmissionTypes';

interface CnopsInsuranceSubmissionReviewProps {
  draft: InsuranceSubmissionDraft;
  busyAction?: 'validate' | 'finalize' | null;
  error?: string | null;
  onChange: (draft: InsuranceSubmissionDraft) => void;
  onValidate: () => void;
  onFinalize: () => void;
  onClose: () => void;
}

const requiredFields: Array<keyof InsuranceAdministrativeSnapshot> = [
  'request_nature',
  'insured_full_name',
  'insured_affiliation_number',
  'insured_registration_number',
  'insured_national_id',
  'insured_address',
  'beneficiary_full_name',
  'beneficiary_birth_date',
  'beneficiary_national_id',
  'beneficiary_sex',
  'practitioner_inpe',
  'care_type',
];

const blockerLabel: Record<string, string> = {
  'administrative.request_nature': 'Nature de la demande',
  'administrative.insured_full_name': 'Nom de l’assuré',
  'administrative.insured_affiliation_number': 'N° affiliation',
  'administrative.insured_registration_number': 'N° immatriculation',
  'administrative.insured_national_id': 'CIN de l’assuré',
  'administrative.insured_address': 'Adresse de l’assuré',
  'administrative.beneficiary_full_name': 'Nom du bénéficiaire',
  'administrative.beneficiary_birth_date': 'Date de naissance',
  'administrative.beneficiary_national_id': 'CIN du bénéficiaire',
  'administrative.beneficiary_sex': 'Sexe du bénéficiaire',
  'administrative.practitioner_inpe': 'INPE du praticien',
  'administrative.care_type': 'Type de soins',
};

const hasValue = (value: unknown): boolean => {
  if (value === null || value === undefined) return false;
  if (typeof value === 'string') return value.trim().length > 0;
  return true;
};

const fmtAmount = (value: number) => `${Number(value || 0).toLocaleString('fr-MA')} MAD`;
const inputClass = 'w-full min-h-11 px-3 rounded-xl border border-slate-200 bg-white text-sm font-bold outline-none focus:ring-2 focus:ring-primary/20';
const labelClass = 'text-[10px] uppercase tracking-wider font-black text-slate-500';

export const CnopsInsuranceSubmissionReview = ({
  draft,
  busyAction = null,
  error = null,
  onChange,
  onValidate,
  onFinalize,
  onClose,
}: CnopsInsuranceSubmissionReviewProps) => {
  const admin = draft.administrative;
  const allMappingsExact = draft.lines.every(line => line.mapping_status === 'EXACT');

  const visibleBlockers = useMemo(() => {
    const unresolved = draft.unresolved_fields.filter(key => {
      if (!key.startsWith('administrative.')) return true;
      const field = key.replace('administrative.', '') as keyof InsuranceAdministrativeSnapshot;
      return !hasValue(admin[field]);
    });
    for (const field of requiredFields) {
      if (!hasValue(admin[field])) {
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
      administrative: { ...draft.administrative, [field]: value },
      status: draft.status === 'VALIDATED' ? 'INCOMPLETE' : draft.status,
      validated_at: draft.status === 'VALIDATED' ? null : draft.validated_at,
      validated_by_practitioner_id: draft.status === 'VALIDATED' ? null : draft.validated_by_practitioner_id,
    });
  };

  const canValidate = draft.status !== 'VALIDATED' && visibleBlockers.length === 0 && allMappingsExact && !busyAction;
  const canFinalize = draft.status === 'VALIDATED' && !busyAction;

  return (
    <div
      data-insurance-review="cnops"
      className="fixed inset-0 z-[120] bg-slate-950/35 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="cnops-review-title"
    >
      <div className="w-full sm:max-w-5xl max-h-[96dvh] sm:max-h-[92vh] overflow-hidden rounded-t-[2rem] sm:rounded-[2rem] bg-white shadow-2xl border border-slate-200 flex flex-col">
        <header className="shrink-0 px-5 sm:px-7 py-5 border-b border-slate-100 bg-gradient-to-r from-white to-primary/5 flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-primary text-[10px] sm:text-xs font-black uppercase tracking-[0.18em]">
              <ShieldCheck size={16} /> CNOPS · Feuille de soins dentaires
            </div>
            <h2 id="cnops-review-title" className="mt-1 text-xl sm:text-2xl font-black text-slate-900">Revue avant validation praticien</h2>
            <p className="mt-1 text-xs sm:text-sm text-slate-500 font-medium">Source Honoraires #{draft.honoraires_document_id} · données cliniques verrouillées</p>
          </div>
          <button type="button" aria-label="Fermer la revue CNOPS" onClick={onClose} className="min-w-11 min-h-11 rounded-xl border border-slate-200 bg-white inline-flex items-center justify-center text-slate-500 hover:bg-slate-50">
            <X size={19} />
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-4 sm:px-7 py-5 space-y-5">
          <section className="rounded-2xl border border-slate-200 overflow-hidden" data-cnops-section="source">
            <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between gap-3">
              <div>
                <h3 className="font-black text-slate-800 text-sm">1. Source Honoraires vérifiée</h3>
                <p className="text-[11px] text-slate-500 mt-0.5">Lecture seule. Actes, dents, montants et mappings NGAP proviennent du serveur.</p>
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

          <section className="rounded-2xl border border-primary/20 bg-primary/[0.025] p-4 sm:p-5" data-cnops-section="administrative">
            <div className="mb-4 flex items-start justify-between gap-3">
              <div>
                <h3 className="font-black text-slate-800 text-sm">2. Données administratives CNOPS</h3>
                <p className="text-[11px] text-slate-500 mt-1">Les champs assuré sont saisis explicitement. Digital Crown ne déduit ni affiliation, ni immatriculation, ni identité assuré.</p>
              </div>
              <span className="shrink-0 inline-flex items-center gap-1 rounded-lg border border-emerald-200 bg-emerald-50 px-2 py-1 text-[9px] font-black uppercase tracking-wider text-emerald-700">
                <BadgeCheck size={13} /> Formulaire cabinet validé
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <label className="space-y-1.5">
                <span className={labelClass}>Nature de la demande</span>
                <select data-cnops-field="request_nature" value={admin.request_nature || ''} onChange={e => updateAdmin('request_nature', (e.target.value || null) as InsuranceRequestNature | null)} className={inputClass}>
                  <option value="">À renseigner</option><option value="EXECUTION">Exécution</option><option value="PRIOR_APPROVAL">Entente préalable</option>
                </select>
              </label>
              <label className="space-y-1.5">
                <span className={labelClass}>Assuré</span>
                <input data-cnops-field="insured_full_name" value={admin.insured_full_name || ''} onChange={e => updateAdmin('insured_full_name', e.target.value || null)} className={inputClass} />
              </label>
              <label className="space-y-1.5">
                <span className={labelClass}>N° affiliation</span>
                <input data-cnops-field="insured_affiliation_number" value={admin.insured_affiliation_number || ''} onChange={e => updateAdmin('insured_affiliation_number', e.target.value || null)} className={inputClass} />
              </label>
              <label className="space-y-1.5">
                <span className={labelClass}>N° immatriculation</span>
                <input data-cnops-field="insured_registration_number" value={admin.insured_registration_number || ''} onChange={e => updateAdmin('insured_registration_number', e.target.value || null)} className={inputClass} />
              </label>
              <label className="space-y-1.5">
                <span className={labelClass}>CIN assuré</span>
                <input data-cnops-field="insured_national_id" value={admin.insured_national_id || ''} onChange={e => updateAdmin('insured_national_id', e.target.value.toUpperCase() || null)} className={inputClass} />
              </label>
              <label className="space-y-1.5">
                <span className={labelClass}>Lien avec l’assuré · optionnel</span>
                <select data-cnops-field="relationship_to_insured" value={admin.relationship_to_insured || ''} onChange={e => updateAdmin('relationship_to_insured', e.target.value || null)} className={inputClass}>
                  <option value="">Assuré lui-même / non renseigné</option><option value="CONJOINT">Conjoint</option><option value="ENFANT">Enfant</option>
                </select>
              </label>
              <label className="space-y-1.5 sm:col-span-2">
                <span className={labelClass}>Adresse assuré</span>
                <input data-cnops-field="insured_address" value={admin.insured_address || ''} onChange={e => updateAdmin('insured_address', e.target.value || null)} className={inputClass} />
              </label>

              <div className="sm:col-span-2 lg:col-span-4 h-px bg-slate-200 my-1" aria-hidden="true" />

              <label className="space-y-1.5">
                <span className={labelClass}>Bénéficiaire</span>
                <input data-cnops-field="beneficiary_full_name" value={admin.beneficiary_full_name || ''} onChange={e => updateAdmin('beneficiary_full_name', e.target.value || null)} className={inputClass} />
              </label>
              <label className="space-y-1.5">
                <span className={labelClass}>Date de naissance</span>
                <input data-cnops-field="beneficiary_birth_date" type="date" value={admin.beneficiary_birth_date || ''} onChange={e => updateAdmin('beneficiary_birth_date', e.target.value || null)} className={inputClass} />
              </label>
              <label className="space-y-1.5">
                <span className={labelClass}>CIN bénéficiaire</span>
                <input data-cnops-field="beneficiary_national_id" value={admin.beneficiary_national_id || ''} onChange={e => updateAdmin('beneficiary_national_id', e.target.value.toUpperCase() || null)} className={inputClass} />
              </label>
              <label className="space-y-1.5">
                <span className={labelClass}>Sexe</span>
                <select data-cnops-field="beneficiary_sex" value={admin.beneficiary_sex || ''} onChange={e => updateAdmin('beneficiary_sex', e.target.value || null)} className={inputClass}>
                  <option value="">À renseigner</option><option value="M">M</option><option value="F">F</option>
                </select>
              </label>
              <label className="space-y-1.5">
                <span className={labelClass}>INPE praticien</span>
                <input data-cnops-field="practitioner_inpe" value={admin.practitioner_inpe || ''} onChange={e => updateAdmin('practitioner_inpe', e.target.value || null)} className={inputClass} />
              </label>
              <label className="space-y-1.5">
                <span className={labelClass}>Type de soins</span>
                <select data-cnops-field="care_type" value={admin.care_type || ''} onChange={e => updateAdmin('care_type', (e.target.value || null) as InsuranceCareType | null)} className={inputClass}>
                  <option value="">À renseigner</option><option value="SOINS">Soins</option><option value="PROTHESE">Prothèse</option><option value="ORTHODONTIE_FACIALE">Orthodontie faciale</option><option value="AUTRES">Autres</option>
                </select>
              </label>
              <label className="space-y-1.5">
                <span className={labelClass}>N° entente préalable · optionnel</span>
                <input data-cnops-field="prior_approval_number" value={admin.prior_approval_number || ''} onChange={e => updateAdmin('prior_approval_number', e.target.value || null)} className={inputClass} />
              </label>
              <label className="space-y-1.5">
                <span className={labelClass}>Date accident · optionnel</span>
                <input data-cnops-field="accident_date" type="date" value={admin.accident_date || ''} onChange={e => updateAdmin('accident_date', e.target.value || null)} className={inputClass} />
              </label>
              <label className="space-y-1.5 sm:col-span-2">
                <span className={labelClass}>Circonstances accident · optionnel</span>
                <input data-cnops-field="accident_circumstances" value={admin.accident_circumstances || ''} onChange={e => updateAdmin('accident_circumstances', e.target.value || null)} className={inputClass} />
              </label>
            </div>

            {visibleBlockers.length > 0 && (
              <div data-cnops-blockers className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-3.5 py-3 text-amber-800">
                <div className="flex items-center gap-2 font-black text-xs"><AlertCircle size={16} /> À compléter avant validation</div>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {visibleBlockers.map(key => <span key={key} className="px-2 py-1 rounded-lg bg-white/80 border border-amber-200 text-[10px] font-bold">{blockerLabel[key] || key}</span>)}
                </div>
              </div>
            )}
          </section>

          <section className="rounded-2xl border border-slate-200 p-4 sm:p-5" data-cnops-section="actions">
            <h3 className="font-black text-slate-800 text-sm">3. Validation et archivage</h3>
            <p className="text-[11px] text-slate-500 mt-1">La validation verrouille le brouillon contre le formulaire CNOPS et la référence NGAP. Le PDF n’est généré qu’après validation praticien.</p>

            {error && <div className="mt-3 rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-3 text-rose-700 text-xs font-bold">{error}</div>}

            <div className="mt-4 flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
              <div className="text-[10px] font-bold text-slate-500">
                Statut : <span className={cn('font-black', draft.status === 'VALIDATED' ? 'text-emerald-700' : 'text-amber-700')}>{draft.status}</span>
                {draft.template.template_hash && <span className="ml-2">· SHA {draft.template.template_hash.slice(0, 8)}…</span>}
              </div>
              <div className="flex flex-col sm:flex-row gap-2">
                <button type="button" data-cnops-action="validate" disabled={!canValidate} onClick={onValidate} className="min-h-11 px-4 rounded-xl border border-primary/20 bg-primary/5 text-primary font-black text-xs inline-flex items-center justify-center gap-2 disabled:opacity-40">
                  {busyAction === 'validate' ? <Loader2 size={16} className="animate-spin" /> : <BadgeCheck size={16} />}
                  Valider comme praticien
                </button>
                <button type="button" data-cnops-action="finalize" disabled={!canFinalize} onClick={onFinalize} className="min-h-11 px-4 rounded-xl bg-primary text-white font-black text-xs inline-flex items-center justify-center gap-2 shadow-lg shadow-primary/20 disabled:opacity-40 disabled:shadow-none">
                  {busyAction === 'finalize' ? <Loader2 size={16} className="animate-spin" /> : <FileCheck2 size={16} />}
                  Générer et archiver le PDF
                </button>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};
