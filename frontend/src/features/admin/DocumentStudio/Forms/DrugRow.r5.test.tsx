import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import '@testing-library/jest-dom/vitest'

import { DrugRow } from './DrugRow'
import type { DrugItem } from './prescriptionTypes'

const baseDrug: DrugItem = {
  id: 1,
  name: '',
  dosage: '',
  forme: '',
  posologie: '',
  type: 'MEDICAMENT',
  quantite: 1,
  non_substituable: false,
}

function renderRow(drug: DrugItem) {
  const onUpdateDrug = vi.fn()
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
      onFormeOpen={vi.fn()}
      onForceAllergy={vi.fn()}
      onToggleType={vi.fn()}
    />,
  )
  return { onUpdateDrug }
}

describe('DrugRow R5 progressive disclosure', () => {
  it('cache dose, forme et posologie tant que le médicament est vide', () => {
    renderRow(baseDrug)

    expect(screen.getByPlaceholderText('NOM DU MÉDICAMENT...')).toBeInTheDocument()
    expect(screen.queryByText('Dose')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Prise')).not.toBeInTheDocument()
    expect(screen.queryByPlaceholderText('Ex. 1 gélule × 3/jour pendant 7 jours')).not.toBeInTheDocument()
    expect(screen.getByText(/Identifiez le médicament pour renseigner forme, dose et posologie/)).toBeInTheDocument()
  })

  it('affiche le Prescription Composer dès qu’un médicament est identifié', () => {
    renderRow({
      ...baseDrug,
      name: 'AMOXICILLINE',
      forme: 'GÉLULES',
      dosage: '500MG',
      posologie: '1 cp x 3 / jour pendant 7 jours',
    })

    expect(screen.getByText('Dose')).toBeInTheDocument()
    expect(screen.getByDisplayValue('500MG')).toBeInTheDocument()
    expect(screen.getByText('GÉLULES')).toBeInTheDocument()
    expect(screen.getByLabelText('Prise')).toHaveValue('1 comprimé')
    expect(screen.getByLabelText('Rythme')).toHaveValue('3 fois par jour')
    expect(screen.getByLabelText('Durée ou limite')).toHaveValue('7 jours')
    expect(screen.getByLabelText('Moment ou condition')).toHaveValue('')
    expect(screen.getByLabelText('Posologie en texte libre')).toBeInTheDocument()
  })

  it('génère la phrase de posologie dans le contrat string existant', () => {
    const { onUpdateDrug } = renderRow({
      ...baseDrug,
      name: 'IBUPROFÈNE',
      forme: 'COMPRIMÉS',
      dosage: '400MG',
      posologie: '1 comprimé, si douleur, sans dépasser 3 fois par jour pendant 3 jours.',
    })

    expect(screen.getByLabelText('Prise')).toHaveValue('1 comprimé')
    expect(screen.getByLabelText('Rythme')).toHaveValue('si douleur')
    expect(screen.getByLabelText('Durée ou limite')).toHaveValue('max 3/jour')
    expect(screen.getByLabelText('Moment ou condition')).toHaveValue('3 jours')

    fireEvent.change(screen.getByLabelText('Moment ou condition'), { target: { value: '5 jours' } })
    expect(onUpdateDrug).toHaveBeenLastCalledWith(
      1,
      'posologie',
      '1 comprimé, si douleur, sans dépasser 3 fois par jour pendant 5 jours.',
    )
  })
})
