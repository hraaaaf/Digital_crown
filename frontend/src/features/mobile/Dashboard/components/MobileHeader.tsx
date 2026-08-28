import { Bell, Calendar, ChevronLeft, ChevronRight, RefreshCw, Shield, Users } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { cn } from '../../../../utils/cn';
import Logo from '../../../../assets/logo.png';
import type { Tab, SyncStatus, Snapshot } from '../types';
import { greeting } from '../utils';
import { MobileNotificationCenter } from './MobileNotificationCenter';

export function MobileHeader({
  activeTab,
  syncStatus,
  snapshot,
  selectedDate,
  setSelectedDate,
  fetchSnapshot,
  totalCount,
  termineCount,
  queuedActionsCount,
  previewMode = false,
}: {
  activeTab: Tab;
  syncStatus: SyncStatus;
  snapshot: Snapshot | null;
  selectedDate: string;
  setSelectedDate: (d: string) => void;
  fetchSnapshot: () => void;
  totalCount: number;
  termineCount: number;
  queuedActionsCount: number;
  previewMode?: boolean;
}) {
  const navigate = useNavigate();
  return (
    <div className="px-6 pt-14 pb-6 relative z-10">
      <div className="flex items-center justify-between gap-3 mb-8">
        <img src={Logo} alt="Digital Crown" className="w-32 sm:w-36 h-auto object-contain drop-shadow-sm origin-left min-w-0" />

        <div className="flex items-center gap-2 shrink-0">
          {previewMode ? (
            <button
              type="button"
              disabled
              aria-label="Notifications désactivées dans la Preview"
              className="relative h-12 w-12 shrink-0 rounded-[16px] border border-glass-border bg-card shadow-elite backdrop-blur-md flex items-center justify-center text-primary"
              style={{ backgroundColor: 'var(--glass-bg)' }}
            >
              <Bell size={18} aria-hidden="true" />
            </button>
          ) : (
            <MobileNotificationCenter />
          )}
          <button
            type="button"
            aria-label="Synchroniser les données mobiles"
            onClick={() => {
              if (typeof navigator !== 'undefined' && navigator.vibrate) navigator.vibrate(50);
              fetchSnapshot();
            }}
            disabled={syncStatus === 'loading'}
            className="min-h-12 flex items-center gap-1.5 px-3 bg-card border border-glass-border rounded-[16px] shadow-elite disabled:opacity-40 active:scale-95 transition-all hover:bg-primary/5 backdrop-blur-md"
            style={{ backgroundColor: 'var(--glass-bg)' }}
          >
            <div className={cn(
              'w-1.5 h-1.5 rounded-full',
              syncStatus === 'loading' ? 'bg-primary animate-pulse'
              : (syncStatus === 'error' || queuedActionsCount > 0) ? 'bg-rose-500 animate-pulse'
              : 'bg-emerald-500'
            )} />
            <RefreshCw size={10} className={cn('text-text-muted', syncStatus === 'loading' ? 'animate-spin' : '')} />
            <span className="text-[9px] font-black text-text-muted uppercase tracking-widest flex items-center gap-1">
              {syncStatus === 'loading' ? 'Sync…' : syncStatus === 'error' ? 'Offline' : 'Live'}
              {queuedActionsCount > 0 && <span className="bg-rose-500 text-white px-1 rounded-full">{queuedActionsCount}</span>}
            </span>
          </button>
        </div>
      </div>

      <div>
        {(activeTab === 'agenda' || activeTab === 'finance') && (
          <div className="flex items-center gap-2 mb-2">
            <Calendar size={12} className="text-primary shrink-0" />
            <button
              onClick={() => {
                const d = new Date(selectedDate);
                d.setDate(d.getDate() - 1);
                setSelectedDate(d.toISOString().split('T')[0]);
              }}
              className="p-1 text-primary bg-primary/10 rounded-full active:scale-90 transition-transform"
            >
              <ChevronLeft size={12} />
            </button>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="bg-transparent border-none text-text-muted font-bold text-xs capitalize outline-none p-0 cursor-pointer text-center min-w-min"
            />
            <button
              onClick={() => {
                const d = new Date(selectedDate);
                d.setDate(d.getDate() + 1);
                setSelectedDate(d.toISOString().split('T')[0]);
              }}
              className="p-1 text-primary bg-primary/10 rounded-full active:scale-90 transition-transform"
            >
              <ChevronRight size={12} />
            </button>
          </div>
        )}

        <h1 className="text-4xl font-black tracking-tight text-primary font-outfit leading-none">
          {activeTab === 'agenda' ? `${greeting()},` :
           activeTab === 'finance' ? 'Finances' :
           activeTab === 'securite' ? 'Sécurité' :
           activeTab === 'lab' ? 'Laboratoire' : ''}
        </h1>

        {snapshot?.is_superadmin && (
          <button
            onClick={() => navigate('/mobile/superadmin')}
            className="mt-4 px-4 py-2 bg-amber-400 hover:bg-amber-500 text-amber-950 rounded-full font-black text-xs shadow-md uppercase tracking-widest flex items-center gap-2 transition-all active:scale-95"
          >
            <Shield size={14} /> SuperAdmin
          </button>
        )}

        {snapshot?.role === 'SECRETAIRE' && (
          <button
            onClick={() => navigate('/mobile/dentists')}
            className="mt-4 px-4 py-2 bg-primary/10 border border-primary/20 text-primary rounded-full font-black text-xs shadow-sm uppercase tracking-widest flex items-center gap-2 transition-all active:scale-95"
          >
            <Users size={13} /> Équipe praticiens
          </button>
        )}

        {activeTab === 'agenda' && totalCount > 0 && (
          <div className="flex items-center gap-2 mt-4">
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-primary/5 border border-primary/10 rounded-full shadow-sm">
              <span className="text-[10px] font-black text-primary">{totalCount} RDV aujourd'hui</span>
            </div>
            {termineCount > 0 && (
              <div className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/5 border border-emerald-500/20 rounded-full shadow-sm">
                <span className="text-[10px] font-black text-emerald-600">{termineCount} terminé{termineCount > 1 ? 's' : ''}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
