import React, { useMemo, useState } from 'react';
import { AlertTriangle, ArrowLeft, ArrowRight, CheckCircle2, Database, GitCompareArrows, LockKeyhole, RotateCcw, ShieldAlert } from 'lucide-react';
import { evaluateMapping, setColumnChoice, setTableChoice, suggestExact, syntheticSource, syntheticTarget,
  type MappingChoices, type SourceInventory, type TargetManifest } from './mappingStudioModel';

/** Inert metadata-only staff preview: NO API, imports, localStorage or credential handling. */
export const MappingStudio: React.FC<{ source?: SourceInventory; target?: TargetManifest }> = ({
  source = syntheticSource, target = syntheticTarget,
}) => {
  const [step, setStep] = useState<'source' | 'mapping' | 'review'>('source');
  const [choices, setChoices] = useState<MappingChoices>({});
  const review = useMemo(() => evaluateMapping(source, target, choices), [source, target, choices]);
  const progress = review.total > 0 ? Math.round(review.reviewed / review.total * 100) : 0;
  const targetNames = target.tables.map(table => table.name);
  const chooseTable = (name: string, choice: string) => {
    setChoices(previous => setTableChoice(previous, name, choice === '__unmapped__' ? null : choice));
    setStep('mapping');
  };
  const chooseColumn = (table: string, column: string, choice: string) => {
    setChoices(previous => setColumnChoice(previous, table, column, choice === '__unmapped__' ? null : choice));
    setStep('mapping');
  };
  const reset = () => { setChoices({}); setStep('source'); };
  const format = (value: string | null | undefined) => value === undefined ? 'À décider' : value === null ? 'Non mappé' : value;
  const selectClass = 'w-full min-w-0 rounded-xl border border-border-main bg-card-bg p-3 text-sm font-semibold text-text-main outline-none focus-visible:ring-2 focus-visible:ring-primary/40 disabled:opacity-50';

  return (
    <section data-testid="migration-mapping-studio" className="mx-auto w-full max-w-6xl space-y-5 text-text-main">
      <header className="relative overflow-hidden rounded-3xl border border-border-main bg-card-bg p-5 shadow-sm sm:p-8">
        <div aria-hidden="true" className="pointer-events-none absolute -right-14 -top-20 h-64 w-64 rounded-full bg-primary/10 blur-3xl" />
        <div className="relative flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0 space-y-3">
            <p className="text-xs font-black uppercase tracking-widest text-primary">Digital Crown · Migration SQL</p>
            <h1 className="text-2xl font-black tracking-tight sm:text-3xl">Studio des correspondances</h1>
            <p className="max-w-2xl text-sm leading-relaxed text-text-muted">Préparez un brouillon entre tables et colonnes. Chaque choix doit être explicite : aucune suggestion n'est appliquée automatiquement.</p>
          </div>
          <div className="space-y-2 lg:text-right">
            <span className="inline-flex items-center gap-2 rounded-full border border-amber-300 bg-amber-50 px-3 py-2 text-xs font-black text-amber-950">
              <ShieldAlert size={16} /> Simulation · aucune migration
            </span>
            <p className="text-xs font-semibold text-text-muted">Mode technicien · métadonnées synthétiques</p>
          </div>
        </div>
      </header>
      <div role="status" className="flex items-start gap-3 rounded-2xl border border-amber-300 bg-amber-50 p-4 text-amber-950">
        <LockKeyhole size={22} className="shrink-0" />
        <div><p className="text-sm font-black">En cours de construction — import strictement désactivé</p>
          <p className="mt-1 text-xs leading-relaxed">Démonstration sans données patient et sans base cabinet. Le schéma cible est fictif. Aucune approbation administrateur, sauvegarde ou validation clinique.</p>
        </div>
      </div>
      <nav aria-label="Étapes du Mapping Studio" className="grid grid-cols-1 gap-2 sm:grid-cols-3">
        {([
          ['source', '01', 'Inventaire', 'Schéma synthétique'],
          ['mapping', '02', 'Correspondances', 'Décisions explicites'],
          ['review', '03', 'Contrôle', 'Brouillon non autorisant'],
        ] as const).map(([key, number, label, subtitle]) => (
          <button key={key} type="button" disabled={key === 'review' && !review.complete} onClick={() => setStep(key)}
            aria-current={step === key ? 'step' : undefined}
            className={'flex min-w-0 items-center gap-3 rounded-2xl border p-4 text-left focus-visible:ring-2 focus-visible:ring-primary/40 disabled:cursor-not-allowed disabled:opacity-45 ' +
              (step === key ? 'border-primary bg-primary/10' : 'border-border-main bg-card-bg')}>
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-sm font-black text-primary">{number}</span>
            <span className="min-w-0"><strong className="block text-sm">{label}</strong><small className="block text-xs text-text-muted">{subtitle}</small></span>
          </button>
        ))}
      </nav>
      {step === 'source' && (
        <div data-testid="mapping-source-step" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <section className="min-w-0 space-y-3 rounded-2xl border border-border-main bg-card-bg p-5">
              <h2 className="flex items-center gap-2 text-lg font-black"><Database className="text-primary" /> Source · copie fictive</h2>
              <p className="text-xs text-text-muted">Dialecte : {source.dialect_declared} · {source.source_format}</p>
              <p className="text-sm font-bold">{source.tables.length} tables inventoriées</p>
              <p className="break-all rounded-lg bg-primary/5 p-3 font-mono text-[11px] text-text-muted">SHA-256 fourni : {source.sha256}</p>
              <p className="text-xs font-semibold text-amber-800">Aucune ligne ou relation réellement vérifiée.</p>
            </section>
            <section className="min-w-0 space-y-3 rounded-2xl border border-border-main bg-card-bg p-5">
              <h2 className="flex items-center gap-2 text-lg font-black"><GitCompareArrows className="text-primary" /> Cible · manifeste illustratif</h2>
              <p className="break-all text-xs text-text-muted">Révision : {target.schema_revision}</p>
              <p className="text-sm font-bold">{target.tables.length} tables cibles fictives</p>
              <p className="text-xs font-semibold text-amber-800">Ne reflète pas le vrai schéma SQLAlchemy de Digital Crown.</p>
              <p className="text-xs text-text-muted">L'adaptateur serveur authentifié est une étape ultérieure.</p>
            </section>
          </div>
          {source.tables.map(table => (
            <div key={table.source_name} className="flex min-w-0 flex-col gap-2 rounded-xl border border-border-main bg-card-bg p-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="min-w-0"><strong className="break-words text-sm">{table.source_name}</strong><p className="text-xs text-text-muted">{table.columns.length} colonnes</p></div>
              <span className="text-xs font-semibold text-text-muted">Suggestion : {suggestExact(table.source_name, target.tables.map(t => t.name)) ?? 'aucune'}</span>
            </div>
          ))}
          <button type="button" onClick={() => setStep('mapping')} className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-black text-white sm:w-auto">Choisir les correspondances <ArrowRight size={17} /></button>
        </div>
      )}
      {step === 'mapping' && (
        <div data-testid="mapping-decisions-step" className="space-y-5">
          <div className="rounded-2xl border border-border-main bg-card-bg p-5">
            <div className="flex items-center justify-between gap-2"><strong className="text-sm">Décisions : {review.reviewed}/{review.total}</strong><span className="text-xs font-black text-primary">{progress}%</span></div>
            <div role="progressbar" aria-label="Progression des décisions" aria-valuenow={review.reviewed} aria-valuemin={0} aria-valuemax={review.total} className="mt-3 h-2 overflow-hidden rounded-full bg-primary/10"><div className="h-full rounded-full bg-primary" style={{ width: progress + '%' }} /></div>
            <p className="mt-3 text-xs text-text-muted">Non mappé est un choix explicite à faire par champ. Aucune valeur proposée n'est présélectionnée.</p>
          </div>
          {source.tables.map((table, ti) => {
            const choice = choices[table.source_name];
            const dest = target.tables.find(candidate => candidate.name === choice?.target);
            return (
              <section key={table.source_name} data-testid={'mapping-table-' + ti} className="min-w-0 space-y-4 rounded-2xl border border-border-main bg-card-bg p-4 shadow-sm sm:p-6">
                <div className="flex min-w-0 flex-col justify-between gap-4 lg:flex-row">
                  <div className="min-w-0"><p className="text-xs font-black uppercase tracking-widest text-text-muted">Table source {ti + 1}</p><h2 className="break-words text-lg font-black">{table.source_name}</h2><p className="text-xs text-text-muted">Proposé : {suggestExact(table.source_name, targetNames) ?? 'aucun'}</p></div>
                  <div className="min-w-0 w-full lg:max-w-xs">
                    <label htmlFor={'table-choice-' + ti} className="mb-2 block text-xs font-black">Table cible</label>
                    <select id={'table-choice-' + ti} className={selectClass} value={choice?.target === undefined ? '' : choice.target === null ? '__unmapped__' : choice.target} onChange={event => chooseTable(table.source_name, event.target.value)}>
                      <option value="" disabled>Choisir explicitement…</option>
                      <option value="__unmapped__">Ne pas mapper cette table</option>
                      {target.tables.map(t => <option key={t.name} value={t.name}>{t.name}</option>)}
                    </select>
                  </div>
                </div>
                <div className="grid gap-3">
                  {table.columns.map((column, ci) => {
                    const value = choice?.columns[column.name]?.target;
                    const hint = dest ? suggestExact(column.name, dest.columns) : null;
                    const credential = /password|passwd|pwd|secret|token|credential|apikey|api_key|privatekey|private_key|hashed|salt|oauth|session_key|otp|authentication/i.test(column.name);
                    return (
                      <div key={column.name} className="grid min-w-0 gap-2 rounded-xl border border-border-main/80 bg-primary/[0.025] p-3 sm:grid-cols-2 sm:items-center">
                        <div className="min-w-0">
                          <label htmlFor={'column-choice-' + ti + '-' + ci} className="block break-words text-sm font-black">{column.name}</label>
                          <p className="text-xs text-text-muted">{column.declared_type} · {credential ? 'Credential : mapping interdit' : 'Proposé : ' + (hint ?? 'aucun')}</p>
                        </div>
                        <select id={'column-choice-' + ti + '-' + ci} className={selectClass} disabled={choice?.target === undefined}
                          value={value === undefined ? '' : value === null ? '__unmapped__' : value} onChange={event => chooseColumn(table.source_name, column.name, event.target.value)}>
                          <option value="" disabled>Décider pour ce champ…</option>
                          <option value="__unmapped__">Non mappé (explicite)</option>
                          {!credential && dest?.columns.map(col => <option key={col} value={col}>{col}</option>)}
                        </select>
                      </div>
                    );
                  })}
                </div>
              </section>
            );
          })}
          {review.issues.some(issue => issue !== 'REVIEW_INCOMPLETE') && (
            <p role="alert" className="flex items-center gap-2 rounded-xl border border-rose-300 bg-rose-50 p-4 text-sm font-bold text-rose-900">
              <AlertTriangle size={19} /> Choix incompatibles ou collision : {review.issues.filter(issue => issue !== 'REVIEW_INCOMPLETE').join(', ')}
            </p>
          )}
          <div className="flex flex-col gap-3 sm:flex-row">
            <button type="button" onClick={() => setStep('source')} className="inline-flex justify-center gap-2 rounded-xl border border-border-main bg-card-bg px-5 py-3 text-sm font-black"><ArrowLeft size={17} /> Inventaire</button>
            <button type="button" disabled={!review.complete} onClick={() => setStep('review')} className="inline-flex justify-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-black text-white disabled:cursor-not-allowed disabled:opacity-40">Contrôler le brouillon <ArrowRight size={17} /></button>
            <button type="button" onClick={reset} className="inline-flex justify-center gap-2 rounded-xl border border-border-main px-5 py-3 text-sm font-black text-text-muted sm:ml-auto"><RotateCcw size={17} /> Réinitialiser</button>
          </div>
        </div>
      )}
      {step === 'review' && review.complete && (
        <section data-testid="mapping-review-step" className="space-y-5 rounded-2xl border border-border-main bg-card-bg p-4 sm:p-7">
          <h2 className="flex items-center gap-2 text-xl font-black"><CheckCircle2 className="text-emerald-700" /> Brouillon structurellement complet</h2>
          <p className="text-sm text-text-muted">La présence des décisions ne valide ni les données cliniques, ni l'identité admin, ni l'intégrité du vrai schéma Digital Crown.</p>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">{([
            ['Tables source', review.tableCount], ['Champs source', review.columnCount],
            ['Décisions', review.reviewed], ['Non mappés', review.unmapped],
          ] as const).map(([name, count]) => <div key={name} className="rounded-xl bg-primary/5 p-3"><strong className="block text-2xl font-black">{count}</strong><small className="text-xs text-text-muted">{name}</small></div>)}</div>
          {source.tables.map(table => <div key={table.source_name} className="rounded-xl border border-border-main p-4">
            <p className="break-words text-sm font-black">{table.source_name} → {format(choices[table.source_name]?.target)}</p>
            <ul className="mt-2 space-y-1 text-xs text-text-muted">{table.columns.map(col => <li key={col.name} className="break-words">{col.name} → {format(choices[table.source_name]?.columns[col.name]?.target)}</li>)}</ul>
          </div>)}
          <div role="status" className="rounded-xl bg-amber-50 p-4 text-sm font-bold text-amber-950">Brouillon non sauvegardé. Approbation admin, dry-run, backup, import et rollback non disponibles.</div>
          <button type="button" disabled data-testid="migration-import-disabled" className="w-full cursor-not-allowed rounded-xl bg-slate-900 px-6 py-4 text-sm font-black text-white opacity-55 sm:w-auto">Importer les données — désactivé</button>
          <button type="button" onClick={() => setStep('mapping')} className="mt-2 w-full rounded-xl border border-border-main px-5 py-3 text-sm font-black sm:ml-3 sm:w-auto">Corriger les correspondances</button>
        </section>
      )}
      <footer className="rounded-2xl border border-border-main bg-card-bg p-4 text-xs leading-relaxed text-text-muted">
        <strong>Limites.</strong> Métadonnées fictives uniquement ; aucune extraction de dossiers, sauvegarde de profils ou transfert réseau. La version opérationnelle devra vérifier les schémas côté serveur, l'autorité de l'administrateur, le tenant et le dry-run.
      </footer>
    </section>
  );
};
export default MappingStudio;
