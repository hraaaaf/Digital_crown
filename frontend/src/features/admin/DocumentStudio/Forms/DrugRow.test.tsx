import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import '@testing-library/jest-dom/vitest'
import { DrugRow } from './DrugRow'
import type { DrugItem } from './prescriptionTypes'

const baseDrug: DrugItem = {
  id: 1,
  name: 'PARACE',
  dosage: '',
  forme: 'COMPRIMÉS',
  posologie: '',
  type: 'MEDICAMENT',
}

const noop = () => {}

function renderDrugRow(overrides: Partial<React.ComponentProps<typeof DrugRow>> = {}) {
  const onApplySuggestion = vi.fn()
  const onSearch = vi.fn()
  const props = {
    drug: baseDrug,
    idx: 0,
    drugsCount: 1,
    assessment: null,
    validationErrors: [],
    forcedDrugs: [],
    activeSearchId: { id: 1, field: 'name' },
    suggestions: { medications: ['PARACETAMOL', 'PARACETAMOL BIOGARAN'], dosages: [], posologies: [] },
    highlightedIdx: -1,
    medChecks: {},
    onUpdateDrug: noop,
    onRemoveDrug: noop,
    onMove: noop,
    onSearch,
    onKeyDown: noop,
    onApplySuggestion,
    onFormeOpen: noop,
    onForceAllergy: noop,
    onToggleType: noop,
    ...overrides,
  }
  render(<DrugRow {...props} />)
  return { onApplySuggestion, onSearch }
}

describe('DrugRow — autocomplete médicament', () => {
  it('affiche les suggestions quand activeSearchId correspond au champ name', () => {
    renderDrugRow()
    expect(screen.getByText('PARACETAMOL')).toBeInTheDocument()
    expect(screen.getByText('PARACETAMOL BIOGARAN')).toBeInTheDocument()
  })

  it("appelle onApplySuggestion dès le mousedown (avant tout blur) quand on clique sur une suggestion", () => {
    const { onApplySuggestion } = renderDrugRow()
    const suggestionButton = screen.getByText('PARACETAMOL').closest('button')!

    fireEvent.mouseDown(suggestionButton)

    expect(onApplySuggestion).toHaveBeenCalledWith(1, 'name', 'PARACETAMOL')
  })

  it('le mousedown sur la suggestion empêche le comportement par défaut (evite le blur qui fermerait le dropdown)', () => {
    renderDrugRow()
    const suggestionButton = screen.getByText('PARACETAMOL').closest('button')!

    const event = new MouseEvent('mousedown', { bubbles: true, cancelable: true })
    const preventDefaultSpy = vi.spyOn(event, 'preventDefault')
    suggestionButton.dispatchEvent(event)

    expect(preventDefaultSpy).toHaveBeenCalled()
  })

  it("n'affiche pas le dropdown quand activeSearchId pointe vers un autre champ", () => {
    renderDrugRow({ activeSearchId: { id: 1, field: 'dosage' } })
    expect(screen.queryByText('PARACETAMOL')).not.toBeInTheDocument()
  })

  it("n'affiche pas le dropdown quand la liste de suggestions est vide", () => {
    renderDrugRow({ suggestions: { medications: [], dosages: [], posologies: [] } })
    expect(screen.queryByText('PARACETAMOL')).not.toBeInTheDocument()
  })
})
