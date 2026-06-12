import React from 'react';
import { useOfflineQueue } from '../../hooks/useOfflineQueue';
import { CloudOff, Cloud, RefreshCw, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const OfflineQueueViewer: React.FC = () => {
  const { queue, isOffline } = useOfflineQueue();

  if (!isOffline && queue.length === 0) return null;

  return (
    <AnimatePresence>
      <motion.div 
        initial={{ y: 50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: 50, opacity: 0 }}
        className="fixed bottom-20 left-4 right-4 z-50 pointer-events-none"
      >
        <div className="bg-slate-900 text-white rounded-2xl p-4 shadow-xl pointer-events-auto border border-slate-800">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              {isOffline ? (
                <CloudOff className="w-5 h-5 text-amber-400" />
              ) : (
                <RefreshCw className="w-5 h-5 text-blue-400 animate-spin" />
              )}
              <h3 className="font-semibold text-sm">
                {isOffline ? 'Mode Hors-ligne' : 'Synchronisation...'}
              </h3>
            </div>
            <span className="bg-slate-800 px-2 py-1 rounded-full text-xs font-bold">
              {queue.length} action{queue.length > 1 ? 's' : ''}
            </span>
          </div>

          {queue.length > 0 ? (
            <div className="space-y-2 max-h-32 overflow-y-auto pr-1 custom-scrollbar">
              {queue.map((action) => (
                <div key={action.id} className="flex items-center justify-between bg-slate-800/50 p-2 rounded-xl">
                  <div className="flex items-center gap-2 overflow-hidden">
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                      action.method === 'POST' ? 'bg-emerald-500/20 text-emerald-400' :
                      action.method === 'DELETE' ? 'bg-rose-500/20 text-rose-400' :
                      'bg-blue-500/20 text-blue-400'
                    }`}>
                      {action.method}
                    </span>
                    <span className="text-xs text-slate-300 truncate w-40">
                      {new URL(action.url).pathname.split('/').pop() || 'action'}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500">
                    {new Date(action.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-slate-400 flex items-center gap-1.5">
              <AlertCircle className="w-3.5 h-3.5" />
              Toutes les actions sont synchronisées.
            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
};
