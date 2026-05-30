import { Calendar, TrendingUp, MessageSquare, ShieldCheck } from 'lucide-react';
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
  return (
    <nav className="fixed bottom-6 left-6 right-6 h-[68px] backdrop-blur-2xl border rounded-[32px] flex items-center justify-around px-6 shadow-elite-hover z-50" style={{ backgroundColor: 'var(--glass-bg)', borderColor: 'var(--glass-border)' }}>
      {([
        {
          id: 'agenda' as Tab,
          icon: Calendar,
          label: 'Agenda',
          dot: totalCount > 0 && termineCount < totalCount,
          allowedRoles: ['DENTISTE', 'ADMIN', 'SECRETAIRE']
        },
        {
          id: 'finance' as Tab,
          icon: TrendingUp,
          label: 'Finance',
          dot: false,
          allowedRoles: ['DENTISTE', 'ADMIN']
        },
        {
          id: 'lab' as Tab,
          icon: MessageSquare,
          label: 'Envois Labo',
          dot: labJobs.some(job => job.status === 'PRESCRIPTION'),
          allowedRoles: ['DENTISTE', 'ADMIN']
        },
        {
          id: 'securite' as Tab,
          icon: ShieldCheck,
          label: 'Sécurité',
          dot: false,
          allowedRoles: ['DENTISTE', 'ADMIN']
        },
      ]).filter(t => t.allowedRoles.includes(snapshot?.role ?? 'DENTISTE')).map(({ id, icon: Icon, label, dot }) => (
        <button
          key={id}
          onClick={() => setActiveTab(id)}
          className={cn(
            'relative flex flex-col items-center gap-1 transition-all duration-200',
            activeTab === id ? 'text-primary scale-105' : 'text-text-muted'
          )}
        >
          {dot && (
            <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 bg-primary rounded-full animate-pulse" />
          )}
          <Icon size={21} />
          <span className="text-[9px] font-black uppercase tracking-widest">{label}</span>
        </button>
      ))}
    </nav>
  );
}
