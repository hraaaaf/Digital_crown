import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, Filter, ChevronLeft, ChevronRight, ChevronDown, RefreshCw } from 'lucide-react';
import { api } from '../../../services/api';
import { cn } from '../../../utils/cn';
import { SettingsReadError } from '../Settings/components/SharedUI';

interface AuditLog {
  id: number;
  timestamp: string;
  user_id: number;
  employer_id: number;
  action: string;
  resource_type: string;
  resource_id: string;
  severity: string;
  ip_address: string;
  details: string;
}

const actionLabels: Record<string, string> = {
  LOGIN_SUCCESS: 'Connexion réussie',
  LOGIN_FAIL: 'Échec de connexion',
  CREATE: 'Création',
  UPDATE: 'Modification',
  DELETE: 'Suppression',
  GENERATE: 'Génération de document',
  ACCESS_DENIED: 'Accès refusé',
  EXPORT_DB: 'Sauvegarde exportée',
  MOBILE_PAIRING_TOKEN_ISSUED: "Code d'appairage mobile créé",
  MOBILE_ACCESS_REVOKED: 'Accès mobiles révoqués',
};

const resourceLabels: Record<string, string> = {
  User: 'Compte utilisateur',
  Patient: 'Patient',
  DatabaseBackup: 'Sauvegarde',
  ZKAMasterKey: 'Accès mobile',
  Document: 'Document',
  Appointment: 'Rendez-vous',
};

const severityLabels: Record<string, string> = {
  INFO: 'Information',
  WARNING: 'Attention',
  CRITICAL: 'Critique',
};

const severityColors: Record<string, string> = {
  INFO: 'bg-emerald-500/10 text-emerald-700 border-emerald-500/20',
  WARNING: 'bg-amber-500/10 text-amber-700 border-amber-500/20',
  CRITICAL: 'bg-red-500/10 text-red-700 border-red-500/20',
};

const readableResource = (log: AuditLog) => {
  const base = resourceLabels[log.resource_type] || log.resource_type || 'Ressource';
  return log.resource_id ? `${base} #${log.resource_id}` : base;
};

