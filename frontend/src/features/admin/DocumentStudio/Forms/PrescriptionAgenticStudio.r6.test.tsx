import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import '@testing-library/jest-dom/vitest'

const legacyMount = vi.fn()

vi.mock('./PrescriptionAgenticStudioLegacy', () => ({
  PrescriptionAgenticStudio: (props: any) => {
    legacyMount(props)
    return <div data-testid="legacy-studio">legacy</div>
  },
}))

vi.mock('../../../../services/api', () => ({
  api: {
    post: vi.fn(async () => ({ data: [] })),
    interceptors: {
      request: { use: vi.fn(() => 1), eject: vi.fn() },
      response: { use: vi.fn(() => 2), eject: vi.fn() },
    },
  },
}))

import { PrescriptionAgenticStudio } from './PrescriptionAgenticStudio'

describe('PrescriptionAgenticStudio R6 protocol visibility', () => {
  beforeEach(() => legacyMount.mockClear())

  it('réaffiche Mes protocoles en remontant le studio legacy', () => {
    render(
      <PrescriptionAgenticStudio
        patientId=""
        drugs={[]}
        setDrugs={vi.fn()}
        onUpdateDrug={vi.fn()}
        onRemoveDrug={vi.fn()}
        onAddDrug={vi.fn()}
        validationErrors={[]}
      />,
    )

    const callsBeforeRestore = legacyMount.mock.calls.length
    expect(callsBeforeRestore).toBeGreaterThan(0)

    fireEvent.click(screen.getByRole('button', { name: 'Mes protocoles' }))

    expect(legacyMount.mock.calls.length).toBeGreaterThan(callsBeforeRestore)
  })
})
