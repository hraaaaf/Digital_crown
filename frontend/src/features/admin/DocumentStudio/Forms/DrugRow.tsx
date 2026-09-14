import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertCircle, CalendarDays, ChevronRight, ChevronUp, ChevronDown,
  Clock3, Microscope, Pill, Trash2, Utensils,
} from 'lucide-react';
import { cn } from '../../../../utils/cn';
import type { DrugItem } from './prescriptionTypes';
import { getFormeIcon } from './prescriptionTypes';
import {
  PRESCRIPTION_AMOUNT_OPTIONS,
  PRESCRIPTION_CONSTRAINT_OPTIONS,
  PRESCRIPTION_CONTEXT_OPTIONS,
  PRESCRIPTION_FREQUENCY_OPTIONS,
  composePrescriptionPosology,
  composerRecognitionCount,
  parsePrescriptionPosology,
  type PrescriptionComposerState,
} from './PrescriptionComposer';
import type { ValidationError } from '../useDocumentGenerator';

export interface DrugRowProps {
  drug: DrugItem;
  idx: number;
  drugsCount: number;
  assessment: any;
  validationErrors: ValidationError[];
  forcedDrugs: number[];
  activeSearchId: { id: number; field: string } | null;
  suggestions: { medications: string[]; dosages: string[]; posologies: string[] };
  highlightedIdx: number;
  medChecks: Record<number, { known: boolean; exists?: boolean; available_mg?: number[]; dci?: string }>;
  onUpdateDrug: (id: number, field: keyof DrugItem, val: any) => void;
  onRemoveDrug: (id: number) => void;
  onMove: (id: number, direction: 'up' | 'down') => void;
  onSearch: (id: number, field: string, val: string) => void;
  onKeyDown: (e: React.KeyboardEvent, id: number, field: string) => void;
  onApplySuggestion: (id: number, field: string, val: string) => void;
  onFormeOpen: (e: React.MouseEvent<HTMLButtonElement>, drugId: number) => void;
  onForceAllergy: (id: number) => void;
  onToggleType: (id: number, type: 'MEDICAMENT' | 'EXAMEN') => void;
}

