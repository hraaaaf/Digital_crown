import React, { useState, useEffect, useRef } from 'react';
import { BrainCircuit, Check, ArrowRight, Zap } from 'lucide-react';
import { api, API_BASE } from '../services/api';
import { useAuthStore } from '../stores/useAuthStore';
import { Link, useNavigate } from 'react-router-dom';

// Typewriter Effect Component
const TypewriterText = ({ text, delay = 5 }: { text: string, delay?: number }) => {
  const [currentText, setCurrentText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (currentIndex < text.length) {
      const timeout = setTimeout(() => {
        setCurrentText(prevText => prevText + text[currentIndex]);
        setCurrentIndex(prevIndex => prevIndex + 1);
      }, delay);
      return () => clearTimeout(timeout);
    }
  }, [currentIndex, delay, text]);

  return <span>{currentText}</span>;
};

export const GhostBrainWidget = () => {
  const [unreadCount, setUnreadCount] = useState(0);
  const [insights, setInsights] = useState<any[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const widgetRef = useRef<HTMLDivElement>(null);
  const { user } = useAuthStore();
  const navigate = useNavigate();
  
  const employerId = user?.employer_id || user?.id;

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (widgetRef.current && !widgetRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (!employerId) return;

    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let isCleaned = false;
    let retryCount = 0;
    const MAX_RETRIES = 8;

    const connectWS = () => {
      if (isCleaned) return;
      if (retryCount >= MAX_RETRIES) return;

      const wsUrl = `${API_BASE.replace(/^http/, 'ws')}/api/ai/ws/ghost-insights/${employerId}`;
      ws = new WebSocket(wsUrl);

      ws.onopen = () => { retryCount = 0; };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.insights) {
            setInsights(data.insights);
            setUnreadCount(data.unread_count);
          }
        } catch (err) {
          console.error("GhostBrain WS Parse Error:", err);
        }
      };

      ws.onclose = () => {
        if (isCleaned) return;
        retryCount++;
        const delay = Math.min(5000 * retryCount, 60000);
        reconnectTimer = setTimeout(connectWS, delay);
      };
    };

    connectWS();

    return () => {
      isCleaned = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (ws) {
        ws.onclose = null;
        ws.close();
        ws = null;
      }
    };
  }, [employerId]);

  const markAsRead = async (logId: number) => {
    // Optimistic Update
    setInsights(prev => prev.filter(i => i.id !== logId));
    setUnreadCount(prev => Math.max(0, prev - 1));

    try {
      await api.post(`/ai/ghost-insights/${logId}/read`);
    } catch (err) {
      console.error("Failed to mark as read:", err);
      // Fallback WS refresh sera envoyé si échec car count != last_count en BDD
    }
  };

  const getQuickAction = (insight: any) => {
    const text = insight.content.toLowerCase();
    if (text.includes("échéance") || text.includes("impayé") || text.includes("encaissement")) {
      return {
        label: "Voir Trésorerie",
        icon: <Zap size={10} />,
        onClick: () => {
          navigate(`/accounting?tab=treasury`);
          setIsOpen(false);
          markAsRead(insight.id);
        }
      };
    }
    if (text.includes("rendez-vous") || text.includes("absent")) {
      return {
        label: "Voir Agenda",
        icon: <Zap size={10} />,
        onClick: () => {
          navigate(`/agenda`);
          setIsOpen(false);
          markAsRead(insight.id);
        }
      };
    }
    
    // Default action : Access Patient File
    if (insight.patient_id) {
        return {
            label: "Dossier Patient",
            icon: <ArrowRight size={10} />,
            onClick: () => {
                navigate(`/patients/${insight.patient_id}`);
                setIsOpen(false);
                markAsRead(insight.id);
            }
        };
    }
    
    return null;
  };

  return (
    <div className="relative" ref={widgetRef}>
      {/* Widget Trigger */}
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="p-2.5 text-text-muted hover:text-primary hover:bg-primary/5 rounded-elite-sm transition-elite relative group"
        title="Ghost Brain Insights"
      >
        <BrainCircuit size={20} className={`transition-elite ${unreadCount > 0 ? 'text-primary' : ''} group-hover:scale-110`} />
        {unreadCount > 0 && (
          <span className="absolute top-2.5 right-2.5 w-3 h-3 bg-primary text-white text-[7px] font-black rounded-full border-2 border-card-bg flex items-center justify-center animate-pulse shadow-[0_0_8px_rgba(212,175,55,0.8)]">
            {unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div className="absolute top-full right-0 mt-2 w-[340px] bg-card-bg/95 border border-primary/20 rounded-3xl shadow-[0_0_40px_rgba(212,175,55,0.15)] p-5 animate-in slide-in-from-top-2 duration-300 z-50 backdrop-blur-xl">
          <div className="flex items-center justify-between mb-4 border-b border-border-main pb-3">
             <div className="flex items-center gap-3">
                 <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary relative">
                     <div className="absolute inset-0 bg-primary/20 rounded-full animate-ping opacity-50" />
                     <BrainCircuit size={16} />
                 </div>
                 <div>
                    <h4 className="text-[11px] font-black text-primary uppercase tracking-widest leading-none">Ghost Brain V2</h4>
                    <p className="text-[9px] text-text-muted font-bold mt-1">Conscience Proactive</p>
                 </div>
             </div>
             {unreadCount > 0 && (
               <button 
                 onClick={() => {
                   insights.forEach(i => markAsRead(i.id));
                 }}
                 className="text-[9px] font-bold text-primary hover:underline"
               >
                 Tout marquer comme lu
               </button>
             )}
          </div>

          <div className="max-h-72 overflow-y-auto pr-1 space-y-3 custom-scrollbar">
            {insights.length > 0 ? (
              insights.map(insight => {
                const quickAction = getQuickAction(insight);
                
                return (
                  <div key={insight.id} className="p-3 bg-background border border-border-main rounded-2xl relative group hover:border-primary/30 transition-all shadow-sm hover:shadow-md">
                      <div className="flex justify-between items-start mb-1">
                          <Link 
                              to={`/patients/${insight.patient_id}`}
                              onClick={() => setIsOpen(false)}
                              className="text-[9px] font-black px-2 py-0.5 rounded-full bg-primary/10 text-primary uppercase hover:bg-primary hover:text-white transition-colors cursor-pointer"
                              title="Accéder au dossier patient"
                          >
                              {insight.insight_type}
                          </Link>
                          <span className="text-[8px] text-text-muted font-bold">
                             {new Date(insight.created_at).toLocaleDateString()}
                          </span>
                      </div>
                      
                      <div className="cursor-pointer" onClick={() => {
                         if(insight.patient_id) {
                            navigate(`/patients/${insight.patient_id}`);
                            setIsOpen(false);
                         }
                      }}>
                          <p className="text-[11px] font-medium text-main mt-2 leading-relaxed" style={{ color: 'var(--text-main)' }}>
                              <TypewriterText text={insight.content} delay={8} />
                          </p>
                      </div>
                      
                      <div className="mt-3 flex items-center justify-between border-t border-border-main/50 pt-2">
                          <button 
                              onClick={() => markAsRead(insight.id)}
                              className="flex items-center gap-1 text-[9px] font-black text-text-muted hover:text-green-500 transition-colors uppercase"
                          >
                              <Check size={12} /> Marquer comme lu
                          </button>

                          {quickAction && (
                              <button
                                  onClick={quickAction.onClick}
                                  className="flex items-center gap-1.5 text-[9px] font-black bg-primary/10 text-primary px-2 py-1 rounded-lg hover:bg-primary hover:text-white transition-colors uppercase"
                              >
                                  {quickAction.icon}
                                  {quickAction.label}
                              </button>
                          )}
                      </div>
                  </div>
                );
              })
            ) : (
              <div className="text-center py-6 flex flex-col items-center gap-2">
                 <Check size={24} className="text-primary/30" />
                 <p className="text-[10px] font-bold text-text-muted italic">Aucune nouvelle déduction.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

