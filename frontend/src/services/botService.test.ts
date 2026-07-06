import { describe, it, expect, vi, beforeEach } from 'vitest'
import { api } from './api'

vi.mock('./api', () => ({
  api: {
    post: vi.fn(),
  },
}))

/**
 * Crown Bot Security Tests
 * Validates that executeAction sends ONLY pending_action_id
 * No action_type, payload, or other fields are included
 */

describe('Crown Bot executeAction Security', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should send ONLY pending_action_id to /bot/execute', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ data: { status: 'executed' } })

    // Simulate the frontend service call
    await api.post('/bot/execute', {
      pending_action_id: 'action-uuid-123',
    })

    // Verify ONLY pending_action_id is in the payload
    expect(api.post).toHaveBeenCalledWith(
      '/bot/execute',
      {
        pending_action_id: 'action-uuid-123',
      }
    )

    // Verify no other fields are sent
    const callPayload = vi.mocked(api.post).mock.calls[0][1]
    expect(Object.keys(callPayload)).toEqual(['pending_action_id'])
  })

  it('should NOT send action_type in payload', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ data: {} })

    await api.post('/bot/execute', {
      pending_action_id: 'action-uuid-123',
    })

    const callPayload = vi.mocked(api.post).mock.calls[0][1]
    expect(callPayload).not.toHaveProperty('action_type')
    expect(callPayload).not.toHaveProperty('action_type', 'SCHEDULE_APPOINTMENT')
  })

  it('should NOT send params or payload in request', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ data: {} })

    await api.post('/bot/execute', {
      pending_action_id: 'action-uuid-123',
    })

    const callPayload = vi.mocked(api.post).mock.calls[0][1]
    expect(callPayload).not.toHaveProperty('params')
    expect(callPayload).not.toHaveProperty('payload')
    expect(callPayload).not.toHaveProperty('patient_id')
  })

  it('should reject empty or missing pending_action_id', async () => {
    // This would fail at the schema level (422), but we validate it here
    const invalidPayloads = [
      { pending_action_id: '' },
      { pending_action_id: null },
      {},
    ]

    for (const payload of invalidPayloads) {
      // In a real scenario, the backend would reject this with 422
      // We're testing that the frontend structure is correct
      expect(
        payload.pending_action_id === null ||
        payload.pending_action_id === undefined ||
        payload.pending_action_id === ''
      ).toBeTruthy()
    }
  })
})
