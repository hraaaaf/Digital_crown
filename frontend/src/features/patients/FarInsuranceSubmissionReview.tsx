import { useMemo } from 'react';
import {
  AlertCircle,
  BadgeCheck,
  FileCheck2,
  FileText,
  Loader2,
  LockKeyhole,
  ShieldCheck,
  X,
} from 'lucide-react';
import { cn } from '../../utils/cn';
import type {
  InsuranceAdministrativeSnapshot,
  InsuranceClaimContext,
  InsuranceSubmissionDraft,
} from './InsuranceSubmissionTypes';

interface FarInsuranceSubmissionReviewProps {
  draft: InsuranceSubmissionDraft;
  busyAction?: 'validate' | 'finalize' | null;
  error?: string | null;
  onChange: (draft: InsuranceSubmissionDraft) => void;
  onValidate: () => void;
  onFinalize: () => void;
  onClose: () => void;
}

const requiredFields: Array<keyof InsuranceAdministrativeSnapshot> = [
  'insured_national_id',
  'insured_account_number',
  'insured_phone',
  'insured_full_name',
  'insured_grade',
  'insured_unit',
  'insured_address',
  'beneficiary_full_name',
  'beneficiary_birth_date',
  'relationship_to_insured',
  'claim_context',
  'practitioner_inpe',
];

const blockerLabel: Record<string, string> = {
  'administrative.insured_national_id': 'CIN de l’adhérent',
  'administrative.insured_account_number': 'N° de compte',
  'administrative.insured_phone': 'Téléphone',
  'administrative.insured_full_name': 'Nom et prénom de l’adhérent',
  'administrative.insured_grade': 'Grade',
  'administrative.insured_unit': 'Unité',
  'administrative.insured_address': 'Adresse',
  'administrative.beneficiary_full_name': 'Nom du bénéficiaire',
  'administrative.beneficiary_birth_date': 'Date de naissance',
  'administrative.relationship_to_insured': 'Lien avec l’adhérent',
  'administrative.claim_context': 'Contexte maladie / maternité / accident',
  'administrative.practitioner_inpe': 'INPE du praticien',
  'form.capacity': 'Maximum 6 lignes dentaires sur la référence FAR',
  'far_prescription.separate_validation_required': 'Ordonnance liée : validation séparée requise',
};

const hasValue = (value: unknown): boolean => {
  if (value === null || value === undefined) return false;
  if (typeof value === 'string') return value.trim().length > 0;
  return true;
};

const fmtAmount = (value: number) => `${Number(value || 0).toLocaleString('fr-MA')} MAD`;
const inputClass = 'w-full min-h-11 px-3 rounded-xl border border-slate-200 bg-white text-sm font-bold outline-none focus:ring-2 focus:ring-primary/20';
const labelClass = 'text-[10px] uppercase tracking-wider font-black text-slate-500';

