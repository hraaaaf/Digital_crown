import { useEffect, useRef, useState } from 'react';
import { Bell, BookOpen, Bot, CalendarDays, ClipboardList, FlaskConical, LayoutDashboard, MoreHorizontal, Package, Plus, ShieldCheck, ShoppingCart, TrendingUp, UserRound, Users, UsersRound, X } from 'lucide-react';
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
    { id: 'frontdesk' as Tab, icon: ClipboardList, label: 'Accueil', allowedRoles: ['DENTISTE', 'ADMIN', 'SECRETAIRE'] },
    { id: 'notifications' as Tab, icon: Bell, label: 'Notifications', allowedRoles: ['DENTISTE', 'ADMIN', 'SECRETAIRE'] },
    { id: 'stock' as Tab, icon: Package, label: 'Stock', allowedRoles: ['DENTISTE', 'ADMIN', 'SECRETAIRE'] },
    { id: 'library' as Tab, icon: BookOpen, label: 'Bibliothèque', allowedRoles: ['DENTISTE', 'ADMIN'] },
    { id: 'marketplace' as Tab, icon: ShoppingCart, label: 'Approvisionnement', allowedRoles: ['DENTISTE', 'ADMIN'] },
    { id: 'dentists' as Tab, icon: Users, label: 'Équipe', allowedRoles: ['DENTISTE', 'ADMIN', 'SECRETAIRE'] },
    { id: 'finance' as Tab, icon: TrendingUp, label: 'Trésorerie', allowedRoles: ['DENTISTE', 'ADMIN'] },
    { id: 'lab' as Tab, icon: FlaskConical, label: 'Envois Labo', allowedRoles: ['DENTISTE', 'ADMIN'] },
    { id: 'bot' as Tab, icon: Bot, label: 'Assistant · En cours de construction', allowedRoles: ['DENTISTE', 'ADMIN', 'SECRETAIRE'] },
    {
      id: 'securite' as Tab,
      icon: ShieldCheck,
      label: 'Sécurité',
      allowedRoles: ['DENTISTE', 'ADMIN', 'SECRETAIRE'],
    },
  ].filter(tab => tab.allowedRoles.includes(role));

  const isMoreActive = secondaryTabs.some(tab => tab.id === activeTab);
  const agendaHasPending = totalCount > 0 && termineCount < totalCount;
  // Five equally sized targets. The active highlight glides between them;
  // quick actions and Plus retain their existing callbacks/permissions.
  const selectedNavIndex = quickActionsOpen ? 2
    : moreOpen || isMoreActive ? 4
      : activeTab === 'patients' ? 3
        : activeTab === 'agenda' ? 1 : 0;
  const navItemClass = 'relative z-10 flex min-h-[54px] min-w-0 flex-col items-center justify-center gap-0.5 rounded-[23px] text-[11px] font-semibold transition-[color,transform] duration-200 ease-out active:scale-[0.94] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 motion-reduce:transition-none motion-reduce:active:scale-100';
  const navLabelClass = 'max-w-full truncate';


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
            className="absolute inset-0 backdrop-blur-[3px]"
            style={{ backgroundColor: 'color-mix(in srgb, var(--text-main) 48%, transparent)' }}
            aria-label="Fermer le menu Plus"
            onClick={() => setMoreOpen(false)}
          />
          <section
            ref={moreDialogRef}
            tabIndex={-1}
            role="dialog"
            aria-modal="true"
            aria-labelledby="mobile-more-title"
            className="absolute left-3 right-3 bottom-[calc(96px+env(safe-area-inset-bottom))] mx-auto max-w-[720px] rounded-[26px] border border-border-main bg-card p-4 shadow-elite"
            style={{ backgroundColor: 'var(--card-bg)', fontFamily: 'var(--app-font-family, "Inter", system-ui, sans-serif)' }}
          >
            <div className="mb-3 flex items-center justify-between gap-3">
              <div>
                <h2 id="mobile-more-title" className="text-[20px] font-bold text-text-main">Plus</h2>
                <p className="mt-0.5 text-[12px] font-medium text-text-muted">Accès secondaires</p>
              </div>
              <button
                type="button"
                aria-label="Fermer Plus"
                onClick={() => setMoreOpen(false)}
                className="grid h-11 w-11 place-items-center rounded-full border border-glass-border bg-background text-text-muted"
              >
                <X size={18} />
              </button>
            </div>

            <div className="grid gap-2 max-h-[min(62dvh,560px)] overflow-y-auto overscroll-contain pr-0.5">
              {secondaryTabs.some(tab => tab.id === 'waiting-room') && (
                <p className="px-2 py-1 text-[11px] font-bold uppercase tracking-wider text-primary">Accueil &amp; attente</p>
              )}
              {secondaryTabs.map(({ id, icon: Icon, label, badge }) => (
                <button
                  key={id}
                  type="button"
                  data-mobile-more-item={id}
                  aria-label={id === 'bot' ? 'Assistant' : label}
                  onClick={() => selectTab(id)}
                  className={cn('flex min-h-[54px] items-center gap-3 rounded-[16px] border border-border-main bg-background px-3.5 text-left text-text-main transition-colors active:bg-primary/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50', id === 'waiting-room' || id === 'frontdesk' ? 'border-primary/25 bg-primary/5' : '')}
                >
                  <span className="relative grid h-10 w-10 shrink-0 place-items-center rounded-[13px] bg-primary/10 text-primary">
                    <Icon size={19} />
                  </span>
                  <span className="flex-1 text-[14px] font-semibold leading-snug">{label}</span>
                  {badge != null && (
                    <span data-mob5i-waiting-badge className="grid min-h-7 min-w-7 place-items-center rounded-full bg-warning-surface border border-warning-border px-2 text-[11px] font-bold text-warning">
                      {badge}
                    </span>
                  )}
                </button>
              ))}
              {secondaryTabs.length === 0 && (
                <div className="rounded-[18px] border border-glass-border bg-background px-4 py-4 text-[11px] font-medium text-text-muted">
                  Aucun accès secondaire disponible pour ce rôle.
                </div>
              )}
            </div>
          </section>
        </div>
      )}

      <nav
        data-mobile-bottom-nav
        data-pocket-glass-nav
        inert={moreOpen}
        aria-label="Navigation mobile principale"
        className="fixed left-3 right-3 z-[65] mx-auto h-[76px] max-w-[720px] overflow-hidden rounded-[30px] border shadow-elite isolate"
        style={{
          backgroundColor: 'color-mix(in srgb, var(--card-bg) 88%, transparent)',
          borderColor: 'color-mix(in srgb, var(--primary) 14%, var(--glass-border) 86%)',
          WebkitBackdropFilter: 'blur(24px) saturate(165%)',
          backdropFilter: 'blur(24px) saturate(165%)',
          bottom: 'max(12px, env(safe-area-inset-bottom))',
        }}
      >
        <div className="relative grid h-full grid-cols-5 items-center px-1.5">
          <span
            data-mobile-nav-indicator
            aria-hidden="true"
            className="pointer-events-none absolute z-0 h-[56px] rounded-[24px] border transition-transform duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] motion-reduce:transition-none"
            style={{
              left: '6px',
              top: '50%',
              width: 'calc((100% - 12px) / 5)',
              transform: `translate(${selectedNavIndex * 100}%, -50%)`,
              backgroundColor: 'color-mix(in srgb, var(--primary) 11%, transparent)',
              borderColor: 'color-mix(in srgb, var(--primary) 14%, transparent)',
            }}
          />
          <button
            data-mobile-nav-item="today"
            type="button"
            aria-current={activeTab === 'today' ? 'page' : undefined}
            onClick={() => selectTab('today')}
            className={cn(navItemClass, activeTab === 'today' ? 'text-primary' : 'text-text-muted')}
          >
            <span className="relative grid h-8 w-11 place-items-center">
              <LayoutDashboard size={21} strokeWidth={activeTab === 'today' ? 2.35 : 1.9} />
              {agendaHasPending && <span className="absolute right-0.5 top-0.5 h-1.5 w-1.5 rounded-full bg-primary ring-2 ring-card" />}
            </span>
            <span className={navLabelClass}>Aujourd’hui</span>
          </button>

          <button
            data-mobile-nav-item="agenda"
            type="button"
            aria-current={activeTab === 'agenda' ? 'page' : undefined}
            onClick={() => selectTab('agenda')}
            className={cn(navItemClass, activeTab === 'agenda' ? 'text-primary' : 'text-text-muted')}
          >
            <span className="grid h-8 w-11 place-items-center"><CalendarDays size={21} strokeWidth={activeTab === 'agenda' ? 2.35 : 1.9} /></span>
            <span className={navLabelClass}>Agenda</span>
          </button>

          <button
            data-mobile-nav-item="actions"
            type="button"
            aria-label={quickActionsOpen ? 'Fermer les actions rapides' : 'Ouvrir les actions rapides'}
            aria-expanded={quickActionsOpen}
            disabled={!quickActionsAvailable}
            onClick={() => {
              setMoreOpen(false);
              onToggleQuickActions();
            }}
            className={cn(navItemClass, 'disabled:cursor-not-allowed disabled:opacity-35', quickActionsOpen ? 'text-primary' : 'text-text-muted')}
          >
            <span className="grid h-8 w-11 place-items-center">
              {quickActionsOpen ? <X size={21} strokeWidth={2.2} /> : <Plus size={23} strokeWidth={2.2} />}
            </span>
            <span className={navLabelClass}>Actions</span>
          </button>

          <button
            data-mobile-nav-item="patients"
            type="button"
            aria-current={activeTab === 'patients' ? 'page' : undefined}
            onClick={() => selectTab('patients')}
            className={cn(navItemClass, activeTab === 'patients' ? 'text-primary' : 'text-text-muted')}
          >
            <span className="grid h-8 w-11 place-items-center"><UserRound size={21} strokeWidth={activeTab === 'patients' ? 2.35 : 1.9} /></span>
            <span className={navLabelClass}>Patients</span>
          </button>

          <button
            ref={moreTriggerRef}
            data-mobile-nav-item="more"
            type="button"
            aria-current={isMoreActive ? 'page' : undefined}
            aria-expanded={moreOpen}
            onClick={() => {
              if (typeof navigator !== 'undefined' && navigator.vibrate) navigator.vibrate(35);
              setMoreOpen(value => !value);
            }}
            className={cn(navItemClass, isMoreActive || moreOpen ? 'text-primary' : 'text-text-muted')}
          >
            <span className="grid h-8 w-11 place-items-center"><MoreHorizontal size={22} strokeWidth={isMoreActive || moreOpen ? 2.35 : 1.9} /></span>
            <span className={navLabelClass}>Plus</span>
          </button>
        </div>
      </nav>
    </>
  );
}
