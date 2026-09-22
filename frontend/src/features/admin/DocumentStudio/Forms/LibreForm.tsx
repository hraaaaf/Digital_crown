import React, { useEffect, useRef } from 'react';
import { cn } from '../../../../utils/cn';
import { api } from '../../../../services/api';
import { TemplateOverwriteDialog } from './TemplateOverwriteDialog';

import type { ValidationError } from '../useDocumentGenerator';
import { isLibreDirty, setLibreDirty } from '../LibreDirtyState';
import { AlertCircle, Bold, Italic, Underline, Table, Type, FileText, Save, X } from 'lucide-react';

type LibreTemplateSummary = {
  id: string;
  name: string;
  description?: string | null;
};

type LibreTemplateDetail = LibreTemplateSummary & {
  body_html?: string | null;
};

export const LibreTemplatePresets: React.FC<{
  title: string;
  content: string;
  onApply: (title: string, content: string) => void;
}> = ({ title, content, onApply }) => {
  const [templates, setTemplates] = React.useState<LibreTemplateSummary[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [applyingId, setApplyingId] = React.useState<string | null>(null);
  const [pendingTemplate, setPendingTemplate] = React.useState<{ name: string; body: string } | null>(null);
  const [showSave, setShowSave] = React.useState(false);
  const [templateName, setTemplateName] = React.useState('');
  const [templateBody, setTemplateBody] = React.useState('');
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState('');

  const loadTemplates = React.useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get('/templates', {
        params: { type: 'DOCUMENT_LIBRE', is_system: false },
      });
      setTemplates(Array.isArray(response?.data) ? response.data : []);
    } catch {
      setTemplates([]);
      setError('Impossible de charger les modèles de document libre.');
    } finally {
      setLoading(false);
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
      const template = response?.data as LibreTemplateDetail | undefined;
      const body = String(template?.body_html || '').trim();
      if (!template?.name || !body) {
        setError('Ce modèle est incomplet et ne peut pas être appliqué.');
        return;
      }
      const wouldReplace = (title.trim() && title.trim() !== template.name) || (content.trim() && content.trim() !== body);
      if (wouldReplace) {
        setPendingTemplate({ name: template.name, body });
        return;
      }
      onApply(template.name, body);
    } catch {
      setError('Impossible d’appliquer ce modèle.');
    } finally {
      setApplyingId(null);
    }
  };

  const openSave = () => {
    setTemplateName(title.trim().slice(0, 100));
    setTemplateBody(content);
    setError('');
    setShowSave(true);
  };

  const saveTemplate = async () => {
    const name = templateName.trim();
    const body = templateBody.trim();
    if (!name || body.length < 10 || saving) return;

    setSaving(true);
    setError('');
    try {
      const response = await api.post('/templates', {
        type: 'DOCUMENT_LIBRE',
        style_key: 'saninova',
        name,
        description: 'Modèle de document libre du cabinet',
        body_html: body,
        is_system: false,
        is_default: false,
      });
      const created = response?.data as LibreTemplateDetail | undefined;
      if (created?.id) {
        setTemplates(prev => [
          ...prev.filter(item => item.id !== created.id),
          { id: created.id, name: created.name, description: created.description },
        ]);
      } else {
        await loadTemplates();
      }
      setShowSave(false);
    } catch (requestError: any) {
      const status = requestError?.response?.status;
      setError(
        status === 403
          ? 'Vous n’avez pas l’autorisation d’enregistrer un modèle.'
          : requestError?.response?.data?.detail || 'Impossible d’enregistrer ce modèle.',
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="border-b border-slate-200 bg-white/70 px-5 py-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-[9px] font-black uppercase tracking-[0.18em] text-slate-400">Mes modèles</div>
          <p className="mt-1 text-[10px] font-semibold text-slate-500">
            Un modèle remplit le titre et le contenu uniquement après votre clic.
          </p>
        </div>
        <button
          type="button"
          onClick={openSave}
          disabled={!title.trim() || content.trim().length < 10}
          className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-primary/20 bg-white px-3 py-2 text-[10px] font-black uppercase tracking-wider text-primary transition-colors hover:bg-primary/5 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Save size={14} /> Enregistrer comme modèle
        </button>
      </div>

      <div className="mt-3 flex flex-wrap gap-2" aria-label="Modèles de document libre du cabinet">
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

      {error && <p role="alert" className="mt-3 rounded-xl bg-rose-50 px-3 py-2 text-[10px] font-bold text-rose-700">{error}</p>}

      {pendingTemplate && (
        <TemplateOverwriteDialog
          modelName={pendingTemplate.name}
          scopeLabel="Document libre"
          onCancel={() => setPendingTemplate(null)}
          onConfirm={() => {
            onApply(pendingTemplate.name, pendingTemplate.body);
            setPendingTemplate(null);
          }}
        />
      )}

      {showSave && (
        <div className="fixed inset-0 z-[130] flex items-center justify-center bg-slate-950/40 p-4" role="dialog" aria-modal="true" aria-labelledby="libre-template-save-title">
          <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Document libre</p>
                <h3 id="libre-template-save-title" className="mt-1 text-lg font-black text-slate-900">Enregistrer comme modèle</h3>
              </div>
              <button type="button" onClick={() => setShowSave(false)} className="rounded-lg p-2 text-slate-400 hover:bg-slate-50" aria-label="Fermer">
                <X size={16} />
              </button>
            </div>

            <div className="mt-5 space-y-4">
              <label className="block space-y-1.5">
                <span className="text-xs font-bold text-slate-600">Nom du modèle / titre appliqué *</span>
                <input
                  value={templateName}
                  onChange={event => setTemplateName(event.target.value)}
                  maxLength={100}
                  className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm font-semibold outline-none focus:border-primary focus:ring-2 focus:ring-primary/10"
                  placeholder="Ex. Lettre au médecin traitant"
                />
              </label>
              <label className="block space-y-1.5">
                <span className="text-xs font-bold text-slate-600">Contenu du modèle *</span>
                <textarea
                  value={templateBody}
                  onChange={event => setTemplateBody(event.target.value)}
                  className="min-h-44 w-full resize-y rounded-xl border border-slate-200 px-3 py-2.5 text-sm leading-relaxed outline-none focus:border-primary focus:ring-2 focus:ring-primary/10"
                  aria-label="Contenu du modèle de document libre"
                />
              </label>
              <p className="text-[10px] font-semibold text-slate-500">
                Destinataire, date, format et alignement restent propres au document en cours.
              </p>
            </div>

            <div className="mt-5 flex flex-wrap justify-end gap-2">
              <button type="button" onClick={() => setShowSave(false)} className="min-h-10 rounded-xl border border-slate-200 px-4 py-2 text-sm font-bold text-slate-600">
                Annuler
              </button>
              <button
                type="button"
                onClick={() => void saveTemplate()}
                disabled={!templateName.trim() || templateBody.trim().length < 10 || saving}
                className="min-h-10 rounded-xl bg-primary px-4 py-2 text-sm font-black text-white disabled:opacity-40"
              >
                {saving ? 'Enregistrement…' : 'Enregistrer le modèle'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

interface LibreFormProps {
  title: string;
  setTitle: (val: string) => void;
  content: string;
  setContent: (val: string) => void;
  customPatient: string;
  setCustomPatient: (val: string) => void;
  customDate: string;
  setCustomDate: (val: string) => void;
  hideHeader: boolean;
  setHideHeader: (val: boolean) => void;
  pageSize: 'A5' | 'A4';
  setPageSize: (val: 'A5' | 'A4') => void;
  alignment: 'left' | 'center' | 'right' | 'justify';
  setAlignment: (val: 'left' | 'center' | 'right' | 'justify') => void;
  validationErrors?: ValidationError[];
}

export const LibreForm: React.FC<LibreFormProps> = ({
  title, setTitle,
  content, setContent,
  customPatient, setCustomPatient,
  customDate, setCustomDate,
  hideHeader, setHideHeader,
  pageSize, setPageSize,
  alignment, setAlignment,
  validationErrors = []
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      if (!isLibreDirty()) return;
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, []);

  const markDirty = () => setLibreDirty(true);

  const insertTag = (openTag: string, closeTag: string) => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selected = content.substring(start, end);
    
    const newText = content.substring(0, start) + openTag + selected + closeTag + content.substring(end);
    markDirty();
    setContent(newText);
    
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(start + openTag.length, start + openTag.length + selected.length);
    }, 10);
  };

  const handleTableInsert = () => {
    const tableSnippet = `\n| Colonne 1 | Colonne 2 |\n|-----------|-----------|\n| Ligne 1   | Valeur    |\n`;
    insertTag(tableSnippet, '');
  };

  const inputClass = "w-full px-4 py-3 bg-white/70 border border-slate-100 rounded-xl text-sm outline-none focus:ring-4 focus:ring-primary/5 focus:border-primary transition-all duration-300 shadow-sm font-bold text-slate-800";
  const labelClass = "text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] block mb-2 ml-1";
  const titleError = validationErrors.find(e => e.field === 'libreTitle');
  const contentError = validationErrors.find(e => e.field === 'libreContent');

  return (
    <div className="space-y-6 animate-in fade-in duration-500 h-full flex flex-col max-w-4xl mx-auto py-8 w-full">
      
      {/* 🌟 Header Glassmorphism */}
      <div className="bg-white/40 backdrop-blur-xl rounded-[2.5rem] border border-white/60 p-8 shadow-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 blur-[80px] -mr-32 -mt-32 rounded-full pointer-events-none" />
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative z-10">
          <div className="md:col-span-1">
            <label className={labelClass}>Titre du Document</label>
            <input type="text" className={cn(inputClass, titleError && "border-red-300 shadow-red-50")} value={title} onChange={(e) => { markDirty(); setTitle(e.target.value); }} placeholder="Ex: ORDONNANCE, LETTRE..." />
            {titleError && (
              <div className="mt-2 text-[9px] font-black text-red-500 uppercase tracking-widest flex items-center gap-1">
                <AlertCircle size={12} /> Titre Requis
              </div>
            )}
          </div>
          <div>
            <label className={labelClass}>Destinataire <span className="opacity-50">(Optionnel)</span></label>
            <input type="text" className={inputClass} value={customPatient} onChange={(e) => { markDirty(); setCustomPatient(e.target.value); }} placeholder="Ex: À qui de droit..." />
          </div>
          <div>
            <label className={labelClass}>Date/Lieu <span className="opacity-50">(Optionnel)</span></label>
            <input type="text" className={inputClass} value={customDate} onChange={(e) => { markDirty(); setCustomDate(e.target.value); }} placeholder="Ex: Rabat, le 12/05/2026" />
          </div>
          
          <div className="md:col-span-3 flex flex-wrap items-center justify-between gap-6 mt-4 p-4 bg-slate-50/50 rounded-2xl border border-slate-100">
            <div className="flex items-center gap-3">
              <input 
                type="checkbox" 
                id="hideHeader" 
                checked={hideHeader} 
                onChange={(e) => { markDirty(); setHideHeader(e.target.checked); }}
                className="w-4 h-4 rounded border-slate-300 text-primary focus:ring-primary accent-primary"
              />
              <label htmlFor="hideHeader" className="text-[11px] font-black text-slate-500 uppercase tracking-widest cursor-pointer">Masquer l'en-tête patient</label>
            </div>

            <div className="flex gap-8">
              <div className="flex items-center gap-3">
                <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Format</span>
                <div className="flex bg-white p-1 rounded-xl shadow-sm border border-slate-100 gap-1">
                  {['A5', 'A4'].map((size) => (
                    <button 
                      key={size}
                      type="button"
                      onClick={() => { markDirty(); setPageSize(size as 'A5' | 'A4'); }}
                      className={cn(
                        "px-4 py-1.5 rounded-lg text-[10px] font-black transition-all",
                        pageSize === size ? "bg-primary text-white shadow-md shadow-primary/20" : "text-slate-400 hover:text-slate-600 hover:bg-slate-50"
                      )}
                    >
                      {size}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex items-center gap-3">
                <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Alignement</span>
                <div className="flex bg-white p-1 rounded-xl shadow-sm border border-slate-100 gap-1">
                  {[
                    { id: 'left', label: 'Gauche' },
                    { id: 'center', label: 'Centre' },
                    { id: 'right', label: 'Droite' },
                    { id: 'justify', label: 'Justifié' }
                  ].map((align) => (
                    <button 
                      key={align.id}
                      type="button"
                      onClick={() => { markDirty(); setAlignment(align.id as 'left' | 'center' | 'right' | 'justify'); }}
                      className={cn(
                        "px-3 py-1.5 rounded-lg text-[10px] font-black transition-all",
                        alignment === align.id ? "bg-primary text-white shadow-md shadow-primary/20" : "text-slate-400 hover:text-slate-600 hover:bg-slate-50"
                      )}
                    >
                      {align.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ✍️ Zone de Rédaction avec Toolbar */}
      <div className="flex-1 min-h-[400px] flex flex-col bg-white rounded-[2.5rem] border border-slate-200 shadow-sm overflow-hidden relative">
        
        <LibreTemplatePresets
          title={title}
          content={content}
          onApply={(nextTitle, nextContent) => {
            markDirty();
            setTitle(nextTitle);
            setContent(nextContent);
          }}
        />

        {/* Toolbar */}
        <div className="px-6 py-4 bg-slate-50/80 border-b border-slate-200 flex items-center gap-2 flex-wrap">
          <div className="flex bg-white rounded-xl shadow-sm border border-slate-200 p-1">
             <button type="button" onClick={() => insertTag('<b>', '</b>')} className="p-2 text-slate-500 hover:text-primary hover:bg-primary/5 rounded-lg transition-all" title="Gras">
               <Bold size={16} strokeWidth={2.5} />
             </button>
             <button type="button" onClick={() => insertTag('<i>', '</i>')} className="p-2 text-slate-500 hover:text-primary hover:bg-primary/5 rounded-lg transition-all" title="Italique">
               <Italic size={16} strokeWidth={2.5} />
             </button>
             <button type="button" onClick={() => insertTag('<u>', '</u>')} className="p-2 text-slate-500 hover:text-primary hover:bg-primary/5 rounded-lg transition-all" title="Souligné">
               <Underline size={16} strokeWidth={2.5} />
             </button>
          </div>
          
          <div className="w-px h-6 bg-slate-200 mx-2" />
          
          <div className="flex bg-white rounded-xl shadow-sm border border-slate-200 p-1">
             <button type="button" onClick={() => insertTag('<font size="16">', '</font>')} className="flex items-center gap-2 px-3 py-2 text-slate-500 hover:text-primary hover:bg-primary/5 rounded-lg transition-all" title="Agrandir">
               <Type size={16} /> <span className="text-[10px] font-black uppercase tracking-widest">Grand Titre</span>
             </button>
             <button type="button" onClick={handleTableInsert} className="flex items-center gap-2 px-3 py-2 text-slate-500 hover:text-primary hover:bg-primary/5 rounded-lg transition-all" title="Tableau">
               <Table size={16} /> <span className="text-[10px] font-black uppercase tracking-widest">Tableau</span>
             </button>
          </div>
        </div>

        <textarea
          ref={textareaRef}
          className={cn(
            "w-full flex-1 p-8 text-sm font-medium text-slate-700 outline-none transition-all resize-none leading-relaxed custom-scrollbar",
            contentError ? "bg-red-50/30" : "bg-transparent"
          )}
          value={content}
          onChange={(e) => { markDirty(); setContent(e.target.value); }}
          placeholder="Rédigez votre document ici... Utilisez la barre d'outils pour mettre en forme le texte."
        />
        {contentError && (
          <div className="absolute bottom-6 right-6 px-5 py-3 bg-red-50 border border-red-200 rounded-2xl text-[10px] font-black text-red-600 uppercase tracking-widest flex items-center gap-2 shadow-lg">
            <AlertCircle size={16} /> Le contenu ne peut être vide
          </div>
        )}
      </div>
    </div>
  );
};