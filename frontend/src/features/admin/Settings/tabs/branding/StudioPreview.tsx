import React, { useEffect, useRef, useState } from 'react';
import type { Scope } from './types';
import { cn } from '../../../../../utils/cn';
import {
  Activity,
  AlertCircle,
  ArrowRight,
  Calendar,
  CheckCircle2,
  ExternalLink,
  FileText,
  Loader2,
  RefreshCcw,
  Users,
} from 'lucide-react';
import { api } from '../../../../../services/api';
import toast from 'react-hot-toast';

interface StudioPreviewProps {
  profile: any;
  scope: Scope;
}

const TEMPLATE_LABELS: Record<string, string> = {
  swiss: 'Swiss Clinic',
  royal: 'Royal Elite',
  clinical: 'Clinical Grid',
  modern: 'Modern Flush',
  heritage: "L'Héritage",
};

export const StudioPreview: React.FC<StudioPreviewProps> = ({ profile, scope }) => {
  const [realPdfUrl, setRealPdfUrl] = useState<string | null>(null);
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
  const [pdfIsStale, setPdfIsStale] = useState(true);
  const blobUrlRef = useRef<string | null>(null);
  const hasGeneratedRef = useRef(false);

  useEffect(() => {
    const ref = blobUrlRef;
    return () => {
      if (ref.current) URL.revokeObjectURL(ref.current);
    };
  }, []);

  useEffect(() => {
    if (hasGeneratedRef.current) setPdfIsStale(true);
  }, [profile]);

  const handleGenerateRealPdf = async () => {
    if (isGeneratingPdf) return;
    setIsGeneratingPdf(true);
    try {
      const sanitizedPayload = { ...profile };
      for (const key in sanitizedPayload) {
        if (sanitizedPayload[key] === '') sanitizedPayload[key] = null;
      }

      const res = await api.post('/documents/sample-preview', sanitizedPayload);
      let pdfPath = res.data.pdf_url;
      if (pdfPath && !pdfPath.startsWith('/')) pdfPath = `/${pdfPath}`;

      const pdfBlob = await api.get(pdfPath, { responseType: 'blob' });
      if (blobUrlRef.current) URL.revokeObjectURL(blobUrlRef.current);
      const blobUrl = URL.createObjectURL(new Blob([pdfBlob.data], { type: 'application/pdf' }));
      blobUrlRef.current = blobUrl;
      setRealPdfUrl(blobUrl);
      hasGeneratedRef.current = true;
      setPdfIsStale(false);
    } catch (e: any) {
      console.error('Erreur API PDF:', e);
      const msg = e.response?.data?.detail || e.message || String(e);
      toast.error(`Erreur : ${msg}`);
    } finally {
      setIsGeneratingPdf(false);
    }
  };

  const renderAppPreview = () => (
    <div className="flex h-full w-full overflow-hidden bg-[#FAFAFA]">
      <div className="flex w-[62px] flex-col items-center gap-6 border-r border-[var(--border-color)] bg-white py-6">
        <div className="h-8 w-8 rounded-lg" style={{ backgroundColor: profile.primary_color || 'var(--primary)' }} />
        <div className="h-6 w-6 rounded-md bg-[var(--border-color)]" />
        <div className="h-6 w-6 rounded-md bg-[var(--border-color)]" />
      </div>
      <div className="flex w-[200px] flex-col gap-4 border-r border-[var(--border-color)] bg-[#F8F9FA] p-5">
        <div className="h-3 w-24 rounded bg-[var(--border-color)]" />
        <div className="flex h-8 w-full items-center gap-2 rounded-md border border-[var(--border-color)] bg-white px-3">
          <div className="h-3 w-3 rounded-full" style={{ backgroundColor: profile.accent_color || 'var(--accent)' }} />
          <div className="h-2 w-16 rounded bg-[var(--border-color)]" />
        </div>
        <div className="flex h-8 w-full items-center gap-2 rounded-md bg-transparent px-3 opacity-50">
          <div className="h-3 w-3 rounded-full bg-[var(--border-color)]" />
          <div className="h-2 w-20 rounded bg-[var(--border-color)]" />
        </div>
      </div>
      <div className="flex flex-1 flex-col gap-8 p-8">
        <h2 className="text-[28px] font-medium text-[var(--text-main)]">Tableau de bord</h2>

        <div className="grid grid-cols-3 gap-4">
          {[Activity, Users, Calendar].map((Icon, i) => (
            <div key={i} className="rounded-xl border border-[var(--border-color)] bg-white p-5 shadow-sm">
              <div
                className="mb-4 flex h-8 w-8 items-center justify-center rounded-lg"
                style={{
                  backgroundColor: profile.primary_color ? `${profile.primary_color}26` : 'var(--primary)15',
                  color: profile.primary_color || 'var(--primary)',
                }}
              >
                <Icon size={16} />
              </div>
              <div className="mb-2 h-6 w-16 rounded bg-[var(--border-color)]" />
              <div className="h-2 w-24 rounded bg-[var(--border-color)] opacity-50" />
            </div>
          ))}
        </div>

        <div className="flex flex-col gap-4 rounded-xl border border-[var(--border-color)] bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between border-b border-[var(--border-color)] pb-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-[var(--border-color)]" />
              <div>
                <div className="mb-1 h-3 w-24 rounded bg-[var(--border-color)]" />
                <div className="h-2 w-16 rounded bg-[var(--border-color)] opacity-50" />
              </div>
            </div>
            <div
              className="rounded-full px-3 py-1 text-[11px] font-bold uppercase"
              style={{
                backgroundColor: profile.secondary_color ? `${profile.secondary_color}26` : 'var(--secondary)15',
                color: profile.secondary_color || 'var(--secondary)',
              }}
            >
              En cours
            </div>
          </div>
          <div className="flex items-center justify-between pt-2">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-[var(--border-color)]" />
              <div>
                <div className="mb-1 h-3 w-32 rounded bg-[var(--border-color)]" />
                <div className="h-2 w-20 rounded bg-[var(--border-color)] opacity-50" />
              </div>
            </div>
            <button
              type="button"
              className="flex items-center gap-2 rounded-lg px-4 py-2 text-[13px] font-semibold text-white transition-opacity hover:opacity-90"
              style={{ backgroundColor: profile.primary_color || 'var(--primary)' }}
            >
              Dossier <ArrowRight size={14} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const templateLabel = TEMPLATE_LABELS[profile.selected_template] || 'Modèle document';

  const renderDocumentPreview = () => (
    <div className="flex h-full w-full flex-col bg-slate-50">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-white px-4 py-3 sm:px-5">
        <div className="min-w-0">
          <div className="text-[10px] font-black uppercase tracking-[0.14em] text-slate-400">Rendu PDF réel</div>
          <div className="truncate text-sm font-black text-slate-800">{templateLabel}</div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div
            className={cn(
              'flex min-h-9 items-center gap-1.5 rounded-full border px-3 text-[10px] font-black uppercase tracking-wide',
              realPdfUrl && !pdfIsStale
                ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                : 'border-amber-200 bg-amber-50 text-amber-700',
            )}
            role="status"
            aria-live="polite"
          >
            {realPdfUrl && !pdfIsStale ? <CheckCircle2 size={13} /> : <AlertCircle size={13} />}
            {realPdfUrl && !pdfIsStale ? 'Rendu à jour' : 'À actualiser'}
          </div>

          <button
            type="button"
            onClick={handleGenerateRealPdf}
            disabled={isGeneratingPdf}
            className="flex min-h-10 items-center gap-2 rounded-xl bg-primary px-4 py-2 text-[10px] font-black uppercase tracking-widest text-white shadow-sm transition-all hover:opacity-90 disabled:cursor-wait disabled:opacity-60 sm:text-[11px]"
            style={{ backgroundColor: 'var(--primary)' }}
          >
            {isGeneratingPdf ? <Loader2 size={15} className="animate-spin" /> : <RefreshCcw size={15} />}
            {realPdfUrl ? 'Actualiser le rendu' : 'Générer le rendu'}
          </button>

          {realPdfUrl && (
            <button
              type="button"
              onClick={() => window.open(realPdfUrl, '_blank')}
              className="flex min-h-10 items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-[10px] font-black uppercase tracking-widest text-slate-600 transition-all hover:border-primary hover:text-primary"
            >
              <ExternalLink size={14} />
              Ouvrir
            </button>
          )}
        </div>
      </div>

      <div className="relative flex-1 overflow-hidden bg-slate-200/60 p-3 sm:p-5">
        {realPdfUrl ? (
          <div className="relative h-full overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl">
            {pdfIsStale && (
              <div className="absolute inset-x-3 top-3 z-10 flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50/95 px-3 py-2 text-[11px] font-semibold text-amber-800 shadow-sm backdrop-blur">
                <AlertCircle size={15} className="shrink-0" />
                Les réglages ont changé. Le PDF affiché correspond à la dernière génération.
              </div>
            )}
            <iframe src={realPdfUrl} className="h-full w-full border-none" title={`Rendu PDF réel — ${templateLabel}`} />
          </div>
        ) : (
          <div className="flex h-full min-h-[520px] flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center">
            <div className="mb-5 flex h-20 w-20 items-center justify-center rounded-[2rem] bg-slate-100 text-slate-300 shadow-inner">
              <FileText size={38} />
            </div>
            <h4 className="text-sm font-black uppercase tracking-widest text-slate-600">PDF réel non généré</h4>
            <p className="mt-3 max-w-sm text-sm leading-relaxed text-slate-400">
              Générez le rendu pour vérifier exactement le modèle produit par le moteur documentaire.
            </p>
            <button
              type="button"
              onClick={handleGenerateRealPdf}
              disabled={isGeneratingPdf}
              className="mt-6 flex min-h-11 items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-[11px] font-black uppercase tracking-widest text-white shadow-lg transition-opacity hover:opacity-90 disabled:opacity-60"
              style={{ backgroundColor: 'var(--primary)' }}
            >
              {isGeneratingPdf ? <Loader2 size={16} className="animate-spin" /> : <RefreshCcw size={16} />}
              Générer le rendu PDF réel
            </button>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="flex h-[720px] min-h-[640px] flex-col overflow-hidden rounded-[2rem] border border-slate-200/60 bg-white/90 shadow-xl ring-1 ring-black/5 backdrop-blur-3xl sm:h-[820px] sm:rounded-[2.5rem] xl:sticky xl:top-[18px] xl:h-[calc(100vh-36px)] xl:min-h-[680px]">
      <div className="z-10 flex items-center justify-between border-b border-slate-200 bg-white/40 p-5 backdrop-blur-md sm:p-6">
        <div className="flex items-center gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-600">
            <Activity size={20} />
          </div>
          <div>
            <span className="mb-1 block text-[10px] font-black uppercase leading-none tracking-widest text-slate-400">
              {scope === 'app' ? 'Aperçu application' : 'Aperçu document'}
            </span>
            <span className="text-base font-black tracking-tight text-slate-800">
              {scope === 'app' ? 'Tableau de bord' : 'PDF réel'}
            </span>
          </div>
        </div>
      </div>

      <div className="relative flex-1 overflow-hidden bg-[var(--bg-medical-pearl)]">
        <div
          className={cn(
            'absolute inset-0 transition-opacity duration-250',
            scope === 'app' ? 'z-10 opacity-100' : 'pointer-events-none z-0 opacity-0',
          )}
        >
          {renderAppPreview()}
        </div>

        <div
          className={cn(
            'absolute inset-0 transition-opacity duration-250',
            scope === 'doc' ? 'z-10 opacity-100' : 'pointer-events-none z-0 opacity-0',
          )}
        >
          {renderDocumentPreview()}
        </div>
      </div>
    </div>
  );
};
