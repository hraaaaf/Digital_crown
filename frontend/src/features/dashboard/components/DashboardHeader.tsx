import { useEffect, useRef, useState, type RefObject } from 'react';
import { Calendar, ChevronRight, Loader2, Plus, Search, Smartphone, UserPlus, X } from 'lucide-react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { cn } from '../../../utils/cn';
import type { CabinetHealthDisplayState } from '../../../hooks/useCabinetHealth';
import { dashboardItemVariants } from '../animations';
import type { SearchPatientResult } from '../types';

const SEARCH_RESULTS_ID = 'dashboard-patient-search-results';
const QUICK_ADD_MENU_ID = 'dashboard-quick-add-menu';

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
  mobileButtonRef,
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
  mobileButtonRef: RefObject<HTMLButtonElement | null>;
}) => {
  const [isAddMenuOpen, setIsAddMenuOpen] = useState(false);
  const searchButtonRef = useRef<HTMLButtonElement>(null);
  const addButtonRef = useRef<HTMLButtonElement>(null);
  const addMenuRef = useRef<HTMLDivElement>(null);

  const closeSearchAndRestoreFocus = () => {
    search.close();
    window.setTimeout(() => searchButtonRef.current?.focus(), 0);
  };

  const closeAddMenuAndRestoreFocus = () => {
    setIsAddMenuOpen(false);
    window.setTimeout(() => addButtonRef.current?.focus(), 0);
  };

  useEffect(() => {
    if (!isAddMenuOpen) return;

    const firstMenuItem = addMenuRef.current?.querySelector<HTMLElement>('[role="menuitem"]');
    firstMenuItem?.focus();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        closeAddMenuAndRestoreFocus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isAddMenuOpen]);

  return (
    <motion.header variants={dashboardItemVariants} className="flex flex-col md:flex-row md:items-end justify-between gap-6">
      <div>
        <h1 className="text-4xl font-black tracking-tight font-outfit text-primary">Bonjour, {displayName}</h1>
        <div className="flex items-center gap-3 mt-3 bg-card-bg/60 backdrop-blur-md px-4 py-2 rounded-elite-sm border border-border-main w-fit">
          <Calendar size={16} className="text-primary" aria-hidden="true" />
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
                    ? <Loader2 size={18} className="text-primary ml-2 animate-spin flex-shrink-0" aria-hidden="true" />
                    : <Search size={18} className="text-text-muted ml-2 flex-shrink-0" aria-hidden="true" />}
                  <input
                    type="text"
                    autoFocus
                    aria-label="Chercher un patient"
                    aria-controls={SEARCH_RESULTS_ID}
                    aria-expanded={search.results.length > 0}
                    aria-autocomplete="list"
                    placeholder="Nom, prénom ou n° de dossier..."
                    value={search.query}
                    onChange={event => search.change(event.target.value)}
                    onBlur={() => { if (!search.query) search.close(); }}
                    onKeyDown={event => {
                      if (event.key === 'Escape') {
                        event.preventDefault();
                        closeSearchAndRestoreFocus();
                      }
                    }}
                    className="w-full bg-transparent border-none focus:outline-none focus:ring-0 text-sm px-2 py-1.5"
                  />
                  <button
                    type="button"
                    onClick={closeSearchAndRestoreFocus}
                    aria-label="Fermer la recherche patient"
                    className="min-w-11 min-h-11 flex items-center justify-center text-text-muted hover:text-red-500 flex-shrink-0 rounded-full"
                  >
                    <X size={16} aria-hidden="true" />
                  </button>
                </div>
                {search.results.length > 0 && (
                  <div
                    id={SEARCH_RESULTS_ID}
                    role="list"
                    className="absolute top-full mt-2 right-0 w-72 bg-white dark:bg-slate-800 border border-border-main rounded-2xl shadow-2xl overflow-hidden"
                  >
                    {search.results.map(patient => (
                      <button
                        key={patient.id}
                        type="button"
                        onClick={() => {
                          onNavigatePatient(patient.id);
                          search.close();
                        }}
                        className="w-full min-h-11 flex items-center gap-3 px-4 py-3 hover:bg-primary/5 focus-visible:bg-primary/5 transition-colors text-left border-b border-border-main last:border-0"
                      >
                        <div className="w-9 h-9 bg-primary/10 text-primary rounded-xl flex items-center justify-center font-black text-sm flex-shrink-0" aria-hidden="true">
                          {(patient.nom || '?').charAt(0)}
                        </div>
                        <div className="min-w-0">
                          <p className="font-black text-sm text-primary truncate">{(patient.nom || '').toUpperCase()} {patient.prenom || ''}</p>
                          <p className="text-[10px] text-text-muted font-medium">{patient.numero_dossier || `#${patient.id}`}</p>
                        </div>
                        <ChevronRight size={14} className="text-text-muted ml-auto flex-shrink-0" aria-hidden="true" />
                      </button>
                    ))}
                  </div>
                )}
                {search.query.trim() && !search.loading && search.results.length === 0 && (
                  <div
                    id={SEARCH_RESULTS_ID}
                    role="status"
                    className="absolute top-full mt-2 right-0 w-72 bg-white dark:bg-slate-800 border border-border-main rounded-2xl shadow-xl px-4 py-3 text-sm text-text-muted font-medium text-center"
                  >
                    Aucun patient trouvé
                  </div>
                )}
              </div>
            ) : (
              <button
                ref={searchButtonRef}
                type="button"
                onClick={search.open}
                aria-label="Chercher un patient"
                className="min-w-11 min-h-11 p-3 bg-white dark:bg-slate-800 text-text-muted hover:text-primary rounded-full shadow-sm border border-border-main transition-all"
                title="Chercher un patient"
              >
                <Search size={20} aria-hidden="true" />
              </button>
            )}
          </div>
        )}

        {(canReadPatients || canUseAgenda) && (
          <div className="relative">
            <button
              ref={addButtonRef}
              type="button"
              onClick={() => setIsAddMenuOpen(value => !value)}
              aria-label="Ajout rapide"
              aria-haspopup="menu"
              aria-expanded={isAddMenuOpen}
              aria-controls={QUICK_ADD_MENU_ID}
              className="min-w-11 min-h-11 p-3 bg-primary text-white hover:bg-primary/90 rounded-full shadow-md transition-all flex items-center justify-center"
              title="Ajout Rapide"
            >
              <Plus size={20} aria-hidden="true" />
            </button>
            {isAddMenuOpen && (
              <>
                <div className="fixed inset-0 z-10" onClick={closeAddMenuAndRestoreFocus} aria-hidden="true" />
                <div
                  ref={addMenuRef}
                  id={QUICK_ADD_MENU_ID}
                  role="menu"
                  className="absolute top-14 right-0 bg-white dark:bg-slate-800 border border-border-main rounded-xl shadow-xl w-48 py-2 z-20 animate-in fade-in zoom-in-95"
                >
                  {canReadPatients && (
                    <Link
                      to="/patients/new"
                      role="menuitem"
                      onClick={() => setIsAddMenuOpen(false)}
                      className="min-h-11 flex items-center gap-3 px-4 py-2 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors text-sm font-semibold"
                    >
                      <UserPlus size={16} className="text-primary" aria-hidden="true" />
                      Nouveau Patient
                    </Link>
                  )}
                  {canUseAgenda && (
                    <Link
                      to="/agenda"
                      role="menuitem"
                      onClick={() => setIsAddMenuOpen(false)}
                      className="min-h-11 flex items-center gap-3 px-4 py-2 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors text-sm font-semibold"
                    >
                      <Calendar size={16} className="text-emerald-500" aria-hidden="true" />
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
            ref={mobileButtonRef}
            type="button"
            onClick={onOpenMobile}
            aria-label="Appairer le téléphone mobile"
            className="min-h-11 flex items-center gap-2 px-4 py-3 bg-indigo-50 text-indigo-600 hover:bg-indigo-100 font-bold text-sm rounded-elite-lg transition-all border border-indigo-100 shadow-sm"
            title="Appairer le téléphone"
          >
            <Smartphone size={20} aria-hidden="true" />
            <span className="hidden md:inline">Mobile</span>
          </button>
        )}

        {canAdmin && (
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
        )}
      </div>
    </motion.header>
  );
};
