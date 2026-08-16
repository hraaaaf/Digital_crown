import { useState } from 'react';
import { Calendar, ChevronRight, Loader2, Plus, Search, Smartphone, UserPlus, X } from 'lucide-react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { cn } from '../../../utils/cn';
import type { CabinetHealthDisplayState } from '../../../hooks/useCabinetHealth';
import { dashboardItemVariants } from '../animations';
import type { SearchPatientResult } from '../types';

export const DashboardHeader = ({
  displayName,
  dateLabel,
  canReadPatients,
  canUseAgenda,
  canAdmin,
  systemStatus,
  search,
  onNavigatePatient,
  onOpenMobile,
}: {
  displayName: string;
  dateLabel: string;
  canReadPatients: boolean;
  canUseAgenda: boolean;
  canAdmin: boolean;
  systemStatus: CabinetHealthDisplayState;
  search: {
    isExpanded: boolean;
    query: string;
    results: SearchPatientResult[];
    loading: boolean;
    open: () => void;
    close: () => void;
    change: (value: string) => void;
  };
  onNavigatePatient: (patientId: number) => void;
  onOpenMobile: () => void;
}) => {
  const [isAddMenuOpen, setIsAddMenuOpen] = useState(false);

  return (
    <motion.header variants={dashboardItemVariants} className="flex flex-col md:flex-row md:items-end justify-between gap-6">
      <div>
        <h1 className="text-4xl font-black tracking-tight font-outfit text-primary">Bonjour, {displayName}</h1>
        <div className="flex items-center gap-3 mt-3 bg-card-bg/60 backdrop-blur-md px-4 py-2 rounded-elite-sm border border-border-main w-fit">
          <Calendar size={16} className="text-primary" />
          <p className="text-text-muted font-bold text-sm">{dateLabel}</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {canReadPatients && (
          <div className="relative flex items-center">
            {search.isExpanded ? (
              <div className="absolute right-0 z-30 animate-in fade-in slide-in-from-right-4">
                <div className="flex items-center bg-white dark:bg-slate-800 border border-border-main rounded-full px-2 py-1 shadow-elite w-72">
                  {search.loading
                    ? <Loader2 size={18} className="text-primary ml-2 animate-spin flex-shrink-0" />
                    : <Search size={18} className="text-text-muted ml-2 flex-shrink-0" />}
                  <input
                    type="text"
                    autoFocus
                    placeholder="Nom, prénom ou n° de dossier..."
                    value={search.query}
                    onChange={event => search.change(event.target.value)}
                    onBlur={() => { if (!search.query) search.close(); }}
                    className="w-full bg-transparent border-none focus:outline-none focus:ring-0 text-sm px-2 py-1.5"
                  />
                  <button type="button" onClick={search.close} className="text-text-muted hover:text-red-500 mr-2 flex-shrink-0">
                    <X size={16} />
                  </button>
                </div>
                {search.results.length > 0 && (
                  <div className="absolute top-full mt-2 right-0 w-72 bg-white dark:bg-slate-800 border border-border-main rounded-2xl shadow-2xl overflow-hidden">
                    {search.results.map(patient => (
                      <button
                        key={patient.id}
                        onMouseDown={() => {
                          onNavigatePatient(patient.id);
                          search.close();
                        }}
                        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-primary/5 transition-colors text-left border-b border-border-main last:border-0"
                      >
                        <div className="w-9 h-9 bg-primary/10 text-primary rounded-xl flex items-center justify-center font-black text-sm flex-shrink-0">
                          {(patient.nom || '?').charAt(0)}
                        </div>
                        <div className="min-w-0">
                          <p className="font-black text-sm text-primary truncate">{(patient.nom || '').toUpperCase()} {patient.prenom || ''}</p>
                          <p className="text-[10px] text-text-muted font-medium">{patient.numero_dossier || `#${patient.id}`}</p>
                        </div>
                        <ChevronRight size={14} className="text-text-muted ml-auto flex-shrink-0" />
                      </button>
                    ))}
                  </div>
                )}
                {search.query.trim() && !search.loading && search.results.length === 0 && (
                  <div className="absolute top-full mt-2 right-0 w-72 bg-white dark:bg-slate-800 border border-border-main rounded-2xl shadow-xl px-4 py-3 text-sm text-text-muted font-medium text-center">
                    Aucun patient trouvé
                  </div>
                )}
              </div>
            ) : (
              <button
                onClick={search.open}
                className="p-3 bg-white dark:bg-slate-800 text-text-muted hover:text-primary rounded-full shadow-sm border border-border-main transition-all"
                title="Chercher un patient"
              >
                <Search size={20} />
              </button>
            )}
          </div>
        )}

        {(canReadPatients || canUseAgenda) && (
          <div className="relative">
            <button
              onClick={() => setIsAddMenuOpen(value => !value)}
              className="p-3 bg-primary text-white hover:bg-primary/90 rounded-full shadow-md transition-all flex items-center justify-center"
              title="Ajout Rapide"
            >
              <Plus size={20} />
            </button>
            {isAddMenuOpen && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setIsAddMenuOpen(false)} />
                <div className="absolute top-14 right-0 bg-white dark:bg-slate-800 border border-border-main rounded-xl shadow-xl w-48 py-2 z-20 animate-in fade-in zoom-in-95">
                  {canReadPatients && (
                    <Link
                      to="/patients/new"
                      onClick={() => setIsAddMenuOpen(false)}
                      className="flex items-center gap-3 px-4 py-2 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors text-sm font-semibold"
                    >
                      <UserPlus size={16} className="text-primary" />
                      Nouveau Patient
                    </Link>
                  )}
                  {canUseAgenda && (
                    <Link
                      to="/agenda"
                      onClick={() => setIsAddMenuOpen(false)}
                      className="flex items-center gap-3 px-4 py-2 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors text-sm font-semibold"
                    >
                      <Calendar size={16} className="text-emerald-500" />
                      Nouveau RDV
                    </Link>
                  )}
                </div>
              </>
            )}
          </div>
        )}

        {canAdmin && (
          <button
            onClick={onOpenMobile}
            className="flex items-center gap-2 px-4 py-3 bg-indigo-50 text-indigo-600 hover:bg-indigo-100 font-bold text-sm rounded-elite-lg transition-all border border-indigo-100 shadow-sm"
            title="Appairer le téléphone"
          >
            <Smartphone size={20} />
            <span className="hidden md:inline">Mobile</span>
          </button>
        )}

        <div className="flex items-center gap-4 bg-card-bg/40 p-2 rounded-elite-lg border border-border-main shadow-elite transition-elite hover:bg-card-bg/60">
          <div className="px-6 py-3 rounded-elite-sm flex flex-col items-end">
            <span className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-1">Statut système</span>
            <div className="flex items-center gap-2" role="status" aria-live="polite">
              {systemStatus.isLoading
                ? <Loader2 size={12} className="text-slate-400 animate-spin" aria-hidden="true" />
                : <div className={cn('w-2 h-2 rounded-full', systemStatus.dotClassName)} aria-hidden="true" />}
              <span className="text-sm font-black text-main uppercase tracking-tighter" style={{ color: 'var(--text-main)' }}>
                {systemStatus.label}
              </span>
            </div>
          </div>
        </div>
      </div>
    </motion.header>
  );
};
