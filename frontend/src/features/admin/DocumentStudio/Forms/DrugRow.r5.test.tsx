import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

import { DrugRow } from './DrugRow';
import type { DrugItem } from './prescriptionTypes';

const baseDrug: DrugItem = {
  id: 1,
  name: '',
  dosage: '',
  forme: '',
  posologie: '',
  type: 'MEDICAMENT',
  quantite: 1,
  non_substituable: false,
};

function renderRow(drug: DrugItem) {
  const onUpdateDrug = vi.fn();
  render(
    <DrugRow
      drug={drug}
      idx={0}
      drugsCount={1}
      assessment={null}
      validationErrors={[]}
      forcedDrugs={[]}
      activeSearchId={null}
      suggestions={{ medications: [], dosages: [], posologies: [] }}
      highlightedIdx={-1}
      medChecks={{}}
      onUpdateDrug={onUpdateDrug}
      onRemoveDrug={vi.fn()}
      onMove={vi.fn()}
      onSearch={vi.fn()}
      onKeyDown={vi.fn()}
      onApplySuggestion={vi.fn()}
      onForceAllergy={vi.fn()}
      onToggleType={vi.fn()}
    />,
  );
  return { onUpdateDrug };
}

const identified = (drug: DrugItem): DrugItem => ({
  ...drug,
  catalogPresentationId: 'cnops:test',
  catalogDci: drug.name,
  catalogSourceId: 'cnops-open-data-medications',
  catalogSourceLabel: 'CNOPS Open Data — Référentiel des médicaments',
  catalogSnapshotDate: '2021-12-13',
  catalogMarketingStatusVerified: false,
  it('invalide la provenance sans effacer dose, forme ou posologie lors d’une édition manuelle du nom', () => {
    const { onUpdateDrug } = renderRow(identified({
      ...baseDrug,
      name: 'AMOXICILLINE',
      forme: 'GÉLULES',
      dosage: '500MG',
      posologie: '1 comprimé x 3 / jour pendant 7 jours',
    }));

    fireEvent.change(screen.getByPlaceholderText('NOM OU DCI DU MÉDICAMENT...'), {
      target: { value: 'AMOXICILLINE MANUELLE' },
    });

    expect(onUpdateDrug).toHaveBeenCalledWith(1, 'catalogPresentationId', undefined);
    expect(onUpdateDrug).toHaveBeenCalledWith(1, 'catalogSourceId', undefined);
    expect(onUpdateDrug).toHaveBeenCalledWith(1, 'name', 'AMOXICILLINE MANUELLE');
    expect(onUpdateDrug).not.toHaveBeenCalledWith(1, 'dosage', '');
    expect(onUpdateDrug).not.toHaveBeenCalledWith(1, 'forme', '');
    expect(onUpdateDrug).not.toHaveBeenCalledWith(1, 'posologie', '');
  });

});

