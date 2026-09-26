import React from 'react';
import type {
  CatalogActApplicability,
  CatalogDentition,
  CatalogSelectionMode,
  CatalogToothType,
  CatalogTreatmentArea,
} from '../hooks/useCatalogStore';
import { normalizeCatalogActApplicability } from '../hooks/useCatalogStore';
import { cn } from '../../../../utils/cn';

interface Props {
  value: CatalogActApplicability;
  onChange: (value: CatalogActApplicability) => void;
}

const Section: React.FC<React.PropsWithChildren<{ title: string; hint?: string }>> = ({ title, hint, children }) => (
  <div className="space-y-2.5">
    <div>
      <p className="text-[11px] font-black uppercase tracking-[0.14em] text-slate-600">{title}</p>
      {hint && <p className="mt-0.5 text-[11px] text-slate-400">{hint}</p>}
    </div>
    {children}
  </div>
);

const ChoiceRow = <T extends string,>({
  values,
  selected,
  onToggle,
}: {
  values: Array<{ value: T; label: string }>;
  selected: T[];
  onToggle: (value: T) => void;
}) => (
  <div className="flex flex-wrap gap-2">
    {values.map(option => {
      const active = selected.includes(option.value);
      return (
        <button
          key={option.value}
          type="button"
          aria-pressed={active}
          onClick={() => onToggle(option.value)}
          className={cn(
            'rounded-xl border px-3 py-2 text-[11px] font-bold transition',
            active
              ? 'border-slate-900 bg-slate-900 text-white'
              : 'border-slate-200 bg-white text-slate-600 hover:border-slate-400',
          )}
        >
          {option.label}
        </button>
      );
    })}
  </div>
);

const toggle = <T extends string,>(values: T[], value: T): T[] =>
  values.includes(value) ? values.filter(item => item !== value) : [...values, value];

