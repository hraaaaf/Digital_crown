import { cn } from '../utils/cn';

const ASSURANCE_CONFIG: Record<string, { label: string; className: string }> = {
  CNOPS: { label: 'CNOPS', className: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
  CNSS: { label: 'CNSS', className: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' },
  MUTUELLE_FAR: { label: 'MUT_FAR', className: 'bg-purple-500/10 text-purple-400 border-purple-500/20' },
};
const DEFAULT_CLASS = 'bg-amber-500/10 text-amber-400 border-amber-500/20';

interface AssuranceBadgeProps {
  assurance: string | null | undefined;
  size?: 'compact' | 'full';
  /** PatientDetails n'affiche historiquement rien pour AUCUNE/null (pas de badge "Privé"). */
  hideWhenNone?: boolean;
}

export const AssuranceBadge = ({ assurance, size = 'full', hideWhenNone = false }: AssuranceBadgeProps) => {
  if (!assurance || assurance === 'AUCUNE') {
    if (hideWhenNone) return null;
    if (size === 'compact') {
      return <span className="text-text-muted text-[8px] font-black uppercase tracking-widest border border-border-main/40 px-2 py-0.5 rounded-md">Privé</span>;
    }
    return <span className="text-text-muted text-[10px] font-bold uppercase">Privé</span>;
  }
  const config = ASSURANCE_CONFIG[assurance] ?? { label: assurance, className: DEFAULT_CLASS };
  const sizeClasses = size === 'compact' ? 'px-2.5 py-1 rounded-md text-[8px]' : 'px-2.5 py-1 rounded-lg text-[10px]';
  return (
    <span className={cn(sizeClasses, 'font-black uppercase tracking-widest border shadow-sm', config.className)}>
      {config.label}
    </span>
  );
};
