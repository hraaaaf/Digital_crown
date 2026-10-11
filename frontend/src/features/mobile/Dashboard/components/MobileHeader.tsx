import { Bell, Calendar, ChevronLeft, ChevronRight, RefreshCw, Search } from 'lucide-react';
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
  return (
    <div className="px-4 sm:px-6 pt-[max(18px,env(safe-area-inset-top))] pb-3 relative z-10">
      <div className="flex items-center justify-between gap-2 sm:gap-3 mb-4">
        <div data-dc-pocket-brand className="flex min-w-0 items-center gap-2">
          <img src={Logo} alt="Digital Crown Pocket" className="w-[92px] min-[430px]:w-24 sm:w-28 h-auto object-contain drop-shadow-sm origin-left min-w-0" />
          <span className="shrink-0 rounded-full border border-primary/15 bg-primary/10 px-2 py-1 text-[10px] font-bold uppercase tracking-[0.14em] text-primary">
            Pocket
          </span>
        </div>

        <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
          {!previewMode && activeTab !== 'patients' && onOpenPatients && (
            <button
              type="button"
              aria-label="Ouvrir la recherche patients"
              onClick={onOpenPatients}
              className="relative h-11 w-11 shrink-0 rounded-[16px] border border-glass-border bg-card shadow-elite backdrop-blur-md flex items-center justify-center text-primary active:scale-95 transition-transform"
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
              className="relative h-11 w-11 shrink-0 rounded-[16px] border border-glass-border bg-card shadow-elite backdrop-blur-md flex items-center justify-center text-primary"
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
            className="h-11 w-11 sm:w-auto sm:min-w-11 flex items-center justify-center gap-1.5 px-0 sm:px-3 bg-card border border-glass-border rounded-[16px] shadow-elite disabled:opacity-40 active:scale-95 transition-all hover:bg-primary/5 backdrop-blur-md"
            style={{ backgroundColor: 'var(--glass-bg)' }}
          >
            <div className={cn(
              'w-1.5 h-1.5 rounded-full',
              syncStatus === 'loading' ? 'bg-primary animate-pulse'
              : (syncStatus === 'error' || queuedActionsCount > 0) ? 'bg-danger animate-pulse'
              : syncStatus === 'success' ? 'bg-success' : 'bg-text-muted'
            )} />
            <RefreshCw size={10} className={cn('text-text-muted', syncStatus === 'loading' ? 'animate-spin' : '')} />
            <span className="hidden sm:flex text-[9px] font-black text-text-muted uppercase tracking-widest items-center gap-1">
              {syncStatus === 'loading' ? 'Mise à jour…' : syncStatus === 'error' ? 'Hors ligne' : 'À jour'}
              {queuedActionsCount > 0 && <span className="bg-danger-surface text-danger border border-danger-border px-1 rounded-full">{queuedActionsCount}</span>}
            </span>
            {queuedActionsCount > 0 && (
              <span aria-label={`${queuedActionsCount} modification(s) en attente de synchronisation`} className="sm:hidden ml-1 rounded-full bg-warning-surface px-1.5 text-[11px] font-bold text-warning">
                {queuedActionsCount}
              </span>
            )}
          </button>
        </div>
      </div>

      <div>
        {(activeTab === 'today' || activeTab === 'agenda' || activeTab === 'finance') && (
          <div className="flex items-center gap-1.5 mb-1.5">
            <Calendar size={16} className="text-primary shrink-0" />
            <button
              aria-label="Jour précédent"
              onClick={() => setSelectedDate(moveLocalDate(selectedDate, -1))}
              className="min-h-11 min-w-11 inline-flex items-center justify-center text-primary bg-primary/10 rounded-full active:scale-90 transition-transform"
            >
              <ChevronLeft size={17} />
            </button>
            <input
              type="date"
              aria-label="Choisir la date du planning"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="min-h-11 min-w-0 max-w-[148px] flex-1 bg-transparent border-none text-text-main font-semibold text-[16px] capitalize outline-none px-1 py-0 cursor-pointer text-center focus-visible:ring-2 focus-visible:ring-primary/50 rounded-xl"
            />
            <button
              aria-label="Jour suivant"
              onClick={() => setSelectedDate(moveLocalDate(selectedDate, 1))}
              className="min-h-11 min-w-11 inline-flex items-center justify-center text-primary bg-primary/10 rounded-full active:scale-90 transition-transform"
            >
              <ChevronRight size={17} />
            </button>
          </div>
        )}

        {!(['stock', 'frontdesk', 'lab'] as Tab[]).includes(activeTab) && <h1 className="text-[28px] min-[430px]:text-[31px] font-bold tracking-tight text-text-main leading-tight">
          {activeTab === 'today' ? `${greeting()},` :
           activeTab === 'agenda' ? 'Agenda' :
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
           activeTab === 'marketplace' ? 'Catalogue' :
           activeTab === 'bot' ? 'Assistant' : ''}
        </h1>}

        {(activeTab === 'today' || activeTab === 'agenda') && totalCount > 0 && (
          <div className="flex flex-wrap items-center gap-2 mt-2.5">
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-primary/5 border border-primary/10 rounded-full shadow-sm">
              <span className="text-[12px] font-semibold text-primary">
                {totalCount} RDV {selectedDate === localDateKey()
                  ? "aujourd'hui"
                  : `le ${new Date(`${selectedDate}T12:00:00`).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })}`}
              </span>
            </div>
            {termineCount > 0 && (
              <div className="flex items-center gap-1.5 px-3 py-1.5 bg-success-surface border border-success-border rounded-full shadow-sm">
                <span className="text-[12px] font-semibold text-success">{termineCount} terminé{termineCount > 1 ? 's' : ''}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
