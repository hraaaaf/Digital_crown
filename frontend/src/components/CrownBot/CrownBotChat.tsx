import { useState, useRef, useEffect } from 'react';
import { Send, X, Bot, User, Check, XCircle, Loader2, Menu, Plus, Trash2, MessageSquare, Archive } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { cn } from '../../utils/cn';

interface Message {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  actionType?: string;
  pendingAction?: any;
  suggestions?: string[];
  isThinking?: boolean;
}

interface Session {
  id: string;
  title: string;
  updated_at: string;
}

export function CrownBotChat({ onClose }: { onClose?: () => void }) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      sender: 'bot',
      text: 'Bonjour ! Je suis Crown Bot. Que puis-je faire pour vous aujourd\'hui ?',
      suggestions: ['Mon programme du jour', 'Créer un RDV', 'Finance du jour']
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  
  // Sessions State
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const fetchSessions = async () => {
    try {
      const { api } = await import('../../services/api');
      const res = await api.get('/bot/sessions');
      setSessions(res.data);
    } catch (err) {
      console.error("Erreur lors de la récupération des sessions", err);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const startNewSession = () => {
    setCurrentSessionId(null);
    setMessages([
      {
        id: 'welcome',
        sender: 'bot',
        text: 'Bonjour ! Je suis Crown Bot. Que puis-je faire pour vous aujourd\'hui ?',
        suggestions: ['Mon programme du jour', 'Créer un RDV', 'Finance du jour']
      }
    ]);
    setIsSidebarOpen(false);
  };

  const loadSession = async (id: string) => {
    try {
      setIsLoading(true);
      const { api } = await import('../../services/api');
      const res = await api.get(`/bot/sessions/${id}/messages`);
      
      const loadedMessages = res.data.map((m: any) => ({
        id: m.id,
        sender: m.sender,
        text: m.text,
        actionType: m.actionType,
        pendingAction: m.pendingAction,
        suggestions: m.suggestions
      }));
      
      if (loadedMessages.length === 0) {
        startNewSession();
        return;
      }
      
      setMessages(loadedMessages);
      setCurrentSessionId(id);
      setIsSidebarOpen(false);
    } catch (err) {
      console.error("Erreur lors du chargement de la session", err);
    } finally {
      setIsLoading(false);
    }
  };

  const archiveSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const { api } = await import('../../services/api');
      await api.delete(`/bot/sessions/${id}`);
      setSessions(prev => prev.filter(s => s.id !== id));
      if (currentSessionId === id) {
        startNewSession();
      }
    } catch (err) {
      console.error("Erreur lors de l'archivage", err);
    }
  };

  const handleSend = async (text: string) => {
    if (!text.trim()) return;
    
    const userMsg: Message = { id: Date.now().toString(), sender: 'user', text };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const { api } = await import('../../services/api');
      const payload: any = { message: text };
      if (currentSessionId) {
        payload.session_id = currentSessionId;
      }
      
      const res = await api.post('/bot/chat', payload);
      const data = res.data;
      
      if (data.session_id && data.session_id !== currentSessionId) {
        setCurrentSessionId(data.session_id);
        fetchSessions();
      }
      
      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: data.message,
        actionType: data.action_type,
        pendingAction: data.pending_action,
        suggestions: data.suggestions
      };
      
      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: "Désolé, je n'ai pas pu traiter votre demande."
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmAction = async (msgId: string, actionData: any) => {
    // Optimistic UI update
    setMessages(prev => prev.map(m => m.id === msgId ? { ...m, pendingAction: null, text: m.text + '\n\n*Action confirmée en cours...*' } : m));
    setIsLoading(true);
    
    try {
      const { api } = await import('../../services/api');
      const res = await api.post('/bot/execute', { pending_action: actionData });
      const data = res.data;
      
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        sender: 'bot',
        text: data.message || "Action exécutée avec succès."
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        sender: 'bot',
        text: "Erreur lors de l'exécution de l'action."
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-card shadow-2xl rounded-t-[24px] sm:rounded-[24px] overflow-hidden border border-border-main relative z-50">
      
      {/* Sidebar Overlay */}
      {isSidebarOpen && (
        <div 
          className="absolute inset-0 bg-black/20 z-40"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={cn(
        "absolute left-0 top-0 bottom-0 w-64 bg-slate-50 border-r border-slate-200 z-50 flex flex-col transition-transform duration-300",
        isSidebarOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <h3 className="font-semibold text-slate-700">Historique</h3>
          <button onClick={() => setIsSidebarOpen(false)} className="p-1 hover:bg-slate-200 rounded-md">
            <X size={16} className="text-slate-500" />
          </button>
        </div>
        
        <div className="p-2">
          <button 
            onClick={startNewSession}
            className="w-full flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 hover:border-primary hover:text-primary rounded-lg text-sm font-medium transition-colors"
          >
            <Plus size={16} />
            Nouvelle conversation
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.length === 0 ? (
            <p className="text-xs text-center text-slate-400 mt-4">Aucune conversation</p>
          ) : (
            sessions.map(session => (
              <div 
                key={session.id}
                onClick={() => loadSession(session.id)}
                className={cn(
                  "group flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors",
                  currentSessionId === session.id ? "bg-primary/10 text-primary" : "hover:bg-slate-200 text-slate-700"
                )}
              >
                <div className="flex items-center gap-2 overflow-hidden">
                  <MessageSquare size={14} className="shrink-0" />
                  <span className="text-sm truncate">{session.title}</span>
                </div>
                <button 
                  onClick={(e) => archiveSession(session.id, e)}
                  title="Archiver la conversation"
                  className="p-1 text-slate-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <Archive size={14} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-primary text-white">
        <div className="flex items-center gap-3">
          <button 
            onClick={() => setIsSidebarOpen(true)}
            className="p-2 -ml-2 hover:bg-white/10 rounded-full transition-colors"
          >
            <Menu size={18} />
          </button>
          <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
            <Bot size={18} />
          </div>
          <div>
            <h3 className="font-bold font-outfit text-sm leading-tight">Crown Bot</h3>
            <p className="text-[10px] text-white/70">Assistant IA Déterministe</p>
          </div>
        </div>
        {onClose && (
          <button onClick={onClose} className="p-2 bg-white/10 hover:bg-white/20 rounded-full transition-colors">
            <X size={16} />
          </button>
        )}
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/50">
        {messages.map(msg => (
          <div key={msg.id} className={cn("flex gap-3", msg.sender === 'user' ? "flex-row-reverse" : "")}>
            <div className={cn(
              "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
              msg.sender === 'user' ? "bg-slate-200 text-slate-600" : "bg-primary/10 text-primary"
            )}>
              {msg.sender === 'user' ? <User size={14} /> : <Bot size={14} />}
            </div>
            
            <div className={cn(
              "max-w-[80%] rounded-[16px] p-3 text-sm shadow-sm",
              msg.sender === 'user' 
                ? "bg-primary text-white rounded-tr-none" 
                : "bg-white border border-slate-100 text-slate-800 rounded-tl-none"
            )}>
              {msg.sender === 'bot' ? (
                <div className="prose prose-sm prose-slate max-w-none [&>p]:mb-2 [&>ul]:list-disc [&>ul]:ml-4 [&>ul]:mb-2 [&>ol]:list-decimal [&>ol]:ml-4 [&>ol]:mb-2 last:[&>*]:mb-0">
                  <ReactMarkdown>{msg.text}</ReactMarkdown>
                </div>
              ) : (
                <div className="whitespace-pre-wrap">{msg.text}</div>
              )}

              {/* Pending Action Confirmation */}
              {msg.pendingAction && (
                <div className="mt-4 p-3 bg-amber-50 border border-amber-100 rounded-[12px]">
                  <p className="text-xs font-semibold text-amber-800 mb-2">Confirmez-vous cette action ?</p>
                  <pre className="text-[10px] bg-white p-2 rounded border border-amber-50 mb-3 overflow-x-auto text-amber-900">
                    {JSON.stringify(msg.pendingAction, null, 2)}
                  </pre>
                  <div className="flex gap-2">
                    <button 
                      onClick={() => handleConfirmAction(msg.id, msg.pendingAction)}
                      className="flex-1 flex items-center justify-center gap-1.5 py-1.5 bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-bold rounded-[8px] transition-colors"
                    >
                      <Check size={14} /> Confirmer
                    </button>
                    <button 
                      onClick={() => setMessages(prev => prev.map(m => m.id === msg.id ? { ...m, pendingAction: null, text: m.text + '\n\n*Action annulée.*' } : m))}
                      className="flex-1 flex items-center justify-center gap-1.5 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 text-xs font-bold rounded-[8px] transition-colors"
                    >
                      <XCircle size={14} /> Annuler
                    </button>
                  </div>
                </div>
              )}

              {/* Suggestions */}
              {msg.suggestions && msg.suggestions.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {msg.suggestions.map((s, i) => (
                    <button 
                      key={i}
                      onClick={() => handleSend(s)}
                      className="px-2.5 py-1 bg-primary/5 hover:bg-primary/10 border border-primary/10 text-primary text-[11px] font-semibold rounded-full transition-colors"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center shrink-0">
              <Bot size={14} />
            </div>
            <div className="bg-white border border-slate-100 rounded-[16px] rounded-tl-none p-3 shadow-sm flex items-center gap-2">
              <Loader2 size={14} className="animate-spin text-primary" />
              <span className="text-xs text-slate-500">Crown Bot réfléchit...</span>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Input Area */}
      <div className="p-3 bg-white border-t border-slate-100">
        <form 
          onSubmit={(e) => { e.preventDefault(); handleSend(input); }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Posez votre question..."
            className="flex-1 bg-slate-100 border-none rounded-full px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-primary/20"
            disabled={isLoading}
          />
          <button 
            type="submit" 
            disabled={!input.trim() || isLoading}
            className="w-10 h-10 rounded-full bg-primary text-white flex items-center justify-center disabled:opacity-50 hover:bg-primary-hover transition-colors shrink-0 shadow-md"
          >
            <Send size={16} className="ml-1" />
          </button>
        </form>
      </div>
    </div>
  );
}
