import React, { useState, useRef, useEffect } from 'react';
import {
  Send, X, Bot, User, Check, XCircle, Loader2, Menu, Plus,
  Archive, BrainCircuit, Zap, ArrowRight, MessageSquare, Crown, Sparkles,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { api, API_BASE, getRuntimeAuthToken } from '../../services/api';
import { mobileFetch } from '../../services/zka/mobileFetch';
import { useAuthStore } from '../../stores/useAuthStore';
import { cn } from '../../utils/cn';
import { CrownBotWorkflowPreview } from './CrownBotWorkflowPreview';
import { CrownBotGuidedConversationG5 } from './CrownBotGuidedConversationG5';

interface Message {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  actionType?: string;
  pendingAction?: any;
  pendingActionId?: string;
  suggestions?: string[];
  showUpsell?: boolean;
}

interface Session {
  id: string;
  title: string;
  updated_at: string;
}

interface GhostInsight {
  id: number;
  insight_type: string;
  content: string;
  patient_id?: number;
  created_at: string;
}

type Tab = 'chat' | 'brain';

const buildGhostBrainWsUrl = (employerId: number | string) => {
  const baseUrl = `${API_BASE.replace(/^http/, 'ws')}/api/ai/ws/ghost-insights/${employerId}`;
  const token = getRuntimeAuthToken();
  return token ? `${baseUrl}?token=${encodeURIComponent(token)}` : baseUrl;
};

function PendingActionCard({
  action,
  onConfirm,
  onCancel,
}: {
  action: any;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const p = action?.params ?? {};
  const type = action?.type ?? '';

  const rows: { label: string; value: string }[] = [];

  if (type === 'CREATE_APPOINTMENT') {
    if (p.patient_name || p.patient_id) rows.push({ label: 'Patient', value: p.patient_name || `#${p.patient_id}` });
    if (p.datetime_start) {
      const d = new Date(p.datetime_start);
      rows.push({ label: 'Date', value: d.toLocaleDateString('fr-FR', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' }) });
      rows.push({ label: 'Heure', value: d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) });
    }
    if (p.motif) rows.push({ label: 'Motif', value: p.motif });
    if (p.duration_minutes) rows.push({ label: 'Durée', value: `${p.duration_minutes} min` });
  } else if (type === 'OPEN_PRESCRIPTION_EDITOR') {
    if (p.patient_id || p.patient_name) rows.push({ label: 'Patient', value: p.patient_name || `#${p.patient_id}` });
    if (p.procedure) rows.push({ label: 'Acte', value: p.procedure });
    if (p.suggested_drugs?.length) {
      rows.push({ label: 'Médicaments', value: p.suggested_drugs.map((d: any) => d.name || d).join(', ') });
    }
  } else if (type === 'OPEN_DEVIS_EDITOR') {
    if (p.patient_id || p.patient_name) rows.push({ label: 'Patient', value: p.patient_name || `#${p.patient_id}` });
    if (p.procedure) rows.push({ label: 'Acte', value: p.procedure });
    if (p.tooth_number) rows.push({ label: 'Dent', value: p.tooth_number });
  }

  const label = type === 'CREATE_APPOINTMENT' ? '📅 Créer ce rendez-vous ?'
    : type === 'OPEN_PRESCRIPTION_EDITOR' ? '💊 Ouvrir l\'éditeur d\'ordonnance ?'
    : type === 'OPEN_DEVIS_EDITOR' ? '📄 Ouvrir le module devis ?'
    : '✅ Confirmer cette action ?';

  return (
    <div className="mt-4 p-3 bg-warning-surface border border-warning-border rounded-[12px]">
      <p className="text-xs font-bold text-warning mb-2">{label}</p>
      {rows.length > 0 && (
        <div className="space-y-1 mb-3">
          {rows.map((row, i) => (
            <div key={i} className="flex items-start gap-2 text-xs">
              <span className="text-warning font-bold w-20 shrink-0">{row.label}</span>
              <span className="text-text-main font-medium">{row.value}</span>
            </div>
          ))}
        </div>
      )}
      <div className="flex gap-2">
        <button onClick={onConfirm}
          className="flex-1 flex items-center justify-center gap-1.5 py-1.5 bg-primary hover:bg-secondary text-on-primary text-xs font-bold rounded-[8px] transition-colors">
          <Check size={14} /> Confirmer
        </button>
        <button onClick={onCancel}
          className="flex-1 flex items-center justify-center gap-1.5 py-1.5 bg-input-field hover:bg-input-field text-text-main text-xs font-bold rounded-[8px] transition-colors">
          <XCircle size={14} /> Annuler
        </button>
      </div>
    </div>
  );
}

function PremiumUpsellCard({ onClose }: { onClose: () => void }) {
  return (
    <div className="mt-4 rounded-[16px] overflow-hidden border border-warning-border shadow-lg">
      {/* Header gradient */}
      <div className="bg-gradient-to-r from-primary to-secondary px-4 py-3 flex items-center gap-2">
        <div className="w-7 h-7 rounded-full bg-on-primary/20 flex items-center justify-center shrink-0">
          <Crown size={14} className="text-on-primary" />
        </div>
        <div>
          <p className="text-on-primary font-black text-xs tracking-wide leading-none">Crown Bot Premium</p>
          <p className="text-on-primary/75 text-xs mt-0.5">Limite de l’assistant atteinte</p>
        </div>
      </div>

      {/* Body */}
      <div className="bg-warning-surface px-4 py-3">
        <p className="text-warning text-xs font-semibold mb-2 leading-relaxed">
          Vous avez utilisé vos <strong>3 échanges</strong> gratuits. Passez à Premium pour des conversations illimitées.
        </p>
        <ul className="space-y-1 mb-3">
          {[
            'Conversations avec l’assistant',
            'Mémoire contextuelle étendue',
            'Actions avancées (ordonnances et devis)',
          ].map((item) => (
            <li key={item} className="flex items-start gap-1.5 text-xs text-warning font-medium">
              <Sparkles size={10} className="text-warning mt-0.5 shrink-0" />
              {item}
            </li>
          ))}
        </ul>
        <div className="flex gap-2">
          <a
            href="/settings?tab=license"
            className="flex-1 flex items-center justify-center gap-1.5 py-2 bg-gradient-to-r from-primary to-secondary hover:from-secondary hover:to-primary text-on-primary text-xs font-black rounded-[8px] transition-all shadow-md shadow-elite"
          >
            <Crown size={12} /> Passer à Premium
          </a>
          <button
            onClick={onClose}
            className="px-3 py-2 bg-warning-surface hover:bg-warning-border text-warning text-xs font-bold rounded-[8px] transition-colors"
          >
            Plus tard
          </button>
        </div>
      </div>
    </div>
  );
}

const TypewriterText = ({ text, delay = 5 }: { text: string; delay?: number }) => {
  const [current, setCurrent] = useState('');
  const [idx, setIdx] = useState(0);
  useEffect(() => {
    if (idx < text.length) {
      const t = setTimeout(() => {
        setCurrent(p => p + text[idx]);
        setIdx(p => p + 1);
      }, delay);
      return () => clearTimeout(t);
    }
  }, [idx, delay, text]);
  return <span>{current}</span>;
};

function getPageContext(pathname: string): { title: string; desc: string; suggestions: string[] } {
  if (pathname === '/' || pathname === '/dashboard') return {
    title: 'Tableau de bord',
    desc: "Vous êtes sur le tableau de bord. Je peux vous résumer votre journée, vos rendez-vous ou les finances du jour.",
    suggestions: ['Mon programme du jour', 'Finances du jour', 'Créer un RDV'],
  };
  if (/^\/patients\/new/.test(pathname)) return {
    title: 'Nouveau patient',
    desc: "Vous créez un nouveau dossier patient. Besoin d'aide pour remplir les informations ou choisir les motifs de consultation ?",
    suggestions: ['Quels motifs choisir ?', 'Aide à la saisie', 'Champs obligatoires'],
  };
  if (/^\/patients\/\d+/.test(pathname)) return {
    title: 'Dossier patient',
    desc: "Vous consultez un dossier patient. Je peux analyser le plan de traitement, suggérer des actes ou résumer l'historique.",
    suggestions: ['Résumer le dossier', 'Suggérer des actes', 'Vérifier le plan de traitement'],
  };
  if (/^\/patients/.test(pathname)) return {
    title: 'Liste des patients',
    desc: "Vous êtes sur la liste des patients. Je peux vous aider à trouver un patient ou filtrer par statut.",
    suggestions: ['Chercher un patient', 'Patients sans RDV', 'Patients urgents'],
  };
  if (/^\/agenda/.test(pathname)) return {
    title: 'Agenda',
    desc: "Vous gérez l'agenda. Je peux vous aider à créer un rendez-vous, vérifier les disponibilités ou lister les absences.",
    suggestions: ['Créer un RDV', 'Disponibilités du jour', 'RDV annulés'],
  };
  if (/^\/accounting/.test(pathname)) return {
    title: 'Comptabilité',
    desc: "Vous êtes dans la comptabilité. Je peux vous résumer la trésorerie, les impayés ou les recettes du mois.",
    suggestions: ['Résumé trésorerie', 'Impayés en cours', 'Recettes du mois'],
  };
  if (/^\/settings/.test(pathname)) return {
    title: 'Paramètres',
    desc: "Vous configurez le cabinet. Besoin d'aide pour la facturation, le branding ou les préférences de l’assistant ?",
    suggestions: ['Configurer la facturation', 'Branding du cabinet', 'Paramètres de l’assistant'],
  };
  if (/^\/bibliotheque/.test(pathname)) return {
    title: 'Bibliothèque',
    desc: "Vous êtes dans la bibliothèque de documents. Je peux vous aider à créer une ordonnance, un certificat ou un courrier.",
    suggestions: ['Créer une ordonnance', 'Générer un certificat', 'Rédiger un courrier'],
  };
  return {
    title: 'Crown Bot',
    desc: "Bonjour ! Je suis Crown Bot, votre assistant. Comment puis-je vous aider ?",
    suggestions: ['Mon programme du jour', 'Créer un RDV', 'Finance du jour'],
  };
}

export function CrownBotChat({
  onClose,
  onUnreadChange,
}: {
  onClose?: () => void;
  onUnreadChange?: (n: number) => void;
}) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const employerId = user?.employer_id || user?.id;
  const ghostScopeKey = `${employerId ?? ''}:${user?.id ?? ''}`;
  const ghostEpochRef = useRef(0);

  const pageCtx = getPageContext(location.pathname);
  // Explicit opt-in on BOTH frontend and server. OFF means the existing screen
  // remains untouched. Backend independently rejects preview when flag is OFF.
  const zeroLlmPreviewEnabled = import.meta.env.VITE_CROWN_BOT_WORKFLOW_PREVIEW_ENABLED === 'true';
  // G5 adds a deterministic chat *inside this real floating/sidecar CrownBot*.
  // Four independent opt-ins are needed; default OFF preserves existing UX.
  const guidedChatEnabled = zeroLlmPreviewEnabled
    && import.meta.env.VITE_CROWN_BOT_GUIDED_NLU_ENABLED === 'true'
    && import.meta.env.VITE_CROWN_BOT_CB03_G3_ENABLED === 'true'
    && import.meta.env.VITE_CROWN_BOT_CB03_CHAT_ENABLED === 'true';

  // Chat state
  const [messages, setMessages] = useState<Message[]>([{
    id: 'welcome', sender: 'bot', text: pageCtx.desc, suggestions: pageCtx.suggestions,
  }]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const historyRequestEpoch = useRef(0);
  const [historyBusy, setHistoryBusy] = useState(false);
  const [historyError, setHistoryError] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const historyToggleRef = useRef<HTMLButtonElement>(null);
  const historyDrawerRef = useRef<HTMLDivElement>(null);
  const historyCloseRef = useRef<HTMLButtonElement>(null);
  const brainTabRef = useRef<HTMLButtonElement>(null);
  const chatTabRef = useRef<HTMLButtonElement>(null);
  const selectTabFromKeyboard = (event: React.KeyboardEvent<HTMLButtonElement>, current: Tab) => {
    let next: Tab;
    switch (event.key) {
      case 'ArrowRight': next = current === 'brain' ? 'chat' : 'brain'; break;
      case 'ArrowLeft': next = current === 'brain' ? 'chat' : 'brain'; break;
      case 'Home': next = 'brain'; break;
      case 'End': next = 'chat'; break;
      default: return;
    }
    event.preventDefault();
    setActiveTab(next);
    (next === 'brain' ? brainTabRef : chatTabRef).current?.focus();
  };
  const historyWasOpenRef = useRef(false);
  useEffect(() => {
    if (isSidebarOpen) {
      historyCloseRef.current?.focus();
    } else if (historyWasOpenRef.current) {
      // Return focus after Escape, selection or the close button. It remains
      // visible in both sidecar and floating web layouts.
      historyToggleRef.current?.focus();
    }
    historyWasOpenRef.current = isSidebarOpen;
  }, [isSidebarOpen]);

  // Tab & Mémoire contextuelle state
  // First value in one click when experimental preview is explicitly ON:
  // display the three useful read-only actions immediately after opening.
  // Flag OFF preserves the legacy contextual memory tab unchanged.
  const [activeTab, setActiveTab] = useState<Tab>(guidedChatEnabled || zeroLlmPreviewEnabled ? 'chat' : 'brain');
  // One atomic server snapshot; never decrement the unread badge without
  // removing the corresponding insight from the same authoritative version.
  const [ghostState, setGhostState] = useState<{
    scopeKey: string; insights: GhostInsight[]; unreadCount: number
  }>({ scopeKey: '', insights: [], unreadCount: 0 });
  const { insights, unreadCount } = ghostState.scopeKey === ghostScopeKey
    ? ghostState : { insights: [], unreadCount: 0 };

  useEffect(() => {
    setGhostState({ scopeKey: ghostScopeKey, insights: [], unreadCount: 0 });
    return () => { ghostEpochRef.current += 1; };
  }, [ghostScopeKey]);

  // Reset welcome message when route changes
  useEffect(() => {
    const ctx = getPageContext(location.pathname);
    setMessages([{ id: 'welcome', sender: 'bot', text: ctx.desc, suggestions: ctx.suggestions }]);
    setCurrentSessionId(null);
    historyRequestEpoch.current += 1;
    setHistoryBusy(false);
    setHistoryError('');
  }, [location.pathname]);

  // Propagate unread count to parent
  useEffect(() => {
    onUnreadChange?.(unreadCount);
  }, [unreadCount, onUnreadChange]);

  // Mémoire contextuelle WebSocket
  useEffect(() => {
    if (!employerId) return;
    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let isCleaned = false;
    let retryCount = 0;
    const MAX_RETRIES = 8;

    const connectWS = () => {
      if (isCleaned || retryCount >= MAX_RETRIES) return;
      const wsUrl = buildGhostBrainWsUrl(employerId);
      const currentSocket = new WebSocket(wsUrl);
      ws = currentSocket;
      ws.onopen = () => {
        if (!isCleaned && ws === currentSocket) retryCount = 0;
      };
      ws.onmessage = (event) => {
        // Disposed tenant sockets and abandoned reconnects cannot push
        // patient alerts into the current principal's browser session.
        if (isCleaned || ws !== currentSocket) return;
        try {
          const data = JSON.parse(event.data);
          if (Array.isArray(data.insights) && Number.isSafeInteger(data.unread_count)
              && data.unread_count >= 0) {
            setGhostState({
              scopeKey: ghostScopeKey,
              insights: data.insights,
              unreadCount: data.unread_count,
            });
          }
        } catch (err) {
          console.error('GhostBrain WS parse error:', err);
        }
      };
      ws.onclose = () => {
        if (isCleaned || ws !== currentSocket) return;
        retryCount++;
        reconnectTimer = setTimeout(connectWS, Math.min(5000 * retryCount, 60000));
      };
    };

    connectWS();
    return () => {
      isCleaned = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (ws) { ws.onclose = null; ws.close(); }
    };
  }, [employerId, ghostScopeKey]);

  // Chat scroll
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  // Sessions
  const fetchSessions = async () => {
    try {
      const res = await api.get('/bot/sessions');
      setSessions(res.data);
    } catch (err) {
      console.error('Sessions fetch error:', err);
    }
  };
  useEffect(() => { fetchSessions(); }, []);

  const startNewSession = () => {
    historyRequestEpoch.current += 1;
    setCurrentSessionId(null);
    setHistoryBusy(false);
    setHistoryError('');
    setActiveTab(guidedChatEnabled || zeroLlmPreviewEnabled ? 'chat' : 'brain');
    const ctx = getPageContext(location.pathname);
    setMessages([{ id: 'welcome', sender: 'bot', text: ctx.desc, suggestions: ctx.suggestions }]);
    setIsSidebarOpen(false);
  };

  const loadSession = async (id: string) => {
    const epoch = ++historyRequestEpoch.current;
    setHistoryBusy(true);
    setHistoryError('');
    setCurrentSessionId(null);
    setActiveTab('chat');
    setIsSidebarOpen(false);
    try {
      const res = await api.get(`/bot/sessions/${encodeURIComponent(id)}/messages`);
      if (epoch !== historyRequestEpoch.current) return;
      if (!Array.isArray(res.data) || !res.data.every((m: unknown) => {
        const row = m as { id?: unknown; sender?: unknown; text?: unknown };
        return (typeof row.id === 'string' || typeof row.id === 'number')
          && typeof row.text === 'string'
          && ['user', 'bot', 'assistant'].includes(String(row.sender));
      })) throw new Error('Invalid history response');
      // Read-only text only; legacy pending action IDs must never be revived.
      setMessages(res.data.map((m: {id: string | number;sender: string;text: string}) => ({
        id: String(m.id), sender: m.sender === 'user' ? 'user' : 'bot', text: m.text,
      })));
      setCurrentSessionId(id);
    } catch {
      if (epoch === historyRequestEpoch.current) {
        setMessages([]);
        setHistoryError('Historique indisponible. Aucun ancien message affiché.');
      }
    } finally {
      if (epoch === historyRequestEpoch.current) setHistoryBusy(false);
    }
  };

  const archiveSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.delete(`/bot/sessions/${id}`);
      setSessions(prev => prev.filter(s => s.id !== id));
      if (currentSessionId === id) startNewSession();
    } catch (err) {
      console.error('Session archive error:', err);
    }
  };

  const handleSend = async (text: string) => {
    if (!text.trim()) return;
    setMessages(prev => [...prev, { id: Date.now().toString(), sender: 'user', text }]);
    setInput('');
    setIsLoading(true);

    const botId = (Date.now() + 1).toString();
    let botText = '';
    let placeholderAdded = false;

    const ensurePlaceholder = () => {
      if (placeholderAdded) return;
      placeholderAdded = true;
      setIsLoading(false);
      setMessages(prev => [...prev, { id: botId, sender: 'bot', text: '' }]);
    };
    const updateBot = (patch: Partial<Message>) =>
      setMessages(prev => prev.map(m => (m.id === botId ? { ...m, ...patch } : m)));

    // Contexte patient : si on est sur un dossier patient, on rattache la conversation
    const patientMatch = location.pathname.match(/^\/patients\/(\d+)/);
    const patientId = patientMatch ? Number(patientMatch[1]) : undefined;

    try {
      const token = getRuntimeAuthToken();
      const requestInit: RequestInit = {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        credentials: location.pathname.startsWith('/mobile') ? 'omit' : 'include',
        body: JSON.stringify({
          message: text,
          ...(currentSessionId ? { session_id: currentSessionId } : {}),
          ...(patientId ? { patient_id: patientId } : {}),
        }),
      };
      const res = location.pathname.startsWith('/mobile')
        ? await mobileFetch(`${API_BASE}/api/bot/chat/stream`, requestInit)
        : await fetch(`${API_BASE}/api/bot/chat/stream`, requestInit);
      if (!res.ok || !res.body) throw new Error(`stream ${res.status}`);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const parts = buf.split('\n\n');
        buf = parts.pop() || '';
        for (const part of parts) {
          const line = part.split('\n').find(l => l.startsWith('data:'));
          if (!line) continue;
          let evt: any;
          try { evt = JSON.parse(line.slice(5).trim()); } catch { continue; }

          if (evt.type === 'session') {
            if (evt.session_id && evt.session_id !== currentSessionId) setCurrentSessionId(evt.session_id);
          } else if (evt.type === 'token') {
            ensurePlaceholder();
            botText += evt.content;
            updateBot({ text: botText });
          } else if (evt.type === 'final') {
            ensurePlaceholder();
            updateBot({
              text: evt.message ?? botText,
              actionType: evt.action_type,
              pendingAction: evt.pending_action,
              pendingActionId: evt.pending_action_id,
              suggestions: evt.suggestions,
              showUpsell: evt.show_upsell === true,
            });
            if (evt.session_id && evt.session_id !== currentSessionId) setCurrentSessionId(evt.session_id);
            fetchSessions();
          } else if (evt.type === 'error') {
            ensurePlaceholder();
            botText = evt.message || "Désolé, une erreur est survenue.";
            updateBot({ text: botText });
          }
        }
      }
    } catch (err) {
      console.error('Bot stream error:', err);
      if (!placeholderAdded) {
        setMessages(prev => [...prev, { id: botId, sender: 'bot', text: "Désolé, je n'ai pas pu traiter votre demande." }]);
      } else {
        updateBot({ text: botText || "Désolé, je n'ai pas pu traiter votre demande." });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const dismissUpsell = (msgId: string) => {
    setMessages(prev => prev.map(m => m.id === msgId ? { ...m, showUpsell: false } : m));
  };

  const handleConfirmAction = async (msgId: string, _actionData: any, actionId?: string) => {
    if (!actionId) {
      setMessages(prev => [...prev, { id: Date.now().toString(), sender: 'bot', text: "Action expirée ou non retrouvée. Veuillez reformuler votre demande." }]);
      return;
    }
    setMessages(prev => prev.map(m =>
      m.id === msgId ? { ...m, pendingAction: null, pendingActionId: undefined, text: m.text + '\n\n*Action confirmée en cours...*' } : m,
    ));
    setIsLoading(true);
    try {
      const res = await api.post('/bot/execute', { pending_action_id: actionId });
      const data = res.data;

      // Redirect si l'action ouvre un module (prescription, devis)
      if (data.action_type === 'redirect' && data.data?.redirect_url) {
        navigate(data.data.redirect_url);
        onClose?.();
        return;
      }

      setMessages(prev => [...prev, {
        id: Date.now().toString(), sender: 'bot',
        text: data.message || "Action exécutée avec succès.",
      }]);
    } catch {
      setMessages(prev => [...prev, {
        id: Date.now().toString(), sender: 'bot',
        text: "Erreur lors de l'exécution de l'action.",
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Mémoire contextuelle actions
  const markAsRead = async (logId: number) => {
    const requestEpoch = ghostEpochRef.current;
    try {
      const receipt = await api.post(`/ai/ghost-insights/${logId}/read`);
      if (receipt?.data?.status !== 'read') {
        throw new Error('GhostBrain read acknowledgement missing');
      }
      setGhostState(previous => {
        // A late ACK from an obsolete principal or an older WS snapshot
        // must never acknowledge a different patient's notification.
        if (ghostEpochRef.current !== requestEpoch
            || previous.scopeKey !== ghostScopeKey
            || !previous.insights.some(insight => insight.id === logId)) {
          return previous;
        }
        return {
          scopeKey: previous.scopeKey,
          insights: previous.insights.filter(insight => insight.id !== logId),
          unreadCount: Math.max(0, previous.unreadCount - 1),
        };
      });
    } catch (err) {
      console.error('markAsRead error:', err);
    }
  };

  const markAllRead = () => { insights.forEach(i => markAsRead(i.id)); };

  const getQuickAction = (insight: GhostInsight) => {
    const text = insight.content.toLowerCase();
    if (text.includes('échéance') || text.includes('impayé') || text.includes('encaissement'))
      return { label: 'Voir Trésorerie', icon: <Zap size={10} />, onClick: () => { navigate('/accounting?tab=treasury'); onClose?.(); markAsRead(insight.id); } };
    if (text.includes('rendez-vous') || text.includes('absent'))
      return { label: 'Voir Agenda', icon: <Zap size={10} />, onClick: () => { navigate('/agenda'); onClose?.(); markAsRead(insight.id); } };
    if (insight.patient_id)
      return { label: 'Dossier Patient', icon: <ArrowRight size={10} />, onClick: () => { navigate(`/patients/${insight.patient_id}`); onClose?.(); markAsRead(insight.id); } };
    return null;
  };

  return (
    <div className="flex flex-col h-full bg-card shadow-2xl rounded-t-[24px] sm:rounded-[24px] overflow-hidden border border-border-main relative z-50">

      {/* Sidebar overlay */}
      {isSidebarOpen && (
        <div className="absolute inset-0 bg-black/20 z-40" onClick={() => setIsSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <div data-cb01-history-drawer
        ref={historyDrawerRef}
        role="dialog"
        aria-modal={isSidebarOpen}
        aria-label="Historique Crown Bot"
        inert={!isSidebarOpen}
        aria-hidden={!isSidebarOpen}
        onKeyDown={event => {
          if (isSidebarOpen && event.key === 'Tab') {
            const buttons = Array.from(historyDrawerRef.current?.querySelectorAll<HTMLButtonElement>(
              'button:not([disabled])',
            ) ?? []);
            if (buttons.length) {
              const first = buttons[0], last = buttons[buttons.length - 1];
              if (event.shiftKey && document.activeElement === first) {
                event.preventDefault();
                last.focus();
              } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault();
                first.focus();
              }
            }
          }
          // Do not propagate Escape to the enclosing desktop sidecar:
          // closing History must not close the whole Crown Bot panel.
          if (isSidebarOpen && event.key === 'Escape') {
            event.preventDefault();
            event.stopPropagation();
            setIsSidebarOpen(false);
          }
        }}
        className={cn(
          'absolute left-0 top-0 bottom-0 w-64 bg-background border-r border-border-main z-50 flex flex-col transition-transform duration-300',
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full',
        )}>
        <div className="p-4 border-b border-border-main flex items-center justify-between">
          <h3 className="font-semibold text-text-main">Historique</h3>
          <button type="button" ref={historyCloseRef} aria-label="Fermer l'historique Crown Bot" onClick={() => setIsSidebarOpen(false)} className="min-h-11 min-w-11 rounded-md p-2 hover:bg-input-field focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">
            <X size={16} className="text-text-muted" />
          </button>
        </div>
        <div className="p-2">
          <button onClick={startNewSession} className="w-full flex items-center gap-2 px-3 py-2 bg-card border border-border-main hover:border-primary hover:text-primary rounded-lg text-sm font-medium transition-colors">
            <Plus size={16} /> Nouvelle conversation
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.length === 0
            ? <p className="text-xs text-center text-text-muted mt-4">Aucune conversation</p>
            : sessions.map(session => (
              <div key={session.id}
                className={cn('group flex items-center gap-1 p-1 rounded-lg transition-colors',
                  currentSessionId === session.id ? 'bg-primary/10 text-primary' : 'hover:bg-input-field text-text-main')}
              >
                <button type="button" onClick={() => { void loadSession(session.id); }}
                  aria-label={`Ouvrir la conversation ${session.title}`}
                  className="flex min-h-11 min-w-0 flex-1 items-center gap-2 rounded-md p-2 text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">
                  <MessageSquare size={14} className="shrink-0" />
                  <span className="text-sm truncate">{session.title}</span>
                </button>
                <button type="button" onClick={(e) => {
                    if (window.confirm(`Archiver « ${session.title} » ? Cette conversation ne sera plus accessible depuis l'historique.`)) {
                      void archiveSession(session.id, e);
                    }
                  }}
                  aria-label={`Archiver la conversation ${session.title}`}
                  className="min-h-11 min-w-11 rounded-md p-2 text-text-muted hover:text-danger focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">
                  <Archive size={14} />
                </button>
              </div>
            ))
          }
        </div>
      </div>

      {/* Header + tabs */}
      <div className="flex flex-col bg-primary text-on-primary shrink-0">
        <div className="flex items-center justify-between px-4 pt-4 pb-2">
          <div className="flex items-center gap-3">
            <button type="button" ref={historyToggleRef} aria-label="Ouvrir l'historique Crown Bot" aria-expanded={isSidebarOpen} onClick={() => setIsSidebarOpen(true)} className="min-h-11 min-w-11 p-2 -ml-2 hover:bg-on-primary/10 rounded-full transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-white">
              <Menu size={18} />
            </button>
            <div className="w-8 h-8 rounded-full bg-on-primary/20 flex items-center justify-center">
              <Bot size={18} />
            </div>
            <div>
              <h3 className="font-bold font-outfit text-sm leading-tight">Crown Bot</h3>
              <p className="text-xs text-on-primary/90">{pageCtx.title}</p>
            </div>
          </div>
          {onClose && (
            <button type="button" aria-label="Fermer Crown Bot" onClick={onClose} className="min-h-11 min-w-11 p-2 bg-on-primary/10 hover:bg-on-primary/20 rounded-full transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-white">
              <X size={16} />
            </button>
          )}
        </div>

        {/* Two keyboard-operable tabs: Arrow keys/Home/End select and focus. */}
        <div className="flex px-4 gap-1" role="tablist" aria-label="Vues de Crown Bot">
          <button type="button" ref={brainTabRef} role="tab"
            id="cb01-tab-brain" aria-controls={activeTab === 'brain' ? 'cb01-panel-brain' : undefined}
            aria-selected={activeTab === 'brain'} tabIndex={activeTab === 'brain' ? 0 : -1}
            onKeyDown={event => selectTabFromKeyboard(event, 'brain')}
            onClick={() => setActiveTab('brain')}
            className={cn('flex min-h-11 items-center gap-1.5 px-3 py-2 text-xs font-bold rounded-t-lg transition-colors relative focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white',
              activeTab === 'brain' ? 'bg-on-primary/20 text-on-primary' : 'text-on-primary/90 hover:bg-on-primary/10 hover:text-on-primary')}
          >
            <BrainCircuit size={15} aria-hidden="true" /> Mémoire contextuelle
            {unreadCount > 0 && (
              <span aria-label={`${unreadCount} nouvelles alertes`}
                className="ml-1 flex min-h-5 min-w-5 items-center justify-center rounded-full bg-warning px-1 text-xs font-bold text-text-main">
                {unreadCount}
              </span>
            )}
          </button>
          <button type="button" ref={chatTabRef} role="tab"
            id="cb01-tab-chat" aria-controls={activeTab === 'chat' ? 'cb01-panel-chat' : undefined}
            aria-selected={activeTab === 'chat'} tabIndex={activeTab === 'chat' ? 0 : -1}
            onKeyDown={event => selectTabFromKeyboard(event, 'chat')}
            onClick={() => setActiveTab('chat')}
            className={cn('flex min-h-11 items-center gap-1.5 px-3 py-2 text-xs font-bold rounded-t-lg transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white',
              activeTab === 'chat' ? 'bg-on-primary/20 text-on-primary' : 'text-on-primary/90 hover:bg-on-primary/10 hover:text-on-primary')}
          >
            <MessageSquare size={15} aria-hidden="true" /> Chat
          </button>
        </div>
      </div>

      {/* ── TAB: CHAT — Bientôt disponible ── */}
      {activeTab === 'chat' && (historyBusy || !!historyError || !!currentSessionId) && (
        <section role="tabpanel" id="cb01-panel-chat" aria-labelledby="cb01-tab-chat"
          className="min-h-0 flex-1 overflow-y-auto bg-background p-4">
          <div role="region" aria-label="Conversation archivée — lecture seule">
          <div className="mb-3 flex items-center justify-between gap-2">
            <div>
              <h4 className="text-sm font-bold text-text-main">Historique · lecture seule</h4>
              <p className="text-xs text-text-muted">
                {sessions.find(s => s.id === currentSessionId)?.title || 'Conversation sélectionnée'}
              </p>
            </div>
            <button type="button" onClick={startNewSession}
              className="min-h-11 rounded-lg border border-border-main bg-card px-3 text-xs font-semibold text-text-main">
              Retour aux actions
            </button>
          </div>
          {historyBusy && <p role="status">Chargement de la conversation…</p>}
          {historyError && <p role="alert" className="text-danger">{historyError}</p>}
          {!historyBusy && !historyError && currentSessionId && (
            <ol aria-label="Messages historiques" className="space-y-2">
              {messages.length ? messages.map(message => (
                <li key={message.id} className="rounded-lg border border-border-main bg-card p-3">
                  <p className="text-xs font-semibold text-text-muted">
                    {message.sender === 'user' ? 'Vous' : 'Crown Bot'}
                  </p>
                  <p className="whitespace-pre-wrap break-words text-sm text-text-main">{message.text}</p>
                </li>
              )) : <li className="text-sm text-text-muted">Aucun message dans cette conversation.</li>}
            </ol>
          )}
          </div>
        </section>
      )}
      {activeTab === 'chat' && !historyBusy && !historyError && !currentSessionId && guidedChatEnabled && (
        // This is the genuine bottom-right CrownBotChat instance mounted by
        // MainLayout, not a standalone G3 test form or a forged chat history.
        <div role="tabpanel" id="cb01-panel-chat" aria-labelledby="cb01-tab-chat"
          className="flex min-h-0 min-w-0 flex-1 flex-col">
          <CrownBotGuidedConversationG5
            key={`${user?.id ?? 'unknown'}:${employerId ?? 'unknown'}:${location.pathname}`}
            practitionerId={user?.role === 'DENTISTE' ? Number(user.id) : undefined}
          />
        </div>
      )}
      {activeTab === 'chat' && !historyBusy && !historyError && !currentSessionId && !guidedChatEnabled && zeroLlmPreviewEnabled && (
        // Clinical safety: route or staff identity changes invalidate a prior
        // patient's scoped read/proposal. A responsive 200% reflow leaves the
        // key unchanged and therefore preserves the unfinished draft.
        <div role="tabpanel" id="cb01-panel-chat" aria-labelledby="cb01-tab-chat"
          className="flex min-h-0 min-w-0 flex-1 flex-col">
          <CrownBotWorkflowPreview
            key={`${user?.id ?? 'unknown'}:${employerId ?? 'unknown'}:${location.pathname}`}
            practitionerId={user?.role === 'DENTISTE' ? Number(user.id) : undefined}
            requirePractitioner={user?.role === 'DENTISTE'}
          />
        </div>
      )}
      {activeTab === 'chat' && !historyBusy && !historyError && !currentSessionId && !guidedChatEnabled && !zeroLlmPreviewEnabled && (
        <div role="tabpanel" id="cb01-panel-chat" aria-labelledby="cb01-tab-chat"
          className="flex-1 flex flex-col items-center justify-center gap-6 p-8 bg-background">
          <div className="relative">
            <div className="w-20 h-20 rounded-[2rem] bg-gradient-to-tr from-primary/20 to-secondary/20 flex items-center justify-center shadow-inner border border-border-main">
              <MessageSquare size={36} className="text-primary/40" />
            </div>
            
          </div>

          <div className="text-center space-y-2">
            <h3 className="font-black text-text-main text-sm tracking-tight">Assistant conversationnel</h3>
            <p className="text-xs text-text-muted leading-relaxed max-w-[220px]">
              Cette fonction n’est pas accessible depuis cet écran.
            </p>
          </div>

          <div className="flex flex-col gap-2 w-full max-w-[240px]">
            {['Créer un RDV', 'Résumer un dossier', 'Générer une ordonnance'].map((item) => (
              <div key={item} className="flex items-center gap-2.5 px-4 py-2.5 bg-card border border-border-main rounded-xl opacity-40 cursor-not-allowed select-none">
                <Sparkles size={13} className="text-primary shrink-0" />
                <span className="text-xs font-semibold text-text-muted">{item}</span>
              </div>
            ))}
          </div>

          <p className="text-xs text-text-muted font-bold uppercase tracking-widest">
            Assistant Digital Crown
          </p>
        </div>
      )}

      {/* ── TAB: GHOST BRAIN ── */}
      {activeTab === 'brain' && (
        <div role="tabpanel" id="cb01-panel-brain" aria-labelledby="cb01-tab-brain"
          className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar bg-background">
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center text-primary relative">
                <div className="absolute inset-0 bg-primary/20 rounded-full animate-ping opacity-40" />
                <BrainCircuit size={14} />
              </div>
              <div>
                <p className="text-xs font-black text-primary uppercase tracking-widest leading-none">Mémoire contextuelle</p>
                <p className="text-xs text-text-muted font-bold mt-0.5">Suivi contextuel</p>
              </div>
            </div>
            {unreadCount > 0 && (
              <button onClick={markAllRead} className="min-h-11 rounded-md px-2 text-xs font-bold text-primary hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">
                Tout marquer comme lu
              </button>
            )}
          </div>

          {insights.length > 0 ? insights.map(insight => {
            const quickAction = getQuickAction(insight);
            return (
              <div key={insight.id} className="p-3 bg-card border border-border-main rounded-2xl group hover:border-primary/30 transition-all shadow-sm hover:shadow-md">
                <div className="flex justify-between items-start mb-1">
                  {insight.patient_id ? (
                    <Link to={`/patients/${insight.patient_id}`} onClick={() => onClose?.()}
                      className="text-xs font-black px-2 py-0.5 rounded-full bg-primary/10 text-primary uppercase hover:bg-primary hover:text-on-primary transition-colors">
                      {insight.insight_type}
                    </Link>
                  ) : (
                    <span className="text-xs font-black px-2 py-0.5 rounded-full bg-primary/10 text-primary uppercase">
                      {insight.insight_type}
                    </span>
                  )}
                  <span className="text-xs text-text-muted font-bold">
                    {new Date(insight.created_at).toLocaleDateString()}
                  </span>
                </div>
                {insight.patient_id ? (
                  <Link to={`/patients/${insight.patient_id}`} onClick={() => onClose?.()}
                    aria-label="Ouvrir le dossier patient associé à cette alerte"
                    className="mt-2 block min-h-11 rounded-md p-2 text-text-main hover:bg-input-field focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary">
                    <p className="text-xs font-medium leading-relaxed">
                      <TypewriterText text={insight.content} delay={8} />
                    </p>
                  </Link>
                ) : (
                  <div className="mt-2">
                    <p className="text-xs font-medium text-text-main leading-relaxed">
                      <TypewriterText text={insight.content} delay={8} />
                    </p>
                  </div>
                )}
                <div className="mt-3 flex items-center justify-between border-t border-border-main pt-2">
                  <button onClick={() => markAsRead(insight.id)}
                    className="flex min-h-11 items-center gap-1 rounded-md px-2 text-xs font-black text-text-main hover:text-success transition-colors uppercase focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">
                    <Check size={12} /> Marquer comme lu
                  </button>
                  {quickAction && (
                    <button onClick={quickAction.onClick}
                      className="flex min-h-11 items-center gap-1.5 text-xs font-black bg-primary/10 text-primary px-3 py-2 rounded-lg hover:bg-primary hover:text-on-primary transition-colors uppercase focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary">
                      {quickAction.icon} {quickAction.label}
                    </button>
                  )}
                </div>
              </div>
            );
          }) : (
            <div className="text-center py-10 flex flex-col items-center gap-2">
              <Check size={24} className="text-primary/30" />
              <p className="text-xs font-bold text-text-muted italic">Aucune nouvelle déduction.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
