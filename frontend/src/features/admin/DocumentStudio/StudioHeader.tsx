import React, { useEffect, useMemo, useState } from 'react';
import { Calendar as CalendarIcon, Stethoscope } from 'lucide-react';
import { useParams } from 'react-router-dom';
import { api } from '../../../services/api';
import { useAuthStore } from '../../../stores/useAuthStore';
import { cn } from '../../../utils/cn';
import { DOCUMENT_STUDIO_LABELS, type CertifiableDocumentStudioTab } from './DocumentStudioVocabulary';
import {
  clearDocumentAuthorPractitionerId,
  installDocumentAuthorRequestGuard,
  setDocumentAuthorPractitionerId,
  type DocumentPractitionerOption,
} from './DocumentAuthorSelection';

interface StudioHeaderProps {
  patientName: string;
  docDate: string;
  onDateChange: (date: string) => void;
  activeTab: CertifiableDocumentStudioTab;
  showOdontoPanoramique: boolean;
  onToggleOdonto: () => void;
  onGenerate?: (archive: boolean, print: boolean, isPreview: boolean, force: boolean) => void;
  loading?: boolean;
  sideStudioType?: 'NONE' | 'PREVIEW';
  onTogglePreview?: () => void;
}

export const StudioHeader: React.FC<StudioHeaderProps> = ({
  patientName,
  docDate,
  onDateChange,
  activeTab,
  showOdontoPanoramique,
  onToggleOdonto,
}) => {
  const documentLabel = DOCUMENT_STUDIO_LABELS[activeTab];
  const compactHonorairesMobile = activeTab === 'honoraires';
  const { id: patientId } = useParams();
  const currentUser = useAuthStore(state => state.user);
  const [practitioners, setPractitioners] = useState<DocumentPractitionerOption[]>([]);
  const [authorPractitionerId, setAuthorPractitionerId] = useState<number | null>(null);
  const [authorLoading, setAuthorLoading] = useState(false);

  const currentUserId = useMemo(() => {
    const parsed = Number(currentUser?.id);
    return Number.isFinite(parsed) ? parsed : null;
  }, [currentUser?.id]);

  useEffect(() => installDocumentAuthorRequestGuard(api), []);

  useEffect(() => {
    let cancelled = false;
    clearDocumentAuthorPractitionerId();
    setAuthorPractitionerId(null);

    const loadAuthorContext = async () => {
      if (!patientId) return;
      setAuthorLoading(true);
      try {
        const [directoryResponse, assignmentResponse] = await Promise.all([
          api.get('/patients/_clinic/practitioners'),
          api.get(`/patients/${patientId}/practitioner`),
        ]);
        if (cancelled) return;

        const directory = Array.isArray(directoryResponse.data)
          ? directoryResponse.data.filter((item: any) => Number.isFinite(Number(item?.id))).map((item: any) => ({
              id: Number(item.id),
              name: String(item.name || `Praticien ${item.id}`),
              role: String(item.role || 'DENTISTE'),
            }))
          : [];
        setPractitioners(directory);

        const referentId = Number(assignmentResponse.data?.practitioner?.id);
        const referent = directory.find((item: DocumentPractitionerOption) => item.id === referentId);
        const current = currentUserId !== null
          ? directory.find((item: DocumentPractitionerOption) => item.id === currentUserId)
          : undefined;
        const resolved = referent || current || (directory.length === 1 ? directory[0] : undefined);
        const selectedId = resolved?.id ?? null;
        setAuthorPractitionerId(selectedId);
        setDocumentAuthorPractitionerId(selectedId);
      } catch (error) {
        if (!cancelled) {
          console.error('Impossible de charger les praticiens du document:', error);
          setPractitioners([]);
          setAuthorPractitionerId(null);
          clearDocumentAuthorPractitionerId();
        }
      } finally {
        if (!cancelled) setAuthorLoading(false);
      }
    };

    void loadAuthorContext();
    return () => {
      cancelled = true;
      clearDocumentAuthorPractitionerId();
    };
  }, [patientId, currentUserId]);

  const handleAuthorChange = (value: string) => {
    const parsed = Number(value);
    const selectedId = Number.isFinite(parsed) && practitioners.some(item => item.id === parsed)
      ? parsed
      : null;
    setAuthorPractitionerId(selectedId);
    setDocumentAuthorPractitionerId(selectedId);
  };

  return (
    <div className={cn(
      "sticky top-0 z-[60] -mt-1 -mx-1 mb-2 bg-white/85 dark:bg-slate-950/80 backdrop-blur-3xl rounded-2xl border border-slate-200/70 dark:border-white/10 flex flex-col md:flex-row justify-between items-start md:items-center shrink-0 transition-all duration-300 shadow-sm",
      compactHonorairesMobile ? "p-2 gap-2 sm:p-3 sm:gap-3" : "p-2.5 sm:p-3 gap-3",
    )}>
      <div className={cn("flex min-w-0 items-center", compactHonorairesMobile ? "gap-2 sm:gap-3" : "gap-3")}>
        <div className={cn(
          "shrink-0 bg-primary/10 rounded-xl flex items-center justify-center text-primary border border-primary/10",
          compactHonorairesMobile ? "w-8 h-8 sm:w-9 sm:h-9" : "w-9 h-9",
        )} style={{ color: 'var(--primary)' }}>
          <CalendarIcon size={17} />
        </div>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <h2 className="text-sm sm:text-base font-black text-primary tracking-tight leading-none" style={{ color: 'var(--primary)' }}>
              Studio Documentaire
            </h2>
            <span className="rounded-full bg-slate-100 dark:bg-slate-800 px-2 py-1 text-[9px] font-black uppercase tracking-wider text-slate-500 dark:text-slate-300">
              {documentLabel}
            </span>
          </div>
          <p className={cn(
            "flex min-w-0 items-center gap-2 text-[10px] font-bold text-slate-500 dark:text-slate-400",
            compactHonorairesMobile ? "mt-1 sm:mt-1.5" : "mt-1.5",
          )}>
            <span className="shrink-0 uppercase tracking-widest">Patient actif</span>
            <span aria-hidden="true" className="text-slate-300 dark:text-slate-700">•</span>
            <span className="truncate font-black tracking-tight text-slate-900 dark:text-white">{patientName}</span>
          </p>
        </div>
      </div>

      <div className={cn(
        "flex w-full flex-wrap items-center md:w-auto md:justify-end",
        compactHonorairesMobile ? "gap-1.5 sm:gap-2" : "gap-2",
      )}>
        {(activeTab === 'honoraires' || activeTab === 'devis') && (
          <button
            type="button"
            onClick={onToggleOdonto}
            aria-pressed={showOdontoPanoramique}
            className={cn(
              "flex min-h-11 items-center gap-2 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50",
              compactHonorairesMobile ? "px-2.5 sm:px-3 py-2" : "px-3 py-2",
              showOdontoPanoramique
                ? "bg-primary text-white shadow-lg shadow-primary/30"
                : "bg-white dark:bg-slate-900 text-primary border border-primary/20 hover:bg-primary/5"
            )}
            style={showOdontoPanoramique ? { backgroundColor: 'var(--primary)' } : { color: 'var(--primary)', borderColor: 'var(--primary)' }}
          >
            {showOdontoPanoramique ? "Réduire Schéma" : "Afficher Schéma"}
          </button>
        )}

        <div className="min-w-[190px] flex-1 md:flex-none bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-white/10 p-2.5 flex flex-col items-start gap-1">
          <label htmlFor="document-studio-author" className="text-[9px] font-black text-slate-400 uppercase flex items-center gap-1 leading-none h-3">
            <Stethoscope size={10} /> Auteur clinique
          </label>
          <select
            id="document-studio-author"
            data-p3-author-selector
            aria-label="Auteur clinique du document"
            className="min-h-8 w-full bg-transparent text-xs font-black text-slate-700 dark:text-slate-200 outline-none cursor-pointer focus-visible:ring-2 focus-visible:ring-primary/40 rounded-md disabled:cursor-not-allowed disabled:opacity-60"
            value={authorPractitionerId ?? ''}
            onChange={(event) => handleAuthorChange(event.target.value)}
            disabled={authorLoading || practitioners.length === 0}
          >
            <option value="">{authorLoading ? 'Chargement…' : 'Choisir un praticien'}</option>
            {practitioners.map(practitioner => (
              <option key={practitioner.id} value={practitioner.id}>{practitioner.name}</option>
            ))}
          </select>
        </div>

        <div className={cn(
          "min-w-[140px] flex-1 md:flex-none bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-white/10",
          compactHonorairesMobile
            ? "h-11 px-2 py-0 flex flex-row items-center gap-1.5 sm:h-auto sm:p-2.5 sm:flex-col sm:items-start sm:gap-1"
            : "p-2.5 flex flex-col items-start gap-1",
        )}>
          <label
            htmlFor="document-studio-date"
            className={cn(
              "text-[9px] font-black text-slate-400 uppercase items-center gap-1 leading-none h-3",
              compactHonorairesMobile ? "sr-only sm:not-sr-only sm:flex" : "flex",
            )}
          >
            <CalendarIcon size={10} /> Date d'émission
          </label>
          <input
            id="document-studio-date"
            type="date"
            aria-label={compactHonorairesMobile ? "Date d'émission" : undefined}
            className={cn(
              "bg-transparent text-xs font-black text-slate-700 dark:text-slate-200 outline-none w-full cursor-pointer focus-visible:ring-2 focus-visible:ring-primary/40 rounded-md",
              compactHonorairesMobile ? "min-h-11 sm:min-h-8" : "min-h-8",
            )}
            value={docDate}
            onChange={(e) => onDateChange(e.target.value)}
          />
        </div>
      </div>
    </div>
  );
};