export const CatalogActApplicabilityEditor: React.FC<Props> = ({ value, onChange }) => {
  const current = normalizeCatalogActApplicability(value);
  const patch = (next: Partial<CatalogActApplicability>) => onChange({ ...current, ...next });

  return (
    <div className="space-y-5 rounded-[1.5rem] border border-slate-200 bg-slate-50/70 p-4 sm:p-5">
      <div>
        <p className="text-sm font-black text-slate-800">Contexte odontogramme</p>
        <p className="mt-1 text-xs leading-relaxed text-slate-500">
          Ces règles pilotent les suggestions. Une liste vide signifie “tous”. Un acte non suggéré peut rester accessible par recherche.
        </p>
      </div>

      <Section title="Dentition" hint="Primaire, permanente, ou les deux.">
        <ChoiceRow<CatalogDentition>
          values={[
            { value: 'PRIMARY', label: 'Temporaire' },
            { value: 'PERMANENT', label: 'Permanente' },
          ]}
          selected={current.dentitions}
          onToggle={item => patch({ dentitions: toggle(current.dentitions, item) })}
        />
      </Section>

      <Section title="Type de dent" hint="Laisser vide pour tout type de dent.">
        <ChoiceRow<CatalogToothType>
          values={[
            { value: 'INCISOR', label: 'Incisive' },
            { value: 'CANINE', label: 'Canine' },
            { value: 'PREMOLAR', label: 'Prémolaire' },
            { value: 'MOLAR', label: 'Molaire' },
          ]}
          selected={current.tooth_types}
          onToggle={item => patch({ tooth_types: toggle(current.tooth_types, item) })}
        />
      </Section>

      <Section title="Mode de sélection">
        <ChoiceRow<CatalogSelectionMode>
          values={[
            { value: 'INDIVIDUAL', label: 'Ciblé' },
            { value: 'GROUP', label: 'Groupé' },
            { value: 'GENERAL', label: 'Général' },
          ]}
          selected={current.selection_modes}
          onToggle={item => patch({ selection_modes: toggle(current.selection_modes, item) })}
        />
      </Section>

      <Section title="Portée clinique" hint="Compatible avec les zones dentaires utilisées par l’acte.">
        <ChoiceRow<CatalogTreatmentArea>
          values={[
            { value: 'SURFACE', label: 'Face' },
            { value: 'TOOTH', label: 'Dent' },
            { value: 'TOOTH_RANGE', label: 'Plage de dents' },
            { value: 'QUADRANT', label: 'Quadrant' },
            { value: 'ARCH', label: 'Arcade' },
            { value: 'MOUTH', label: 'Bouche' },
          ]}
          selected={current.treatment_areas}
          onToggle={item => patch({ treatment_areas: toggle(current.treatment_areas, item) })}
        />
      </Section>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <label className="space-y-2">
          <span className="text-[11px] font-black uppercase tracking-wide text-slate-500">Priorité suggestion</span>
          <input
            type="number"
            aria-label="Priorité suggestion"
            min={0}
            max={100}
            value={current.suggestion_priority}
            onChange={event => patch({ suggestion_priority: Math.max(0, Math.min(100, Number(event.target.value) || 0)) })}
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm font-bold"
          />
          <span className="block text-[10px] text-slate-400">0 = recherche uniquement</span>
        </label>
        <label className="space-y-2">
          <span className="text-[11px] font-black uppercase tracking-wide text-slate-500">Min. dents</span>
          <input
            type="number"
            aria-label="Minimum de dents"
            min={0}
            value={current.min_selected_teeth}
            onChange={event => patch({ min_selected_teeth: Math.max(0, Number(event.target.value) || 0) })}
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm font-bold"
          />
        </label>
        <label className="space-y-2">
          <span className="text-[11px] font-black uppercase tracking-wide text-slate-500">Max. dents</span>
          <input
            type="number"
            aria-label="Maximum de dents"
            min={1}
            value={current.max_selected_teeth ?? ''}
            placeholder="∞"
            onChange={event => patch({ max_selected_teeth: event.target.value ? Math.max(1, Number(event.target.value)) : null })}
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm font-bold"
          />
        </label>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <label className="space-y-2">
          <span className="text-[11px] font-black uppercase tracking-wide text-slate-500">Âge min. optionnel</span>
          <input
            type="number"
            aria-label="Âge minimum"
            min={0}
            max={120}
            value={current.age_min ?? ''}
            placeholder="—"
            onChange={event => patch({ age_min: event.target.value ? Number(event.target.value) : null })}
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm font-bold"
          />
        </label>
        <label className="space-y-2">
          <span className="text-[11px] font-black uppercase tracking-wide text-slate-500">Âge max. optionnel</span>
          <input
            type="number"
            aria-label="Âge maximum"
            min={0}
            max={120}
            value={current.age_max ?? ''}
            placeholder="—"
            onChange={event => patch({ age_max: event.target.value ? Number(event.target.value) : null })}
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm font-bold"
          />
          <span className="block text-[10px] text-slate-400">Secondaire : la dentition reste prioritaire.</span>
        </label>
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        <label className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-3">
          <span className="text-xs font-bold text-slate-600">Dent présente requise</span>
          <input
            type="checkbox"
            checked={current.requires_present_tooth}
            onChange={event => patch({ requires_present_tooth: event.target.checked })}
            className="h-4 w-4 accent-slate-900"
          />
        </label>
        <label className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-3">
          <span className="text-xs font-bold text-slate-600">Dent absente requise</span>
          <input
            type="checkbox"
            checked={current.requires_missing_tooth}
            onChange={event => patch({ requires_missing_tooth: event.target.checked })}
            className="h-4 w-4 accent-slate-900"
          />
        </label>
      </div>

      <label className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-3">
        <span>
          <span className="block text-xs font-bold text-slate-700">Accessible par recherche si non suggéré</span>
          <span className="mt-0.5 block text-[10px] text-slate-400">Permet les cas cliniques rares sans polluer les raccourcis.</span>
        </span>
        <input
          type="checkbox"
          checked={current.searchable_when_not_suggested}
          onChange={event => patch({ searchable_when_not_suggested: event.target.checked })}
          className="h-4 w-4 accent-slate-900"
        />
      </label>
    </div>
  );
};

export default CatalogActApplicabilityEditor;