export const DrugRow: React.FC<DrugRowProps> = ({
  drug, idx, drugsCount, validationErrors,
  activeSearchId, suggestions, highlightedIdx, medChecks,
  onUpdateDrug, onRemoveDrug, onMove, onSearch, onKeyDown,
  onApplySuggestion, onFormeOpen, onToggleType,
}) => {
  const fieldError = validationErrors.find(e => e.field === `drug_${idx}`);
  const isRadio = drug.type === 'EXAMEN';
  const hasIdentity = isRadio || Boolean(drug.name.trim());
  const medCheck = medChecks[drug.id];
  const fmtMg = (mg: number) => (mg < 1000 ? `${mg}mg` : `${mg / 1000}g`);
  const nationalMsg = medCheck && medCheck.known && medCheck.exists === false && medCheck.available_mg?.length
    ? `Dosage non répertorié dans le référentiel local${medCheck.dci ? ` (${medCheck.dci})` : ''} — présentations connues : ${medCheck.available_mg.map(fmtMg).join(', ')}.`
    : null;
  const isNameSuggestOpen = activeSearchId?.id === drug.id && activeSearchId?.field === 'name' && suggestions.medications.length > 0;
  const cardLabel = isRadio ? `Examen ${String(idx + 1).padStart(2, '0')}` : `Médicament ${String(idx + 1).padStart(2, '0')}`;
  const composer = parsePrescriptionPosology(drug.posologie);
  const composerRecognized = composerRecognitionCount(composer);
  const hasCustomPosology = Boolean(drug.posologie.trim()) && composerRecognized < 2;

  const updateComposer = (field: keyof PrescriptionComposerState, value: string) => {
    const next = { ...composer, [field]: value };
    onUpdateDrug(drug.id, 'posologie', composePrescriptionPosology(next));
  };

  return (
    <motion.div
      key={drug.id}
      data-ordonnance-drug-card
      data-drug-type={drug.type}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'relative min-w-0 rounded-2xl border bg-card/95 p-3 text-text-main shadow-sm transition-all sm:p-4',
        fieldError
          ? 'border-red-300 bg-red-50/40'
          : 'border-border-main/90 hover:border-border-hover hover:shadow-elite',
        isRadio && 'ring-1 ring-amber-300/40',
        isNameSuggestOpen && 'z-50',
      )}
    >
      <div className="flex min-w-0 flex-col items-stretch gap-2.5 sm:flex-row sm:items-start sm:gap-3">
        <div
          className="inline-flex w-fit shrink-0 self-start rounded-xl border border-border-main bg-input-field/70 p-1"
          role="group"
          aria-label="Type de ligne"
        >
          <button
            type="button"
            onClick={() => onToggleType(drug.id, 'MEDICAMENT')}
            className={cn(
              'flex h-11 w-11 items-center justify-center rounded-lg transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/40',
              !isRadio ? 'bg-card text-primary shadow-sm' : 'text-text-muted hover:bg-card/70 hover:text-text-main',
            )}
            title="Médicament"
            aria-label="Type médicament"
            aria-pressed={!isRadio}
          >
            <Pill size={16} />
          </button>
          <button
            type="button"
            onClick={() => onToggleType(drug.id, 'EXAMEN')}
            className={cn(
              'flex h-11 w-11 items-center justify-center rounded-lg transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/40',
              isRadio ? 'bg-card text-primary shadow-sm' : 'text-text-muted hover:bg-card/70 hover:text-text-main',
            )}
            title="Radio / Examen"
            aria-label="Type radio ou examen"
            aria-pressed={isRadio}
          >
            <Microscope size={16} />
          </button>
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex min-w-0 items-start justify-between gap-2">
            <div className="relative min-w-0 flex-1">
              <div className="mb-1 text-[9px] font-black uppercase tracking-[0.16em] text-text-muted">
                {cardLabel}
              </div>
              <input
                type="text"
                className="min-h-11 w-full min-w-0 border-none bg-transparent px-0 py-1 text-base font-black uppercase tracking-tight text-text-main outline-none placeholder:text-text-muted/55 focus:ring-0 sm:text-lg"
                placeholder={isRadio ? "DÉTAILS DE L'EXAMEN RADIOLOGIQUE..." : 'NOM DU MÉDICAMENT...'}
                value={drug.name}
                onChange={e => onSearch(drug.id, 'name', e.target.value.toUpperCase())}
                onFocus={() => { if (drug.name.length >= 1) onSearch(drug.id, 'name', drug.name); }}
                onKeyDown={e => onKeyDown(e, drug.id, 'name')}
              />

              <AnimatePresence>
                {isNameSuggestOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 4 }}
                    className="absolute left-0 right-0 top-full z-[100] mt-2 max-h-[300px] overflow-y-auto rounded-2xl border border-border-main bg-card py-2 shadow-2xl"
                  >
                    {suggestions.medications.map((m, i) => (
                      <button
                        key={m}
                        type="button"
                        onMouseDown={e => { e.preventDefault(); onApplySuggestion(drug.id, 'name', m); }}
                        className={cn(
                          'flex min-h-11 w-full items-center justify-between px-4 py-2 text-left text-xs font-black transition-colors sm:px-5',
                          i === highlightedIdx
                            ? 'bg-primary/10 text-primary'
                            : 'text-text-main hover:bg-primary/5 hover:text-primary',
                        )}
                      >
                        <span className="truncate">{m}</span>
                        <ChevronRight size={13} className="shrink-0 opacity-50" />
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <div className="flex shrink-0 items-center gap-1">
              <div className="hidden items-center gap-1 lg:flex" aria-label="Réordonner la ligne">
                <button
                  type="button"
                  onClick={() => onMove(drug.id, 'up')}
                  disabled={idx === 0}
                  className="flex h-11 w-11 items-center justify-center rounded-xl text-text-muted transition-all hover:bg-primary/10 hover:text-primary disabled:pointer-events-none disabled:opacity-25"
                  title="Monter"
                  aria-label="Monter le médicament"
                >
                  <ChevronUp size={16} strokeWidth={2.6} />
                </button>
                <button
                  type="button"
                  onClick={() => onMove(drug.id, 'down')}
                  disabled={idx === drugsCount - 1}
                  className="flex h-11 w-11 items-center justify-center rounded-xl text-text-muted transition-all hover:bg-primary/10 hover:text-primary disabled:pointer-events-none disabled:opacity-25"
                  title="Descendre"
                  aria-label="Descendre le médicament"
                >
                  <ChevronDown size={16} strokeWidth={2.6} />
                </button>
              </div>
              <button
                type="button"
                onClick={() => onRemoveDrug(drug.id)}
                className="flex h-11 w-11 items-center justify-center rounded-xl text-text-muted transition-all hover:bg-red-50 hover:text-red-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-300"
                title="Supprimer"
                aria-label={isRadio ? "Supprimer l'examen" : 'Supprimer le médicament'}
              >
                <Trash2 size={17} />
              </button>
            </div>
          </div>

          {!hasIdentity && !isRadio && (
            <p className="mt-1 text-[10px] font-semibold leading-relaxed text-text-muted">
              Identifiez le médicament pour renseigner forme, dose et posologie.
            </p>
          )}

          {!isRadio && hasIdentity && (
            <div className="mt-3 min-w-0 space-y-3">
              <div className="flex min-w-0 flex-wrap content-start items-center gap-2">
                <button
                  type="button"
                  onClick={e => onFormeOpen(e, drug.id)}
                  className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-border-main bg-input-field/70 px-3 py-2 text-[10px] font-black uppercase tracking-wide text-text-main transition-all hover:border-primary/30 hover:bg-card hover:text-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/30"
                >
                  {getFormeIcon(drug.forme)}
                  <span className="max-w-[9rem] truncate">{drug.forme.startsWith('AUTRE') ? 'AUTRE' : (drug.forme || 'FORME')}</span>
                </button>

                {drug.forme.startsWith('AUTRE') && (
                  <input
                    type="text"
                    className="min-h-11 w-32 max-w-full rounded-xl border border-border-main bg-input-field/70 px-3 py-2 text-[10px] font-black uppercase tracking-wide text-text-main outline-none placeholder:text-text-muted/60 focus:border-primary/40 focus:ring-2 focus:ring-primary/10"
                    placeholder="PRÉCISER..."
                    value={drug.forme.includes(':') ? drug.forme.split(':')[1].trim() : ''}
                    onChange={e => onUpdateDrug(drug.id, 'forme', `AUTRE: ${e.target.value}`)}
                  />
                )}

                <label className="flex min-h-11 min-w-[8.5rem] items-center gap-2 rounded-xl border border-border-main bg-input-field/70 px-3 py-2">
                  <span className="shrink-0 text-[9px] font-black uppercase tracking-wide text-text-muted">Dose</span>
                  <input
                    type="text"
                    className="min-w-0 flex-1 border-none bg-transparent p-0 text-[11px] font-black uppercase tracking-wide text-text-main outline-none placeholder:text-text-muted/55 focus:ring-0"
                    placeholder="500MG"
                    value={drug.dosage}
                    onFocus={() => onSearch(drug.id, 'dosage', drug.dosage)}
                    onChange={e => onSearch(drug.id, 'dosage', e.target.value)}
                  />
                </label>

                <button
                  type="button"
                  onClick={() => onUpdateDrug(drug.id, 'non_substituable', !drug.non_substituable)}
                  className={cn(
                    'min-h-11 min-w-11 rounded-xl border px-3 py-2 text-[10px] font-black uppercase tracking-wide transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/30',
                    drug.non_substituable
                      ? 'border-primary bg-primary text-white shadow-sm'
                      : 'border-border-main bg-input-field/70 text-text-muted hover:border-primary/30 hover:bg-card hover:text-primary',
                  )}
                  title="Non substituable"
                  aria-pressed={Boolean(drug.non_substituable)}
                >
                  NS
                </button>
              </div>

              <div
                data-ordonnance-prescription-composer
                className="rounded-2xl border border-border-main bg-glass-bg/70 p-2.5 shadow-sm backdrop-blur-xl sm:p-3"
              >
                <div className="mb-2 flex flex-wrap items-center justify-between gap-2 px-0.5">
                  <span className="text-[9px] font-black uppercase tracking-[0.16em] text-text-muted">Prescription structurée</span>
                  {hasCustomPosology && (
                    <span className="text-[8px] font-bold text-text-muted">Texte libre actif · un choix reconstruit la phrase</span>
                  )}
                </div>

                <div className="grid min-w-0 grid-cols-2 gap-2 xl:grid-cols-4">
                  <label className="relative min-w-0">
                    <Pill size={14} className="pointer-events-none absolute left-3 top-1/2 z-10 -translate-y-1/2 text-text-muted" />
                    <select
                      data-composer-field="amount"
                      aria-label="Prise"
                      value={composer.amount}
                      onChange={e => updateComposer('amount', e.target.value)}
                      className="min-h-11 w-full appearance-none rounded-xl border border-border-main bg-input-field/80 py-2 pl-9 pr-7 text-[10px] font-black text-text-main outline-none transition-all hover:border-primary/30 focus:border-primary/40 focus:ring-2 focus:ring-primary/10"
                    >
                      <option value="">Prise</option>
                      {PRESCRIPTION_AMOUNT_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
                    </select>
                    <ChevronDown size={13} className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted" />
                  </label>

                  <label className="relative min-w-0">
                    <Clock3 size={14} className="pointer-events-none absolute left-3 top-1/2 z-10 -translate-y-1/2 text-text-muted" />
                    <select
                      data-composer-field="frequency"
                      aria-label="Rythme"
                      value={composer.frequency}
                      onChange={e => updateComposer('frequency', e.target.value)}
                      className="min-h-11 w-full appearance-none rounded-xl border border-border-main bg-input-field/80 py-2 pl-9 pr-7 text-[10px] font-black text-text-main outline-none transition-all hover:border-primary/30 focus:border-primary/40 focus:ring-2 focus:ring-primary/10"
                    >
                      <option value="">Rythme</option>
                      {PRESCRIPTION_FREQUENCY_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
                    </select>
                    <ChevronDown size={13} className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted" />
                  </label>

                  <label className="relative min-w-0">
                    <CalendarDays size={14} className="pointer-events-none absolute left-3 top-1/2 z-10 -translate-y-1/2 text-text-muted" />
                    <select
                      data-composer-field="constraint"
                      aria-label="Durée ou limite"
                      value={composer.constraint}
                      onChange={e => updateComposer('constraint', e.target.value)}
                      className="min-h-11 w-full appearance-none rounded-xl border border-border-main bg-input-field/80 py-2 pl-9 pr-7 text-[10px] font-black text-text-main outline-none transition-all hover:border-primary/30 focus:border-primary/40 focus:ring-2 focus:ring-primary/10"
                    >
                      <option value="">Durée / max</option>
                      {PRESCRIPTION_CONSTRAINT_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
                    </select>
                    <ChevronDown size={13} className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted" />
                  </label>

                  <label className="relative min-w-0">
                    <Utensils size={14} className="pointer-events-none absolute left-3 top-1/2 z-10 -translate-y-1/2 text-text-muted" />
                    <select
                      data-composer-field="context"
                      aria-label="Moment ou condition"
                      value={composer.context}
                      onChange={e => updateComposer('context', e.target.value)}
                      className="min-h-11 w-full appearance-none rounded-xl border border-border-main bg-input-field/80 py-2 pl-9 pr-7 text-[10px] font-black text-text-main outline-none transition-all hover:border-primary/30 focus:border-primary/40 focus:ring-2 focus:ring-primary/10"
                    >
                      <option value="">Moment / durée</option>
                      {PRESCRIPTION_CONTEXT_OPTIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
                    </select>
                    <ChevronDown size={13} className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted" />
                  </label>
                </div>

                <div
                  data-composer-summary
                  className="mt-2 min-h-11 rounded-xl border border-border-main/80 bg-input-field/45 px-3 py-2.5 text-xs font-bold leading-relaxed text-text-main"
                >
                  {drug.posologie || 'Sélectionnez les paramètres de prise pour générer la phrase de prescription.'}
                </div>

                <details className="mt-1.5 group">
                  <summary className="cursor-pointer select-none px-1 py-1.5 text-[9px] font-black uppercase tracking-[0.14em] text-text-muted hover:text-primary">
                    Texte libre
                  </summary>
                  <label className="mt-1 block min-w-0 rounded-xl border border-border-main bg-input-field/70 px-3 py-2.5 transition-all focus-within:border-primary/30 focus-within:bg-card focus-within:ring-2 focus-within:ring-primary/10">
                    <textarea
                      rows={2}
                      aria-label="Posologie en texte libre"
                      className="min-h-[3.25rem] w-full min-w-0 resize-none border-none bg-transparent p-0 text-xs font-bold leading-relaxed text-text-main outline-none placeholder:text-text-muted/55 focus:ring-0"
                      placeholder="Ex. 1 gélule × 3/jour pendant 7 jours"
                      value={drug.posologie}
                      onFocus={() => onSearch(drug.id, 'posologie', drug.posologie)}
                      onChange={e => {
                        onSearch(drug.id, 'posologie', e.target.value);
                        e.target.style.height = 'auto';
                        e.target.style.height = `${e.target.scrollHeight}px`;
                      }}
                    />
                  </label>
                </details>
              </div>
            </div>
          )}

          {nationalMsg && (
            <div className="mt-3 flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2.5 text-[11px] font-bold text-amber-800">
              <AlertCircle size={14} className="mt-0.5 shrink-0" />
              <span>{nationalMsg}</span>
            </div>
          )}

          {fieldError && (
            <div className="mt-3 flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-[11px] font-bold text-red-700">
              <AlertCircle size={14} className="mt-0.5 shrink-0" />
              <span>{fieldError.message}</span>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};
