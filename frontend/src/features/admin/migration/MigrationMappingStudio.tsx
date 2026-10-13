import { useId, useMemo, useRef, useState, type ChangeEvent } from 'react';
import { AlertTriangle, ArrowLeft, ArrowRight, CheckCircle2, Database, LockKeyhole } from 'lucide-react';
import {
  isCredentialName, isSupportedJsonSize, parseSourceInventory, parseTargetInventory,
  progress, proposeColumn, proposeTable, type ReviewDecisions,
  type SchemaInventory, type TargetInventory,
} from './MappingStudioPolicy';
import {
  fetchMigrationPreflight, runSyntheticStaffRehearsal,
  downloadOfficialSyntheticFile, dryrunOfficialSyntheticFile, type SyntheticFileDryrun,
  type Preflight, type Rehearsal,
} from './migrationGateway';

type Props = { initialSource?: SchemaInventory; initialTarget?: TargetInventory };
type Stage = 'load' | 'review' | 'summary';
const card = 'rounded-2xl border border-border-main bg-card-bg/80 p-4 shadow-sm sm:p-6';
const inputClass = 'w-full min-w-0 rounded-xl border border-border-main bg-card-bg p-3 text-sm font-semibold text-text-main';
const buttonClass = 'inline-flex min-h-11 items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-bold disabled:cursor-not-allowed disabled:opacity-40';

