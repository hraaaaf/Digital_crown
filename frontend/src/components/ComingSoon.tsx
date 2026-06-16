import { Construction } from 'lucide-react';

interface ComingSoonProps {
  title: string;
  description?: string;
}

/**
 * Placeholder « Bientôt disponible » pour les sections en construction.
 */
export const ComingSoon = ({ title, description }: ComingSoonProps) => (
  <div className="w-full min-h-[70vh] flex flex-col items-center justify-center p-8 text-center">
    <div className="w-20 h-20 rounded-3xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-500 mb-6 shadow-sm">
      <Construction size={40} />
    </div>
    <span className="text-[10px] font-black uppercase tracking-[0.25em] text-amber-500 mb-2">
      En construction
    </span>
    <h1 className="text-2xl font-black text-text-main tracking-tight mb-3">{title}</h1>
    <p className="text-sm text-text-muted font-bold max-w-md leading-relaxed">
      {description ?? 'Cette section sera bientôt disponible. Merci de votre patience.'}
    </p>
  </div>
);
