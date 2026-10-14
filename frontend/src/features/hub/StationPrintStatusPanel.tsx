import type { StationFlowLanguage } from './StationAppointmentArrival';

/**
 * LOT04.8-D: presentational-only Station print state. No callbacks, PDF,
 * browser print or HTTP request. Default disabled until B/C are certified.
 */
export type StationPrintVisualStatus = 'disabled' | 'held' | 'uncertain' | 'failed';

const COPY = {
  fr: {
    label: 'Retrait de document',
    disabled: 'L’impression depuis cette Station est en cours de construction.',
    held: 'Demande enregistrée. Adressez-vous à l’accueil avant toute remise.',
    uncertain: 'L’état de l’impression doit être vérifié par le personnel. Ne relancez pas la demande.',
    failed: 'La demande n’a pas abouti. Adressez-vous au personnel du cabinet.',
  },
  en: {
    label: 'Document collection',
    disabled: 'Printing from this Station is under construction.',
    held: 'Request recorded. Contact reception before collecting any document.',
    uncertain: 'Staff must verify the print status. Do not submit the request again.',
    failed: 'The request did not complete. Please contact reception staff.',
  },
  ar: {
    label: 'استلام الوثيقة',
    disabled: 'خدمة الطباعة من هذه المحطة قيد الإنشاء.',
    held: 'تم تسجيل الطلب. يُرجى مراجعة الاستقبال قبل تسلّم أي وثيقة.',
    uncertain: 'يجب على الموظفين التحقق من حالة الطباعة. لا تُعيدوا إرسال الطلب.',
    failed: 'لم يكتمل الطلب. يُرجى مراجعة موظفي الاستقبال.',
  },
} as const;

export type StationPrintStatusPanelProps = {
  language?: StationFlowLanguage;
  status?: StationPrintVisualStatus;
};

/**
 * Render only. Rendering a simulated status does not authorize, submit, or
 * certify a physical print. No action button is intentionally provided.
 */
export function StationPrintStatusPanel({
  language = 'fr',
  status = 'disabled',
}: StationPrintStatusPanelProps) {
  const copy = COPY[language];
  const urgent = status === 'uncertain' || status === 'failed';
  return (
    <section
      aria-label={copy.label}
      aria-live={urgent ? 'assertive' : 'polite'}
      data-testid="station-print-status-panel"
      data-print-status={status}
      dir={language === 'ar' ? 'rtl' : 'ltr'}
      className="w-full max-w-full min-w-0 rounded-xl border border-slate-200 bg-white px-3 py-3 text-start shadow-sm dark:border-slate-700 dark:bg-slate-900"
    >
      <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
        {copy.label}
      </h3>
      <p className="mt-2 max-w-full break-words text-sm leading-relaxed text-slate-700 dark:text-slate-200">
        {copy[status]}
      </p>
    </section>
  );
}
