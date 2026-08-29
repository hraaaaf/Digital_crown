import React, { useRef, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Database,
  Download,
  FileSearch,
  Loader2,
  RotateCcw,
  Shield,
  Upload,
  X,
} from 'lucide-react';
import { SettingsSection } from '../components/SharedUI';
import { MobileSecurity } from '../../Security/MobileSecurity';
import { AuditLogViewer } from '../../Security/AuditLogViewer';
import { api } from '../../../../services/api';
import toast from 'react-hot-toast';

const backupFilename = (contentDisposition?: string): string => {
  const match = contentDisposition?.match(/filename\*?=(?:UTF-8''|\")?([^\";]+)/i);
  return match?.[1]?.replace(/\"/g, '').trim() || 'digital-crown-backup.enc';
};

type RestoreState = {
  restore_id: string;
  status: string;
  original_name: string;
  size_bytes: number;
  archive_type: string;
  backup_created_at?: string | null;
  compatible: boolean;
  restore_database: boolean;
  restore_media: boolean;
  media_file_count?: number;
  preserved: string[];
  warnings: string[];
  errors: string[];
  prepared_at?: string;
  smoke_check?: string;
  rollback?: string;
  message?: string;
};

type StepTone = 'pending' | 'active' | 'done' | 'danger';

const terminalRestoreStates = new Set(['success', 'rolled_back', 'rollback_failed', 'blocked']);
const restoreInFlightStates = new Set(['scheduled', 'applying', 'restarting', 'rolling_back']);

const formatBytes = (value = 0): string => {
  if (value < 1024) return `${value} o`;
  const units = ['Ko', 'Mo', 'Go', 'To'];
  let current = value / 1024;
  let unit = units[0];
  for (let index = 1; index < units.length && current >= 1024; index += 1) {
    current /= 1024;
    unit = units[index];
  }
  return `${current.toFixed(current >= 10 ? 1 : 2)} ${unit}`;
};

const apiErrorMessage = (error: unknown, fallback: string): string => {
  const response = error as { response?: { data?: { detail?: string } } };
  return response.response?.data?.detail || fallback;
};

const restoreStepTones = (restore: RestoreState | null): StepTone[] => {
  if (!restore) return ['active', 'pending', 'pending', 'pending'];
  if (restore.status === 'blocked') return ['danger', 'pending', 'pending', 'pending'];
  if (restore.status === 'preflight_ready') return ['done', 'active', 'pending', 'pending'];
  if (restore.status === 'prepared') return ['done', 'done', 'active', 'pending'];
  if (['scheduled', 'applying', 'restarting'].includes(restore.status)) return ['done', 'done', 'active', 'pending'];
  if (restore.status === 'success') return ['done', 'done', 'done', 'done'];
  if (restore.status === 'rolling_back') return ['done', 'done', 'done', 'active'];
  if (restore.status === 'rolled_back') return ['done', 'done', 'done', 'danger'];
  if (restore.status === 'rollback_failed') return ['done', 'done', 'danger', 'danger'];
  return ['active', 'pending', 'pending', 'pending'];
};

const stepClasses: Record<StepTone, string> = {
  pending: 'border-slate-200 bg-white text-slate-500',
  active: 'border-blue-300 bg-blue-50 text-blue-900',
  done: 'border-emerald-200 bg-emerald-50 text-emerald-900',
  danger: 'border-rose-200 bg-rose-50 text-rose-900',
};

const dotClasses: Record<StepTone, string> = {
  pending: 'bg-slate-100 text-slate-500',
  active: 'bg-blue-100 text-blue-700',
  done: 'bg-emerald-100 text-emerald-700',
  danger: 'bg-rose-100 text-rose-700',
};

const RestoreLifecycle = ({ restore }: { restore: RestoreState | null }) => {
  const tones = restoreStepTones(restore);
  const steps = [
    ['Analyse', 'Vérifier la sauvegarde'],
    ['Secours', 'Créer un état de retour'],
    ['Restauration', 'Remplacer de façon contrôlée'],
    ['Vérification', 'Contrôler le redémarrage'],
  ];

  return (
    <div className="mt-6 grid grid-cols-2 xl:grid-cols-4 gap-2.5" data-testid="restore-lifecycle">
      {steps.map(([label, detail], index) => {
        const tone = tones[index];
        return (
          <div key={label} className={`min-h-[118px] rounded-2xl border p-3.5 sm:p-4 ${stepClasses[tone]}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-black ${dotClasses[tone]}`}>
              {tone === 'done' ? '✓' : index + 1}
            </div>
            <p className="mt-3 text-sm font-black">{index + 1} · {label}</p>
            <p className="mt-1 text-[11px] sm:text-xs leading-relaxed opacity-70">{detail}</p>
          </div>
        );
      })}
    </div>
  );
};

export const SecurityTab: React.FC = () => {
  const [isExporting, setIsExporting] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isPreparing, setIsPreparing] = useState(false);
  const [isApplying, setIsApplying] = useState(false);
  const [restore, setRestore] = useState<RestoreState | null>(null);
  const [confirmation, setConfirmation] = useState('');
  const [restoreError, setRestoreError] = useState<string | null>(null);
  const restoreInputRef = useRef<HTMLInputElement>(null);

  const handleExportDB = async () => {
    setIsExporting(true);
    try {
      const response = await api.get('/admin/export-db', { responseType: 'blob' });
      const filename = backupFilename(response.headers['content-disposition']);
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/octet-stream' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
      toast.success('Sauvegarde chiffrée créée et téléchargée');
    } catch (error) {
      toast.error('Impossible de créer une sauvegarde chiffrée vérifiée');
      console.error('Verified backup export error:', error);
    } finally {
      setIsExporting(false);
    }
  };

  const handleRestoreFile = async (file?: File) => {
    if (!file) return;
    setIsAnalyzing(true);
    setRestoreError(null);
    setRestore(null);
    setConfirmation('');
    try {
      const body = new FormData();
      body.append('backup', file);
      const response = await api.post<RestoreState>('/admin/restore/preflight', body, { timeout: 120_000 });
      setRestore(response.data);
      if (response.data.compatible) toast.success('Analyse validée, aucune donnée active modifiée');
      else toast.error('Sauvegarde analysée mais incompatible');
    } catch (error) {
      const message = apiErrorMessage(error, 'Impossible d’analyser cette sauvegarde.');
      setRestoreError(message);
      toast.error(message);
    } finally {
      setIsAnalyzing(false);
      if (restoreInputRef.current) restoreInputRef.current.value = '';
    }
  };

  const handlePrepareRestore = async () => {
    if (!restore || restore.status !== 'preflight_ready') return;
    setIsPreparing(true);
    setRestoreError(null);
    try {
      const response = await api.post<RestoreState>(`/admin/restore/${restore.restore_id}/prepare`, {}, { timeout: 600_000 });
      setRestore(response.data);
      setConfirmation('');
      toast.success('Point de secours créé et vérifié');
    } catch (error) {
      const message = apiErrorMessage(error, 'Impossible de préparer le point de secours.');
      setRestoreError(message);
      toast.error(message);
    } finally {
      setIsPreparing(false);
    }
  };

  const pollRestoreStatus = async (restoreId: string) => {
    const deadline = Date.now() + 120_000;
    while (Date.now() < deadline) {
      try {
        const response = await api.get<RestoreState>(`/admin/restore/${restoreId}/status`);
        setRestore(response.data);
        if (terminalRestoreStates.has(response.data.status)) {
          if (response.data.status === 'success') toast.success('Restauration vérifiée après redémarrage');
          else if (response.data.status === 'rolled_back') toast.error('L’état précédent a été restauré automatiquement');
          else if (response.data.status === 'rollback_failed') toast.error('Retour à l’état précédent impossible : intervention locale requise');
          return;
        }
      } catch {
        // Le backend est volontairement indisponible pendant l'apply hors-processus.
      }
      await new Promise((resolve) => window.setTimeout(resolve, 1500));
    }
    setRestoreError('Le redémarrage prend plus de temps que prévu. Le statut réapparaîtra dès le retour du service local.');
  };

  const handleApplyRestore = async () => {
    if (!restore || restore.status !== 'prepared' || confirmation !== 'RESTAURER') return;
    setIsApplying(true);
    setRestoreError(null);
    try {
      const response = await api.post<RestoreState>(`/admin/restore/${restore.restore_id}/apply`, { confirmation });
      setRestore(response.data);
      await pollRestoreStatus(restore.restore_id);
    } catch (error) {
      const message = apiErrorMessage(error, 'Impossible d’engager la restauration.');
      setRestoreError(message);
      toast.error(message);
    } finally {
      setIsApplying(false);
    }
  };

  const handleCancelRestore = async () => {
    if (!restore) {
      setRestoreError(null);
      setConfirmation('');
      return;
    }
    if (restoreInFlightStates.has(restore.status)) return;
    try {
      await api.delete(`/admin/restore/${restore.restore_id}`);
    } catch (error) {
      console.error('Guided restore cancellation error:', error);
    }
    setRestore(null);
    setRestoreError(null);
    setConfirmation('');
  };

  const restoreInFlight = Boolean(restore && restoreInFlightStates.has(restore.status));
  const canPrepare = Boolean(restore?.compatible && restore.status === 'preflight_ready' && !isPreparing && !restoreInFlight);
  const canApply = Boolean(
    restore?.compatible
    && restore.status === 'prepared'
    && confirmation === 'RESTAURER'
    && !restoreInFlight
    && !isApplying,
  );

  return (
    <div className="space-y-12">
      <SettingsSection
        title="Sécurité & Souveraineté"
        subtitle="Contrôlez vos données cliniques et vos accès mobiles."
        icon={<Shield size={32} />}
      >
        <div className="bg-slate-50 border border-slate-200 rounded-[2.5rem] p-6 sm:p-10 flex flex-col items-center justify-center text-center gap-6">
          <div className="w-20 h-20 sm:w-24 sm:h-24 bg-white rounded-full flex items-center justify-center shadow-xl text-slate-700 border border-slate-100">
            <Database size={40} />
          </div>
          <div className="max-w-md">
            <h4 className="font-black text-xl text-slate-800">Sauvegarde chiffrée vérifiée</h4>
            <p className="text-sm text-slate-500 mt-2 font-medium">Crée une copie chiffrée et vérifiée de vos données cabinet avant de la télécharger.</p>
          </div>
          <button
            onClick={handleExportDB}
            disabled={isExporting}
            className="w-full sm:w-auto min-h-[48px] px-6 sm:px-10 py-4 sm:py-5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-2xl font-black transition-all shadow-2xl shadow-emerald-600/20 flex items-center justify-center gap-3 sm:gap-4 group hover:scale-[1.02] disabled:opacity-70 disabled:hover:scale-100 disabled:cursor-not-allowed"
          >
            {isExporting ? <Loader2 size={24} className="animate-spin shrink-0" /> : <Download size={24} className="group-hover:translate-y-1 transition-transform shrink-0" />}
            {isExporting ? 'Création et vérification...' : 'Créer et télécharger la sauvegarde'}
          </button>
        </div>

        <div className="mt-8 rounded-[2.25rem] border border-amber-200 bg-gradient-to-br from-amber-50 via-white to-white p-5 sm:p-8 shadow-sm">
          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-5">
            <div className="flex items-start gap-4 min-w-0">
              <div className="w-12 h-12 rounded-2xl bg-amber-100 text-amber-700 flex items-center justify-center shrink-0">
                <RotateCcw size={24} />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <h4 className="font-black text-xl text-slate-900">Restauration guidée</h4>
                  <span className="px-2.5 py-1 rounded-full text-[11px] font-black tracking-wide uppercase bg-amber-100 text-amber-800">Action sensible</span>
                </div>
                <p className="text-sm text-slate-600 mt-2 font-medium max-w-2xl">
                  Digital Crown vérifie d’abord votre sauvegarde et crée un point de secours avant toute modification.
                </p>
              </div>
            </div>

            <div className="w-full lg:w-auto shrink-0">
              <input
                ref={restoreInputRef}
                type="file"
                className="hidden"
                accept=".enc,.zip,.dcbackup,application/zip,application/octet-stream"
                onChange={(event) => void handleRestoreFile(event.target.files?.[0])}
                disabled={isAnalyzing || restoreInFlight}
              />
              <button
                type="button"
                onClick={() => restoreInputRef.current?.click()}
                disabled={isAnalyzing || restoreInFlight}
                className="w-full lg:w-auto min-h-[48px] px-5 py-3.5 rounded-2xl bg-slate-900 hover:bg-slate-800 text-white font-black flex items-center justify-center gap-3 transition disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {isAnalyzing ? <Loader2 size={20} className="animate-spin" /> : <FileSearch size={20} />}
                {isAnalyzing ? 'Analyse en cours...' : 'Analyser une sauvegarde'}
              </button>
            </div>
          </div>

          <RestoreLifecycle restore={restore} />

          {restoreError && (
            <div className="mt-5 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-bold text-rose-800 flex items-start gap-3">
              <AlertTriangle size={18} className="mt-0.5 shrink-0" />
              <span>{restoreError}</span>
            </div>
          )}

          {restore && (
            <div className="mt-5 rounded-3xl border border-slate-200 bg-white p-4 sm:p-6 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    {restore.compatible ? <CheckCircle2 size={20} className="text-emerald-600 shrink-0" /> : <AlertTriangle size={20} className="text-rose-600 shrink-0" />}
                    <h5 className="font-black text-slate-900">{restore.compatible ? 'Analyse validée' : 'Analyse bloquée'}</h5>
                  </div>
                  <p className="text-xs text-slate-500 mt-1 truncate max-w-xl" title={restore.original_name}>{restore.original_name}</p>
                </div>
                <span className={`self-start px-3 py-1.5 rounded-full text-xs font-black ${restore.compatible ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}`}>
                  {restore.archive_type}
                </span>
              </div>

              <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
                <div className="rounded-2xl bg-slate-50 p-4">
                  <p className="text-[11px] uppercase tracking-wide font-black text-slate-400">Taille</p>
                  <p className="font-black text-slate-800 mt-1">{formatBytes(restore.size_bytes)}</p>
                </div>
                <div className="rounded-2xl bg-slate-50 p-4">
                  <p className="text-[11px] uppercase tracking-wide font-black text-slate-400">Base de données</p>
                  <p className="font-black text-slate-800 mt-1">{restore.restore_database ? 'Restaurée' : 'Préservée'}</p>
                </div>
                <div className="rounded-2xl bg-slate-50 p-4">
                  <p className="text-[11px] uppercase tracking-wide font-black text-slate-400">Médias</p>
                  <p className="font-black text-slate-800 mt-1">{restore.restore_media ? `Restaurés${restore.media_file_count ? ` · ${restore.media_file_count}` : ''}` : 'Préservés'}</p>
                </div>
                <div className="rounded-2xl bg-slate-50 p-4">
                  <p className="text-[11px] uppercase tracking-wide font-black text-slate-400">Date backup</p>
                  <p className="font-black text-slate-800 mt-1 break-words">{restore.backup_created_at || 'Non renseignée'}</p>
                </div>
              </div>

              {(restore.warnings.length > 0 || restore.errors.length > 0) && (
                <div className="mt-4 space-y-2">
                  {restore.warnings.map((warning) => (
                    <div key={warning} className="rounded-xl bg-amber-50 border border-amber-100 px-3 py-2 text-xs font-bold text-amber-800 flex gap-2">
                      <AlertTriangle size={15} className="shrink-0" /> {warning}
                    </div>
                  ))}
                  {restore.errors.map((error) => (
                    <div key={error} className="rounded-xl bg-rose-50 border border-rose-100 px-3 py-2 text-xs font-bold text-rose-800 flex gap-2">
                      <X size={15} className="shrink-0" /> {error}
                    </div>
                  ))}
                </div>
              )}

              {restore.compatible && restore.status === 'preflight_ready' && (
                <div className="mt-6 pt-5 border-t border-slate-100">
                  <div className="rounded-2xl border border-blue-200 bg-blue-50 p-4 sm:p-5">
                    <p className="font-black text-sm text-slate-900">Étape suivante : créer le point de secours</p>
                    <p className="text-xs text-slate-600 mt-1">Aucune donnée active n’est modifiée à cette étape. Vous pourrez encore annuler ensuite.</p>
                    <button
                      type="button"
                      onClick={() => void handlePrepareRestore()}
                      disabled={!canPrepare}
                      className="mt-4 w-full sm:w-auto min-h-[48px] rounded-xl bg-slate-900 hover:bg-slate-800 px-5 py-3 text-sm font-black text-white transition disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      {isPreparing ? <Loader2 size={18} className="animate-spin" /> : <CheckCircle2 size={18} />}
                      {isPreparing ? 'Création du secours...' : 'Préparer la restauration'}
                    </button>
                  </div>
                </div>
              )}

              {restore.compatible && restore.status === 'prepared' && (
                <div className="mt-6 pt-5 border-t border-slate-100">
                  <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-900 flex items-start gap-3">
                    <CheckCircle2 size={18} className="mt-0.5 shrink-0" />
                    <span>Point de secours créé et vérifié. La restauration peut maintenant être engagée.</span>
                  </div>
                  <div className="mt-4 rounded-2xl bg-slate-950 p-4 sm:p-5 text-white">
                    <p className="font-black text-sm">Confirmation finale</p>
                    <p className="text-xs text-slate-300 mt-1">Tapez <span className="font-black text-white">RESTAURER</span>. Digital Crown s’arrêtera puis effectuera le remplacement hors du processus actif.</p>
                    <div className="mt-4 flex flex-col sm:flex-row gap-3">
                      <input
                        value={confirmation}
                        onChange={(event) => setConfirmation(event.target.value)}
                        disabled={restoreInFlight || isApplying}
                        placeholder="RESTAURER"
                        autoComplete="off"
                        className="min-w-0 min-h-[48px] flex-1 rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm font-black tracking-wide text-white placeholder:text-slate-600 outline-none focus:border-amber-400 disabled:opacity-60"
                      />
                      <button
                        type="button"
                        onClick={handleApplyRestore}
                        disabled={!canApply}
                        className="min-h-[48px] rounded-xl bg-amber-500 hover:bg-amber-400 px-5 py-3 text-sm font-black text-slate-950 transition disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                      >
                        {isApplying || restoreInFlight ? <Loader2 size={18} className="animate-spin" /> : <Upload size={18} />}
                        {restoreInFlight ? 'Restauration en cours...' : 'Redémarrer et restaurer'}
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {restoreInFlight && (
                <div className="mt-5 rounded-2xl border border-blue-200 bg-blue-50 px-4 py-4 text-blue-900 flex items-start gap-3">
                  <Loader2 size={18} className="mt-0.5 shrink-0 animate-spin" />
                  <div>
                    <p className="font-black text-sm">Restauration en cours</p>
                    <p className="text-xs font-medium mt-1">Digital Crown redémarre et vérifiera automatiquement que le service local et la base répondent correctement.</p>
                  </div>
                </div>
              )}

              {terminalRestoreStates.has(restore.status) && restore.status !== 'blocked' && (
                <div className={`mt-5 rounded-2xl px-4 py-4 border ${restore.status === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : restore.status === 'rolled_back' ? 'bg-amber-50 border-amber-200 text-amber-900' : 'bg-rose-50 border-rose-200 text-rose-900'}`}>
                  <p className="font-black text-sm">{restore.message || (restore.status === 'success' ? 'Restauration terminée' : 'Restauration interrompue')}</p>
                  <p className="text-xs font-bold mt-1">Vérification du redémarrage : {restore.smoke_check || '—'} · Retour à l’état précédent : {restore.rollback || '—'}</p>
                </div>
              )}

              {!restoreInFlight && (
                <div className="mt-4 flex justify-end">
                  <button type="button" onClick={() => void handleCancelRestore()} className="min-h-[44px] px-4 py-2 text-sm font-black text-slate-500 hover:text-slate-800 flex items-center gap-2">
                    <X size={16} /> Fermer cette analyse
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="pt-10 border-t border-slate-100">
          <MobileSecurity />
        </div>

        <div className="pt-10 border-t border-slate-100">
          <AuditLogViewer />
        </div>
      </SettingsSection>
    </div>
  );
};
