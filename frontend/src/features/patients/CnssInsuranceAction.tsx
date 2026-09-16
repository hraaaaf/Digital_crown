import { useState } from 'react';
import { createPortal } from 'react-dom';
import { Loader2, ShieldCheck } from 'lucide-react';
import { api } from '../../services/api';
import { CnssInsuranceSubmissionReview } from './CnssInsuranceSubmissionReview';
import type {
  InsuranceFinalizationResult,
  InsuranceSubmissionDraft,
} from './InsuranceSubmissionTypes';

interface CnssInsuranceActionProps {
  honorairesDocumentId: number;
  onArchived: () => void;
  onCloseMenu: () => void;
}

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
  const [reviewError, setReviewError] = useState<string | null>(null);

  const handlePrepare = async () => {
    setBusyAction('prepare');
    setReviewError(null);
    try {
      const response = await api.post<InsuranceSubmissionDraft>(
        '/documents/insurance-submissions/prepare',
        { honoraires_document_id: honorairesDocumentId, organization: 'CNSS' },
      );
      setDraft(response.data);
    } catch (error) {
      const message = apiErrorMessage(error, 'Impossible de préparer la feuille de soins CNSS.');
      console.error('Erreur préparation CNSS:', error);
      window.alert(message);
    } finally {
      setBusyAction(null);
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
      console.error('Erreur validation CNSS:', error);
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
      setDraft(null);
      onCloseMenu();
      onArchived();
      window.alert(`PDF CNSS archivé : ${result.original_filename}`);
    } catch (error) {
      console.error('Erreur finalisation CNSS:', error);
      setReviewError(apiErrorMessage(error, "Le PDF CNSS n'a pas pu être généré et archivé."));
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

  return (
    <>
      <button
        data-insurance-action="prepare-cnss"
        data-m4c-touch
        role="menuitem"
        type="button"
        disabled={busyAction === 'prepare'}
        onClick={() => void handlePrepare()}
        className="w-full min-h-11 px-3 rounded-lg hover:bg-primary/5 text-primary font-bold text-xs inline-flex items-center gap-2 transition-colors disabled:opacity-60"
      >
        {busyAction === 'prepare' ? <Loader2 size={16} className="animate-spin" /> : <ShieldCheck size={16} />}
        {busyAction === 'prepare' ? 'Préparation CNSS…' : 'Préparer CNSS'}
      </button>

      {draft && typeof document !== 'undefined' && createPortal(
        <CnssInsuranceSubmissionReview
          draft={draft}
          busyAction={busyAction === 'validate' || busyAction === 'finalize' ? busyAction : null}
          error={reviewError}
          onChange={setDraft}
          onValidate={() => void handleValidate()}
          onFinalize={() => void handleFinalize()}
          onClose={handleCloseReview}
        />,
        document.body,
      )}
    </>
  );
};
