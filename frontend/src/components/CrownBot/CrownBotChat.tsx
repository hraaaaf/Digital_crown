import { useState, useRef, useEffect } from 'react';
import { Send, X, Bot, User, Check, XCircle, Loader2 } from 'lucide-react';
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

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (text: string) => {
    if (!text.trim()) return;
    
    const userMsg: Message = { id: Date.now().toString(), sender: 'user', text };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const token = localStorage.getItem('token'); // Fallback token
      const res = await fetch('/api/bot/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ message: text })
      });

      if (!res.ok) throw new Error('Erreur API');
      const data = await res.json();
      
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
      const token = localStorage.getItem('token');
      const res = await fetch('/api/bot/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ pending_action: actionData })
      });
      
      if (!res.ok) throw new Error('Erreur API');
      const data = await res.json();
      
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
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-primary text-white">
        <div className="flex items-center gap-3">
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
                : "bg-white border border-slate-100 text-slate-800 rounded-tl-none whitespace-pre-wrap"
            )}>
              {msg.text}

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
