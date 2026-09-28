import { useEffect, useRef, useState } from 'react';
import { Bell, CalendarDays, ClipboardList, MoreHorizontal, ShieldCheck, UserRound, UsersRound, X } from 'lucide-react';
import { cn } from '../../../../utils/cn';
import type { Tab, Snapshot } from '../types';

export function MobileBottomNav({
  activeTab,
  setActiveTab,
  totalCount,
  termineCount,
  snapshot,
  quickActionsAvailable,
  quickActionsOpen,
  onToggleQuickActions,
}: {
  activeTab: Tab;
  setActiveTab: (t: Tab) => void;
  totalCount: number;
  termineCount: number;
  snapshot: Snapshot | null;
  quickActionsAvailable: boolean;
  quickActionsOpen: boolean;
  onToggleQuickActions: () => void;
}) {
  const [moreOpen, setMoreOpen] = useState(false);
  const moreDialogRef = useRef<HTMLElement | null>(null);
  const moreTriggerRef = useRef<HTMLButtonElement | null>(null);
  const role = snapshot?.role ?? '';
  const waitingCount = snapshot?.appointments.filter(appointment => appointment.status === 'EN_ATTENTE').length ?? 0;
  const secondaryTabs = [
    {
      id: 'waiting-room' as Tab,
      icon: UsersRound,
      label: 'Salle d’attente',
      allowedRoles: ['DENTISTE', 'ADMIN', 'SECRETAIRE'],
      badge: waitingCount > 0 ? waitingCount : undefined,
    },
    {
      id: 'frontdesk' as Tab,
      icon: ClipboardList,
      label: 'Accueil',
      allowedRoles: ['DENTISTE', 'ADMIN', 'SECRETAIRE'],
    },
    {
      id: 'securite' as Tab,
      icon: ShieldCheck,
      label: 'Sécurité',
      allowedRoles: ['DENTISTE', 'ADMIN', 'SECRETAIRE'],
    },
  ].filter(tab => tab.allowedRoles.includes(role));

  const isMoreActive = secondaryTabs.some(tab => tab.id === activeTab);
  const agendaHasPending = totalCount > 0 && termineCount < totalCount;

  useEffect(() => {
    if (!moreOpen) return;

    const dialog = moreDialogRef.current;
    const focusable = Array.from(dialog?.querySelectorAll<HTMLElement>(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
    ) ?? []);
    (focusable[0] ?? dialog)?.focus();

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        setMoreOpen(false);
        return;
      }
      if (event.key !== 'Tab' || !dialog) return;

      const currentFocusable = Array.from(dialog.querySelectorAll<HTMLElement>(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
      ));
      if (currentFocusable.length === 0) {
        event.preventDefault();
        dialog.focus();
        return;
      }

      const first = currentFocusable[0];
      const last = currentFocusable[currentFocusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => {
      window.removeEventListener('keydown', onKeyDown);
      if (moreTriggerRef.current) moreTriggerRef.current.focus();
    };
  }, [moreOpen]);

  const selectTab = (tab: Tab) => {
    if (typeof navigator !== 'undefined' && navigator.vibrate) navigator.vibrate(35);
    setMoreOpen(false);
    setActiveTab(tab);
  };

  return (
    <>
      {moreOpen && (
        <div className="fixed inset-0 z-[60]" data-mobile-more-menu>
          <button
            type="button"
            className="absolute inset-0 bg-slate-950/15 backdrop-blur-[1px]"
            aria-label="Fermer le menu Plus"
            onClick={() => setMoreOpen(false)}
          />
          <section
            ref={moreDialogRef}
            tabIndex={-1}
            role="dialog"
            aria-modal="true"
            aria-labelledby="mobile-more-title"
            className="absolute left-4 right-4 bottom-[100px] mx-auto max-w-[720px] rounded-[28px] border border-glass-border bg-card p-4 shadow-elite-hover"
            style={{ backgroundColor: 'var(--glass-bg)', fontFamily: 'var(--app-font-family, "Inter", system-ui, sans-serif)' }}
          >
            <div className="mb-3 flex items-center justify-between gap-3">
              <div>
                <h2 id="mobile-more-title" className="text-[18px] font-black text-text-main">Plus</h2>
                <p className="mt-0.5 text-[10px] font-bold text-text-muted">Accès secondaires</p>
              </div>
              <button
                type="button"
                aria-label="Fermer Plus"
                onClick={() => setMoreOpen(false)}
                className="grid h-10 w-10 place-items-center rounded-full border border-glass-border bg-background text-text-muted"
              >
                <X size={18} />
              </button>
            </div>

            <div className="grid gap-2.5 max-h-[min(60dvh,520px)] overflow-y-auto pr-0.5">
              {secondaryTabs.map(({ id, icon: Icon, label, badge }) => (
                <button
                  key={id}
                  type="button"
                  data-mobile-more-item={id}
                  onClick={() => selectTab(id)}
                  className="flex min-h-[56px] items-center gap-3 rounded-[18px] border border-glass-border bg-background px-4 text-left text-text-main active:scale-[0.99]"
                >
                  <span className="relative grid h-9 w-9 place-items-center rounded-full bg-primary/10 text-primary">
                    <Icon size={18} />
                  </span>
                  <span className="flex-1 text-[11px] font-black">{label}</span>
                  {badge != null && (
                    <span data-mob5i-waiting-badge className="grid min-h-7 min-w-7 place-items-center rounded-full bg-amber-500/10 px-2 text-[10px] font-black text-amber-700">
                      {badge}
                    </span>
                  )}
                </button>
              ))}
              {secondaryTabs.length === 0 && (
                <div className="rounded-[18px] border border-glass-border bg-background px-4 py-4 text-[10px] font-bold text-text-muted">
                  Aucun accès secondaire disponible pour ce rôle.
                </div>
              )}
            </div>
          </section>
        </div>
      )}

      <nav
        data-mobile-bottom-nav
        aria-label="Navigation mobile principale"
        className="fixed left-3 right-3 mx-auto h-[76px] max-w-[720px] rounded-[34px] border backdrop-blur-2xl shadow-elite-hover z-[65]"
        style={{
          backgroundColor: 'var(--glass-bg)',
          borderColor: 'var(--glass-border)',
          bottom: 'max(12px, env(safe-area-inset-bottom))',
        }}
      >
        <div className="grid h-full grid-cols-5 items-center px-1.5">
          <button
            type="button"
            aria-current={activeTab === 'agenda' ? 'page' : undefined}
            onClick={() => selectTab('agenda')}
            className={cn(
              'relative flex min-h-[52px] min-w-0 flex-col items-center justify-center gap-0.5 rounded-[22px] text-[9px] font-bold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40',
              activeTab === 'agenda' ? 'text-primary' : 'text-text-muted'
            )}
          >
            <span className="relative grid h-8 w-11 place-items-center">
              <CalendarDays size={20} strokeWidth={activeTab === 'agenda' ? 2.35 : 1.9} />
              {agendaHasPending && <span className="absolute right-0.5 top-0.5 h-1.5 w-1.5 rounded-full bg-primary ring-2 ring-white/80" />}
            </span>
            <span className="max-w-full truncate">Aujourd’hui</span>
          </button>

          <button
            type="button"
            aria-current={activeTab === 'patients' ? 'page' : undefined}
            onClick={() => selectTab('patients')}
            className={cn(
              'flex min-h-[52px] min-w-0 flex-col items-center justify-center gap-0.5 rounded-[22px] text-[9px] font-bold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40',
              activeTab === 'patients' ? 'text-primary' : 'text-text-muted'
            )}
          >
            <span className="grid h-8 w-11 place-items-center"><UserRound size={20} strokeWidth={activeTab === 'patients' ? 2.35 : 1.9} /></span>
            <span className="max-w-full truncate">Patients</span>
          </button>

          <div className="relative grid h-full place-items-center">
            <button
              type="button"
              aria-label={quickActionsOpen ? 'Fermer les actions rapides' : 'Ouvrir les actions rapides'}
              aria-expanded={quickActionsOpen}
              disabled={!quickActionsAvailable}
              onClick={() => {
                setMoreOpen(false);
                onToggleQuickActions();
              }}
              className="absolute -top-4 grid h-[60px] w-[60px] place-items-center rounded-full border-[3px] border-white bg-primary text-white shadow-[0_8px_30px_rgba(var(--primary-rgb),0.4)] transition-transform active:scale-95 disabled:cursor-not-allowed disabled:opacity-35"
            >
              {quickActionsOpen ? <X size={24} /> : <span className="text-[30px] font-light leading-none">+</span>}
            </button>
          </div>

          <button
            type="button"
            aria-current={activeTab === 'notifications' ? 'page' : undefined}
            onClick={() => selectTab('notifications')}
            className={cn(
              'relative flex min-h-[52px] min-w-0 flex-col items-center justify-center gap-0.5 rounded-[22px] text-[9px] font-bold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40',
              activeTab === 'notifications' ? 'text-primary' : 'text-text-muted'
            )}
          >
            <span className="relative grid h-8 w-11 place-items-center">
              <Bell size={20} strokeWidth={activeTab === 'notifications' ? 2.35 : 1.9} />
            </span>
            <span className="max-w-full truncate">Alertes</span>
          </button>

          <button
            ref={moreTriggerRef}
            type="button"
            aria-current={isMoreActive ? 'page' : undefined}
            aria-expanded={moreOpen}
            onClick={() => {
              if (typeof navigator !== 'undefined' && navigator.vibrate) navigator.vibrate(35);
              setMoreOpen(value => !value);
            }}
            className={cn(
              'flex min-h-[52px] min-w-0 flex-col items-center justify-center gap-0.5 rounded-[22px] text-[9px] font-bold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40',
              isMoreActive || moreOpen ? 'text-primary' : 'text-text-muted'
            )}
          >
            <span className="grid h-8 w-11 place-items-center"><MoreHorizontal size={21} strokeWidth={isMoreActive || moreOpen ? 2.35 : 1.9} /></span>
            <span className="max-w-full truncate">Plus</span>
          </button>
        </div>
      </nav>
    </>
  );
}
