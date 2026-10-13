import { Bell, RefreshCw } from 'lucide-react';
import Logo from '../../assets/logo.png';
import { greeting } from '../mobile/Dashboard/utils';

export function PatientPocketHeader({ title, subtitle, busy, onSync, onMore, paired }: {
  title?: string;
  subtitle: string;
  busy: boolean;
  paired: boolean;
  onSync: () => void;
  onMore: () => void;
}) {
  return <header className="relative z-10 pb-5 pt-[max(18px,env(safe-area-inset-top))]">
    <div className="mb-4 flex items-center justify-between gap-2 sm:gap-3">
      <div data-dc-pocket-brand className="flex min-w-0 items-center gap-2">
        <img src={Logo} alt="Digital Crown Pocket" className="h-auto w-[92px] min-w-0 origin-left object-contain drop-shadow-sm min-[430px]:w-24 sm:w-28" />
        <span className="shrink-0 rounded-full border border-primary/15 bg-primary/10 px-2 py-1 text-[10px] font-bold uppercase tracking-[0.14em] text-primary">Pocket</span>
      </div>
      {paired && <div className="flex shrink-0 items-center gap-1.5 sm:gap-2">
        <button type="button" aria-label="Ouvrir les notifications patient" onClick={onMore} className="flex h-11 w-11 items-center justify-center rounded-[16px] border border-glass-border bg-card text-primary shadow-elite backdrop-blur-md active:scale-95" style={{ backgroundColor: 'var(--glass-bg)' }}><Bell size={18} aria-hidden="true" /></button>
        <button type="button" aria-label="Synchroniser mon espace" onClick={onSync} disabled={busy} className="flex h-11 w-11 items-center justify-center rounded-[16px] border border-glass-border bg-card text-primary shadow-elite backdrop-blur-md disabled:opacity-40 active:scale-95" style={{ backgroundColor: 'var(--glass-bg)' }}><RefreshCw size={18} aria-hidden="true" className={busy ? 'animate-spin' : ''} /></button>
      </div>}
    </div>
    <h1 className="text-[28px] font-bold leading-tight tracking-tight text-text-main min-[430px]:text-[31px]">{title || `${greeting()},`}</h1>
    <p className="mt-1.5 text-[13px] font-medium text-text-muted">{subtitle}</p>
  </header>;
}
