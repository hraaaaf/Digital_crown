import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import '@testing-library/jest-dom/vitest'
import { QuickEntryBar } from './QuickEntryBar'
import type { DrugItem } from './prescriptionTypes'

const noop = () => {}

function renderQuickEntryBar(overrides: Partial<React.ComponentProps<typeof QuickEntryBar>> = {}) {
  const onAddDrug = vi.fn()
  const hydrateMedicationDetails = vi.fn(async (drug: DrugItem) => drug)
  const parseQuickEntry = vi.fn((text: string): DrugItem => ({
    id: 1, name: text.toUpperCase(), dosage: '', forme: 'COMPRIMÉS',
    posologie: '', type: 'MEDICAMENT', quantite: 1, non_substituable: false,
  }))
  const props = {
    quickVal: 'PARACE',
    setQuickVal: noop,
    quickSuggestions: ['PARACETAMOL', 'PARACETAMOL BIOGARAN'],
    quickHighlightedIdx: -1,
    setQuickHighlightedIdx: noop,
    onSearchChange: noop,
    onAddDrug,
    onSetStep: noop,
    hydrateMedicationDetails,
    parseQuickEntry,
    ...overrides,
  }
  render(<QuickEntryBar {...props} />)
  return { onAddDrug, hydrateMedicationDetails, parseQuickEntry }
}

describe('QuickEntryBar — autocomplete médicament (Saisie Rapide)', () => {
  it('affiche les suggestions quand la liste est non vide', () => {
    renderQuickEntryBar()
    expect(screen.getByText('PARACETAMOL')).toBeInTheDocument()
    expect(screen.getByText('PARACETAMOL BIOGARAN')).toBeInTheDocument()
  })

  it("ajoute le médicament dès le mousedown sur une suggestion (avant tout blur)", async () => {
    const { onAddDrug, parseQuickEntry } = renderQuickEntryBar()
    const suggestionButton = screen.getByText('PARACETAMOL').closest('button')!

    await fireEvent.mouseDown(suggestionButton)

    expect(parseQuickEntry).toHaveBeenCalledWith('PARACETAMOL')
    expect(onAddDrug).toHaveBeenCalled()
  })

  it('le mousedown sur la suggestion empêche le comportement par défaut (évite le blur qui fermerait le dropdown)', () => {
    renderQuickEntryBar()
    const suggestionButton = screen.getByText('PARACETAMOL').closest('button')!

    const event = new MouseEvent('mousedown', { bubbles: true, cancelable: true })
    const preventDefaultSpy = vi.spyOn(event, 'preventDefault')
    suggestionButton.dispatchEvent(event)

    expect(preventDefaultSpy).toHaveBeenCalled()
  })

  it('les boutons de suggestion sont type="button" (jamais un submit implicite)', () => {
    renderQuickEntryBar()
    const suggestionButton = screen.getByText('PARACETAMOL').closest('button')!
    expect(suggestionButton).toHaveAttribute('type', 'button')
  })

  it("n'affiche pas le dropdown quand la liste de suggestions est vide", () => {
    renderQuickEntryBar({ quickSuggestions: [] })
    expect(screen.queryByText('PARACETAMOL')).not.toBeInTheDocument()
  })
})