export function MigrationMappingStudio({ initialSource, initialTarget }: Props) {
  const sourceId = useId();
  const targetId = useId();
  const demoFileId = useId();
  const uploadGeneration = useRef({ source: 0, target: 0 });
  const [source, setSource] = useState<SchemaInventory | null>(initialSource ?? null);
  const [target, setTarget] = useState<TargetInventory | null>(initialTarget ?? null);
  const [decisions, setDecisions] = useState<ReviewDecisions>({});
  const [stage, setStage] = useState<Stage>('load');
  const [error, setError] = useState<string | null>(null);
  const [preflight, setPreflight] = useState<Preflight | null>(null);
  const [rehearsal, setRehearsal] = useState<Rehearsal | null>(null);
  const [gatewayError, setGatewayError] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);
  const [rehearsing, setRehearsing] = useState(false);
  const [officialDemoSha, setOfficialDemoSha] = useState<string | null>(null);
  const [fileResult, setFileResult] = useState<SyntheticFileDryrun | null>(null);
  const [downloadingDemo, setDownloadingDemo] = useState(false);
  const [checkingDemoFile, setCheckingDemoFile] = useState(false);

  async function downloadFixture() {
    setDownloadingDemo(true);
    setOfficialDemoSha(null);
    setFileResult(null);
    setGatewayError(null);
    try {
      const { bytes, sha } = await downloadOfficialSyntheticFile();
      const url = URL.createObjectURL(new Blob([bytes], { type: 'application/vnd.sqlite3' }));
      try {
        const element = document.createElement('a');
        element.href = url;
        element.download = 'digital-crown-synthetic-100x200.db';
        document.body.append(element);
        element.click();
        element.remove();
      } finally {
        // The Blob contains only canonical fake fixture values.
        URL.revokeObjectURL(url);
      }
      setOfficialDemoSha(sha);
    } catch {
      setGatewayError('Téléchargement fictif impossible. Aucun transfert de données autorisé.');
    } finally {
      setDownloadingDemo(false);
    }
  }

  async function checkFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.currentTarget.files?.[0];
    event.currentTarget.value = '';
    setFileResult(null);
    setGatewayError(null);
    if (!file || !officialDemoSha || !preflight?.physical_subset_checked) return;
    setCheckingDemoFile(true);
    try {
      setFileResult(await dryrunOfficialSyntheticFile(file, officialDemoSha));
    } catch {
      setGatewayError('Fichier refusé : seul le fichier fictif Digital Crown téléchargé ici est accepté. Aucune donnée clinique envoyée.');
    } finally {
      setCheckingDemoFile(false);
    }
  }

  async function checkPreflight() {
    setChecking(true);
    setGatewayError(null);
    setPreflight(null);
    setRehearsal(null);
    setFileResult(null);
    setOfficialDemoSha(null);
    try {
      setPreflight(await fetchMigrationPreflight());
    } catch {
      // 401, 403, 423, schema mismatch or transport errors are never treated as ready.
      setGatewayError('Vérification serveur refusée ou indisponible. Aucune importation autorisée.');
    } finally {
      setChecking(false);
    }
  }
  async function rehearseSynthetic() {
    setRehearsing(true);
    setGatewayError(null);
    setRehearsal(null);
    try {
      setRehearsal(await runSyntheticStaffRehearsal());
    } catch {
      setGatewayError('Simulation fictive non certifiée. Aucun dossier patient modifié.');
    } finally {
      setRehearsing(false);
    }
  }
  function useObservedTarget() {
    if (!preflight?.physical_subset_checked || !preflight.target_preview) return;
    try {
      // Target schema is only an OBSERVED subset, never an authorized mapping.
      setTarget(parseTargetInventory(JSON.stringify(preflight.target_preview)));
      setDecisions({});
      setStage('load');
      setError(null);
    } catch {
      setGatewayError('Inventaire cible refusé : données serveur incohérentes.');
    }
  }
  const tally = useMemo(() => source && target ? progress(source, target, decisions) : null, [source, target, decisions]);

  async function loadReport(event: ChangeEvent<HTMLInputElement>, kind: 'source' | 'target') {
    const file = event.currentTarget.files?.[0];
    const generation = ++uploadGeneration.current[kind];
    event.currentTarget.value = '';
    setStage('load');
    setDecisions({});
    setError(null);
    if (kind === 'source') setSource(null); else setTarget(null);
    if (!file) return;
    try {
      if (!isSupportedJsonSize(file.size)) throw new Error('TAILLE_JSON_INVALIDE');
      const contents = await file.text();
      if (uploadGeneration.current[kind] !== generation) return;
      if (kind === 'source') setSource(parseSourceInventory(contents));
      else setTarget(parseTargetInventory(contents));
    } catch (cause) {
      if (uploadGeneration.current[kind] !== generation) return;
      setError(cause instanceof Error ? cause.message : 'RAPPORT_INVALIDE');
    }
  }
  function chooseTable(name: string, selected: string) {
    const value = selected === '' ? undefined : selected === '__unmapped__' ? null : selected;
    setDecisions(previous => ({ ...previous, [name]: { target: value, columns: {} } }));
    setStage('review');
  }
  function chooseColumn(table: string, column: string, selected: string) {
    const value = selected === '' ? undefined : selected === '__unmapped__' ? null : selected;
    setDecisions(previous => {
      const entry = previous[table] || { target: undefined, columns: {} };
      return { ...previous, [table]: { ...entry, columns: { ...entry.columns, [column]: value } } };
    });
    setStage('review');
  }

  return <div data-testid="migration-studio" className="mx-auto flex w-full max-w-6xl min-w-0 flex-col gap-5 pb-12 text-text-main">
    <header className="flex flex-col gap-3 border-b border-border-main pb-5 sm:flex-row sm:items-start sm:justify-between">
      <div className="flex gap-3">
        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary"><Database size={25} /></span>
        <div className="min-w-0">
          <p className="text-xs font-black uppercase tracking-widest text-primary">Digital Crown · migration legacy</p>
          <h1 className="mt-1 text-2xl font-black sm:text-3xl">Mapping Studio</h1>
          <p className="mt-2 text-sm text-text-muted">Préparer les correspondances de colonnes sans toucher aux dossiers patients.</p>
        </div>
      </div>
      <span role="status" className="self-start rounded-full border border-amber-300 bg-amber-50 p-2 text-xs font-bold text-amber-900">
        En construction · Import bloqué
      </span>
    </header>

    <section role="note" aria-label="Limites de certification" className="flex gap-3 rounded-2xl border border-amber-300 bg-amber-50 p-4 text-sm leading-relaxed text-amber-950">
      <AlertTriangle className="mt-1 shrink-0" size={20} />
      <div><strong>Ce parcours ne migre aucune donnée.</strong> Chargez uniquement des inventaires de schémas JSON,
        sans dossiers patients, dumps SQL, mots de passe ni données cliniques. Les fichiers sont analysés
        en mémoire et leur contenu n’est pas envoyé au backend. Seuls un contrôle structurel du serveur et une simulation indépendante de données entièrement fictives peuvent être demandés.
        Un essai de fichier SQLite est possible seulement avec la base **entièrement fictive fournie par Digital Crown**. Aucun véritable export de patient ne doit être sélectionné. Les styles globaux peuvent charger des polices externes. Le schéma cible fourni n’est pas entièrement certifié ;
        aucune approbation administrateur ni dry-run réel n’existe ici.</div>
    </section>

    <section aria-label="Prévol sécurisé du cabinet" className={card + ' space-y-3'}>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div><h2 className="font-black">Service de migration — en construction</h2>
          <p className="mt-1 text-sm text-text-muted">Prévol en lecture seule, réservé au propriétaire connecté sur son poste autorisé.</p></div>
        <button type="button" onClick={() => { void checkPreflight(); }} disabled={checking || rehearsing}
          className={buttonClass + ' border border-border-main'}>
          {checking ? 'Contrôle en cours…' : 'Contrôler le backend sécurisé'}
        </button>
      </div>
      {preflight && <div role="status" className="space-y-2 text-sm">
        <p className="font-bold">{preflight.physical_subset_checked ?
          'Sous-ensemble de tables et révision vérifiés en lecture seule.' :
          'Schéma physique ou révision non conforme : simulation bloquée.'}</p>
        <p className="text-xs text-text-muted">Schéma clinique complet, migration Alembic et import réel : en cours de construction.</p>
        <p className="text-xs text-text-muted">Import de fichiers réels : interdit. Aucun inventaire local n’est transmis.</p>
        <div className="flex flex-col gap-2 sm:flex-row">
          <button type="button" onClick={useObservedTarget}
            disabled={!preflight.physical_subset_checked || !preflight.target_preview}
            className={buttonClass + ' border border-border-main'}>Charger l’aperçu cible observé</button>
          <button type="button" disabled={!preflight.physical_subset_checked || rehearsing || checking}
            onClick={() => { void rehearseSynthetic(); }}
            className={buttonClass + ' border border-border-main'}>
            {rehearsing ? 'Simulation fictive en cours…' : 'Simuler 100 patients et 200 RDV fictifs'}</button>
        </div>
      </div>}
      {preflight?.physical_subset_checked && <div className="space-y-3 rounded-xl border border-border-main p-3 sm:p-4" aria-label="Essai de fichier SQLite fictif">
        <h3 className="text-sm font-black">Essai avec un véritable fichier .db fictif</h3>
        <p className="text-xs text-text-muted">Téléchargez la base générée par Digital Crown (100 patients fictifs, 200 rendez-vous fictifs), puis sélectionnez exactement ce fichier. Le contrôle SHA local refuse tout autre fichier avant envoi au serveur.</p>
        <button type="button" disabled={downloadingDemo || checkingDemoFile} onClick={() => { void downloadFixture(); }}
          className={buttonClass + ' border border-border-main'}>
          {downloadingDemo ? 'Fichier fictif en préparation…' : 'Télécharger la base SQLite fictive'}</button>
        <label htmlFor={demoFileId} className="block text-sm font-bold">Sélectionner uniquement le fichier fictif téléchargé
          <input id={demoFileId} aria-label="Fichier SQLite fictif Digital Crown" type="file" accept=".db,application/vnd.sqlite3"
            disabled={!officialDemoSha || checkingDemoFile || downloadingDemo}
            onChange={event => { void checkFile(event); }}
            className="mt-2 block w-full min-w-0 text-xs file:mr-2 file:rounded-lg file:border-0 file:bg-primary/10 file:p-3 file:font-bold" />
        </label>
        {officialDemoSha && <p role="status" className="text-xs text-text-muted">Fichier fictif préparé · contrôle SHA local activé.</p>}
        {checkingDemoFile && <p role="status" className="text-sm font-bold">Vérification et simulation du fichier fictif en cours…</p>}
        {fileResult && <p role="status" className="rounded-xl border border-emerald-300 bg-emerald-50 p-3 text-sm font-bold text-emerald-950">
          Fichier SQLite fictif vérifié : {fileResult.verified_patients}/100 patients et {fileResult.verified_patient_links}/200 relations contrôlées. Après rollback : {fileResult.after_rollback_patients} patient, {fileResult.after_rollback_appointments} rendez-vous. Aucune écriture dans le cabinet.
        </p>}
      </div>}
      {rehearsal && <p role="status" className="rounded-xl border border-emerald-300 bg-emerald-50 p-3 text-sm font-bold text-emerald-950">
        Simulation fictive : {rehearsal.verified_patients}/100 patients et {rehearsal.verified_patient_links}/200 liens vérifiés,
        {rehearsal.after_rollback_patients} patient et {rehearsal.after_rollback_appointments} RDV conservés après rollback.
        Aucun dossier du cabinet lu ou modifié. Import réel toujours bloqué.
      </p>}
      {gatewayError && <p role="alert" className="rounded-xl border border-red-300 bg-red-50 p-3 text-sm font-bold text-red-800">{gatewayError}</p>}
    </section>

    <nav aria-label="Étapes Mapping Studio" className="grid grid-cols-3 gap-2 text-center text-xs sm:text-sm">
      {([['load','1 · Inventaires'],['review','2 · Correspondances'],['summary','3 · Vérification']] as const).map(([id, text]) =>
        <div key={id} aria-current={stage === id ? 'step' : undefined}
          className={'rounded-xl border p-3 font-bold ' +
            (stage === id ? 'border-primary bg-primary/10 text-primary' : 'border-border-main bg-card-bg text-text-muted')}>{text}</div>)}
    </nav>

    {stage === 'load' && <section aria-label="Choisir les inventaires" className="grid gap-4 lg:grid-cols-2">
      <article className={card}>
        <h2 className="text-lg font-black">1. Schéma source</h2>
        <p className="my-3 text-sm text-text-muted">Rapport JSON de l’inspecteur 05.1, issu d’une copie hors-ligne.</p>
        <label htmlFor={sourceId} className="mb-2 block text-sm font-bold">Rapport source JSON</label>
        <input id={sourceId} aria-label="Rapport source JSON" type="file" accept=".json,application/json"
          onChange={event => { void loadReport(event, 'source'); }}
          className="block w-full min-w-0 text-sm file:mr-2 file:rounded-lg file:border-0 file:bg-primary/10 file:p-3 file:font-bold" />
        <p role="status" className="mt-3 text-xs text-text-muted">
          {source ? source.tables.length + ' tables · SHA ' + source.sourceSha256.slice(0,12) + '…' : 'Aucune source chargée'}
        </p>
      </article>
      <article className={card}>
        <h2 className="text-lg font-black">2. Schéma cible</h2>
        <p className="my-3 text-sm text-text-muted">Manifest de tables/colonnes fourni localement, non certifié par le backend.</p>
        <label htmlFor={targetId} className="mb-2 block text-sm font-bold">Rapport cible JSON</label>
        <input id={targetId} aria-label="Rapport cible JSON" type="file" accept=".json,application/json"
          onChange={event => { void loadReport(event, 'target'); }}
          className="block w-full min-w-0 text-sm file:mr-2 file:rounded-lg file:border-0 file:bg-primary/10 file:p-3 file:font-bold" />
        <p role="status" className="mt-3 text-xs text-text-muted">
          {target ? target.tables.length + ' tables · revision ' + target.schemaRevision : 'Aucune cible chargée'}
        </p>
      </article>
      {error && <p role="alert" className="rounded-xl border border-red-300 bg-red-50 p-3 text-sm font-bold text-red-800 lg:col-span-2">Inventaire refusé : {error}</p>}
      <div className="flex justify-end lg:col-span-2">
        <button type="button" disabled={!source || !target} onClick={() => setStage('review')}
          className={buttonClass + ' bg-primary text-white'}>Examiner les correspondances <ArrowRight size={17} /></button>
      </div>
    </section>}

    {source && target && stage !== 'load' && <>
      <section aria-label="Progression de revue" className={card + ' flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between'}>
        <div><h2 className="font-black">Décisions explicites</h2>
          <p role="status" className="mt-1 text-sm text-text-muted">
            {tally?.reviewed} / {tally?.total} examinées · {tally?.unmapped} non mappées
          </p></div>
        <div className="flex items-center gap-2 text-xs font-bold">{tally?.complete ?
          <CheckCircle2 className="text-emerald-600" size={18} /> : <LockKeyhole className="text-amber-600" size={18} />}
          {tally?.complete ? 'Revue structurelle complète' : 'Revue incomplète'}</div>
      </section>

      {stage === 'review' && <section aria-label="Décisions de mapping" className="space-y-4">
        {source.tables.map(table => {
          const reviewed = decisions[table.name];
          const selectedTable = target.tables.find(t => t.name === reviewed?.target);
          const sensitive = isCredentialName(table.name);
          return <article key={table.name} className={card} data-testid={'mapping-table-'+table.name}>
            <div className="mb-5 flex flex-col gap-3 border-b border-border-main pb-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="min-w-0"><p className="text-xs font-bold uppercase text-text-muted">Table source</p>
                <h3 className="break-all text-lg font-black">{table.name}</h3>
                <p className="mt-1 text-xs text-text-muted">Suggestion : {proposeTable(table.name, target) || 'Aucune'}</p></div>
              <div className="w-full sm:w-64"><label className="mb-2 block text-xs font-bold">Décision sur la table
                <select aria-label={'Destination table '+table.name} className={inputClass}
                  value={reviewed?.target === null ? '__unmapped__' : reviewed?.target ?? ''}
                  onChange={event => chooseTable(table.name, event.target.value)}>
                  <option value="">À décider</option>
                  <option value="__unmapped__">Ne pas importer</option>
                  {!sensitive && target.tables.filter(t => !isCredentialName(t.name)).map(t =>
                    <option key={t.name} value={t.name}>{t.name}</option>)}
                </select></label></div>
            </div>
            {sensitive && <p role="note" className="mb-4 text-sm text-amber-700">Table d’authentification : aucune destination autorisée.</p>}
            <div className="space-y-3">
              {table.columns.map(column => {
                const credential = isCredentialName(column.name);
                const chosen = reviewed?.columns[column.name];
                return <div key={column.name} className="grid min-w-0 gap-3 rounded-xl border border-border-main bg-card-bg/60 p-3 sm:grid-cols-2 sm:items-center">
                  <div className="min-w-0"><p className="break-all text-sm font-bold">{column.name}
                    <span className="ml-2 font-normal text-text-muted">{column.declared_type || ''}</span></p>
                    <p className="mt-1 text-xs text-text-muted">{credential ? 'Secret : mapping interdit' :
                      'Suggestion : '+(proposeColumn(column.name, selectedTable) || 'Aucune')}</p></div>
                  <label className="text-xs font-bold">Décision sur la colonne
                    <select aria-label={'Colonne '+table.name+'.'+column.name} className={inputClass}
                      disabled={reviewed?.target === undefined}
                      value={chosen === null ? '__unmapped__' : chosen ?? ''}
                      onChange={event => chooseColumn(table.name, column.name, event.target.value)}>
                      <option value="">À décider</option>
                      <option value="__unmapped__">Laisser non mappée</option>
                      {!credential && selectedTable?.columns.filter(c => !isCredentialName(c.name)).map(c =>
                        <option key={c.name} value={c.name}>{c.name}</option>)}
                    </select>
                  </label>
                </div>;
              })}
            </div>
          </article>;
        })}
        {!!tally && (tally.collisions > 0 || tally.credentialBlocked > 0) &&
          <p role="alert" className="rounded-xl border border-red-300 bg-red-50 p-3 text-sm text-red-800">
            Collisions ou champs interdits détectés : corrigez les décisions.
          </p>}
        <div className="flex flex-col-reverse justify-between gap-3 sm:flex-row">
          <button type="button" onClick={() => setStage('load')} className={buttonClass + ' border border-border-main'}><ArrowLeft size={17} /> Inventaires</button>
          <button type="button" disabled={!tally?.complete} onClick={() => setStage('summary')} className={buttonClass + ' bg-primary text-white'}>
            Vérifier <ArrowRight size={17} /></button>
        </div>
      </section>}
      {stage === 'summary' && <section aria-label="Synthèse de préparation" className={card + ' space-y-5'}>
        <h2 className="text-xl font-black">Correspondances examinées — non certifiées</h2>
        <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {([['Tables', source.tables.length],['Décisions', tally?.reviewed || 0],['Non mappées', tally?.unmapped || 0],['Collisions', tally?.collisions || 0]] as const).map(([name, val]) =>
            <div key={name} className="rounded-xl border border-border-main p-3"><dt className="text-xs text-text-muted">{name}</dt><dd className="text-2xl font-black">{val}</dd></div>)}
        </dl>
        <h3 className="text-sm font-black">Détail des décisions examinées</h3>
        <ul className="space-y-3" aria-label="Correspondances récapitulées">
          {source.tables.map(table => <li key={table.name} className="rounded-xl border border-border-main p-3">
            <p className="break-all text-sm font-bold">{table.name} → {decisions[table.name]?.target ?? 'Non importée'}</p>
            <ul className="mt-2 space-y-1 pl-3 text-xs text-text-muted">
              {table.columns.map(column => <li key={column.name} className="break-all">
                {column.name} → {decisions[table.name]?.columns[column.name] ?? 'Non mappée'}
              </li>)}
            </ul>
          </li>)}
        </ul>
        <p role="status" className="rounded-xl bg-amber-50 p-4 text-sm font-bold text-amber-950">
          NON VALIDÉ : aucune approbation administrateur, signature de profil, dry-run ou sauvegarde. Aucun import possible.
        </p>
        <div className="flex flex-col justify-between gap-3 sm:flex-row">
          <button type="button" onClick={() => setStage('review')} className={buttonClass + ' border border-border-main'}><ArrowLeft size={17} /> Modifier</button>
          <button type="button" disabled aria-label="Importer — indisponible" className={buttonClass + ' bg-slate-800 text-white'}>
            <LockKeyhole size={17} /> Importer — indisponible
          </button>
        </div>
      </section>}
    </>}
    <footer className="border-t border-border-main pt-4 text-xs leading-relaxed text-text-muted">
      LOT05.2-B, prototype staff. Profils chiffrés, source SQL réelle, validation cible authentifiée, droits serveur et rollback : en cours de construction.
    </footer>
  </div>;
}
export default MigrationMappingStudio;
