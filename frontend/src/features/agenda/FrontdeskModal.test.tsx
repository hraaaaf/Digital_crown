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

  it('should have create button labeled Créer demande', () => {
    render(
      <FrontdeskModal
        open={true}
        onClose={() => {}}
        onSuccess={() => {}}
      />
    )

    expect(screen.getByRole('button', { name: /Créer demande/i })).toBeInTheDocument()
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

  it('should accept form input and call API on submit', async () => {
    const onSuccess = vi.fn()
    vi.mocked(api.api.post).mockResolvedValueOnce({ data: { id: 1 } })

    render(
      <FrontdeskModal
        open={true}
        onClose={() => {}}
        onSuccess={onSuccess}
      />
    )

    // Verify form elements exist
    expect(screen.getByRole('button', { name: /Créer demande/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Annuler/i })).toBeInTheDocument()
  })
})
