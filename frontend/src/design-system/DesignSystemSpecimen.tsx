import React, { useState } from 'react';
import { AlertTriangle, Check, ChevronDown, Loader2, Trash2 } from 'lucide-react';

type Theme = 'default' | 'dark' | 'high-contrast';

const themes: { id: Theme; label: string; className: string }[] = [
  { id: 'default', label: 'Default', className: '' },
  { id: 'dark', label: 'Dark', className: 'dark' },
  { id: 'high-contrast', label: 'High Contrast', className: 'high-contrast' },
];

export default function DesignSystemSpecimen() {
  const [theme, setTheme] = useState<Theme>('default');
  const [loading, setLoading] = useState(false);
  const themeClass = themes.find((item) => item.id === theme)?.className ?? '';

  return (
    <div className={themeClass} data-theme={theme === 'default' ? undefined : theme}>
      <main className="min-h-screen bg-medical-pearl p-3 text-text-main sm:p-5 lg:p-8">
        <div className="mx-auto max-w-6xl space-y-4 sm:space-y-6">
          <header className="rounded-elite border border-border-main bg-card-bg p-5 shadow-elite sm:p-7">
            <p className="text-[10px] font-black uppercase tracking-[0.18em] text-primary">Digital Crown · specimen isolé</p>
            <div className="mt-2 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
              <div>
                <h1 className="font-outfit text-2xl font-black tracking-tight sm:text-3xl">Primitives UI v0.5</h1>
                <p className="mt-1 max-w-2xl text-sm font-semibold text-text-muted">Référence technique sans route produit, logique clinique, API ou donnée patient.</p>
              </div>
              <div className="flex flex-wrap gap-2" aria-label="Thème du specimen">
                {themes.map((item) => (
                  <button key={item.id} type="button" onClick={() => setTheme(item.id)}
                    className={`min-h-11 rounded-xl border px-3 text-xs font-black transition-elite ${theme === item.id ? 'border-primary bg-primary text-white' : 'border-border-main bg-card-bg text-text-muted hover:text-primary'}`}>
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
          </header>

          <section className="grid gap-4 lg:grid-cols-2">
            <SpecimenCard title="Boutons" eyebrow="Actions">
              <div className="flex flex-wrap gap-2">
                <button className="min-h-11 rounded-xl bg-primary px-4 text-xs font-black uppercase tracking-wider text-white">Enregistrer</button>
                <button className="min-h-11 rounded-xl border border-border-main bg-card-bg px-4 text-xs font-black text-text-muted hover:text-primary">Annuler</button>
                <button className="min-h-11 rounded-xl border border-rose-300 bg-card-bg px-4 text-xs font-black text-rose-700">Supprimer</button>
                <button disabled className="min-h-11 rounded-xl bg-primary px-4 text-xs font-black text-white opacity-40">Disabled</button>
                <button onClick={() => { setLoading(true); window.setTimeout(() => setLoading(false), 900); }} className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-primary px-4 text-xs font-black text-white">
                  {loading && <Loader2 className="animate-spin" size={15} />}{loading ? 'Traitement…' : 'Tester loading'}
                </button>
              </div>
            </SpecimenCard>

            <SpecimenCard title="Champs" eyebrow="Formulaires">
              <div className="grid gap-3 sm:grid-cols-2">
                <Field label="Patient"><input className="h-11 w-full rounded-xl border border-border-main bg-background px-3 text-sm font-bold text-text-main outline-none focus:ring-2 focus:ring-primary/20" defaultValue="Jean Dupont" /></Field>
                <Field label="Statut"><div className="relative"><select className="h-11 w-full appearance-none rounded-xl border border-border-main bg-background px-3 pr-9 text-sm font-bold text-text-main outline-none focus:ring-2 focus:ring-primary/20" defaultValue="actif"><option value="actif">Actif</option><option value="archive">Archivé</option></select><ChevronDown className="pointer-events-none absolute right-3 top-3.5 text-text-muted" size={16}/></div></Field>
                <Field label="Erreur"><input aria-invalid="true" className="h-11 w-full rounded-xl border border-rose-400 bg-background px-3 text-sm font-bold text-text-main outline-none" defaultValue="Valeur invalide" /><span role="alert" className="mt-1 block text-xs font-bold text-rose-700">Vérifiez ce champ.</span></Field>
                <Field label="Compact clinique"><input className="h-9 w-full rounded-lg border border-border-main bg-background px-2.5 text-xs font-bold text-text-main outline-none focus:ring-2 focus:ring-primary/20" defaultValue="T1" /></Field>
              </div>
            </SpecimenCard>
          </section>

          <section className="grid gap-4 lg:grid-cols-3">
            <SpecimenCard title="État vide" eyebrow="Empty"><div className="rounded-2xl border-2 border-dashed border-border-main bg-background p-7 text-center"><p className="text-sm font-black">Aucun document</p><p className="mt-1 text-xs font-semibold text-text-muted">Ajoutez un document pour commencer.</p></div></SpecimenCard>
            <SpecimenCard title="Chargement" eyebrow="Loading"><div className="flex min-h-28 items-center justify-center gap-2 text-text-muted"><Loader2 className="animate-spin text-primary" size={22}/><span className="text-sm font-bold">Chargement…</span></div></SpecimenCard>
            <SpecimenCard title="Erreur locale" eyebrow="Error"><div role="alert" className="flex gap-3 rounded-xl bg-rose-50 p-4 text-rose-800"><AlertTriangle className="shrink-0" size={18}/><div><p className="text-sm font-black">Impossible de charger</p><p className="mt-1 text-xs font-semibold">Réessayez sans bloquer le reste de l’écran.</p></div></div></SpecimenCard>
          </section>

          <section className="rounded-elite border border-border-main bg-card-bg p-5 shadow-elite sm:p-7">
            <p className="text-[10px] font-black uppercase tracking-[0.18em] text-primary">Overlay</p>
            <h2 className="mt-1 text-lg font-black">Confirmation destructive</h2>
            <div className="mt-4 max-w-sm rounded-3xl border border-border-main bg-card-bg p-5 shadow-elite">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-rose-50 text-rose-700"><Trash2 size={21}/></div>
              <h3 className="mt-4 text-lg font-black">Supprimer cet élément ?</h3>
              <p className="mt-1 text-sm font-semibold text-text-muted">Une action irréversible doit rester explicite et distincte.</p>
              <div className="mt-5 flex gap-2"><button className="min-h-11 flex-1 rounded-xl border border-border-main font-black text-text-muted">Annuler</button><button className="min-h-11 flex-1 rounded-xl bg-rose-600 font-black text-white">Supprimer</button></div>
            </div>
          </section>

          <footer className="flex items-center gap-2 px-1 text-xs font-bold text-text-muted"><Check size={14} className="text-primary"/>Aucun appel API · aucune donnée patient · aucun changement de route produit.</footer>
        </div>
      </main>
    </div>
  );
}

function SpecimenCard({ title, eyebrow, children }: { title: string; eyebrow: string; children: React.ReactNode }) {
  return <article className="rounded-elite border border-border-main bg-card-bg p-5 shadow-elite"><p className="text-[10px] font-black uppercase tracking-[0.16em] text-primary">{eyebrow}</p><h2 className="mt-1 mb-4 text-lg font-black">{title}</h2>{children}</article>;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="block"><span className="mb-1.5 block text-[10px] font-black uppercase tracking-widest text-text-muted">{label}</span>{children}</label>;
}
