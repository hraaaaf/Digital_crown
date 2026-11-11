import React, { useId, useState } from 'react';
import type { Landmark } from '../cephaloShared';
import { CEPHALO_38_REVIEW_TERMS, CEPHALO_OCCLUSAL_REVIEW_TERMS } from '../cephaloLandmarkReviewLexicon';

interface ReviewLexiconProps {
  presentLandmarks: readonly Landmark[];
  activePointId: string | null;
  palette: {
    bgCard: string;
    border: string;
    text: string;
    textMuted: string;
    accent: string;
  };
}

// Only an informational vocabulary panel. Never accepts a persistence/edit
// callback, computes a clinical value, or promotes any inferred channel.
const normalizeSearch = (value: string): string =>
  value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('fr').trim();

export const CephaloLandmarkReviewLexicon: React.FC<ReviewLexiconProps> = ({
  presentLandmarks, activePointId, palette,
}) => {
  const [query, setQuery] = useState('');
  const fieldId = useId();
  const needle = normalizeSearch(query);
  const visible = (item: { id: string; fr: string; en: string }) =>
    !needle || normalizeSearch([item.id, item.fr, item.en].join(' ')).includes(needle);
  const detector = CEPHALO_38_REVIEW_TERMS.filter(visible);
  const occlusal = CEPHALO_OCCLUSAL_REVIEW_TERMS.filter(visible);
  const presentIds = new Set(presentLandmarks.map(item => item.id.toLowerCase()));
  const activeId = activePointId?.toLowerCase();

  const renderRow = (item: { id: string; fr: string; en: string }, number?: number) => {
    const loaded = presentIds.has(item.id.toLowerCase());
    const selected = activeId === item.id.toLowerCase();
    const source = 'sourceEvidence' in item ? String(item.sourceEvidence) : 'OCCLUSAL_CONSTRUCTION';
    const evidence = source === 'AUTHOR_PAPER_EXPLICIT'
      ? 'Numéro cité par les auteurs · non validé sur ce cliché'
      : source === 'AUTHOR_PAPER_POS16_ONLY'
        ? '« Pos » cité · correspondance modèle non établie'
        : source === 'OCCLUSAL_CONSTRUCTION'
          ? 'Construction distincte · pas un canal SRPose38'
          : 'Nom de référence · identité du canal non certifiée';

    return (
      <li key={item.id}
        data-cephalo-lexicon-id={item.id}
        data-model-channel={number === undefined ? 'false' : 'true'}
        data-clinical-validated="false"
        className="rounded-lg border px-2.5 py-2"
        style={{
          borderColor: selected ? palette.accent : palette.border,
          background: palette.bgCard,
        }}
      >
        <div className="flex items-start justify-between gap-2">
          <span className="min-w-0 text-xs font-semibold" style={{ color: palette.text }}>
            {number === undefined ? 'Constr.' : String(number).padStart(2, '0')}. {item.fr}
          </span>
          {selected && <span className="shrink-0 text-[10px] font-bold" style={{ color: palette.accent }}>Actif</span>}
        </div>
        <div className="mt-1 text-[11px]" style={{ color: palette.textMuted }}>
          <code>{item.id}</code> · {item.en}
        </div>
        <div className="mt-1 text-[10px]" style={{ color: palette.textMuted }}>
          {loaded ? 'Coordonnée chargée (non validée)' : 'Aucune coordonnée chargée'}
        </div>
        <div className="mt-1 text-[10px] italic" style={{ color: palette.textMuted }}>{evidence}</div>
      </li>
    );
  };

  return (
    <section data-cephalo-review-lexicon data-review-only="true"
      role="region" aria-label="Lexique de revue des repères, lecture seule">
      <p className="mb-2 text-xs leading-relaxed" style={{ color: palette.textMuted }}>
        38 canaux du détecteur + 2 repères occlusaux construits, distincts.
        Vocabulaire indicatif uniquement : aucun point automatique certifié cliniquement.
      </p>
      <label htmlFor={fieldId} className="block text-xs font-bold" style={{ color: palette.text }}>
        Rechercher un repère (FR, EN ou ID)
      </label>
      <input id={fieldId} type="search" value={query}
        onChange={event => setQuery(event.target.value)}
        placeholder="Ex. Pog, nasion, incisive"
        className="mt-1 min-h-10 w-full rounded-lg border px-2 text-sm focus-visible:outline-2 focus-visible:outline-offset-2"
        style={{ color: palette.text, background: palette.bgCard, borderColor: palette.border }}
      />
      <div className="mt-2 max-h-72 space-y-3 overflow-y-auto pr-1" tabIndex={0}
        aria-label="Liste défilante des repères">
        {detector.length > 0 && (
          <div>
            <h4 className="mb-1 text-[11px] font-bold" style={{ color: palette.text }}>
              Sorties SRPose38 ({detector.length}/38)
            </h4>
            <ul className="space-y-1.5" data-cephalo-review-detector-list>
              {detector.map(item => renderRow(item, item.index + 1))}
            </ul>
          </div>
        )}
        {occlusal.length > 0 && (
          <div>
            <h4 className="mb-1 text-[11px] font-bold" style={{ color: palette.text }}>
              Constructions occlusales ({occlusal.length}/2)
            </h4>
            <ul className="space-y-1.5" data-cephalo-review-construction-list>
              {occlusal.map(item => renderRow(item))}
            </ul>
          </div>
        )}
        {detector.length === 0 && occlusal.length === 0 && (
          <p className="text-xs" style={{ color: palette.textMuted }}>Aucun repère correspondant.</p>
        )}
      </div>
    </section>
  );
};
