import React from 'react';
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { CEPHALO_38_REVIEW_TERMS, CEPHALO_OCCLUSAL_REVIEW_TERMS } from '../cephaloLandmarkReviewLexicon';
import { REQUIRED_LANDMARKS } from '../cephaloShared';
import { CephaloLandmarkReviewLexicon } from './CephaloLandmarkReviewLexicon';

const palette = {
  bgCard: '#ffffff', border: '#ccddee', text: '#112233',
  textMuted: '#667788', accent: '#114488',
};
const synthetic = [
  { id: 'S', x: 10, y: 21 },
  { id: 'Pog_soft', x: 15, y: 25 },
  { id: 'Occ_Ant', x: 33, y: 32 },
];

afterEach(() => cleanup());

describe('J1.B1-S4 read-only clinician review lexicon', () => {
  it('presents exactly 38 model channels plus 2 separate occlusal constructions', () => {
    const detectorIds = CEPHALO_38_REVIEW_TERMS.map(item => item.id);
    const constructionIds = CEPHALO_OCCLUSAL_REVIEW_TERMS.map(item => item.id);
    expect(detectorIds).toHaveLength(38);
    expect(new Set(detectorIds).size).toBe(38);
    expect(constructionIds).toEqual(['Occ_Ant', 'Occ_Post']);
    expect(new Set([...detectorIds, ...constructionIds])).toEqual(new Set(REQUIRED_LANDMARKS));

    const { container } = render(
      <CephaloLandmarkReviewLexicon presentLandmarks={synthetic} activePointId={null} palette={palette} />,
    );
    expect(container.querySelectorAll('[data-model-channel="true"]')).toHaveLength(38);
    expect(container.querySelectorAll('[data-model-channel="false"]')).toHaveLength(2);
    expect(container.querySelectorAll('[data-clinical-validated="true"]')).toHaveLength(0);
    expect(screen.getByText(/38 canaux du détecteur \+ 2 repères occlusaux construits/)).toBeTruthy();
    expect(screen.getByText(/aucun point automatique certifié cliniquement/)).toBeTruthy();
  });

  it('filters using French, English, synonyms and exact historic IDs without changing coordinates', () => {
    const original = JSON.stringify(synthetic);
    const { container } = render(
      <CephaloLandmarkReviewLexicon presentLandmarks={synthetic} activePointId="Pog_soft" palette={palette} />,
    );
    const searchbox = screen.getByRole('searchbox', { name: /FR, EN, synonyme ou ID/i });
    fireEvent.change(searchbox, { target: { value: 'Pos' } });
    const row = container.querySelector('[data-cephalo-lexicon-id="Pog_soft"]');
    expect(row).not.toBeNull();
    expect(container.querySelectorAll('[data-cephalo-lexicon-id]')).toHaveLength(1);
    expect(within(row as HTMLElement).getByText('Actif')).toBeTruthy();
    expect(within(row as HTMLElement).getByText(/« Pos » cité · correspondance modèle non établie/)).toBeTruthy();
    expect(within(row as HTMLElement).getByText(/Coordonnée chargée \(non validée\)/)).toBeTruthy();

    fireEvent.change(searchbox, { target: { value: 'Selle turcique' } });
    expect(container.querySelectorAll('[data-cephalo-lexicon-id]')).toHaveLength(1);
    expect(container.querySelector('[data-cephalo-lexicon-id="S"]')).not.toBeNull();
    fireEvent.change(searchbox, { target: { value: 'Sella' } });
    expect(container.querySelectorAll('[data-cephalo-lexicon-id]')).toHaveLength(1);
    fireEvent.change(searchbox, { target: { value: 'xyz_not_a_point' } });
    expect(screen.getByText('Aucun repère correspondant.')).toBeTruthy();
    expect(JSON.stringify(synthetic)).toBe(original);
  });

  it('never confuses a constructed occlusal point with a model output', () => {
    const { container } = render(
      <CephaloLandmarkReviewLexicon presentLandmarks={synthetic} activePointId="Occ_Ant" palette={palette} />,
    );
    fireEvent.change(screen.getByRole('searchbox'), { target: { value: 'occlusal' } });
    expect(container.querySelectorAll('[data-model-channel="true"]')).toHaveLength(0);
    expect(container.querySelectorAll('[data-model-channel="false"]')).toHaveLength(2);
    expect(screen.getAllByText(/Construction distincte · pas un canal SRPose38/)).toHaveLength(2);
    expect(container.querySelectorAll('[data-clinical-validated="false"]')).toHaveLength(2);
  });

  it('does not expose controls to change model inference, measures, or landmark coordinates', () => {
    const { container } = render(
      <CephaloLandmarkReviewLexicon presentLandmarks={synthetic} activePointId={null} palette={palette} />,
    );
    expect(container.querySelector('[data-review-only="true"]')).not.toBeNull();
    expect(container.querySelectorAll('button, input[type="number"], input[type="range"]')).toHaveLength(0);
    expect(screen.getByRole('searchbox')).toBeTruthy();
    expect(container.querySelectorAll('[data-cephalo-lexicon-id]')).toHaveLength(40);
  });
});
