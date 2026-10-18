import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, useNavigate } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';
import userEvent from '@testing-library/user-event';

vi.mock('../../services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
  API_BASE: 'http://127.0.0.1:8005',
  getRuntimeAuthToken: vi.fn(() => 'g9-token'),
}));

vi.mock('../../stores/useAuthStore', () => ({
  useAuthStore: () => ({
    user: { id: 9, employer_id: 42 },
  }),
}));

import { api } from '../../services/api';
import { CrownBotChat } from './CrownBotChat';

const getMock = vi.mocked(api.get);
const postMock = vi.mocked(api.post);

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  url: string;
  onopen: ((event?: unknown) => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: ((event?: unknown) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    FakeWebSocket.instances.push(this);
  }

  close() {}

  emit(payload: unknown) {
    this.onmessage?.({ data: JSON.stringify(payload) });
  }
}

function renderCrownBot(onUnreadChange = vi.fn()) {
  render(
    <MemoryRouter initialEntries={['/accounting']}>
      <CrownBotChat onUnreadChange={onUnreadChange} />
    </MemoryRouter>,
  );
  return onUnreadChange;
}

async function seedInsight() {
  await waitFor(() => expect(FakeWebSocket.instances.length).toBeGreaterThan(0));
  act(() => {
    FakeWebSocket.instances.at(-1)?.emit({
      unread_count: 1,
      insights: [{
        id: 501,
        insight_type: 'finance',
        content: 'Impayé à vérifier',
        patient_id: 4,
        created_at: '2026-09-24T10:00:00Z',
      }],
    });
  });
  await screen.findByRole('button', { name: /^Marquer comme lu$/i });
}

