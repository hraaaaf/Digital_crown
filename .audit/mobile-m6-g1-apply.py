from pathlib import Path

ROOT = Path('.')

css_path = ROOT / 'frontend/src/styles/mobileGlassSystem.css'
css = css_path.read_text(encoding='utf-8')
if '--dc-clinical-motif-ready' in css:
    raise SystemExit('M6-G1 motif already present')

motif = r'''

/* M6-G1 — Proprietary clinical motif: abstract nodal network + dental-arch curves. */
:is(
  [data-dc-mobile-shell],
  [data-mobile-context],
  [data-m4a-context],
  [data-m4b-context],
  [data-m4c-context],
  [data-m4d-context]
) {
  position: relative;
  isolation: isolate;
}

:is(
  [data-dc-mobile-shell],
  [data-mobile-context],
  [data-m4a-context],
  [data-m4b-context],
  [data-m4c-context],
  [data-m4d-context]
)::before {
  --dc-clinical-motif-ready: 1;
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  opacity: 0.34;
  background-image:
    radial-gradient(circle at 7px 7px, color-mix(in srgb, var(--primary) 28%, transparent) 1.15px, transparent 1.5px),
    linear-gradient(32deg, transparent 49.7%, color-mix(in srgb, var(--primary) 8%, transparent) 49.9%, color-mix(in srgb, var(--primary) 8%, transparent) 50.1%, transparent 50.3%),
    linear-gradient(148deg, transparent 49.7%, color-mix(in srgb, var(--accent) 7%, transparent) 49.9%, color-mix(in srgb, var(--accent) 7%, transparent) 50.1%, transparent 50.3%),
    radial-gradient(ellipse 74% 34% at 50% -5%, transparent 76%, color-mix(in srgb, var(--primary) 12%, transparent) 76.5%, transparent 77.3%),
    radial-gradient(ellipse 70% 31% at 50% 104%, transparent 76%, color-mix(in srgb, var(--accent) 10%, transparent) 76.5%, transparent 77.3%);
  background-size:
    52px 52px,
    104px 90px,
    104px 90px,
    100% 58%,
    100% 58%;
  background-position:
    0 0,
    0 0,
    52px 0,
    center top,
    center bottom;
  background-repeat: repeat, repeat, repeat, no-repeat, no-repeat;
  -webkit-mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.72), rgba(0, 0, 0, 0.32) 72%, rgba(0, 0, 0, 0.12));
  mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.72), rgba(0, 0, 0, 0.32) 72%, rgba(0, 0, 0, 0.12));
}

:is(
  [data-mobile-context],
  [data-m4a-context],
  [data-m4b-context],
  [data-m4c-context],
  [data-m4d-context]
)::before {
  opacity: 0.20;
}

[data-theme='high-contrast'] :is(
  [data-dc-mobile-shell],
  [data-mobile-context],
  [data-m4a-context],
  [data-m4b-context],
  [data-m4c-context],
  [data-m4d-context]
)::before {
  display: none !important;
}

@media (prefers-reduced-transparency: reduce) {
  :is(
    [data-dc-mobile-shell],
    [data-mobile-context],
    [data-m4a-context],
    [data-m4b-context],
    [data-m4c-context],
    [data-m4d-context]
  )::before {
    opacity: 0.18;
  }
}
'''
css_path.write_text(css.rstrip() + motif + '\n', encoding='utf-8')

nav_path = ROOT / 'frontend/src/features/mobile/Dashboard/components/MobileBottomNav.tsx'
old = nav_path.read_text(encoding='utf-8')
if "scale-105" not in old or "backdrop-blur-2xl" not in old:
    raise SystemExit('MobileBottomNav baseline mismatch')

