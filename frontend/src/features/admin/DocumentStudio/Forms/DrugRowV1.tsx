import React, { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import {
  AlertCircle,
  CalendarDays,
  ChevronDown,
  ChevronRight,
  ChevronUp,
  Clock3,
  Microscope,
  Pill,
  Search,
  Trash2,
  Utensils,
} from 'lucide-react';

import { api } from '../../../../services/api';
import { cn } from '../../../../utils/cn';
import type { ValidationError } from '../useDocumentGenerator';
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
import { PrescriptionContextualChoice } from './PrescriptionContextualChoice';
import type { DrugItem } from './prescriptionTypes';
import { FORMES, getFormeIcon } from './prescriptionTypes';

interface CatalogSource {
  id: string;
  label: string;
  license: string;
  source_url: string;
  snapshot_date: string;
  freshness: 'historical_snapshot' | string;
  current_marketing_status_verified: boolean;
}

export interface CatalogPresentation {
  presentation_id: string;
  nom: string;
  dci: string;
  dosage: string;
  unite: string;
  forme: string;
  source: CatalogSource;
}

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

const presentationStrength = (presentation: CatalogPresentation): string =>
  [presentation.dosage, presentation.unite].filter(Boolean).join(' ').trim();


const fmtMg = (mg: number) => (mg < 1000 ? `${mg}mg` : `${mg / 1000}g`);

export const DrugRow: React.FC<DrugRowProps> = ({
  drug,
  idx,
  drugsCount,
  validationErrors,
  medChecks,
  onUpdateDrug,
  onRemoveDrug,
  onMove,
  onFormeOpen,
  onToggleType,
}) => {
  const [catalogResults, setCatalogResults] = useState<CatalogPresentation[]>([]);
  const [catalogSearching, setCatalogSearching] = useState(false);
  const [catalogError, setCatalogError] = useState(false);
  const [highlightedPresentation, setHighlightedPresentation] = useState(-1);

  const fieldError = validationErrors.find(error => error.field === `drug_${idx}`);
  const isRadio = drug.type === 'EXAMEN';
  const hasIdentity = isRadio || Boolean(drug.name.trim());
  const hasCatalogPresentation = Boolean(drug.catalogPresentationId);
  const medCheck = medChecks[drug.id];
  const composer = parsePrescriptionPosology(drug.posologie);
  const composerRecognized = composerRecognitionCount(composer);
  const hasCustomPosology = Boolean(drug.posologie.trim()) && composerRecognized < 2;
  const catalogOpen = !isRadio && !hasCatalogPresentation && catalogResults.length > 0;
  const cardLabel = isRadio
    ? `Examen ${String(idx + 1).padStart(2, '0')}`
    : `Médicament ${String(idx + 1).padStart(2, '0')}`;

  const nationalMsg = medCheck && medCheck.known && medCheck.exists === false && medCheck.available_mg?.length
    ? `Ce dosage n’est pas disponible parmi les présentations connues. Alternatives : ${medCheck.available_mg.map(fmtMg).join(', ')}.`
    : null;

  useEffect(() => {
    if (isRadio) {
      setCatalogResults([]);
      setCatalogSearching(false);
      setCatalogError(false);
      return;
    }

    const query = (drug.catalogDci || drug.name).trim();
    if (query.length < 2) {
      setCatalogResults([]);
      setCatalogSearching(false);
      setCatalogError(false);
      return;
    }

    let cancelled = false;
    setCatalogSearching(true);
    setCatalogError(false);
    const timer = window.setTimeout(async () => {
      try {
        const response = await api.get('/medications/search', { params: { q: query } });
        if (cancelled) return;
        setCatalogResults(Array.isArray(response.data) ? response.data : []);
        setHighlightedPresentation(-1);
      } catch (error) {
        if (cancelled) return;
        console.error('Medication catalog search failed:', error);
        setCatalogResults([]);
        setCatalogError(true);
      } finally {
        if (!cancelled) setCatalogSearching(false);
      }
    }, 250);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [drug.catalogDci, drug.name, isRadio]);

  const clearCatalogIdentity = () => {
    onUpdateDrug(drug.id, 'catalogPresentationId', undefined);
    onUpdateDrug(drug.id, 'catalogDci', undefined);
    onUpdateDrug(drug.id, 'catalogSourceId', undefined);
    onUpdateDrug(drug.id, 'catalogSourceLabel', undefined);
    onUpdateDrug(drug.id, 'catalogSnapshotDate', undefined);
    onUpdateDrug(drug.id, 'catalogMarketingStatusVerified', undefined);
  };

  const handleNameChange = (value: string) => {
    const next = value.toUpperCase();
    if (hasCatalogPresentation && next !== drug.name) {
      clearCatalogIdentity();
      onUpdateDrug(drug.id, 'dosage', '');
      onUpdateDrug(drug.id, 'forme', '');
      onUpdateDrug(drug.id, 'posologie', '');
    }
    onUpdateDrug(drug.id, 'name', next);
  };

  const applyPresentationIdentity = (presentation: CatalogPresentation, preservePosology: boolean) => {
    onUpdateDrug(drug.id, 'name', presentation.nom);
    onUpdateDrug(drug.id, 'dosage', presentationStrength(presentation));
    onUpdateDrug(drug.id, 'forme', presentation.forme);
    if (!preservePosology) onUpdateDrug(drug.id, 'posologie', '');
    onUpdateDrug(drug.id, 'catalogPresentationId', presentation.presentation_id);
    onUpdateDrug(drug.id, 'catalogDci', presentation.dci || '');
    onUpdateDrug(drug.id, 'catalogSourceId', presentation.source.id);
    onUpdateDrug(drug.id, 'catalogSourceLabel', presentation.source.label);
    onUpdateDrug(drug.id, 'catalogSnapshotDate', presentation.source.snapshot_date);
    onUpdateDrug(
      drug.id,
      'catalogMarketingStatusVerified',
      presentation.source.current_marketing_status_verified,
    );
    setCatalogResults([]);
    setCatalogError(false);
    setHighlightedPresentation(-1);
  };

  const selectPresentation = (presentation: CatalogPresentation) => {
    applyPresentationIdentity(presentation, false);
  };

  const matchingPresentations = catalogResults.filter(presentation => (
    !drug.catalogDci
    || presentation.dci.trim().toLocaleUpperCase() === drug.catalogDci.trim().toLocaleUpperCase()
  ));

  const doseOptions = Array.from(new Map(
    matchingPresentations
      .map(presentation => [presentationStrength(presentation), presentation] as const)
      .filter(([strength]) => Boolean(strength)),
  ).entries()).map(([strength, presentation]) => ({
    value: strength,
    label: strength,
    secondary: presentation.forme || undefined,
  }));

  const formOptions = Array.from(new Map(
    matchingPresentations
      .map(presentation => [presentation.forme?.trim(), presentation] as const)
      .filter(([forme]) => Boolean(forme)),
  ).entries()).map(([forme, presentation]) => ({
    value: forme,
    label: forme,
    secondary: presentationStrength(presentation) || undefined,
  }));

  const amountOptionsForForm = PRESCRIPTION_AMOUNT_OPTIONS.filter(option => {
    const forme = drug.forme.toLocaleUpperCase();
    if (!forme) return true;
    if (forme.includes('COMPR')) return option.value.includes('comprimé');
    if (forme.includes('GÉL') || forme.includes('GEL')) return option.value.includes('gélule');
    if (forme.includes('SACH')) return option.value.includes('sachet');
    if (forme.includes('SIROP') || forme.includes('SUSP') || forme.includes('SOLUTION')) return option.value.includes('ml');
    if (forme.includes('BAIN')) return option.value.includes('rinçage');
    return true;
  });

  const relinkByDose = (value: string) => {
    const exact = matchingPresentations.find(presentation => (
      presentationStrength(presentation) === value
      && (!drug.forme || presentation.forme === drug.forme)
    )) || matchingPresentations.find(presentation => presentationStrength(presentation) === value);
    if (exact) applyPresentationIdentity(exact, true);
    else {
      clearCatalogIdentity();
      onUpdateDrug(drug.id, 'dosage', value);
    }
  };

  const relinkByForm = (value: string) => {
    const exact = matchingPresentations.find(presentation => (
      presentation.forme === value
      && (!drug.dosage || presentationStrength(presentation) === drug.dosage)
    )) || matchingPresentations.find(presentation => presentation.forme === value);
    if (exact) applyPresentationIdentity(exact, true);
    else {
      clearCatalogIdentity();
      onUpdateDrug(drug.id, 'forme', value);
    }
  };

  const handleNameKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (!catalogOpen) return;
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setHighlightedPresentation(index => Math.min(index + 1, catalogResults.length - 1));
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      setHighlightedPresentation(index => Math.max(index - 1, 0));
    } else if (event.key === 'Enter' && highlightedPresentation >= 0) {
      event.preventDefault();
      selectPresentation(catalogResults[highlightedPresentation]);
    } else if (event.key === 'Escape') {
      setCatalogResults([]);
      setHighlightedPresentation(-1);
    }
  };

  const updateComposer = (field: keyof PrescriptionComposerState, value: string) => {
    const next = { ...composer, [field]: value };
    onUpdateDrug(drug.id, 'posologie', composePrescriptionPosology(next));
  };

  return (
    <motion.div
      key={drug.id}
      data-ordonnance-drug-card
      data-drug-type={drug.type}
      data-prescription-intelligence="v1"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'relative min-w-0 rounded-2xl border bg-card/95 p-3 text-text-main shadow-sm transition-all sm:p-4',
        fieldError
          ? 'border-red-300 bg-red-50/40'
          : 'border-border-main/90 hover:border-border-hover hover:shadow-elite',
        isRadio && 'ring-1 ring-amber-300/40',
        catalogOpen && 'z-50',
      )}
    >
      <style>{`
        .prescription-r3-safety-orchestrated [data-ordonnance-quick-entry] { display: none !important; }
      `}</style>

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
              <div className="mb-1 flex items-center gap-2 text-[9px] font-black uppercase tracking-[0.16em] text-text-muted">
                {cardLabel}

              </div>
              <div className="relative">
                {!isRadio && <Search size={14} className="pointer-events-none absolute left-0 top-1/2 -translate-y-1/2 text-text-muted/70" />}
                <input
                  type="text"
                  className={cn(
                    'min-h-11 w-full min-w-0 border-none bg-transparent py-1 text-base font-black uppercase tracking-tight text-text-main outline-none placeholder:text-text-muted/55 focus:ring-0 sm:text-lg',
                    !isRadio && 'pl-5',
                  )}
                  placeholder={isRadio ? "DÉTAILS DE L'EXAMEN RADIOLOGIQUE..." : 'NOM OU DCI DU MÉDICAMENT...'}
                  value={drug.name}
                  onChange={event => handleNameChange(event.target.value)}
                  onKeyDown={handleNameKeyDown}
                  autoComplete="off"
                />
              </div>

              <AnimatePresence>
                {catalogOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 4 }}
                    data-medication-catalog-results
                    className="absolute left-0 right-0 top-full z-[100] mt-2 max-h-[340px] overflow-y-auto rounded-2xl border border-border-main bg-card py-2 shadow-2xl"
                  >
                    <div className="border-b border-border-main px-4 pb-2 pt-1 text-[8px] font-bold text-text-muted sm:px-5">
                      Présentations disponibles
                    </div>
                    {catalogResults.map((presentation, index) => (
                      <button
                        key={presentation.presentation_id}
                        type="button"
                        data-presentation-id={presentation.presentation_id}
                        data-catalog-source-id={presentation.source.id}
                        onMouseDown={event => {
                          event.preventDefault();
                          selectPresentation(presentation);
                        }}
                        className={cn(
                          'flex min-h-14 w-full items-center justify-between gap-3 px-4 py-2 text-left transition-colors sm:px-5',
                          index === highlightedPresentation
                            ? 'bg-primary/10 text-primary'
                            : 'text-text-main hover:bg-primary/5',
                        )}
                      >
                        <span className="min-w-0">
                          <span className="block truncate text-xs font-black">{presentation.nom}</span>
                          <span className="mt-0.5 block truncate text-[9px] font-semibold text-text-muted">
                            {presentation.dci || 'DCI non renseignée'}
                          </span>

                        </span>
                        <span className="flex shrink-0 items-center gap-2">
                          <span className="text-right">
                            <span className="block text-[10px] font-black">{presentationStrength(presentation) || 'Dosage non renseigné'}</span>
                            <span className="mt-0.5 block max-w-[10rem] truncate text-[8px] font-semibold text-text-muted">{presentation.forme || 'Forme non renseignée'}</span>
                          </span>
                          <ChevronRight size={13} className="opacity-50" />
                        </span>
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

          {!isRadio && !hasCatalogPresentation && catalogSearching && (
            <p className="mt-1 text-[9px] font-semibold text-text-muted">Recherche des présentations…</p>
          )}
          {!isRadio && catalogError && (
            <div className="mt-2 flex items-start gap-2 rounded-xl border border-red-200 bg-red-50/70 px-3 py-2 text-[10px] font-semibold text-red-700" role="status">
              <AlertCircle size={13} className="mt-0.5 shrink-0" />
              Recherche médicament indisponible pour le moment.
            </div>
          )}

          {!hasIdentity && !isRadio && (
            <p className="mt-1 text-[10px] font-semibold leading-relaxed text-text-muted">
              Recherchez un médicament puis choisissez explicitement sa présentation.
            </p>
          )}

          {!isRadio && hasIdentity && (
            <div className="mt-3 min-w-0 space-y-3">
              {!hasCatalogPresentation && (
                <div className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50/65 px-3 py-2 text-[10px] font-semibold text-amber-800">
                  <AlertCircle size={14} className="mt-0.5 shrink-0" />
                  Choisissez une présentation pour compléter automatiquement la ligne.
                </div>
              )}

              <div className="grid min-w-0 grid-cols-2 gap-2 lg:grid-cols-[minmax(9rem,1fr)_minmax(8rem,0.8fr)_auto]">
                <PrescriptionContextualChoice
                  ariaLabel="Forme"
                  value={drug.forme}
                  placeholder="Forme"
                  options={formOptions.length ? formOptions : FORMES.map(item => ({ value: item.l, label: item.l }))}
                  onSelect={relinkByForm}
                  onManual={relinkByForm}
                  icon={getFormeIcon(drug.forme)}
                />

                <PrescriptionContextualChoice
                  ariaLabel="Dose"
                  value={drug.dosage}
                  placeholder="Dose"
                  options={doseOptions}
                  onSelect={relinkByDose}
                  onManual={relinkByDose}
                  icon={<Pill size={14} className="shrink-0 text-text-muted" />}
                />

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

              {nationalMsg && (
                <div className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50/70 px-3 py-2 text-[10px] font-semibold text-amber-800">
                  <AlertCircle size={13} className="mt-0.5 shrink-0" /> {nationalMsg}
                </div>
              )}

              <div data-clinical-suggestion-status="blocked" hidden />
              <div
                data-ordonnance-prescription-composer
                className="rounded-2xl border border-border-main bg-glass-bg/70 p-2.5 shadow-sm backdrop-blur-xl sm:p-3"
              >
                <div className="mb-2 flex flex-wrap items-center justify-between gap-2 px-0.5">
                  <span className="text-[9px] font-black uppercase tracking-[0.16em] text-text-muted">Prescription structurée · saisie praticien</span>
                  {hasCustomPosology && (
                    <span className="text-[8px] font-bold text-text-muted">Texte libre actif · un choix reconstruit la phrase</span>
                  )}
                </div>

                <div className="grid min-w-0 grid-cols-2 gap-2 xl:grid-cols-4">
                  <PrescriptionContextualChoice
                    ariaLabel="Prise"
                    value={composer.amount}
                    placeholder="Prise"
                    options={amountOptionsForForm}
                    onSelect={value => updateComposer('amount', value)}
                    onManual={value => updateComposer('amount', value)}
                    icon={<Pill size={14} className="shrink-0 text-text-muted" />}
                  />
                  <PrescriptionContextualChoice
                    ariaLabel="Rythme"
                    value={composer.frequency}
                    placeholder="Rythme"
                    options={PRESCRIPTION_FREQUENCY_OPTIONS}
                    onSelect={value => updateComposer('frequency', value)}
                    onManual={value => updateComposer('frequency', value)}
                    icon={<Clock3 size={14} className="shrink-0 text-text-muted" />}
                  />
                  <PrescriptionContextualChoice
                    ariaLabel="Durée ou limite"
                    value={composer.constraint}
                    placeholder="Durée ou limite"
                    options={PRESCRIPTION_CONSTRAINT_OPTIONS}
                    onSelect={value => updateComposer('constraint', value)}
                    onManual={value => updateComposer('constraint', value)}
                    icon={<CalendarDays size={14} className="shrink-0 text-text-muted" />}
                  />
                  <PrescriptionContextualChoice
                    ariaLabel="Moment ou condition"
                    value={composer.context}
                    placeholder="Moment ou condition"
                    options={PRESCRIPTION_CONTEXT_OPTIONS}
                    onSelect={value => updateComposer('context', value)}
                    onManual={value => updateComposer('context', value)}
                    icon={<Utensils size={14} className="shrink-0 text-text-muted" />}
                  />
                </div>

                <div className="mt-2 rounded-xl border border-border-main/80 bg-card/75 px-3 py-2">
                  <div className="text-[8px] font-black uppercase tracking-[0.14em] text-text-muted">Phrase persistée</div>
                  <div className="mt-1 text-[10px] font-bold leading-relaxed text-text-main">
                    {drug.posologie.trim() || 'Aucune posologie saisie.'}
                  </div>
                </div>

                <label className="mt-2 block">
                  <span className="sr-only">Posologie en texte libre</span>
                  <textarea
                    aria-label="Posologie en texte libre"
                    value={drug.posologie}
                    onChange={event => onUpdateDrug(drug.id, 'posologie', event.target.value)}
                    placeholder="Ex. 1 gélule × 3/jour pendant 7 jours"
                    rows={2}
                    className="min-h-16 w-full resize-y rounded-xl border border-border-main bg-input-field/75 px-3 py-2 text-[11px] font-semibold leading-relaxed text-text-main outline-none placeholder:text-text-muted/55 focus:border-primary/40 focus:ring-2 focus:ring-primary/10"
                  />
                </label>
              </div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};
