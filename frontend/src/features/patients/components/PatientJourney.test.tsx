import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import '@testing-library/jest-dom/vitest'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { PatientJourney } from './PatientJourney'
import * as api from '../../../services/api'

vi.mock('../../../services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}))

const summary = {
  active_plan_steps: 1,
  total_plan_steps: 2,
  remaining_due: 0,
  has_billing_data: true,
  next_appointment: null,
  last_document_date: null,
}

function makeJourneyResponse(events: any[], summaryOverride?: Partial<typeof summary>) {
  return {
    patient_id: 1,
    window_months: 12,
    truncated: false,
    total_events_available: events.length,
    summary: { ...summary, ...summaryOverride },
    events,
  }
}

const EVENT_DOCUMENT = {
  event_key: 'document_archive:1',
  source: 'document_archive',
  type: 'DEVIS',
  ref_id: 1,
  date: '2026-06-01T10:00:00',
  title: 'Devis Composite',
  status: 'ACTIF',
  phase_hint: 'devis',
  navigation_target: 'DOCUMENT',
  related_event_key: null,
}

const EVENT_PAYMENT = {
  event_key: 'payment:1',
  source: 'payment',
  type: 'paiement',
  ref_id: 1,
  date: '2026-05-01T10:00:00',
  title: 'Paiement — 100.00 MAD',
  status: 'ESPECES',
  phase_hint: 'paiement',
  navigation_target: 'ACCOUNTING_TAB',
  related_event_key: null,
}

const EVENT_OLD_OPEN_STEP = {
  event_key: 'treatment_plan_step:1',
  source: 'treatment_plan_step',
  type: 'plan_step',
  ref_id: 1,
  date: '2023-01-01T10:00:00', // > 12 mois
  title: 'Détartrage',
  status: 'pending',
  phase_hint: 'plan',
  navigation_target: 'TREATMENT_PLAN_TAB',
  related_event_key: null,
}

const EVENT_MILESTONE = {
  event_key: 'journey_milestone:1',
  source: 'journey_milestone',
  type: 'DIAGNOSTIC',
  ref_id: 1,
  date: '2026-06-05T10:00:00',
  title: 'Diagnostic',
  status: 'DIAGNOSTIC',
  phase_hint: 'diagnostic',
  navigation_target: 'INLINE',
  related_event_key: null,
}

function mockApiGet(overrides: { events?: any[]; actes?: any[]; documents?: any[]; journeyError?: boolean; summary?: Partial<typeof summary> } = {}) {
  vi.mocked(api.api.get).mockImplementation(async (url: string) => {
    if (url.includes('/journey')) {
      if (overrides.journeyError) throw new Error('network error')
      return { data: makeJourneyResponse(overrides.events ?? [], overrides.summary) }
    }
    if (url.includes('/actes/patient/')) {
      return { data: overrides.actes ?? [] }
    }
    if (url.includes('/documents')) {
      return { data: overrides.documents ?? [] }
    }
    return { data: [] }
  })
}

function LocationDisplay() {
  const location = useLocation()
  return <div data-testid="location-search">{location.search}</div>
}

function renderJourney() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <PatientJourney patientId={1} />
        <LocationDisplay />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('PatientJourney', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('groups events by phase and renders each in its own group', async () => {
    mockApiGet({ events: [EVENT_DOCUMENT, EVENT_PAYMENT] })
    renderJourney()

    await waitFor(() => {
      expect(screen.getByText('Devis')).toBeInTheDocument()
      expect(screen.getByText('Paiements & échéances')).toBeInTheDocument()
    })
    expect(screen.getByText('Devis Composite')).toBeInTheDocument()
  })

  it('renders events within a phase in the order returned by the backend, without re-sorting', async () => {
    // Le backend trie déjà (date DESC) ; le frontend ne doit jamais re-trier localement.
    const newer = { ...EVENT_PAYMENT, event_key: 'payment:2', ref_id: 2, date: '2026-06-01T10:00:00', title: 'Paiement récent' }
    const older = { ...EVENT_PAYMENT, event_key: 'payment:1', ref_id: 1, date: '2026-05-01T10:00:00', title: 'Paiement ancien' }
    mockApiGet({ events: [newer, older] }) // déjà trié desc par le backend

    renderJourney()

    await waitFor(() => expect(screen.getByText('Paiement récent')).toBeInTheDocument())

    const titles = screen.getAllByText(/Paiement (récent|ancien)/).map((el) => el.textContent)
    expect(titles).toEqual(['Paiement récent', 'Paiement ancien'])
  })

  it('filters events by source when a chip is clicked', async () => {
    mockApiGet({ events: [EVENT_DOCUMENT, EVENT_PAYMENT] })
    renderJourney()

    await waitFor(() => expect(screen.getByText('Devis Composite')).toBeInTheDocument())

    const user = userEvent.setup()
    const paymentsChip = screen.getByRole('button', { name: 'Paiements' })
    await user.click(paymentsChip)

    expect(screen.queryByText('Devis Composite')).not.toBeInTheDocument()
    expect(screen.getByText('Paiement — 100.00 MAD')).toBeInTheDocument()
  })

  it('shows an empty state with no crash when there are no events', async () => {
    mockApiGet({ events: [] })
    renderJourney()

    await waitFor(() => {
      expect(screen.getByText("Aucun événement pour l'instant.")).toBeInTheDocument()
    })
  })

  it('shows a loading indicator while the journey is being fetched', () => {
    vi.mocked(api.api.get).mockReturnValue(new Promise(() => {})) // never resolves
    renderJourney()

    expect(screen.getByText(/Chargement du parcours patient/i)).toBeInTheDocument()
  })

  it('shows an error message when the journey request fails', async () => {
    mockApiGet({ journeyError: true })
    renderJourney()

    await waitFor(() => {
      expect(screen.getByText(/Impossible de charger le parcours patient/i)).toBeInTheDocument()
    })
  })

  it('always displays an open item even if it is older than the 12-month window', async () => {
    // Le backend décide de l'inclusion (item ouvert) — le frontend doit juste l'afficher
    // dans la chronologie sans le filtrer localement par date. P2 peut aussi reprendre
    // son titre dans la carte "Prochaine action", d'où le scope explicite ici.
    mockApiGet({ events: [EVENT_OLD_OPEN_STEP] })
    renderJourney()

    await waitFor(() => {
      const chronology = screen.getByLabelText('Chronologie factuelle')
      expect(within(chronology).getByText('Détartrage')).toBeInTheDocument()
    })
  })

  it('navigates to the accounting tab when clicking a payment event', async () => {
    mockApiGet({ events: [EVENT_PAYMENT] })
    renderJourney()

    await waitFor(() => expect(screen.getByText('Paiement — 100.00 MAD')).toBeInTheDocument())

    const user = userEvent.setup()
    await user.click(screen.getByText('Paiement — 100.00 MAD'))

    await waitFor(() => {
      expect(screen.getByTestId('location-search').textContent).toContain('tab=finances')
    })
  })

  it('renders LegacyActeNotes only when the patient has legacy Acte rows', async () => {
    const acte = {
      id: 42,
      libelle: 'Traitement de carie',
      montant: 65,
      notes_cliniques: null,
      attachments: [],
    }
    mockApiGet({ events: [], actes: [acte] })
    renderJourney()

    await waitFor(() => {
      expect(screen.getByText('Actes historiques (1)')).toBeInTheDocument()
    })

    // Section repliée par défaut : la carte n'apparaît qu'après dépliage
    const user = userEvent.setup()
    await user.click(screen.getByText('Actes historiques (1)'))
    await waitFor(() => {
      expect(screen.getByText('Traitement de carie')).toBeInTheDocument()
      expect(screen.getByText('Aucune note clinique pour cette séance.')).toBeInTheDocument()
    })
  })

  it('does not render the legacy actes section when the patient has no Acte rows', async () => {
    mockApiGet({ events: [], actes: [] })
    renderJourney()

    await waitFor(() => {
      expect(screen.getByText("Aucun événement pour l'instant.")).toBeInTheDocument()
    })
    expect(screen.queryByText(/Actes historiques/)).not.toBeInTheDocument()
  })
})

describe('PatientJourney summary card', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows "Solde indéterminé" when the patient has no billing data', async () => {
    mockApiGet({ events: [], summary: { has_billing_data: false, remaining_due: 0 } })
    renderJourney()

    await waitFor(() => {
      expect(screen.getByText('Solde indéterminé')).toBeInTheDocument()
    })
    expect(screen.queryByText(/0 MAD/)).not.toBeInTheDocument()
  })

  it('shows the MAD amount in red when billing data exists and balance is due', async () => {
    mockApiGet({ events: [], summary: { has_billing_data: true, remaining_due: 250 } })
    renderJourney()

    await waitFor(() => {
      expect(screen.getByText(/250.*MAD/)).toBeInTheDocument()
    })
  })
})
