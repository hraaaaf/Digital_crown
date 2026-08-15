import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import '@testing-library/jest-dom/vitest'

import { PrescriptionGuideModal } from './PrescriptionGuideModal'

vi.mock('../DentalPharmacologyArbiter', () => ({
  arbitrateMedication: () => ({
    status: 'applicable',
    regimen: { dosage: '', posology: '', form: '' },
    messages: [],
  }),
}))

vi.mock('../PrescriptionPharmacologyPipeline', () => ({
  buildPatientPharmacologyContext: () => ({
    ageYears: null,
    weightKg: null,
  }),
}))

function renderModal() {
  render(
    <PrescriptionGuideModal
      show
      onClose={vi.fn()}
      guideAge={0}
      setGuideAge={vi.fn()}
      guideWeight={0}
      setGuideWeight={vi.fn()}
      guideCategory="TOUS"
      setGuideCategory={vi.fn()}
      guideSearch=""
      setGuideSearch={vi.fn()}
      guideNationalResults={[]}
      guideSearching={false}
      setGuideSearching={vi.fn()}
      onNationalSearch={vi.fn()}
      assessment={null}
      onAddMolecule={vi.fn()}
    />,
  )
}

describe('PrescriptionGuideModal R6 search-first', () => {
  it('place la recherche comme action primaire et garde l’ajout manuel replié', () => {
    renderModal()

    const search = screen.getByRole('textbox', { name: 'Rechercher un médicament' })
    expect(search).toBeInTheDocument()
    expect(search).toHaveFocus()
    expect(screen.queryByPlaceholderText('Nom / DCI')).not.toBeInTheDocument()
  })

  it('déplie l’ajout manuel seulement sur action explicite', () => {
    renderModal()

    const toggle = screen.getByRole('button', { name: /Ajout manuel praticien/i })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')

    fireEvent.click(toggle)

    expect(toggle).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByPlaceholderText('Nom / DCI')).toBeInTheDocument()
  })
})