new = r'''import { motion, useReducedMotion } from 'framer-motion';
import { Calendar, TrendingUp, MessageSquare, ShieldCheck, Bot } from 'lucide-react';
import { cn } from '../../../../utils/cn';
import type { Tab, Snapshot } from '../types';
import type { LabJob } from '../../../../types/labJob';

export function MobileBottomNav({
  activeTab,
  setActiveTab,
  totalCount,
  termineCount,
  labJobs,
  snapshot,
}: {
  activeTab: Tab;
  setActiveTab: (t: Tab) => void;
  totalCount: number;
  termineCount: number;
  labJobs: LabJob[];
  snapshot: Snapshot | null;
}) {
  const reduceMotion = useReducedMotion();
  const tabs = [
    {
      id: 'agenda' as Tab,
      icon: Calendar,
      label: 'Agenda',
      dot: totalCount > 0 && termineCount < totalCount,
      allowedRoles: ['DENTISTE', 'ADMIN', 'SECRETAIRE'],
    },
    {
      id: 'finance' as Tab,
      icon: TrendingUp,
      label: 'Finance',
      dot: false,
      allowedRoles: ['DENTISTE', 'ADMIN'],
    },
    {
      id: 'lab' as Tab,
      icon: MessageSquare,
      label: 'Envois Labo',
      dot: labJobs.some(job => job.status === 'PRESCRIPTION'),
      allowedRoles: ['DENTISTE', 'ADMIN'],
    },
    {
      id: 'bot' as Tab,
      icon: Bot,
      label: 'Assistant',
      dot: false,
      allowedRoles: ['DENTISTE', 'ADMIN', 'SECRETAIRE'],
    },
    {
      id: 'securite' as Tab,
      icon: ShieldCheck,
      label: 'Sécurité',
      dot: false,
      allowedRoles: ['DENTISTE', 'ADMIN'],
    },
  ].filter(tab => tab.allowedRoles.includes(snapshot?.role ?? 'DENTISTE'));

  return (
    <nav
      data-mobile-bottom-nav
      aria-label="Navigation mobile principale"
      className="fixed left-3 right-3 mx-auto h-[76px] max-w-[720px] backdrop-blur-2xl border rounded-[34px] flex items-center gap-1 px-2 shadow-elite-hover z-50"
      style={{
        backgroundColor: 'var(--glass-bg)',
        borderColor: 'var(--glass-border)',
        bottom: 'max(12px, env(safe-area-inset-bottom))',
      }}
    >
      {tabs.map(({ id, icon: Icon, label, dot }) => {
        const isActive = activeTab === id;
        return (
          <button
            key={id}
            type="button"
            aria-current={isActive ? 'page' : undefined}
            onClick={() => {
              if (typeof navigator !== 'undefined' && navigator.vibrate) navigator.vibrate(50);
              setActiveTab(id);
            }}
            className={cn(
              'relative min-h-[52px] min-w-0 flex-1 rounded-[22px] flex flex-col items-center justify-center gap-0.5 touch-manipulation transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40',
              isActive ? 'text-primary' : 'text-text-muted'
            )}
          >
            <span className="relative grid h-8 w-11 place-items-center">
              {isActive && (
                <motion.span
                  data-mobile-nav-active-pill
                  layoutId="mobile-nav-active-pill"
                  className="absolute inset-0 rounded-full border border-primary/15 bg-primary/10 shadow-[inset_0_1px_0_rgba(255,255,255,0.58)]"
                  transition={reduceMotion
                    ? { duration: 0 }
                    : { type: 'spring', stiffness: 420, damping: 32, mass: 0.7 }}
                />
              )}
              <Icon size={20} strokeWidth={isActive ? 2.35 : 1.9} className="relative z-10" />
              {dot && (
                <span className="absolute right-0.5 top-0.5 z-20 h-1.5 w-1.5 rounded-full bg-primary ring-2 ring-white/80" />
              )}
            </span>
            <span className={cn(
              'max-w-full truncate whitespace-nowrap text-[8px] sm:text-[9px] uppercase tracking-[0.09em]',
              isActive ? 'font-black' : 'font-bold'
            )}>
              {label}
            </span>
          </button>
        );
      })}
    </nav>
  );
}
'''
nav_path.write_text(new, encoding='utf-8')
print('M6-G1 product patch materialized')
