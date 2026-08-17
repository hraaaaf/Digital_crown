import { AlertCircle, Archive, CloudOff, Database, HardDrive } from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from '../../../utils/cn';
import type { CabinetHealthState } from '../../../hooks/useCabinetHealth';
import { dashboardItemVariants } from '../animations';

export const CabinetHealth = ({
  visible,
  healthState,
}: {
  visible: boolean;
  healthState: CabinetHealthState;
}) => {
  if (!visible) return null;

  if (healthState.status === 'unverified') {
    return (
      <motion.section variants={dashboardItemVariants}>
        <h2 className="text-[11px] font-black uppercase tracking-[0.15em] text-text-muted mb-4">Santé du Cabinet</h2>
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-elite-lg shadow-elite p-6 flex items-start gap-4" role="status">
          <AlertCircle size={22} className="text-amber-500 shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <h3 className="text-sm font-black text-amber-600 font-outfit uppercase tracking-tight">Système non vérifié</h3>
            <p className="text-xs font-medium text-text-muted mt-1">
              Le contrôle de santé local est indisponible ou a dépassé le délai de réponse. Une nouvelle vérification sera tentée automatiquement.
            </p>
          </div>
        </div>
      </motion.section>
    );
  }

  if (healthState.status !== 'ready') return null;
  const health = healthState.data;

  return (
    <motion.section variants={dashboardItemVariants}>
      <h2 className="text-[11px] font-black uppercase tracking-[0.15em] text-text-muted mb-4">Santé du Cabinet</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-card-bg rounded-elite-lg border border-border-main shadow-elite p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className={cn(
              'w-9 h-9 rounded-elite-sm flex items-center justify-center border',
              health.database.status === 'ok'
                ? 'bg-emerald-500/10 border-emerald-500/20'
                : 'bg-red-500/10 border-red-500/20',
            )}>
              <Database size={18} className={health.database.status === 'ok' ? 'text-emerald-400' : 'text-red-400'} />
            </div>
            <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">Base de Données</span>
          </div>
          <div className={cn(
            'text-2xl font-black font-outfit',
            health.database.status === 'ok' ? 'text-emerald-400' : 'text-red-500',
          )}>
            {health.database.status === 'ok' ? 'Connectée' : 'Erreur'}
          </div>
          <div className="text-[10px] font-bold text-text-muted mt-1">Connexion à la base réelle</div>
        </div>

        <div className="bg-card-bg rounded-elite-lg border border-border-main shadow-elite p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className={cn(
              'w-9 h-9 rounded-elite-sm flex items-center justify-center border',
              health.disk.status === 'ok'
                ? 'bg-emerald-500/10 border-emerald-500/20'
                : health.disk.status === 'warning'
                  ? 'bg-amber-500/10 border-amber-500/20'
                  : health.disk.status === 'critical'
                    ? 'bg-red-500/10 border-red-500/20'
                    : 'bg-slate-500/10 border-slate-500/20',
            )}>
              <HardDrive size={18} className={
                health.disk.status === 'ok'
                  ? 'text-emerald-400'
                  : health.disk.status === 'warning'
                    ? 'text-amber-400'
                    : health.disk.status === 'critical'
                      ? 'text-red-400'
                      : 'text-slate-400'
              } />
            </div>
            <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">Espace Disque</span>
          </div>
          <div className={cn(
            'text-2xl font-black font-outfit',
            health.disk.status === 'ok'
              ? 'text-emerald-400'
              : health.disk.status === 'warning'
                ? 'text-amber-400'
                : health.disk.status === 'critical'
                  ? 'text-red-500'
                  : 'text-slate-400',
          )}>
            {health.disk.free_gb !== null ? `${health.disk.free_gb.toLocaleString('fr-FR')} Go` : 'Inconnu'}
          </div>
          <div className="text-[10px] font-bold text-text-muted mt-1">Espace libre disponible</div>
        </div>

        <div className="bg-card-bg rounded-elite-lg border border-border-main shadow-elite p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className={cn(
              'w-9 h-9 rounded-elite-sm flex items-center justify-center border',
              health.backup_local.status === 'ok'
                ? 'bg-emerald-500/10 border-emerald-500/20'
                : health.backup_local.status === 'warning'
                  ? 'bg-amber-500/10 border-amber-500/20'
                  : 'bg-red-500/10 border-red-500/20',
            )}>
              <Archive size={18} className={
                health.backup_local.status === 'ok'
                  ? 'text-emerald-400'
                  : health.backup_local.status === 'warning'
                    ? 'text-amber-400'
                    : 'text-red-400'
              } />
            </div>
            <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">Sauvegarde Locale</span>
          </div>
          <div className={cn(
            'text-2xl font-black font-outfit',
            health.backup_local.status === 'ok'
              ? 'text-emerald-400'
              : health.backup_local.status === 'warning'
                ? 'text-amber-400'
                : 'text-red-500',
          )}>
            {health.backup_local.age_hours !== null ? `Il y a ${Math.round(health.backup_local.age_hours)}h` : 'Aucune'}
          </div>
          <div className="text-[10px] font-bold text-text-muted mt-1">Dernière sauvegarde DB + médias</div>
        </div>

        <div className="bg-card-bg rounded-elite-lg border border-border-main shadow-elite p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className={cn(
              'w-9 h-9 rounded-elite-sm flex items-center justify-center border',
              health.offsite.status === 'ok'
                ? 'bg-emerald-500/10 border-emerald-500/20'
                : health.offsite.status === 'warning'
                  ? 'bg-amber-500/10 border-amber-500/20'
                  : 'bg-slate-500/10 border-slate-500/20',
            )}>
              <CloudOff size={18} className={
                health.offsite.status === 'ok'
                  ? 'text-emerald-400'
                  : health.offsite.status === 'warning'
                    ? 'text-amber-400'
                    : 'text-slate-400'
              } />
            </div>
            <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">Sauvegarde Hors-Site</span>
          </div>
          <div className={cn(
            'text-2xl font-black font-outfit',
            health.offsite.status === 'ok'
              ? 'text-emerald-400'
              : health.offsite.status === 'warning'
                ? 'text-amber-400'
                : 'text-slate-400',
          )}>
            {health.offsite.status === 'NOT_CONFIGURED'
              ? 'Non configurée'
              : health.offsite.status === 'ok'
                ? 'À jour'
                : 'À vérifier'}
          </div>
          <div className="text-[10px] font-bold text-text-muted mt-1">Copie réseau hors machine</div>
        </div>
      </div>
    </motion.section>
  );
};
