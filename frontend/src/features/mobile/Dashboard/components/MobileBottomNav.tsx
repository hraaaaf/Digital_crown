import { motion, useReducedMotion } from 'framer-motion';
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