describe('DrugRow R5 progressive disclosure', () => {
  it('cache dose, forme et posologie tant que le médicament est vide', () => {
    renderRow(baseDrug);

    expect(screen.getByPlaceholderText('NOM OU DCI DU MÉDICAMENT...')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Dose' })).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Prise')).not.toBeInTheDocument();
    expect(screen.queryByPlaceholderText('Ex. 1 gélule × 3/jour pendant 7 jours')).not.toBeInTheDocument();
    expect(screen.getByText(/Commencez par choisir le médicament/)).toBeInTheDocument();
  });

  it('affiche le Prescription Composer dès qu’un médicament est identifié', () => {
    renderRow(identified({
      ...baseDrug,
      name: 'AMOXICILLINE',
      forme: 'GÉLULES',
      dosage: '500MG',
      posologie: '1 cp x 3 / jour pendant 7 jours',
    }));

    expect(screen.getByRole('button', { name: 'Dose' })).toHaveTextContent('500MG');
    expect(screen.getByRole('button', { name: 'Forme' })).toHaveTextContent('GÉLULES');
    expect(screen.getByLabelText('Prise')).toHaveTextContent('1 comprimé');
    expect(screen.getByLabelText('Rythme')).toHaveTextContent('3 fois par jour');
    expect(screen.getByLabelText('Durée ou limite')).toHaveTextContent('7 jours');
    expect(screen.getByLabelText('Moment ou condition')).toHaveTextContent('Moment ou condition');
    expect(screen.getByLabelText('Posologie en texte libre')).toBeInTheDocument();
  });

  it('génère la phrase de posologie dans le contrat string existant', () => {
    const { onUpdateDrug } = renderRow(identified({
      ...baseDrug,
      name: 'IBUPROFÈNE',
      forme: 'COMPRIMÉS',
      dosage: '400MG',
      posologie: '1 comprimé, si douleur, sans dépasser 3 fois par jour pendant 3 jours.',
    }));

    expect(screen.getByLabelText('Prise')).toHaveTextContent('1 comprimé');
    expect(screen.getByLabelText('Rythme')).toHaveTextContent('si douleur');
    expect(screen.getByLabelText('Durée ou limite')).toHaveTextContent('max 3/jour');
    expect(screen.getByLabelText('Moment ou condition')).toHaveTextContent('3 jours');

    fireEvent.click(screen.getByLabelText('Moment ou condition'));
    fireEvent.click(screen.getByRole('menuitem', { name: '5 jours' }));
    expect(onUpdateDrug).toHaveBeenLastCalledWith(
      1,
      'posologie',
      '1 comprimé, si douleur, sans dépasser 3 fois par jour pendant 5 jours.',
    );
  });
  it('conserve les deux types de ligne avec leurs icônes médicament et radio/examen', () => {
    const onToggleType = vi.fn();
    render(
      <DrugRow
        drug={baseDrug}
        idx={0}
        drugsCount={1}
        assessment={null}
        validationErrors={[]}
        forcedDrugs={[]}
        activeSearchId={null}
        suggestions={{ medications: [], dosages: [], posologies: [] }}
        highlightedIdx={-1}
        medChecks={{}}
        onUpdateDrug={vi.fn()}
        onRemoveDrug={vi.fn()}
        onMove={vi.fn()}
        onSearch={vi.fn()}
        onKeyDown={vi.fn()}
        onApplySuggestion={vi.fn()}
        onForceAllergy={vi.fn()}
        onToggleType={onToggleType}
      />,
    );

    const medicationButton = screen.getByRole('button', { name: 'Type médicament' });
    const examButton = screen.getByRole('button', { name: 'Type radio ou examen' });
    expect(medicationButton.querySelector('svg')).toBeTruthy();
    expect(examButton.querySelector('svg')).toBeTruthy();

    fireEvent.click(examButton);
    expect(onToggleType).toHaveBeenCalledWith(1, 'EXAMEN');
  });

  it('conserve tous les contrôles de personnalisation praticien sur une ligne médicament identifiée', () => {
    renderRow(identified({
      ...baseDrug,
      name: 'AMOXICILLINE',
      forme: 'GÉLULES',
      dosage: '500MG',
      posologie: '1 cp x 3 / jour pendant 7 jours',
      non_substituable: false,
    }));

    expect(screen.getByRole('button', { name: 'Forme' })).toHaveTextContent('GÉLULES');
    expect(screen.getByRole('button', { name: 'Dose' })).toHaveTextContent('500MG');
    expect(screen.getByLabelText('Prise')).toBeInTheDocument();
    expect(screen.getByLabelText('Rythme')).toBeInTheDocument();
    expect(screen.getByLabelText('Durée ou limite')).toBeInTheDocument();
    expect(screen.getByLabelText('Moment ou condition')).toBeInTheDocument();
    expect(screen.getByLabelText('Posologie en texte libre')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /non substituable/i })).toBeInTheDocument();
  });

  it('garde une ligne radio/examen distincte sans composer médicament', () => {
    renderRow({
      ...baseDrug,
      type: 'EXAMEN',
      name: 'RADIO PANORAMIQUE',
    });

    expect(screen.getByPlaceholderText("DÉTAILS DE L'EXAMEN RADIOLOGIQUE...")).toBeInTheDocument();
    expect(screen.queryByLabelText('Prise')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Rythme')).not.toBeInTheDocument();
  });

});