export const FarInsuranceSubmissionReview = ({
  draft,
  busyAction = null,
  error = null,
  onChange,
  onValidate,
  onFinalize,
  onClose,
}: FarInsuranceSubmissionReviewProps) => {
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
    if (draft.lines.length > 6) unresolved.push('form.capacity');
    if (draft.source_ordonnance_document_id) unresolved.push('far_prescription.separate_validation_required');
    return Array.from(new Set(unresolved));
  }, [admin, draft.lines.length, draft.source_ordonnance_document_id, draft.unresolved_fields]);

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
      data-insurance-review="far"
      className="fixed inset-0 z-[120] bg-slate-950/35 backdrop-blur-sm flex items-end sm:items-center justify-center p-0 sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="far-review-title"
    >
      <div className="w-full sm:max-w-5xl max-h-[96dvh] sm:max-h-[92vh] overflow-hidden rounded-t-[2rem] sm:rounded-[2rem] bg-white shadow-2xl border border-slate-200 flex flex-col">
        <header className="shrink-0 px-5 sm:px-7 py-5 border-b border-slate-100 bg-gradient-to-r from-white to-primary/5 flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-primary text-[10px] sm:text-xs font-black uppercase tracking-[0.18em]">
              <ShieldCheck size={16} /> FAR · Feuille de soins dentaires
            </div>
            <h2 id="far-review-title" className="mt-1 text-xl sm:text-2xl font-black text-slate-900">Revue avant validation praticien</h2>
            <p className="mt-1 text-xs sm:text-sm text-slate-500 font-medium">Source Honoraires #{draft.honoraires_document_id} · référence dérivée validée cabinet</p>
          </div>
          <button type="button" aria-label="Fermer la revue FAR" onClick={onClose} className="min-w-11 min-h-11 rounded-xl border border-slate-200 bg-white inline-flex items-center justify-center text-slate-500 hover:bg-slate-50">
            <X size={19} />
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-4 sm:px-7 py-5 space-y-5">
          <section className="rounded-2xl border border-slate-200 overflow-hidden" data-far-section="source">
            <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between gap-3">
              <div>
                <h3 className="font-black text-slate-800 text-sm">1. Actes dentaires — source Honoraires</h3>
                <p className="text-[11px] text-slate-500 mt-0.5">Lecture seule. Les lignes sont rendues uniquement sur la Page 4 dentaire.</p>
              </div>
              <LockKeyhole size={18} className="text-slate-400 shrink-0" />
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[680px] text-xs">
                <thead className="bg-white text-slate-400 uppercase tracking-wider text-[9px]">
                  <tr>
                    <th className="text-left px-4 py-3">Date</th><th className="text-left px-4 py-3">Acte</th><th className="text-left px-4 py-3">Dent(s)</th><th className="text-left px-4 py-3">NGAP</th><th className="text-left px-4 py-3">Coef.</th><th className="text-right px-4 py-3">Montant</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {draft.lines.map((line, index) => (
                    <tr key={`${line.source.source_line_uid || line.source.honoraires_line_index}-${index}`}>
                      <td className="px-4 py-3 font-semibold text-slate-600 whitespace-nowrap">{line.service_date}</td>
                      <td className="px-4 py-3 font-bold text-slate-800">{line.label}</td>
                      <td className="px-4 py-3 font-semibold text-slate-600">{line.teeth.join(', ') || '—'}</td>
                      <td className="px-4 py-3"><span className={cn('inline-flex items-center px-2 py-1 rounded-lg font-black', line.mapping_status === 'EXACT' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700')}>{line.ngap_code || line.mapping_status}</span></td>
                      <td className="px-4 py-3 font-semibold text-slate-600">{line.ngap_coefficient ?? '—'}</td>
                      <td className="px-4 py-3 text-right font-black text-slate-800 whitespace-nowrap">{fmtAmount(line.amount_mad)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="rounded-2xl border border-primary/20 bg-primary/[0.025] p-4 sm:p-5" data-far-section="administrative">
            <div className="mb-4 flex items-start justify-between gap-3">
              <div>
                <h3 className="font-black text-slate-800 text-sm">2. Données FAR explicites</h3>
                <p className="text-[11px] text-slate-500 mt-1">Compte, téléphone, grade, unité, lien et contexte ne sont jamais déduits automatiquement.</p>
              </div>
              <span className="shrink-0 inline-flex items-center gap-1 rounded-lg border border-emerald-200 bg-emerald-50 px-2 py-1 text-[9px] font-black uppercase tracking-wider text-emerald-700"><BadgeCheck size={13} /> Référence cabinet</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <label className="space-y-1.5"><span className={labelClass}>CIN adhérent</span><input data-far-field="insured_national_id" value={admin.insured_national_id || ''} onChange={e => updateAdmin('insured_national_id', e.target.value.toUpperCase() || null)} className={inputClass} /></label>
              <label className="space-y-1.5"><span className={labelClass}>N° de compte</span><input data-far-field="insured_account_number" value={admin.insured_account_number || ''} onChange={e => updateAdmin('insured_account_number', e.target.value || null)} className={inputClass} /></label>
              <label className="space-y-1.5"><span className={labelClass}>Téléphone</span><input data-far-field="insured_phone" value={admin.insured_phone || ''} onChange={e => updateAdmin('insured_phone', e.target.value || null)} className={inputClass} /></label>
              <label className="space-y-1.5"><span className={labelClass}>Nom et prénom adhérent</span><input data-far-field="insured_full_name" value={admin.insured_full_name || ''} onChange={e => updateAdmin('insured_full_name', e.target.value || null)} className={inputClass} /></label>
              <label className="space-y-1.5"><span className={labelClass}>Grade</span><input data-far-field="insured_grade" value={admin.insured_grade || ''} onChange={e => updateAdmin('insured_grade', e.target.value || null)} className={inputClass} /></label>
              <label className="space-y-1.5"><span className={labelClass}>Unité</span><input data-far-field="insured_unit" value={admin.insured_unit || ''} onChange={e => updateAdmin('insured_unit', e.target.value || null)} className={inputClass} /></label>
              <label className="space-y-1.5 sm:col-span-2"><span className={labelClass}>Adresse adhérent</span><input data-far-field="insured_address" value={admin.insured_address || ''} onChange={e => updateAdmin('insured_address', e.target.value || null)} className={inputClass} /></label>

              <div className="sm:col-span-2 lg:col-span-4 h-px bg-slate-200 my-1" aria-hidden="true" />

              <label className="space-y-1.5"><span className={labelClass}>Bénéficiaire</span><input data-far-field="beneficiary_full_name" value={admin.beneficiary_full_name || ''} onChange={e => updateAdmin('beneficiary_full_name', e.target.value || null)} className={inputClass} /></label>
              <label className="space-y-1.5"><span className={labelClass}>Date de naissance</span><input data-far-field="beneficiary_birth_date" type="date" value={admin.beneficiary_birth_date || ''} onChange={e => updateAdmin('beneficiary_birth_date', e.target.value || null)} className={inputClass} /></label>
              <label className="space-y-1.5"><span className={labelClass}>Lien avec l’adhérent</span><select data-far-field="relationship_to_insured" value={admin.relationship_to_insured || ''} onChange={e => updateAdmin('relationship_to_insured', e.target.value || null)} className={inputClass}><option value="">À renseigner</option><option value="ADHERENT">Adhérent</option><option value="CONJOINT">Conjoint</option><option value="ENFANT">Enfant</option></select></label>
              <label className="space-y-1.5"><span className={labelClass}>Contexte</span><select data-far-field="claim_context" value={admin.claim_context || ''} onChange={e => updateAdmin('claim_context', (e.target.value || null) as InsuranceClaimContext | null)} className={inputClass}><option value="">À renseigner</option><option value="MALADIE">Maladie</option><option value="MATERNITE">Maternité</option><option value="ACCIDENT">Accident</option></select></label>
              <label className="space-y-1.5"><span className={labelClass}>INPE praticien</span><input data-far-field="practitioner_inpe" value={admin.practitioner_inpe || ''} onChange={e => updateAdmin('practitioner_inpe', e.target.value || null)} className={inputClass} /></label>
            </div>

            {visibleBlockers.length > 0 && (
              <div data-far-blockers className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-3.5 py-3 text-amber-800">
                <div className="flex items-center gap-2 font-black text-xs"><AlertCircle size={16} /> À compléter avant validation</div>
                <div className="mt-2 flex flex-wrap gap-1.5">{visibleBlockers.map(key => <span key={key} className="px-2 py-1 rounded-lg bg-white/80 border border-amber-200 text-[10px] font-bold">{blockerLabel[key] || key}</span>)}</div>
              </div>
            )}
          </section>

          <section className="rounded-2xl border border-violet-200 bg-violet-50/40 p-4 sm:p-5" data-far-section="prescription">
            <div className="flex items-start gap-3">
              <div className="min-w-10 min-h-10 rounded-xl bg-white border border-violet-200 inline-flex items-center justify-center text-violet-700"><FileText size={18} /></div>
              <div>
                <h3 className="font-black text-slate-800 text-sm">3. Ordonnance — sous-document indépendant</h3>
                <p className="text-[11px] text-slate-600 mt-1">Aucune molécule, dose, posologie, durée ou fréquence n’est déduite des actes ou du NGAP.</p>
                <p className="text-[11px] font-bold mt-2 text-violet-800">{draft.source_ordonnance_document_id ? `Source ordonnance #${draft.source_ordonnance_document_id} liée — validation dédiée requise avant assemblage.` : 'Aucune ordonnance liée : la Page 2 reste vierge.'}</p>
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 p-4 sm:p-5" data-far-section="actions">
            <h3 className="font-black text-slate-800 text-sm">4. Validation et archivage</h3>
            <p className="text-[11px] text-slate-500 mt-1">Validation serveur contre Honoraires, NGAP et le SHA exact de la référence FAR dérivée.</p>
            {error && <div className="mt-3 rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-3 text-rose-700 text-xs font-bold">{error}</div>}
            <div className="mt-4 flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
              <div className="text-[10px] font-bold text-slate-500">Statut : <span className={cn('font-black', draft.status === 'VALIDATED' ? 'text-emerald-700' : 'text-amber-700')}>{draft.status}</span>{draft.template.template_hash && <span className="ml-2">· SHA {draft.template.template_hash.slice(0, 8)}…</span>}</div>
              <div className="flex flex-col sm:flex-row gap-2">
                <button type="button" data-far-action="validate" disabled={!canValidate} onClick={onValidate} className="min-h-11 px-4 rounded-xl border border-primary/20 bg-primary/5 text-primary font-black text-xs inline-flex items-center justify-center gap-2 disabled:opacity-40">{busyAction === 'validate' ? <Loader2 size={16} className="animate-spin" /> : <BadgeCheck size={16} />}Valider comme praticien</button>
                <button type="button" data-far-action="finalize" disabled={!canFinalize} onClick={onFinalize} className="min-h-11 px-4 rounded-xl bg-primary text-white font-black text-xs inline-flex items-center justify-center gap-2 shadow-lg shadow-primary/20 disabled:opacity-40 disabled:shadow-none">{busyAction === 'finalize' ? <Loader2 size={16} className="animate-spin" /> : <FileCheck2 size={16} />}Générer et archiver le PDF</button>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};