const AuditEntry = ({ log }: { log: AuditLog }) => {
  const [expanded, setExpanded] = useState(false);
  const actionLabel = actionLabels[log.action] || log.action;
  const severityLabel = severityLabels[log.severity] || log.severity;

  return (
    <motion.article
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-bold text-slate-800">{actionLabel}</p>
          <p className="mt-1 text-[10px] font-mono text-slate-400">{log.action}</p>
        </div>
        <span className={cn('shrink-0 rounded-full border px-2 py-1 text-[9px] font-black uppercase', severityColors[log.severity] || 'bg-slate-100 text-slate-600 border-slate-200')}>
          {severityLabel}
        </span>
      </div>
      <div className="mt-3 grid gap-1.5 text-xs text-slate-600">
        <p>{readableResource(log)}</p>
        <p>Utilisateur #{log.user_id}</p>
        <p className="font-mono text-[11px] text-slate-400">
          {new Date(log.timestamp).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
      <button
        type="button"
        onClick={() => setExpanded(value => !value)}
        className="mt-3 flex items-center gap-1 text-xs font-bold text-primary hover:underline"
        aria-expanded={expanded}
      >
        {expanded ? 'Masquer les détails' : 'Voir les détails'}
        <ChevronDown size={14} className={cn('transition-transform', expanded && 'rotate-180')} />
      </button>
      {expanded && (
        <div className="mt-3 rounded-xl bg-slate-50 p-3 text-xs leading-relaxed text-slate-600 break-words">
          <p>{log.details || 'Aucun détail fourni.'}</p>
          <p className="mt-2 text-[10px] text-slate-400">IP : {log.ip_address || 'non fournie'}</p>
        </div>
      )}
    </motion.article>
  );
};

export const AuditLogViewer = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [readError, setReadError] = useState<string | null>(null);
  const [actionFilter, setActionFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const limit = 20;

  const fetchLogs = async () => {
    setLoading(true);
    setReadError(null);
    try {
      const params = new URLSearchParams({ limit: String(limit), offset: String(page * limit) });
      if (actionFilter) params.set('action', actionFilter);
      if (severityFilter) params.set('severity', severityFilter);
      const res = await api.get(`/admin/audit-logs?${params}`);
      setLogs(res.data.logs);
      setTotal(res.data.total);
    } catch (e) {
      console.error('Erreur chargement audit logs', e);
      setReadError("Impossible de charger le journal d'audit réel du cabinet.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchLogs(); }, [page, actionFilter, severityFilter]);

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex items-center gap-4 mb-6">
        <div className="w-12 h-12 rounded-2xl bg-violet-500/10 flex items-center justify-center text-violet-500">
          <Shield size={24} />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-800 dark:text-white font-outfit">Journal d'Audit</h2>
          <p className="text-sm text-slate-500">Traçabilité des actions sensibles du cabinet.</p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 text-xs font-bold text-slate-500 uppercase tracking-widest">
          <Filter size={14} /> Filtres
        </div>
        <select
          value={actionFilter}
          onChange={e => { setActionFilter(e.target.value); setPage(0); }}
          disabled={Boolean(readError)}
          className="max-w-full px-3 py-2 bg-white border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary/20 disabled:opacity-50"
        >
          <option value="">Toutes les actions</option>
          <option value="LOGIN_SUCCESS">Connexion réussie</option>
          <option value="LOGIN_FAIL">Échec de connexion</option>
          <option value="CREATE">Création</option>
          <option value="UPDATE">Modification</option>
          <option value="DELETE">Suppression</option>
          <option value="GENERATE">Génération de document</option>
          <option value="ACCESS_DENIED">Accès refusé</option>
        </select>
        <select
          value={severityFilter}
          onChange={e => { setSeverityFilter(e.target.value); setPage(0); }}
          disabled={Boolean(readError)}
          className="max-w-full px-3 py-2 bg-white border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary/20 disabled:opacity-50"
        >
          <option value="">Toutes les sévérités</option>
          <option value="INFO">Information</option>
          <option value="WARNING">Attention</option>
          <option value="CRITICAL">Critique</option>
        </select>
        <button onClick={fetchLogs} className="p-2 text-slate-400 hover:text-primary transition-colors" title="Rafraîchir" aria-label="Rafraîchir le journal">
          <RefreshCw size={16} />
        </button>
        <span className="sm:ml-auto text-xs font-bold text-slate-400">
          {readError ? '— entrées' : `${total} entrée${total > 1 ? 's' : ''}`}
        </span>
      </div>

      <div>
        {loading ? (
          <div className="rounded-3xl border border-slate-200 bg-white p-12 text-center text-sm font-medium text-slate-400">Chargement...</div>
        ) : readError ? (
          <div className="rounded-3xl border border-slate-200 bg-white p-6">
            <SettingsReadError
              title="Journal d'audit indisponible"
              message={`${readError} Aucun historique vide n'est supposé tant que la lecture n'a pas réussi.`}
              onRetry={fetchLogs}
            />
          </div>
        ) : logs.length === 0 ? (
          <div className="rounded-3xl border border-slate-200 bg-white p-12 text-center text-sm font-medium text-slate-400">Aucun log trouvé</div>
        ) : (
          <>
            <div className="grid gap-3 xl:hidden">
              <AnimatePresence>
                {logs.map(log => <AuditEntry key={log.id} log={log} />)}
              </AnimatePresence>
            </div>

            <div className="hidden xl:block overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-100 text-[10px] font-black text-slate-400 uppercase tracking-widest">
                      <th className="text-left px-5 py-4">Date</th>
                      <th className="text-left px-4 py-4">Action</th>
                      <th className="text-left px-4 py-4">Ressource</th>
                      <th className="text-left px-4 py-4">Sévérité</th>
                      <th className="text-left px-4 py-4">Utilisateur</th>
                      <th className="text-left px-4 py-4">Détails</th>
                    </tr>
                  </thead>
                  <tbody>
                    <AnimatePresence>
                      {logs.map((log, i) => (
                        <AuditTableRow key={log.id} log={log} index={i} />
                      ))}
                    </AnimatePresence>
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {!readError && totalPages > 1 && (
          <div className="mt-3 flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3">
            <button
              onClick={() => setPage(p => Math.max(0, p - 1))}
              disabled={page === 0}
              className="flex items-center gap-1 px-2 py-1.5 text-xs font-bold text-slate-500 hover:text-primary disabled:opacity-30 transition-colors"
            >
              <ChevronLeft size={14} /> Précédent
            </button>
            <span className="text-xs font-bold text-slate-400">Page {page + 1} / {totalPages}</span>
            <button
              onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="flex items-center gap-1 px-2 py-1.5 text-xs font-bold text-slate-500 hover:text-primary disabled:opacity-30 transition-colors"
            >
              Suivant <ChevronRight size={14} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

const AuditTableRow = ({ log, index }: { log: AuditLog; index: number }) => {
  const [expanded, setExpanded] = useState(false);
  const actionLabel = actionLabels[log.action] || log.action;
  const severityLabel = severityLabels[log.severity] || log.severity;

  return (
    <>
      <motion.tr
        initial={{ opacity: 0, y: 5 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.02 }}
        className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors"
      >
        <td className="px-5 py-3 text-xs font-mono text-slate-500 whitespace-nowrap">
          {new Date(log.timestamp).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
        </td>
        <td className="px-4 py-3">
          <p className="text-xs font-bold text-slate-700">{actionLabel}</p>
          <p className="mt-0.5 text-[9px] font-mono text-slate-400">{log.action}</p>
        </td>
        <td className="px-4 py-3 text-xs font-medium text-slate-600">{readableResource(log)}</td>
        <td className="px-4 py-3">
          <span className={cn('text-[9px] font-black px-2 py-0.5 rounded-full border uppercase whitespace-nowrap', severityColors[log.severity] || 'bg-slate-100 text-slate-500 border-slate-200')}>
            {severityLabel}
          </span>
        </td>
        <td className="px-4 py-3 text-xs font-medium text-slate-500 whitespace-nowrap">Utilisateur #{log.user_id}</td>
        <td className="px-4 py-3">
          <button type="button" onClick={() => setExpanded(value => !value)} className="flex items-center gap-1 whitespace-nowrap text-xs font-bold text-primary hover:underline" aria-expanded={expanded}>
            {expanded ? 'Masquer' : 'Voir les détails'}
            <ChevronDown size={13} className={cn('transition-transform', expanded && 'rotate-180')} />
          </button>
        </td>
      </motion.tr>
      {expanded && (
        <tr className="border-b border-slate-100 bg-slate-50/60">
          <td colSpan={6} className="px-5 py-3 text-xs leading-relaxed text-slate-600 break-words">
            {log.details || 'Aucun détail fourni.'}
            <span className="ml-3 text-[10px] text-slate-400">IP : {log.ip_address || 'non fournie'}</span>
          </td>
        </tr>
      )}
    </>
  );
};
