import { cn } from '../../../utils/cn';

interface LegalAnnotationsSwitchProps {
  checked: boolean;
  onChange: () => void;
}

export function LegalAnnotationsSwitch({ checked, onChange }: LegalAnnotationsSwitchProps) {
  return (
    <div className="flex items-center gap-2 mb-3 px-1">
      <button
        type="button"
        onClick={onChange}
        className={cn(
          'relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50',
          checked ? 'bg-primary' : 'bg-slate-200 dark:bg-slate-700',
        )}
        role="switch"
        aria-checked={checked}
        aria-label="Afficher les mentions légales de radioprotection"
      >
        <span
          className={cn(
            'pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200',
            checked ? 'translate-x-4' : 'translate-x-0',
          )}
        />
      </button>
      <span className="text-[10px] font-bold text-text-muted uppercase tracking-widest">
        Mentions légales (Radioprotection)
      </span>
    </div>
  );
}
