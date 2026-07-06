import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import '@testing-library/jest-dom/vitest'
import { PendingRequestCard } from './PendingRequestCard'
import * as api from '../../services/api'

vi.mock('../../services/api', () => ({
  api: {
    post: vi.fn(),
  },
}))

const mockRequest = {
  id: 1,
  patient_name: 'John Doe',
  phone: '0612345678',
  datetime_start: '2026-07-15T10:00:00',
  duration_minutes: 30,
  motif: 'Détartrage',
  status: 'EN_ATTENTE_DEMANDE',
  source: 'frontdesk',
  expires_at: '2026-07-15T10:30:00',
  created_at: '2026-07-15T09:00:00',
}

describe('PendingRequestCard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should display patient information and appointment details', () => {
    render(
      <PendingRequestCard
        request={mockRequest}
        onAction={() => {}}
      />
    )

    expect(screen.getByText('John Doe')).toBeInTheDocument()
    expect(screen.getByText(/0612345678/)).toBeInTheDocument()
    expect(screen.getByText(/Détartrage/)).toBeInTheDocument()
    expect(screen.getByText(/30 min/)).toBeInTheDocument()
  })

  it('should display status EN_ATTENTE_DEMANDE', () => {
    render(
      <PendingRequestCard
        request={mockRequest}
        onAction={() => {}}
      />
    )

    // Component displays status via icon + button labels, not a text label
    expect(screen.getByRole('button', { name: /Demander confirmation/i })).toBeInTheDocument()
  })

  it('should call request-confirmation endpoint when button clicked', async () => {
    const onAction = vi.fn()
    vi.mocked(api.api.post).mockResolvedValueOnce({ data: {} })

    render(
      <PendingRequestCard
        request={mockRequest}
        onAction={onAction}
      />
    )

    const user = userEvent.setup()
    const btn = screen.getByRole('button', { name: /Demander confirmation/i })
    await user.click(btn)

    await waitFor(() => {
      expect(api.api.post).toHaveBeenCalledWith('/appointments/1/request-confirmation')
    })
  })

  it('should call confirm endpoint when confirm button clicked', async () => {
    const onAction = vi.fn()
    const confirmRequest = { ...mockRequest, status: 'EN_ATTENTE_CONFIRM' }
    vi.mocked(api.api.post).mockResolvedValueOnce({ data: {} })

    render(
      <PendingRequestCard
        request={confirmRequest}
        onAction={onAction}
      />
    )

    const user = userEvent.setup()
    const btn = screen.getByRole('button', { name: /Confirmer/i })
    await user.click(btn)

    await waitFor(() => {
      expect(api.api.post).toHaveBeenCalledWith('/appointments/1/confirm')
    })
  })

  it('should call reject endpoint when reject button clicked', async () => {
    const onAction = vi.fn()
    vi.mocked(api.api.post).mockResolvedValueOnce({ data: {} })
    window.confirm = vi.fn(() => true)

    render(
      <PendingRequestCard
        request={mockRequest}
        onAction={onAction}
      />
    )

    const user = userEvent.setup()
    const btn = screen.getByRole('button', { name: /Refuser/i })
    await user.click(btn)

    await waitFor(() => {
      expect(api.api.post).toHaveBeenCalledWith('/appointments/1/reject')
    })
  })

  it('should handle 409 error gracefully', async () => {
    vi.mocked(api.api.post).mockRejectedValueOnce({
      response: { data: { detail: 'Créneau déjà utilisé ou demande expirée' } }
    })
    window.alert = vi.fn()

    render(
      <PendingRequestCard
        request={mockRequest}
        onAction={() => {}}
      />
    )

    const user = userEvent.setup()
    const btn = screen.getByRole('button', { name: /Demander confirmation/i })
    await user.click(btn)

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith('Créneau déjà utilisé ou demande expirée')
    })
  })
})
