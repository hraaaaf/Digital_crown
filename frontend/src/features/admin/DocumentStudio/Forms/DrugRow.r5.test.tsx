import { render, screen } from '@testing-library/react'
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
      onUpdateDrug={vi.fn()}
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
}

describe('DrugRow R5 progressive disclosure', () => {
  it('cache dose, forme et posologie tant que le médicament est vide', () => {
    renderRow(baseDrug)

    expect(screen.getByPlaceholderText('NOM DU MÉDICAMENT...')).toBeInTheDocument()
    expect(screen.queryByText('Dose')).not.toBeInTheDocument()
    expect(screen.queryByPlaceholderText('Ex. 1 gélule × 3/jour pendant 7 jours')).not.toBeInTheDocument()
    expect(screen.getByText(/Les détails de dose, forme et posologie apparaissent/)).toBeInTheDocument()
  })

  it('affiche les détails dès qu’un médicament est identifié', () => {
    renderRow({ ...baseDrug, name: 'AMOXICILLINE', forme: 'GÉLULES', dosage: '500MG' })

    expect(screen.getByText('Dose')).toBeInTheDocument()
    expect(screen.getByDisplayValue('500MG')).toBeInTheDocument()
    expect(screen.getByText('GÉLULES')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Ex. 1 gélule × 3/jour pendant 7 jours')).toBeInTheDocument()
  })
})
