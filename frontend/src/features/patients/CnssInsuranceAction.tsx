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
  preferredOrganization?: SupportedOrganization | null;
  onArchived: () => void;
  onCloseMenu: () => void;
}

type SupportedOrganization = 'CNSS' | 'CNOPS' | 'FAR';
type BusyAction = 'prepare' | 'validate' | 'finalize' | null;

export const insuranceOrganizationFromAssurance = (assurance?: string | null): SupportedOrganization | null => {
  const normalized = String(assurance || '').trim().toUpperCase();
  if (normalized === 'CNSS') return 'CNSS';
  if (normalized === 'CNOPS') return 'CNOPS';
  if (normalized === 'FAR' || normalized === 'MUTUELLE_FAR') return 'FAR';
  return null;
};

const apiErrorMessage = (error: any, fallback: string): string => {
  const detail = error?.response?.data?.detail;
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (detail && typeof detail.message === 'string' && detail.message.trim()) return detail.message;
  return fallback;
};

const organizationLabel: Record<SupportedOrganization, string> = {
  CNSS: 'CNSS',
  CNOPS: 'CNOPS',
  FAR: 'FAR',
};

export const CnssInsuranceAction = ({
  honorairesDocumentId,
  preferredOrganization = null,
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

  const renderPrepareButton = (organization: SupportedOrganization, primary = false) => (
    <button
      data-insurance-action={`prepare-${organization.toLowerCase()}`}
      data-insurance-preferred={primary ? 'true' : undefined}
      data-m4c-touch
      role="menuitem"
      type="button"
      disabled={busyAction === 'prepare'}
      onClick={() => void handlePrepare(organization)}
      className={`w-full min-h-11 px-3 rounded-lg font-bold text-xs inline-flex items-center gap-2 transition-colors disabled:opacity-60 ${
        primary
          ? 'bg-primary/10 text-primary hover:bg-primary/15'
          : 'hover:bg-primary/5 text-primary'
      }`}
    >
      {preparingOrganization === organization ? <Loader2 size={16} className="animate-spin" /> : <ShieldCheck size={16} />}
      {preparingOrganization === organization
        ? `Préparation ${organizationLabel[organization]}…`
        : primary
          ? `Préparer feuille ${organizationLabel[organization]}`
          : `Préparer ${organizationLabel[organization]}`}
    </button>
  );

  const alternatives = preferredOrganization
    ? (['CNSS', 'CNOPS', 'FAR'] as SupportedOrganization[]).filter(item => item !== preferredOrganization)
    : [];

  return (
    <>
      {preferredOrganization ? (
        <>
          {renderPrepareButton(preferredOrganization, true)}
          <details className="group">
            <summary
              data-insurance-action="change-organization"
              className="min-h-9 px-3 rounded-lg cursor-pointer text-[10px] font-black uppercase tracking-wider text-slate-500 hover:text-primary hover:bg-slate-50 flex items-center"
            >
              Changer d’organisme
            </summary>
            <div className="mt-1 border-t border-slate-100 pt-1">
              {alternatives.map((organization, index) => (
                <div key={organization}>
                  {renderPrepareButton(organization)}
                  {index < alternatives.length - 1 && <div className="mx-2 my-0.5 h-px bg-slate-100" aria-hidden="true" />}
                </div>
              ))}
            </div>
          </details>
        </>
      ) : (
        <>
          {renderPrepareButton('CNSS')}
          <div className="mx-2 my-0.5 h-px bg-slate-100" aria-hidden="true" />
          {renderPrepareButton('CNOPS')}
          <div className="mx-2 my-0.5 h-px bg-slate-100" aria-hidden="true" />
          {renderPrepareButton('FAR')}
        </>
      )}

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
