import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import '@testing-library/jest-dom/vitest'
import { FrontdeskModal } from './FrontdeskModal'
import * as api from '../../services/api'

vi.mock('../../services/api', () => ({
  api: {
    post: vi.fn(),
  },
}))

describe('FrontdeskModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should open when open prop is true', () => {
    render(
      <FrontdeskModal
        open={true}
        onClose={() => {}}
        onSuccess={() => {}}
      />
    )
    expect(screen.getByText('Nouvelle demande de RDV')).toBeInTheDocument()
  })

  it('should not render when open prop is false', () => {
    const { container } = render(
      <FrontdeskModal
        open={false}
        onClose={() => {}}
        onSuccess={() => {}}
      />
    )
    expect(container.firstChild).toBeNull()
  })

  it('should submit appointment request with correct fields', async () => {
    const onSuccess = vi.fn()
    vi.mocked(api.api.post).mockResolvedValueOnce({ data: { id: 1 } })

    render(
      <FrontdeskModal
        open={true}
        onClose={() => {}}
        onSuccess={onSuccess}
      />
    )

    const user = userEvent.setup()
    await user.type(screen.getByPlaceholderText('Prénom'), 'Jean')
    await user.type(screen.getByPlaceholderText('Nom'), 'Dupont')
    await user.type(screen.getByPlaceholderText('Téléphone (optionnel)'), '0612345678')
    await user.type(screen.getByPlaceholderText('Motif de la visite'), 'Détartrage')

    const dateInputs = screen.getAllByRole('textbox')
    await user.type(dateInputs[dateInputs.length - 2], '2026-07-15')

    const submitBtn = screen.getByRole('button', { name: /Créer demande/i })
    await user.click(submitBtn)

    await waitFor(() => {
      expect(api.api.post).toHaveBeenCalledWith(
        '/frontdesk/appointment-request',
        expect.objectContaining({
          first_name: 'Jean',
          last_name: 'Dupont',
          phone: '0612345678',
          appointment_reason: 'Détartrage',
          source: 'frontdesk',
        })
      )
    })

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalled()
    })
  })

  it('should close modal on cancel button click', async () => {
    const onClose = vi.fn()
    render(
      <FrontdeskModal
        open={true}
        onClose={onClose}
        onSuccess={() => {}}
      />
    )

    const user = userEvent.setup()
    const cancelBtn = screen.getByRole('button', { name: /Annuler/i })
    await user.click(cancelBtn)

    expect(onClose).toHaveBeenCalled()
  })

  it('should display error message on API failure', async () => {
    vi.mocked(api.api.post).mockRejectedValueOnce({
      response: { data: { detail: 'Créneau déjà utilisé' } }
    })

    render(
      <FrontdeskModal
        open={true}
        onClose={() => {}}
        onSuccess={() => {}}
      />
    )

    const user = userEvent.setup()
    await user.type(screen.getByPlaceholderText('Prénom'), 'Jean')
    await user.type(screen.getByPlaceholderText('Nom'), 'Dupont')

    const submitBtn = screen.getByRole('button', { name: /Créer demande/i })
    await user.click(submitBtn)

    await waitFor(() => {
      expect(screen.getByText('Créneau déjà utilisé')).toBeInTheDocument()
    })
  })
})
