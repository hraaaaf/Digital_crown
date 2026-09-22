import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../../../utils/cn';
import { CheckCircle2, Clock, Edit3, AlertCircle, FileText, Plus, X } from 'lucide-react';
import { api } from '../../../../services/api';
import { TemplateOverwriteDialog } from './TemplateOverwriteDialog';
import {
  CERTIFICATE_TYPE_FREE,
  CERTIFICATE_TYPE_PRESENCE,
  CERTIFICATE_TYPE_WORK_STOP,
  certificateRequiresDuration,
  normalizeCertificateSelection,
} from '../CertificatePolicy';

type CertificateTemplateSummary = {
  id: string;
  name: string;
  description?: string | null;
};

type CertificateTemplateDetail = CertificateTemplateSummary & {
  body_html?: string | null;
};

export const CertificateTemplatePresets: React.FC<{
  content: string;
  onApply: (content: string) => void;
}> = ({ content, onApply }) => {
  const [templates, setTemplates] = React.useState<CertificateTemplateSummary[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [applyingId, setApplyingId] = React.useState<string | null>(null);
  const [pendingTemplate, setPendingTemplate] = React.useState<{ name: string; body: string } | null>(null);
  const [showCreate, setShowCreate] = React.useState(false);
  const [templateName, setTemplateName] = React.useState('');
  const [templateBody, setTemplateBody] = React.useState('');
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState('');
  const mountedRef = React.useRef(true);

  React.useEffect(() => () => {
    mountedRef.current = false;
  }, []);

  const loadTemplates = React.useCallback(async () => {
    if (!mountedRef.current) return;
    setLoading(true);
    setError('');
    try {
      const response = await api.get('/templates', {
        params: { type: 'CERTIFICAT', is_system: false },
      });
      if (mountedRef.current) {
        setTemplates(Array.isArray(response?.data) ? response.data : []);
      }
    } catch {
      if (mountedRef.current) {
        setTemplates([]);
        setError('Impossible de charger les modèles du cabinet.');
      }
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void loadTemplates();
  }, [loadTemplates]);

  const applyTemplate = async (templateId: string) => {
    if (applyingId) return;
    setApplyingId(templateId);
    setError('');
    try {
      const response = await api.get(`/templates/${templateId}`);
      const body = String((response?.data as CertificateTemplateDetail | undefined)?.body_html || '').trim();
      if (!body) {
        setError('Ce modèle ne contient aucun texte réutilisable.');
        return;
      }
      if (content.trim() && content.trim() !== body) {
        setPendingTemplate({
          name: String((response?.data as CertificateTemplateDetail | undefined)?.name || 'Modèle'),
          body,
        });
        return;
      }
      onApply(body);
    } catch {
      setError('Impossible d’appliquer ce modèle.');
    } finally {
      setApplyingId(null);
    }
  };

  const openCreate = () => {
    setTemplateName('');
    setTemplateBody(content);
    setError('');
    setShowCreate(true);
  };

  const createTemplate = async () => {
    const name = templateName.trim();
    const body = templateBody.trim();
    if (!name || body.length < 10 || saving) return;

    setSaving(true);
    setError('');
    try {
      const response = await api.post('/templates', {
        type: 'CERTIFICAT',
        style_key: 'saninova',
        name,
        description: 'Modèle de certificat médical du cabinet',
        body_html: body,
        is_system: false,
        is_default: false,
      });
      const created = response?.data as CertificateTemplateDetail | undefined;
      if (created?.id) {
        setTemplates(prev => [
          ...prev.filter(item => item.id !== created.id),
          { id: created.id, name: created.name, description: created.description },
        ]);
      } else {
        await loadTemplates();
      }
      onApply(body);
      setShowCreate(false);
    } catch (requestError: any) {
      const status = requestError?.response?.status;
      setError(
        status === 403
          ? 'Vous n’avez pas l’autorisation de créer un modèle.'
          : requestError?.response?.data?.detail || 'Impossible d’enregistrer ce modèle.',
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mb-6 rounded-2xl border border-slate-100 bg-slate-50/70 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Modèles du cabinet</div>
          <p className="mt-1 text-[10px] font-semibold text-slate-500">
            Un modèle est appliqué uniquement après votre clic et reste entièrement éditable.
          </p>
        </div>
        <button
          type="button"
          onClick={openCreate}
          className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-primary/20 bg-white px-3 py-2 text-[10px] font-black uppercase tracking-wider text-primary transition-colors hover:bg-primary/5"
        >
          <Plus size={14} /> Créer un modèle
        </button>
      </div>

      <div className="mt-4 flex flex-wrap gap-2" aria-label="Modèles de certificat du cabinet">
        {loading ? (
          <span className="text-[10px] font-bold text-slate-400">Chargement des modèles…</span>
        ) : templates.length > 0 ? (
          templates.map(template => (
            <button
              key={template.id}
              type="button"
              onClick={() => void applyTemplate(template.id)}
              disabled={applyingId !== null}
              className="inline-flex min-h-10 max-w-full items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-left text-[11px] font-bold text-slate-600 transition-all hover:border-primary/30 hover:text-primary disabled:opacity-50"
            >
              <FileText size={14} className="shrink-0" />
              <span className="truncate">{template.name}</span>
            </button>
          ))
        ) : (
          <span className="text-[10px] font-bold text-slate-400">Aucun modèle personnalisé enregistré.</span>
        )}
      </div>

      <p className="mt-3 text-[9px] font-bold leading-relaxed text-slate-400">
        Appliquer un modèle copie son texte dans le brouillon. Le praticien doit le relire et le valider avant génération.
      </p>

      {error && <p role="alert" className="mt-3 rounded-xl bg-rose-50 px-3 py-2 text-[10px] font-bold text-rose-700">{error}</p>}

      {pendingTemplate && (
        <TemplateOverwriteDialog
          modelName={pendingTemplate.name}
          scopeLabel="Certificat médical"
          onCancel={() => setPendingTemplate(null)}
          onConfirm={() => {
            onApply(pendingTemplate.body);
            setPendingTemplate(null);
          }}
        />
      )}

      {showCreate && (
        <div className="fixed inset-0 z-[130] flex items-center justify-center bg-slate-950/40 p-4" role="dialog" aria-modal="true" aria-labelledby="certificate-template-create-title">
          <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Modèle du cabinet</p>
                <h3 id="certificate-template-create-title" className="mt-1 text-lg font-black text-slate-900">Créer un modèle</h3>
              </div>
              <button type="button" onClick={() => setShowCreate(false)} className="rounded-lg p-2 text-slate-400 hover:bg-slate-50" aria-label="Fermer">
                <X size={16} />
              </button>
            </div>

            <div className="mt-5 space-y-4">
              <label className="block space-y-1.5">
                <span className="text-xs font-bold text-slate-600">Nom du modèle *</span>
                <input
                  value={templateName}
                  onChange={event => setTemplateName(event.target.value)}
                  maxLength={100}
                  className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm font-semibold outline-none focus:border-primary focus:ring-2 focus:ring-primary/10"
                  placeholder="Ex. Certificat aptitude traitement"
                />
              </label>
              <label className="block space-y-1.5">
                <span className="text-xs font-bold text-slate-600">Contenu du modèle *</span>
                <textarea
                  value={templateBody}
                  onChange={event => setTemplateBody(event.target.value)}
                  className="min-h-44 w-full resize-y rounded-xl border border-slate-200 px-3 py-2.5 text-sm leading-relaxed outline-none focus:border-primary focus:ring-2 focus:ring-primary/10"
                  placeholder="Texte réutilisable du certificat…"
                  aria-label="Contenu du modèle"
                />
              </label>
              <p className="text-[10px] font-semibold text-slate-500">
                Le modèle ne fixe ni la nature clinique ni une durée. Il prépare uniquement le texte libre.
              </p>
            </div>

            <div className="mt-5 flex flex-wrap justify-end gap-2">
              <button type="button" onClick={() => setShowCreate(false)} className="min-h-10 rounded-xl border border-slate-200 px-4 py-2 text-sm font-bold text-slate-600">
                Annuler
              </button>
              <button
                type="button"
                onClick={() => void createTemplate()}
                disabled={!templateName.trim() || templateBody.trim().length < 10 || saving}
                className="min-h-10 rounded-xl bg-primary px-4 py-2 text-sm font-black text-white disabled:opacity-40"
              >
                {saving ? 'Enregistrement…' : 'Enregistrer'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

interface CertificateFormProps {
  patientId: string;
  certifType: string;
  setCertifType: (type: string) => void;
  certifDays: number;
  setCertifDays: (days: number) => void;
  docDate: string;
  certifStartDate: string;
  setCertifStartDate: (date: string) => void;
  certifCustomMotif: string;
  setCertifCustomMotif: (v: string) => void;
}

export const CertificateForm: React.FC<CertificateFormProps> = ({
  patientId,
  certifType,
  setCertifType,
  certifDays,
  setCertifDays,
  docDate,
  certifStartDate,
  setCertifStartDate,
  certifCustomMotif,
  setCertifCustomMotif,
}) => {
  const [suggestion, setSuggestion] = React.useState<any>(null);

  React.useEffect(() => {
    if (!patientId) return;
    const fetchSuggestion = async () => {
      try {
        const res = await api.get(`/prescriptions/certif-suggest/${patientId}`);
        setSuggestion(res.data);
      } catch (err) {
        console.error('Certif Suggest Error:', err);
      }
    };
    fetchSuggestion();
  }, [patientId]);

  React.useEffect(() => {
    const normalized = normalizeCertificateSelection(certifType, certifCustomMotif);
    if (normalized.type !== certifType) setCertifType(normalized.type);
    if (normalized.content !== certifCustomMotif) setCertifCustomMotif(normalized.content);
  }, [certifType, certifCustomMotif, setCertifType, setCertifCustomMotif]);

  const labelClass = "text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] block mb-4 ml-1";
  const inputClass = "w-full px-5 py-4 bg-white/70 border border-slate-100 rounded-2xl text-sm outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary transition-all duration-300 shadow-sm font-bold text-slate-800";
  const freeContentMissing = certifType === CERTIFICATE_TYPE_FREE && !certifCustomMotif.trim();
  const durationMissing = certificateRequiresDuration(certifType) && (!Number.isInteger(certifDays) || certifDays < 1);

  const certifTypes = [
    {
      id: CERTIFICATE_TYPE_WORK_STOP,
      label: 'Arrêt de travail',
      icon: <Clock size={14} />,
      description: 'Repos prescrit et daté par le praticien',
    },
    {
      id: CERTIFICATE_TYPE_PRESENCE,
      label: 'Présence au cabinet',
      icon: <CheckCircle2 size={14} />,
      description: 'Atteste une présence constatée par le praticien',
    },
    {
      id: CERTIFICATE_TYPE_FREE,
      label: 'Certificat médical',
      icon: <Edit3 size={14} />,
      description: 'Document libre rédigé par le praticien',
    },
  ];

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 max-w-4xl w-full mx-auto py-8">
      <div className="bg-white/40 backdrop-blur-xl rounded-[3rem] border border-white/60 p-10 shadow-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 blur-[80px] -mr-32 -mt-32 rounded-full pointer-events-none" />

        <div className="relative z-10 space-y-10">
          <div>
            <div className="flex items-center justify-between mb-4 gap-4">
              <label className={labelClass + " mb-0"}>Nature du document</label>
              {suggestion && (
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-center gap-2 px-3 py-2 rounded-xl text-[9px] font-bold bg-amber-500/10 text-amber-700 border border-amber-200 max-w-sm"
                  role="status"
                  aria-live="polite"
                >
                  <AlertCircle size={12} className="shrink-0" />
                  <span>
                    Signal documentaire : {suggestion.reason || 'contexte détecté'}. Aucun choix n’est appliqué automatiquement ; le praticien décide du type, du contenu et, le cas échéant, de la durée.
                  </span>
                </motion.div>
              )}
            </div>

            <div className="flex flex-wrap justify-center gap-4">
              {certifTypes.map((type) => (
                <div key={type.id} className="flex flex-col items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setCertifType(type.id)}
                    className={cn(
                      "flex items-center justify-center gap-3 px-6 py-4 rounded-[1.5rem] text-[10px] font-black uppercase tracking-widest transition-all border shadow-sm min-w-[180px]",
                      certifType === type.id
                        ? "bg-primary text-white border-primary shadow-xl shadow-primary/20"
                        : "bg-white text-slate-500 border-slate-100 hover:border-primary/30"
                    )}
                    style={certifType === type.id ? { backgroundColor: 'var(--primary)' } : {}}
                    aria-pressed={certifType === type.id}
                  >
                    <span className={cn(certifType === type.id ? "text-white" : "text-primary/40")}>{type.icon}</span>
                    {type.label}
                  </button>
                  <span className="text-[7px] font-black text-slate-300 uppercase tracking-widest text-center px-4 max-w-[210px]">
                    {type.description}
                  </span>
                </div>
              ))}
            </div>

            {!certifType && (
              <p className="mt-5 text-center text-[9px] font-bold text-slate-400">
                Aucun type sélectionné. Le praticien choisit explicitement la nature du certificat.
              </p>
            )}

            {certifType === CERTIFICATE_TYPE_FREE && (
              <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} className="mt-6">
                <CertificateTemplatePresets content={certifCustomMotif} onApply={setCertifCustomMotif} />
                <label htmlFor="certificate-free-content" className={labelClass}>Contenu du certificat médical</label>
                <textarea
                  id="certificate-free-content"
                  className={cn(
                    inputClass,
                    "min-h-40 resize-y leading-relaxed",
                    freeContentMissing && "border-amber-200 focus:border-amber-400 focus:ring-amber-100",
                  )}
                  placeholder="Rédigez librement le contenu certifié par le praticien..."
                  value={certifCustomMotif}
                  onChange={(e) => setCertifCustomMotif(e.target.value)}
                  autoFocus
                  rows={6}
                  required
                  aria-required="true"
                  aria-invalid={freeContentMissing}
                  aria-describedby="certificate-free-content-help"
                />
                <p
                  id="certificate-free-content-help"
                  className={cn(
                    "mt-2 px-1 text-[9px] font-bold",
                    freeContentMissing ? "text-amber-600" : "text-slate-400",
                  )}
                >
                  {freeContentMissing
                    ? 'Contenu requis avant génération. Le logiciel ne complète jamais ce texte à la place du praticien.'
                    : 'Ce texte est repris tel quel dans le corps du certificat. Aucune suggestion clinique n’est injectée automatiquement.'}
                </p>
              </motion.div>
            )}
          </div>

          {certificateRequiresDuration(certifType) && (
            <div className="pt-8 border-t border-slate-100/50 space-y-6">
              <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_220px] sm:items-end">
                <div>
                  <label htmlFor="certificate-rest-days" className={labelClass + " mb-1"}>Durée du repos</label>
                  <p className="text-[9px] font-bold text-slate-400 italic">À saisir et valider par le praticien. Aucune durée n’est préremplie.</p>
                </div>
                <div>
                  <label htmlFor="certificate-rest-start" className={labelClass + " mb-1"}>Début du repos</label>
                  <input
                    id="certificate-rest-start"
                    type="date"
                    value={certifStartDate || docDate}
                    onChange={(e) => setCertifStartDate(e.target.value)}
                    className="w-full rounded-xl border border-slate-100 bg-white/70 px-4 py-3 text-sm font-bold text-slate-700 shadow-sm outline-none transition-all focus:border-primary focus:ring-4 focus:ring-primary/5"
                  />
                </div>
              </div>

              <div className="flex items-center justify-between gap-4">
                <input
                  id="certificate-rest-days"
                  type="number"
                  min="1"
                  max="365"
                  step="1"
                  inputMode="numeric"
                  value={certifDays > 0 ? certifDays : ''}
                  placeholder="Saisir la durée"
                  onChange={(e) => {
                    const raw = e.target.value;
                    setCertifDays(raw === '' ? 0 : Number.parseInt(raw, 10));
                  }}
                  className={cn(
                    inputClass,
                    "max-w-xs",
                    durationMissing && "border-amber-200 focus:border-amber-400 focus:ring-amber-100",
                  )}
                  aria-label="Durée du repos en jours"
                  aria-required="true"
                  aria-invalid={durationMissing}
                />
                <span className="shrink-0 text-2xl font-black text-primary tracking-tighter" style={{ color: 'var(--primary)' }}>
                  {certifDays > 0
                    ? <>{certifDays} <span className="text-[10px] uppercase tracking-widest ml-1 opacity-40">jours</span></>
                    : <span className="text-sm uppercase tracking-widest opacity-40">Non définie</span>}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center justify-center gap-2 text-slate-400">
        <div className="w-1.5 h-1.5 rounded-full bg-slate-200" />
        <span className="text-[9px] font-black uppercase tracking-[0.3em]">Validation du praticien requise</span>
        <div className="w-1.5 h-1.5 rounded-full bg-slate-200" />
      </div>
    </div>
  );
};