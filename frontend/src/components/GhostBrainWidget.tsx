import React, { useState, useEffect, useRef } from 'react';
import { BrainCircuit, Check, X, Clock, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';

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

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (widgetRef.current && !widgetRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const fetchInsights = async () => {
    try {
      const res = await api.get('/ai/ghost-insights');
      setInsights(res.data.insights || []);
      setUnreadCount(res.data.unread_count || 0);
    } catch (e) {
      console.error("GhostBrain Error:", e);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchInsights();
    const interval = setInterval(fetchInsights, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  const markAsRead = async (logId: number) => {
    try {
      await api.post(`/ai/ghost-insights/${logId}/read`);
      fetchInsights();
    } catch (error) {
      // ignore
    }
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
        <div className="absolute top-full right-0 mt-2 w-80 bg-card-bg/95 border border-primary/20 rounded-3xl shadow-[0_0_40px_rgba(212,175,55,0.15)] p-5 animate-in slide-in-from-top-2 duration-300 z-50 backdrop-blur-xl">
          <div className="flex items-center gap-3 mb-4 border-b border-border-main pb-3">
             <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary relative">
                 <div className="absolute inset-0 bg-primary/20 rounded-full animate-ping opacity-50" />
                 <BrainCircuit size={16} />
             </div>
             <div>
                <h4 className="text-[11px] font-black text-primary uppercase tracking-widest leading-none">Ghost Brain V2</h4>
                <p className="text-[9px] text-text-muted font-bold mt-1">Conscience Proactive</p>
             </div>
          </div>

          <div className="max-h-64 overflow-y-auto pr-1 space-y-3 custom-scrollbar">
            {insights.length > 0 ? (
              insights.map(insight => (
                <div key={insight.id} className="p-3 bg-background border border-border-main rounded-2xl relative group hover:border-primary/30 transition-colors">
                    <div className="flex justify-between items-start mb-1">
                        <span className="text-[9px] font-black px-2 py-0.5 rounded-full bg-primary/10 text-primary uppercase">
                            {insight.insight_type}
                        </span>
                        <span className="text-[8px] text-text-muted font-bold">
                           {new Date(insight.created_at).toLocaleDateString()}
                        </span>
                    </div>
                    <p className="text-[11px] font-medium text-main mt-2 leading-relaxed" style={{ color: 'var(--text-main)' }}>
                        <TypewriterText text={insight.content} delay={8} />
                    </p>
                    
                    <button 
                        onClick={() => markAsRead(insight.id)}
                        className="mt-3 flex items-center gap-1 text-[9px] font-black text-text-muted hover:text-green-500 transition-colors uppercase"
                    >
                        <Check size={12} /> Marquer comme lu
                    </button>
                </div>
              ))
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