describe('CrownBot G9 reachable interaction truth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // The CI synthetic preview opt-in is TRUE; explicitly test both ON/OFF
    // branches instead of inheriting a runner-wide flag by accident.
    vi.stubEnv('VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED', 'false');
    FakeWebSocket.instances = [];
    vi.stubGlobal('WebSocket', FakeWebSocket as any);
    Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', {
      value: vi.fn(),
      configurable: true,
    });
    getMock.mockResolvedValue({ data: [] } as any);
    postMock.mockResolvedValue({ data: { status: 'read' } } as any);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it('CB-01 FIRST_VALUE: opt-in opens directly on the three business actions without a server write', () => {
    vi.stubEnv('VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED', 'true');
    renderCrownBot();
    expect(screen.getByRole('region', { name: 'Assistant Crown Bot — consultation' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Mon programme' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Trouver un patient' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Préparer un RDV' })).toBeInTheDocument();
    expect(postMock).not.toHaveBeenCalled();
    expect(getMock).not.toHaveBeenCalledWith('/appointments/', expect.anything());
  });

  it('keeps an insight visible and unread when backend read-ack is refused', async () => {
    const onUnreadChange = renderCrownBot();
    await seedInsight();

    await waitFor(() => expect(onUnreadChange).toHaveBeenLastCalledWith(1));

    postMock.mockRejectedValueOnce(new Error('read refused'));
    fireEvent.click(screen.getByRole('button', { name: /^Marquer comme lu$/i }));

    await waitFor(() => {
      expect(postMock).toHaveBeenCalledWith('/ai/ghost-insights/501/read');
    });

    expect(screen.getByRole('button', { name: /^Marquer comme lu$/i })).toBeInTheDocument();
    expect(onUnreadChange).toHaveBeenLastCalledWith(1);
  });

  it('removes an insight and decrements unread only after backend read-ack succeeds', async () => {
    const onUnreadChange = renderCrownBot();
    await seedInsight();

    fireEvent.click(screen.getByRole('button', { name: /^Marquer comme lu$/i }));

    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /^Marquer comme lu$/i })).not.toBeInTheDocument();
    });
    expect(postMock).toHaveBeenCalledWith('/ai/ghost-insights/501/read');
    await waitFor(() => {
      expect(onUnreadChange).toHaveBeenLastCalledWith(0);
    });
  });

  it('A02: HTTP 200 without persisted read status cannot hide a clinical alert', async () => {
    const onUnreadChange = renderCrownBot();
    await seedInsight();
    await waitFor(() => expect(onUnreadChange).toHaveBeenLastCalledWith(1));
    postMock.mockResolvedValueOnce({ data: { status: 'pending' } } as any);
    fireEvent.click(screen.getByRole('button', { name: /^Marquer comme lu$/i }));
    await waitFor(() => expect(postMock).toHaveBeenCalledWith('/ai/ghost-insights/501/read'));
    expect(screen.getByRole('button', { name: /^Marquer comme lu$/i })).toBeInTheDocument();
    expect(onUnreadChange).toHaveBeenLastCalledWith(1);
  });

  it('A02: delayed read ACK cannot decrement badge for a replacement WS snapshot', async () => {
    const onUnreadChange = renderCrownBot();
    await seedInsight();
    let finishRead: ((value: { data: { status: string } }) => void) | undefined;
    postMock.mockImplementationOnce(() => new Promise(resolve => { finishRead = resolve; }));
    fireEvent.click(screen.getByRole('button', { name: /^Marquer comme lu$/i }));
    await waitFor(() => expect(postMock).toHaveBeenCalledWith('/ai/ghost-insights/501/read'));
    act(() => {
      FakeWebSocket.instances.at(-1)?.emit({
        unread_count: 1,
        insights: [{
          id: 502, insight_type: 'AGENDA', content: 'Nouvelle alerte',
          patient_id: null, created_at: '2026-10-17T12:00:00Z',
        }],
      });
    });
    expect(screen.getAllByRole('button', { name: /^Marquer comme lu$/i })).toHaveLength(1);
    await act(async () => { finishRead?.({ data: { status: 'read' } }); });
    expect(screen.getAllByRole('button', { name: /^Marquer comme lu$/i })).toHaveLength(1);
    expect(onUnreadChange).toHaveBeenLastCalledWith(1);
    expect(screen.getByRole('button', { name: 'Tout marquer comme lu' })).toBeInTheDocument();
  });

  it('A11Y: the insight patient navigation is a keyboard-reachable link, not a mouse-only div', async () => {
    renderCrownBot();
    await seedInsight();
    const link = screen.getByRole('link', {
      name: 'Ouvrir le dossier patient associé à cette alerte',
    });
    expect(link).toHaveAttribute('href', '/patients/4');
    link.focus();
    expect(link).toHaveFocus();
    expect(link).toHaveClass('focus-visible:outline');
  });

  it('A11Y: tablist is announced and Arrow/Home/End rove one selected tab', async () => {
    const user = userEvent.setup();
    renderCrownBot();
    const list = screen.getByRole('tablist', { name: 'Vues de Crown Bot' });
    const brain = screen.getByRole('tab', { name: /^Mémoire contextuelle/ });
    const chat = screen.getByRole('tab', { name: 'Chat' });
    expect(list).toContainElement(brain);
    expect(list).toContainElement(chat);
    expect(brain).toHaveAttribute('aria-selected', 'true');
    expect(brain).toHaveAttribute('aria-controls', 'cb01-panel-brain');
    expect(chat).not.toHaveAttribute('aria-controls');
    expect(brain).toHaveAttribute('tabindex', '0');
    expect(chat).toHaveAttribute('tabindex', '-1');
    expect(screen.getByRole('tabpanel')).toHaveAttribute('aria-labelledby', 'cb01-tab-brain');
    brain.focus();
    await user.keyboard('{ArrowRight}');
    expect(chat).toHaveFocus();
    expect(chat).toHaveAttribute('aria-selected', 'true');
    expect(chat).toHaveAttribute('aria-controls', 'cb01-panel-chat');
    expect(brain).not.toHaveAttribute('aria-controls');
    expect(brain).toHaveAttribute('tabindex', '-1');
    expect(screen.getByRole('tabpanel')).toHaveAttribute('aria-labelledby', 'cb01-tab-chat');
    await user.keyboard('{Home}');
    expect(brain).toHaveFocus();
    expect(brain).toHaveAttribute('aria-selected', 'true');
    await user.keyboard('{End}');
    expect(chat).toHaveFocus();
    expect(chat).toHaveAttribute('aria-selected', 'true');
    await user.keyboard('{ArrowLeft}');
    expect(brain).toHaveFocus();
    expect(chat).toHaveAttribute('aria-selected', 'false');
  });

  it('A11Y: archiving requires explicit confirmation and can be cancelled by keyboard', async () => {
    const user = userEvent.setup();
    getMock.mockImplementation(async url => {
      if (url === '/bot/sessions') return { data: [
        { id: 'history-archive', title: 'Archive synthétique', updated_at: '2026-10-18' },
      ] } as any;
      return { data: [] } as any;
    });
    const confirmation = vi.spyOn(window, 'confirm').mockReturnValue(false);
    const deletion = vi.mocked(api.delete);
    renderCrownBot();
    fireEvent.click(screen.getByRole('button', { name: "Ouvrir l'historique Crown Bot" }));
    const archive = await screen.findByRole('button', { name: 'Archiver la conversation Archive synthétique' });
    archive.focus();
    await user.keyboard('{Enter}');
    expect(confirmation).toHaveBeenCalledWith(expect.stringContaining('Archive synthétique'));
    expect(deletion).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: 'Ouvrir la conversation Archive synthétique' })).toBeInTheDocument();
    confirmation.mockRestore();
  });

  it('B01: history drawer is inert and inaccessible while closed, enabled when opened', () => {
    renderCrownBot();
    const drawer = document.querySelector('[data-cb01-history-drawer]');
    expect(drawer).toHaveAttribute('inert');
    expect(drawer).toHaveAttribute('aria-hidden', 'true');
    expect(screen.queryByRole('button', { name: 'Nouvelle conversation' })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: "Ouvrir l'historique Crown Bot" }));
    expect(drawer).not.toHaveAttribute('inert');
    expect(drawer).toHaveAttribute('aria-hidden', 'false');
    expect(screen.getByRole('dialog', { name: 'Historique Crown Bot' })).toHaveAttribute('aria-modal', 'true');
    expect(screen.getByRole('button', { name: 'Nouvelle conversation' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: "Fermer l'historique Crown Bot" }));
    expect(drawer).toHaveAttribute('inert');
    expect(drawer).toHaveAttribute('aria-hidden', 'true');
  });

  it('B-NEW-01: keyboard selects a history conversation and Escape restores the opener', async () => {
    const user = userEvent.setup();
    getMock.mockImplementation(async url => {
      if (url === '/bot/sessions') return { data: [
        { id: 'history-1', title: 'Première session', updated_at: '2026-10-17' },
        { id: 'history-2', title: 'Deuxième session', updated_at: '2026-10-17' },
      ] } as any;
      if (url === '/bot/sessions/history-2/messages') {
        return { data: [{ id: 'response-2', sender: 'bot', text: 'Historique deuxième session' }] } as any;
      }
      return { data: [] } as any;
    });
    renderCrownBot();
    await waitFor(() => expect(getMock).toHaveBeenCalledWith('/bot/sessions'));
    const toggle = screen.getByRole('button', { name: "Ouvrir l'historique Crown Bot" });
    toggle.focus();
    await user.keyboard('{Enter}');
    const close = screen.getByRole('button', { name: "Fermer l'historique Crown Bot" });
    expect(close).toHaveFocus();
    const drawer = document.querySelector('[data-cb01-history-drawer]');
    expect(drawer).not.toHaveAttribute('inert');
    await user.tab();
    expect(screen.getByRole('button', { name: 'Nouvelle conversation' })).toHaveFocus();
    await user.tab();
    expect(screen.getByRole('button', { name: 'Ouvrir la conversation Première session' })).toHaveFocus();
    await user.tab();
    expect(screen.getByRole('button', { name: 'Archiver la conversation Première session' })).toHaveFocus();
    await user.tab();
    expect(screen.getByRole('button', { name: 'Ouvrir la conversation Deuxième session' })).toHaveFocus();
    await user.tab();
    expect(screen.getByRole('button', { name: 'Archiver la conversation Deuxième session' })).toHaveFocus();
    await user.tab();
    expect(close).toHaveFocus(); // Tab wraps inside modal
    await user.keyboard('{Shift>}{Tab}{/Shift}');
    expect(screen.getByRole('button', { name: 'Archiver la conversation Deuxième session' })).toHaveFocus();
    await user.keyboard('{Shift>}{Tab}{/Shift}');
    expect(screen.getByRole('button', { name: 'Ouvrir la conversation Deuxième session' })).toHaveFocus();
    await user.keyboard('{Enter}');
    await waitFor(() => expect(getMock).toHaveBeenCalledWith('/bot/sessions/history-2/messages'));
    expect(await screen.findByText('Historique deuxième session')).toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'Conversation archivée — lecture seule' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Confirmer' })).not.toBeInTheDocument();
    await waitFor(() => expect(toggle).toHaveFocus());
    expect(drawer).toHaveAttribute('inert');

    await user.keyboard('{Enter}');
    expect(screen.getByRole('button', { name: "Fermer l'historique Crown Bot" })).toHaveFocus();
    await user.keyboard('{Escape}');
    expect(toggle).toHaveFocus();
    expect(drawer).toHaveAttribute('inert');
    expect(screen.getByRole('button', { name: "Ouvrir l'historique Crown Bot" })).toHaveAttribute('aria-expanded', 'false');
  });

  it('read-only history hides legacy executable pending actions and returns to business CTA', async () => {
    vi.stubEnv('VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED', 'true');
    getMock.mockImplementation(async (url: string) => {
      if (url === '/bot/sessions') return { data: [
        { id: 'safe-1', title: 'Dossier synthétique', updated_at: '2026-10-17' },
      ] } as any;
      if (url === '/bot/sessions/safe-1/messages') return { data: [
        { id: 15, sender: 'bot', text: 'Proposition historique uniquement',
          pendingActionId: 'sensitive-action', pendingAction: { type: 'CREATE_APPOINTMENT' } },
      ] } as any;
      return { data: [] } as any;
    });
    renderCrownBot();
    fireEvent.click(screen.getByRole('button', { name: "Ouvrir l'historique Crown Bot" }));
    fireEvent.click(await screen.findByRole('button', { name: 'Ouvrir la conversation Dossier synthétique' }));
    expect(await screen.findByText('Proposition historique uniquement')).toBeInTheDocument();
    expect(screen.queryByText('sensitive-action')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /confirmer|exécuter/i })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Retour aux actions' }));
    expect(screen.queryByText('Proposition historique uniquement')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Mon programme' })).toBeInTheDocument();
    expect(postMock).not.toHaveBeenCalledWith('/bot/execute', expect.anything());
  });

  it('a late history A response never overwrites the selected history B', async () => {
    let resolveA: ((value: unknown) => void) | undefined;
    getMock.mockImplementation((url: string): Promise<any> => {
      if (url === '/bot/sessions') return Promise.resolve({data:[
        {id:'a',title:'A',updated_at:'2026-10-17'},
        {id:'b',title:'B',updated_at:'2026-10-17'},
      ]});
      if (url === '/bot/sessions/a/messages') {
        return new Promise(resolve => { resolveA = resolve; });
      }
      if (url === '/bot/sessions/b/messages')
        return Promise.resolve({data:[{id:'b1',sender:'bot',text:'Message B seul'}]});
      return Promise.resolve({data:[]});
    });
    renderCrownBot();
    fireEvent.click(screen.getByRole('button', { name: "Ouvrir l'historique Crown Bot" }));
    fireEvent.click(await screen.findByRole('button', { name: 'Ouvrir la conversation A' }));
    fireEvent.click(screen.getByRole('button', { name: "Ouvrir l'historique Crown Bot" }));
    fireEvent.click(screen.getByRole('button', { name: 'Ouvrir la conversation B' }));
    expect(await screen.findByText('Message B seul')).toBeInTheDocument();
    await act(async () => { resolveA?.({data:[{id:'a1',sender:'bot',text:'Message A obsolète'}]}); });
    expect(screen.queryByText('Message A obsolète')).not.toBeInTheDocument();
    expect(screen.getByText('Message B seul')).toBeInTheDocument();
  });

  it('proves the conversation send/action branch is not reachable from the current Chat tab', async () => {
    renderCrownBot();
    await waitFor(() => expect(getMock).toHaveBeenCalledWith('/bot/sessions'));

    fireEvent.click(screen.getByRole('tab', { name: 'Chat' }));

    expect(screen.getByText("Cette fonction n’est pas accessible depuis cet écran.")).toBeInTheDocument();
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Confirmer' })).not.toBeInTheDocument();
  });

  it('discards stale patient identity and unsent dossier draft when navigating to another patient', async () => {
    vi.stubEnv('VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED', 'true');
    postMock
      .mockResolvedValueOnce({ data: {
        status: 'clarification', message: 'Patient : saisissez un identifiant',
        proposal: null,
      } } as any)
      .mockResolvedValueOnce({ data: {
        status: 'read', message: 'Patient identifié dans votre cabinet.',
        patient: { id: 42, nom: 'ANCIEN', prenom: 'DOSSIER', numero_dossier: 'T2-042' },
        proposal: null,
      } } as any);
    const NavigateSyntheticPatient = () => {
      const navigate=useNavigate();
      return <button onClick={() => navigate('/patients/43')}>Autre dossier synthétique</button>;
    };
    render(
      <MemoryRouter initialEntries={['/patients/42']}>
        <CrownBotChat />
        <NavigateSyntheticPatient />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole('tab', { name: 'Chat', exact: true }));
    const region=screen.getByRole('region', { name: 'Assistant Crown Bot — consultation' });
    fireEvent.click(screen.getByRole('button', { name: 'Trouver un patient' }));
    await screen.findByText('Patient : saisissez un identifiant');
    fireEvent.change(screen.getByRole('textbox', { name: 'Votre réponse de simulation' }), {
      target: { value: 'dossier:T2-042' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Envoyer' }));
    await screen.findByText(/Dossier T2-042/);
    expect(postMock).toHaveBeenLastCalledWith('/bot/workflows/preview', {
      messages: ['/patient', 'dossier:T2-042'],
    });
    // A changed patient route must never show a previous patient's result.
    fireEvent.click(screen.getByRole('button', { name: 'Autre dossier synthétique' }));
    const newRegion=screen.getByRole('region', { name: 'Assistant Crown Bot — consultation' });
    expect(newRegion).not.toBe(region);
    expect(screen.queryByText(/Dossier T2-042/)).not.toBeInTheDocument();
    expect(screen.queryByText('Patient identifié dans votre cabinet.')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Trouver un patient' })).toBeInTheDocument();
    expect(screen.queryByRole('textbox', { name: 'Votre réponse de simulation' })).not.toBeInTheDocument();
    expect(postMock).toHaveBeenCalledTimes(2);
    expect(postMock).not.toHaveBeenCalledWith('/bot/execute', expect.anything());
  });

  it('S10 UX: failed new preview never keeps the previous successful patient response visible', async () => {
    vi.stubEnv('VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED', 'true');
    postMock
      .mockResolvedValueOnce({ data: {
        status: 'read',
        message: 'Patient identifié dans votre cabinet.',
        patient: { id: 42, nom: 'ANCIEN', prenom: 'DOSSIER', numero_dossier: 'T2-042' },
        proposal: null,
      } } as any)
      .mockRejectedValueOnce({ response: { status: 503 } });
    renderCrownBot();
    fireEvent.click(screen.getByRole('tab', { name: 'Chat', exact: true }));
    fireEvent.click(screen.getByRole('button', { name: 'Trouver un patient' }));
    await screen.findByText('Patient identifié dans votre cabinet.');
    expect(screen.getByText(/Dossier T2-042/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Préparer un RDV' }));
    await screen.findByText('Vérification serveur impossible. Aucune action effectuée.');
    expect(screen.queryByText('Patient identifié dans votre cabinet.')).not.toBeInTheDocument();
    expect(screen.queryByText(/Dossier T2-042/)).not.toBeInTheDocument();
    expect(screen.queryByText('Étapes saisies : 1/8')).not.toBeInTheDocument();
    expect(postMock).toHaveBeenLastCalledWith('/bot/workflows/preview', { messages: ['/rdv'] });
    expect(postMock).not.toHaveBeenCalledWith('/bot/execute', expect.anything());
  });

  it('exposes safe ZERO-LLM preview inside existing mobile-responsive Chat only when frontend opt-in is explicit', async () => {
    vi.stubEnv('VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED', 'true');
    postMock.mockResolvedValue({ data: {
      status: 'clarification', message: 'Identifiant numérique du patient ?',
    } } as any);
    renderCrownBot();
    await waitFor(() => expect(getMock).toHaveBeenCalledWith('/bot/sessions'));
    // FIRST_VALUE_UI already starts on Chat. Clicking a second time is not required.
    expect(screen.getByRole('tab', { name: 'Chat' })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('region', { name: 'Assistant Crown Bot — consultation' })).toBeInTheDocument();
    expect(screen.getByText(/aucune écriture/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Préparer un RDV' }));
    await waitFor(() => expect(postMock).toHaveBeenCalledWith(
      '/bot/workflows/preview', { messages: ['/rdv'] },
    ));
    await screen.findByText('Identifiant numérique du patient ?');
    expect(postMock).toHaveBeenCalledWith('/bot/workflows/preview', {
      messages: ['/rdv'],
    });
    expect(postMock).not.toHaveBeenCalledWith('/bot/execute', expect.anything());
    expect(screen.queryByRole('button', { name: 'Confirmer' })).not.toBeInTheDocument();
  });

});
