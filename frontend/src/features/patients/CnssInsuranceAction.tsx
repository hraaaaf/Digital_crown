import { useState } from 'react';
import { createPortal } from 'react-dom';
import { Loader2, ShieldCheck } from 'lucide-react';
import { api } from '../../services/api';
import { CnssInsuranceSubmissionReview } from './CnssInsuranceSubmissionReview';
import { CnopsInsuranceSubmissionReview } from './CnopsInsuranceSubmissionReview';
import { FarInsuranceSubmissionReview } from './FarInsuranceSubmissionReview';
import type {
  InsuranceFinalizationResult,
  InsuranceSubmissionDraft,
} from './InsuranceSubmissionTypes';

interface CnssInsuranceActionProps {
  honorairesDocumentId: number;
  onArchived: () => void;
  onCloseMenu: () => void;
}

type SupportedOrganization = 'CNSS' | 'CNOPS' | 'FAR';
type BusyAction = 'prepare' | 'validate' | 'finalize' | null;

const apiErrorMessage = (error: any, fallback: string): string => {
  const detail = error?.response?.data?.detail;
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (detail && typeof detail.message === 'string' && detail.message.trim()) return detail.message;
  return fallback;
};

export const CnssInsuranceAction = ({
  honorairesDocumentId,
  onArchived,
  onCloseMenu,
}: CnssInsuranceActionProps) => {
  const [draft, setDraft] = useState<InsuranceSubmissionDraft | null>(null);
  const [busyAction, setBusyAction] = useState<BusyAction>(null);
  const [preparingOrganization, setPreparingOrganization] = useState<SupportedOrganization | null>(null);
  const [reviewError, setReviewError] = useState<string | null>(null);

  const handlePrepare = async (organization: SupportedOrganization) => {
    setBusyAction('prepare');
    setPreparingOrganization(organization);
    setReviewError(null);
    try {
      const response = await api.post<InsuranceSubmissionDraft>(
        '/documents/insurance-submissions/prepare',
        { honoraires_document_id: honorairesDocumentId, organization },
      );
      setDraft(response.data);
    } catch (error) {
      const message = apiErrorMessage(error, `Impossible de préparer la feuille de soins ${organization}.`);
      console.error(`Erreur préparation ${organization}:`, error);
      window.alert(message);
    } finally {
      setBusyAction(null);
      setPreparingOrganization(null);
    }
  };

  const handleValidate = async () => {
    if (!draft) return;
    setBusyAction('validate');
    setReviewError(null);
    try {
      const response = await api.post<InsuranceSubmissionDraft>(
        '/documents/insurance-submissions/validate',
        draft,
      );
      setDraft(response.data);
    } catch (error) {
      console.error(`Erreur validation ${draft.organization}:`, error);
      setReviewError(apiErrorMessage(error, 'La validation praticien a été refusée.'));
    } finally {
      setBusyAction(null);
    }
  };

  const handleFinalize = async () => {
    if (!draft) return;
    setBusyAction('finalize');
    setReviewError(null);
    try {
      const response = await api.post<InsuranceFinalizationResult>(
        '/documents/insurance-submissions/finalize',
        draft,
      );
      const result = response.data;
      const organization = draft.organization;
      setDraft(null);
      onCloseMenu();
      onArchived();
      window.alert(`PDF ${organization} archivé : ${result.original_filename}`);
    } catch (error) {
      console.error(`Erreur finalisation ${draft.organization}:`, error);
      setReviewError(apiErrorMessage(error, `Le PDF ${draft.organization} n'a pas pu être généré et archivé.`));
    } finally {
      setBusyAction(null);
    }
  };

  const handleCloseReview = () => {
    if (busyAction) return;
    setDraft(null);
    setReviewError(null);
    onCloseMenu();
  };

  const reviewProps = draft ? {
    draft,
    busyAction: busyAction === 'validate' || busyAction === 'finalize' ? busyAction : null,
    error: reviewError,
    onChange: setDraft,
    onValidate: () => void handleValidate(),
    onFinalize: () => void handleFinalize(),
    onClose: handleCloseReview,
  } : null;

  return (
    <>
      <button
        data-insurance-action="prepare-cnss"
        data-m4c-touch
        role="menuitem"
        type="button"
        disabled={busyAction === 'prepare'}
        onClick={() => void handlePrepare('CNSS')}
        className="w-full min-h-11 px-3 rounded-lg hover:bg-primary/5 text-primary font-bold text-xs inline-flex items-center gap-2 transition-colors disabled:opacity-60"
      >
        {preparingOrganization === 'CNSS' ? <Loader2 size={16} className="animate-spin" /> : <ShieldCheck size={16} />}
        {preparingOrganization === 'CNSS' ? 'Préparation CNSS…' : 'Préparer CNSS'}
      </button>
      <div className="mx-2 my-0.5 h-px bg-slate-100" aria-hidden="true" />
      <button
        data-insurance-action="prepare-cnops"
        data-m4c-touch
        role="menuitem"
        type="button"
        disabled={busyAction === 'prepare'}
        onClick={() => void handlePrepare('CNOPS')}
        className="w-full min-h-11 px-3 rounded-lg hover:bg-primary/5 text-primary font-bold text-xs inline-flex items-center gap-2 transition-colors disabled:opacity-60"
      >
        {preparingOrganization === 'CNOPS' ? <Loader2 size={16} className="animate-spin" /> : <ShieldCheck size={16} />}
        {preparingOrganization === 'CNOPS' ? 'Préparation CNOPS…' : 'Préparer CNOPS'}
      </button>
      <div className="mx-2 my-0.5 h-px bg-slate-100" aria-hidden="true" />
      <button
        data-insurance-action="prepare-far"
        data-m4c-touch
        role="menuitem"
        type="button"
        disabled={busyAction === 'prepare'}
        onClick={() => void handlePrepare('FAR')}
        className="w-full min-h-11 px-3 rounded-lg hover:bg-primary/5 text-primary font-bold text-xs inline-flex items-center gap-2 transition-colors disabled:opacity-60"
      >
        {preparingOrganization === 'FAR' ? <Loader2 size={16} className="animate-spin" /> : <ShieldCheck size={16} />}
        {preparingOrganization === 'FAR' ? 'Préparation FAR…' : 'Préparer FAR'}
      </button>

      {draft && reviewProps && typeof document !== 'undefined' && createPortal(
        draft.organization === 'CNOPS'
          ? <CnopsInsuranceSubmissionReview {...reviewProps} />
          : draft.organization === 'FAR'
            ? <FarInsuranceSubmissionReview {...reviewProps} />
            : <CnssInsuranceSubmissionReview {...reviewProps} />,
        document.body,
      )}
    </>
  );
};
