import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, Filter, ChevronLeft, ChevronRight, RefreshCw } from 'lucide-react';
import { api } from '../../../services/api';
import { cn } from '../../../utils/cn';

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

const severityColors: Record<string, string> = {
  INFO: 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20',
  WARNING: 'bg-amber-500/10 text-amber-600 border-amber-500/20',
  CRITICAL: 'bg-red-500/10 text-red-600 border-red-500/20',
};

export const AuditLogViewer = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const limit = 20;

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ limit: String(limit), offset: String(page * limit) });
      if (actionFilter) params.set('action', actionFilter);
      if (severityFilter) params.set('severity', severityFilter);
      const res = await api.get(`/admin/audit-logs?${params}`);
      setLogs(res.data.logs);
      setTotal(res.data.total);
    } catch (e) {
      console.error('Erreur chargement audit logs', e);
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

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 text-xs font-bold text-slate-500 uppercase tracking-widest">
          <Filter size={14} /> Filtres
        </div>
        <select
          value={actionFilter}
          onChange={e => { setActionFilter(e.target.value); setPage(0); }}
          className="px-3 py-2 bg-white border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary/20"
        >
          <option value="">Toutes les actions</option>
          <option value="LOGIN_SUCCESS">Connexion réussie</option>
          <option value="LOGIN_FAIL">Échec connexion</option>
          <option value="CREATE">Création</option>
          <option value="UPDATE">Modification</option>
          <option value="DELETE">Suppression</option>
          <option value="GENERATE">Génération document</option>
          <option value="ACCESS_DENIED">Accès refusé</option>
        </select>
        <select
          value={severityFilter}
          onChange={e => { setSeverityFilter(e.target.value); setPage(0); }}
          className="px-3 py-2 bg-white border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary/20"
        >
          <option value="">Toutes les sévérités</option>
          <option value="INFO">INFO</option>
          <option value="WARNING">WARNING</option>
          <option value="CRITICAL">CRITICAL</option>
        </select>
        <button onClick={fetchLogs} className="p-2 text-slate-400 hover:text-primary transition-colors" title="Rafraîchir">
          <RefreshCw size={16} />
        </button>
        <span className="ml-auto text-xs font-bold text-slate-400">{total} entrée{total > 1 ? 's' : ''}</span>
      </div>

      {/* Logs table */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-sm font-medium">Chargement...</div>
        ) : logs.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-sm font-medium">Aucun log trouvé</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-[10px] font-black text-slate-400 uppercase tracking-widest">
                  <th className="text-left px-6 py-4">Date</th>
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
                    <motion.tr
                      key={log.id}
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.02 }}
                      className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors"
                    >
                      <td className="px-6 py-3 text-xs font-mono text-slate-500 whitespace-nowrap">
                        {new Date(log.timestamp).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}
                      </td>
                      <td className="px-4 py-3 text-xs font-black text-slate-700">{log.action}</td>
                      <td className="px-4 py-3 text-xs font-medium text-slate-600">
                        {log.resource_type}{log.resource_id ? `#${log.resource_id}` : ''}
                      </td>
                      <td className="px-4 py-3">
                        <span className={cn('text-[9px] font-black px-2 py-0.5 rounded-full border uppercase', severityColors[log.severity] || 'bg-slate-100 text-slate-500 border-slate-200')}>
                          {log.severity}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs font-medium text-slate-500">#{log.user_id}</td>
                      <td className="px-4 py-3 text-xs text-slate-400 max-w-[200px] truncate" title={log.details}>
                        {log.details || '—'}
                      </td>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-slate-100">
            <button
              onClick={() => setPage(p => Math.max(0, p - 1))}
              disabled={page === 0}
              className="flex items-center gap-1 px-3 py-1.5 text-xs font-bold text-slate-500 hover:text-primary disabled:opacity-30 transition-colors"
            >
              <ChevronLeft size={14} /> Précédent
            </button>
            <span className="text-xs font-bold text-slate-400">Page {page + 1} / {totalPages}</span>
            <button
              onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              className="flex items-center gap-1 px-3 py-1.5 text-xs font-bold text-slate-500 hover:text-primary disabled:opacity-30 transition-colors"
            >
              Suivant <ChevronRight size={14} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
