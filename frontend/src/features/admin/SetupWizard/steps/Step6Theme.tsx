import React from 'react';
import { Sun, Moon, Sparkles, HeartPulse, CheckCircle2, Info } from 'lucide-react';
import { cn } from '../../../../utils/cn';

interface Props {
  selectedTheme: 'elite' | 'emerald' | 'rose' | 'prestige';
  setSelectedTheme: (v: 'elite' | 'emerald' | 'rose' | 'prestige') => void;
}

const THEMES = [
  { id: 'elite' as const, label: 'Lumière Pure', class: 'bg-card border-border-main', desc: 'Clarté & Pro', icon: Sun, iconColor: 'text-amber-500' },
  { id: 'emerald' as const, label: 'Escale Zen', class: 'bg-emerald-500/5 border-emerald-500/20', desc: 'Sérénité', icon: Sparkles, iconColor: 'text-emerald-500' },
  { id: 'rose' as const, label: 'Rose Prestige', class: 'bg-rose-500/5 border-rose-500/20', desc: 'Esthétique', icon: HeartPulse, iconColor: 'text-rose-500' },
  { id: 'prestige' as const, label: 'Nuit Intense', class: 'bg-card border-border-main text-text-main', desc: 'Luxe', icon: Moon, iconColor: 'text-primary' },
] as const;

export const Step6Theme: React.FC<Props> = ({ selectedTheme, setSelectedTheme }) => (
  <div className="space-y-6 animate-in fade-in duration-300">
    <div className="text-center mb-8">
      <h2 className="text-2xl font-black text-text-main">Design & Ambiance</h2>
      <p className="text-sm text-text-muted">Prévisualisez le même thème que dans Réglages.</p>
    </div>

    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {THEMES.map((t) => (
        <button
          type="button"
          key={t.id}
          onClick={() => setSelectedTheme(t.id)}
          className={cn(
            "flex items-center sm:flex-col sm:items-center gap-4 p-5 sm:p-6 rounded-[2rem] border-2 transition-all group relative overflow-hidden text-left sm:text-center",
            t.class,
            selectedTheme === t.id ? "ring-4 ring-primary/20 border-primary shadow-xl shadow-primary/10" : "opacity-70 hover:opacity-100"
          )}
        >
          <div className={cn("inline-flex w-14 h-14 shrink-0 rounded-[1.25rem] items-center justify-center transition-transform group-hover:rotate-6", t.id === 'prestige' ? 'bg-white/10' : 'bg-white shadow-inner')}>
            <t.icon size={28} className={t.iconColor} />
          </div>
          <div>
            <span className="block text-[10px] font-black uppercase tracking-[0.2em] mb-1">{t.label}</span>
            <span className="text-[9px] opacity-60 font-medium">{t.desc}</span>
          </div>
          {selectedTheme === t.id && (
            <div className="absolute top-4 right-4"><CheckCircle2 size={20} className="text-primary" /></div>
          )}
        </button>
      ))}
    </div>

    <div className="mt-8 flex items-start gap-3 rounded-2xl border border-blue-100 bg-blue-50/60 p-4 text-blue-900">
      <Info size={18} className="mt-0.5 shrink-0 text-blue-600" />
      <div>
        <p className="text-xs font-black">Aperçu uniquement</p>
        <p className="mt-1 text-[11px] font-medium leading-relaxed text-blue-800/80">Le thème n’est enregistré localement qu’après la confirmation backend finale. Quitter ou échouer pendant l’installation ne modifie pas vos préférences persistantes.</p>
      </div>
    </div>
  </div>
);
