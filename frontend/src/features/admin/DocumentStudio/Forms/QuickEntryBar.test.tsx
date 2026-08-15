import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { beforeEach, describe, it, expect, vi } from 'vitest'
import '@testing-library/jest-dom/vitest'
import { QuickEntryBar } from './QuickEntryBar'
import type { DrugItem } from './prescriptionTypes'
import { api } from '../../../../services/api'

vi.mock('../../../../services/api', () => ({
  api: { get: vi.fn() },
}))

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
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(api.get).mockResolvedValue({
      data: { recent_medications: [], frequent_medications: [] },
    } as any)
  })

  it('affiche les suggestions quand la liste est non vide', () => {
    renderQuickEntryBar()
    expect(screen.getByText('PARACETAMOL')).toBeInTheDocument()
    expect(screen.getByText('PARACETAMOL BIOGARAN')).toBeInTheDocument()
  })

  it("ajoute le médicament dès le mousedown sur une suggestion (avant tout blur)", async () => {
    const { onAddDrug, parseQuickEntry } = renderQuickEntryBar()
    const suggestionButton = screen.getByText('PARACETAMOL').closest('button')!

    fireEvent.mouseDown(suggestionButton)

    await waitFor(() => expect(onAddDrug).toHaveBeenCalled())
    expect(parseQuickEntry).toHaveBeenCalledWith('PARACETAMOL')
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

  it('affiche les médicaments récents et fréquents lorsque la saisie est vide', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: {
        recent_medications: ['DOLIPRANE', 'AUGMENTIN'],
        frequent_medications: ['AUGMENTIN', 'KIN'],
      },
    } as any)
    const { onAddDrug, parseQuickEntry } = renderQuickEntryBar({ quickVal: '', quickSuggestions: [] })

    const recent = await screen.findByRole('button', { name: 'DOLIPRANE' })
    expect(screen.getByRole('button', { name: 'KIN' })).toBeInTheDocument()

    fireEvent.click(recent)
    await waitFor(() => expect(onAddDrug).toHaveBeenCalledTimes(1))
    expect(parseQuickEntry).toHaveBeenCalledWith('DOLIPRANE')
  })

  it('ignore un second Enter tant que le premier ajout est encore en cours', async () => {
    let resolveHydration: ((drug: DrugItem) => void) | undefined
    const hydrateMedicationDetails = vi.fn((drug: DrugItem) => new Promise<DrugItem>(resolve => {
      resolveHydration = resolve
    }))
    const { parseQuickEntry, onAddDrug } = renderQuickEntryBar({ hydrateMedicationDetails })
    const input = screen.getByPlaceholderText('Médicament, dosage, forme, posologie…')

    fireEvent.keyDown(input, { key: 'Enter' })
    fireEvent.keyDown(input, { key: 'Enter' })

    expect(parseQuickEntry).toHaveBeenCalledTimes(1)
    expect(hydrateMedicationDetails).toHaveBeenCalledTimes(1)

    resolveHydration?.({
      id: 1, name: 'PARACE', dosage: '', forme: 'COMPRIMÉS',
      posologie: '', type: 'MEDICAMENT', quantite: 1, non_substituable: false,
    })
    await waitFor(() => expect(onAddDrug).toHaveBeenCalledTimes(1))
  })
})
