import { Bell, Calendar, ChevronLeft, ChevronRight, RefreshCw, Search, Shield } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { cn } from '../../../../utils/cn';
import Logo from '../../../../assets/logo.png';
import type { Tab, SyncStatus, Snapshot } from '../types';
import { greeting } from '../utils';
import { MobileNotificationCenter } from './MobileNotificationCenter';

function localDateKey(date = new Date()): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function moveLocalDate(value: string, delta: number): string {
  const parsed = new Date(`${value}T12:00:00`);
  if (Number.isNaN(parsed.getTime())) return value;
  parsed.setDate(parsed.getDate() + delta);
  return localDateKey(parsed);
}


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
  onOpenPatients,
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
  onOpenPatients?: () => void;
  previewMode?: boolean;
}) {
  const navigate = useNavigate();
  return (
    <div className="px-4 sm:px-6 pt-14 pb-6 relative z-10">
      <div className="flex items-center justify-between gap-2 sm:gap-3 mb-8">
        <div data-dc-pocket-brand className="flex min-w-0 items-center gap-2">
          <img src={Logo} alt="Digital Crown Pocket" className="w-24 min-[430px]:w-28 sm:w-36 h-auto object-contain drop-shadow-sm origin-left min-w-0" />
          <span className="shrink-0 rounded-full border border-primary/15 bg-primary/10 px-2 py-1 text-[9px] font-black uppercase tracking-[0.14em] text-primary">
            Pocket
          </span>
        </div>

        <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
          {!previewMode && activeTab !== 'patients' && onOpenPatients && (
            <button
              type="button"
              aria-label="Ouvrir la recherche patients"
              onClick={onOpenPatients}
              className="relative h-12 w-12 shrink-0 rounded-[16px] border border-glass-border bg-card shadow-elite backdrop-blur-md flex items-center justify-center text-primary active:scale-95 transition-transform"
              style={{ backgroundColor: 'var(--glass-bg)' }}
            >
              <Search size={18} aria-hidden="true" />
            </button>
          )}
          {previewMode ? (
            <button
              type="button"
              disabled
              aria-label="Notifications désactivées dans la démonstration"
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
            className="h-12 w-12 sm:w-auto sm:min-w-12 flex items-center justify-center gap-1.5 px-0 sm:px-3 bg-card border border-glass-border rounded-[16px] shadow-elite disabled:opacity-40 active:scale-95 transition-all hover:bg-primary/5 backdrop-blur-md"
            style={{ backgroundColor: 'var(--glass-bg)' }}
          >
            <div className={cn(
              'w-1.5 h-1.5 rounded-full',
              syncStatus === 'loading' ? 'bg-primary animate-pulse'
              : (syncStatus === 'error' || queuedActionsCount > 0) ? 'bg-rose-500 animate-pulse'
              : 'bg-emerald-500'
            )} />
            <RefreshCw size={10} className={cn('text-text-muted', syncStatus === 'loading' ? 'animate-spin' : '')} />
            <span className="hidden sm:flex text-[9px] font-black text-text-muted uppercase tracking-widest items-center gap-1">
              {syncStatus === 'loading' ? 'Mise à jour…' : syncStatus === 'error' ? 'Hors ligne' : 'À jour'}
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
              aria-label="Jour précédent"
              onClick={() => setSelectedDate(moveLocalDate(selectedDate, -1))}
              className="min-h-11 min-w-11 inline-flex items-center justify-center text-primary bg-primary/10 rounded-full active:scale-90 transition-transform"
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
              aria-label="Jour suivant"
              onClick={() => setSelectedDate(moveLocalDate(selectedDate, 1))}
              className="min-h-11 min-w-11 inline-flex items-center justify-center text-primary bg-primary/10 rounded-full active:scale-90 transition-transform"
            >
              <ChevronRight size={12} />
            </button>
          </div>
        )}

        <h1 className="text-4xl font-black tracking-tight text-primary leading-none">
          {activeTab === 'agenda' ? `${greeting()},` :
           activeTab === 'patients' ? 'Patients' :
           activeTab === 'finance' ? 'Finances' :
           activeTab === 'securite' ? 'Sécurité' :
           activeTab === 'lab' ? 'Laboratoire' :
           activeTab === 'dentists' ? 'Équipe' :
           activeTab === 'waiting-room' ? "Salle d’attente" :
           activeTab === 'frontdesk' ? 'Accueil' :
           activeTab === 'notifications' ? 'Alertes' :
           activeTab === 'stock' ? 'Stock' :
           activeTab === 'library' ? 'Bibliothèque' :
           activeTab === 'marketplace' ? 'Marketplace' :
           activeTab === 'bot' ? 'Assistant' : ''}
        </h1>

        {snapshot?.is_superadmin && (
          <button
            onClick={() => navigate('/mobile/superadmin')}
            className="mt-4 px-4 py-2 bg-amber-400 hover:bg-amber-500 text-amber-950 rounded-full font-black text-xs shadow-md uppercase tracking-widest flex items-center gap-2 transition-all active:scale-95"
          >
            <Shield size={14} /> SuperAdmin
          </button>
        )}

        {activeTab === 'agenda' && totalCount > 0 && (
          <div className="flex items-center gap-2 mt-4">
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-primary/5 border border-primary/10 rounded-full shadow-sm">
              <span className="text-[10px] font-black text-primary">
                {totalCount} RDV {selectedDate === localDateKey()
                  ? "aujourd'hui"
                  : `le ${new Date(`${selectedDate}T12:00:00`).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })}`}
              </span>
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
