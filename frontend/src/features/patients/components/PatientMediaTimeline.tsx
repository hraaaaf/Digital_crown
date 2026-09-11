import { useCallback, useEffect, useMemo, useRef, useState, type ChangeEvent } from 'react';
import { Eye, FileText, Image as ImageIcon, Images, Loader2, RefreshCcw, Upload, X } from 'lucide-react';
import toast from 'react-hot-toast';

import { api } from '../../../services/api';

interface ClinicalAsset {
  id: number;
  patient_id: number;
  asset_type: 'PHOTO' | 'RADIOGRAPH' | 'DOCUMENT' | string;
  source_kind: string;
  mime_type?: string | null;
  byte_size?: number | null;
  timepoint?: string | null;
  captured_at?: string | null;
  created_at: string;
  thumbnail_asset_id?: number | null;
}

interface PatientMediaTimelineProps {
  patientId: number;
}

interface ViewerState {
  asset: ClinicalAsset;
  url: string;
}

const assetTypeLabel: Record<string, string> = {
  PHOTO: 'Photo',
  RADIOGRAPH: 'Radiographie',
  DOCUMENT: 'Document',
};

const timepointOrder = (value: string) => {
  const match = /^T(\d+)$/.exec(value);
  return match ? Number(match[1]) : Number.MAX_SAFE_INTEGER;
};

const formatDate = (value?: string | null) => {
  if (!value) return 'Date inconnue';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Date inconnue';
  return date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' });
};

const AuthenticatedThumbnail = ({ patientId, assetId }: { patientId: number; assetId?: number | null }) => {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    let disposed = false;
    let objectUrl: string | null = null;

    if (!assetId) {
      setUrl(null);
      return () => undefined;
    }

    api.get(`/patients/${patientId}/assets/${assetId}/content`, { responseType: 'blob' })
      .then((response) => {
        if (disposed) return;
        objectUrl = URL.createObjectURL(response.data);
        setUrl(objectUrl);
      })
      .catch(() => {
        if (!disposed) setUrl(null);
      });

    return () => {
      disposed = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [assetId, patientId]);

  if (!url) {
    return (
      <div className="absolute inset-0 flex items-center justify-center bg-slate-50 text-slate-300">
        <Images size={38} strokeWidth={1.6} />
      </div>
    );
  }

  return <img src={url} alt="Aperçu clinique" className="absolute inset-0 h-full w-full object-cover" />;
};

export const PatientMediaTimeline = ({ patientId }: PatientMediaTimelineProps) => {
  const [items, setItems] = useState<ClinicalAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [assetType, setAssetType] = useState<'PHOTO' | 'RADIOGRAPH' | 'DOCUMENT'>('PHOTO');
  const [timepoint, setTimepoint] = useState('T0');
  const [viewer, setViewer] = useState<ViewerState | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadAssets = useCallback(async () => {
    try {
      setLoadError(false);
      const response = await api.get(`/patients/${patientId}/assets`);
      setItems(Array.isArray(response.data?.items) ? response.data.items : []);
    } catch {
      setLoadError(true);
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    setLoading(true);
    void loadAssets();
  }, [loadAssets]);

  useEffect(() => () => {
    if (viewer?.url) URL.revokeObjectURL(viewer.url);
  }, [viewer?.url]);

  const grouped = useMemo(() => {
    const groups = new Map<string, ClinicalAsset[]>();
    for (const item of items) {
      const key = item.timepoint || 'Sans repère';
      const bucket = groups.get(key) || [];
      bucket.push(item);
      groups.set(key, bucket);
    }
    return Array.from(groups.entries()).sort(([left], [right]) => {
      const delta = timepointOrder(left) - timepointOrder(right);
      if (delta !== 0) return delta;
      return left.localeCompare(right, 'fr');
    });
  }, [items]);

  const openAsset = async (asset: ClinicalAsset) => {
    try {
      const response = await api.get(`/patients/${patientId}/assets/${asset.id}/content`, { responseType: 'blob' });
      const url = URL.createObjectURL(response.data);
      setViewer((current) => {
        if (current?.url) URL.revokeObjectURL(current.url);
        return { asset, url };
      });
    } catch {
      toast.error("Impossible d'ouvrir ce média clinique");
    }
  };

  const closeViewer = () => {
    setViewer((current) => {
      if (current?.url) URL.revokeObjectURL(current.url);
      return null;
    });
  };

  const handleFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;

    const expectedDocument = file.type === 'application/pdf';
    if (expectedDocument && assetType !== 'DOCUMENT') {
      toast.error('Un PDF doit être importé comme Document');
      return;
    }
    if (!expectedDocument && assetType === 'DOCUMENT') {
      toast.error('Le type Document attend un PDF');
      return;
    }

    const data = new FormData();
    data.append('file', file);
    data.append('asset_type', assetType);
    data.append('source_kind', 'UPLOAD');
    if (timepoint) data.append('timepoint', timepoint);

    try {
      setUploading(true);
      await api.post(`/patients/${patientId}/assets/import`, data);
      toast.success('Média clinique importé');
      await loadAssets();
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      toast.error(typeof detail === 'string' ? detail : "Échec de l'import du média");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div data-testid="patient-media-timeline" className="min-w-0 space-y-5 p-1 sm:p-2">
      <div className="flex flex-col gap-4 rounded-[1.75rem] border border-border-main bg-card-bg p-4 sm:p-5 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0">
          <div className="mb-1 flex items-center gap-2 text-primary">
            <Images size={20} />
            <h2 className="text-lg font-black tracking-tight text-main sm:text-xl">Médiathèque clinique</h2>
          </div>
          <p className="max-w-2xl text-sm font-medium text-text-muted">
            Suivi longitudinal T0, T1, T2… des photos, radiographies et documents cliniques.
          </p>
        </div>

        <div className="grid w-full gap-2 sm:grid-cols-[1fr_1fr_auto] lg:w-auto" aria-label="Import média clinique">
          <select
            aria-label="Type de média"
            value={assetType}
            onChange={(event) => setAssetType(event.target.value as 'PHOTO' | 'RADIOGRAPH' | 'DOCUMENT')}
            className="h-10 rounded-xl border border-border-main bg-card-bg px-3 text-xs font-black uppercase tracking-wide text-main outline-none focus:border-primary"
          >
            <option value="PHOTO">Photo</option>
            <option value="RADIOGRAPH">Radiographie</option>
            <option value="DOCUMENT">Document PDF</option>
          </select>
          <select
            aria-label="Repère temporel"
            value={timepoint}
            onChange={(event) => setTimepoint(event.target.value)}
            className="h-10 rounded-xl border border-border-main bg-card-bg px-3 text-xs font-black uppercase tracking-wide text-main outline-none focus:border-primary"
          >
            <option value="">Sans repère</option>
            <option value="T0">T0</option>
            <option value="T1">T1</option>
            <option value="T2">T2</option>
          </select>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-primary px-4 text-xs font-black uppercase tracking-widest text-white shadow-sm transition-all hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {uploading ? <Loader2 size={15} className="animate-spin" /> : <Upload size={15} />}
            Importer
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp,application/pdf"
            className="hidden"
            onChange={handleFile}
          />
        </div>
      </div>

      {loading && (
        <div className="flex min-h-[320px] items-center justify-center text-text-muted">
          <Loader2 size={28} className="animate-spin" />
        </div>
      )}

      {!loading && loadError && (
        <div className="flex min-h-[320px] flex-col items-center justify-center gap-4 rounded-[1.75rem] border border-border-main bg-card-bg p-8 text-center">
          <RefreshCcw size={30} className="text-text-muted" />
          <div>
            <h3 className="font-black text-main">Médiathèque indisponible</h3>
            <p className="mt-1 text-sm text-text-muted">La liste des médias n’a pas pu être chargée.</p>
          </div>
          <button type="button" onClick={() => void loadAssets()} className="rounded-xl border border-border-main px-4 py-2 text-xs font-black uppercase tracking-widest text-primary">Réessayer</button>
        </div>
      )}

      {!loading && !loadError && items.length === 0 && (
        <div className="flex min-h-[320px] flex-col items-center justify-center rounded-[1.75rem] border border-dashed border-border-main bg-card-bg/60 p-8 text-center">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/5 text-primary"><Images size={30} /></div>
          <h3 className="text-lg font-black text-main">Aucun média longitudinal</h3>
          <p className="mt-2 max-w-md text-sm text-text-muted">Importez un premier média et associez-lui un repère T0, T1 ou T2 pour démarrer le suivi.</p>
        </div>
      )}

      {!loading && !loadError && grouped.map(([label, assets]) => (
        <section key={label} aria-label={`Temps ${label}`} className="space-y-3">
          <div className="flex items-center gap-3 px-1">
            <span className="inline-flex h-9 min-w-9 items-center justify-center rounded-xl bg-primary px-3 text-xs font-black tracking-wider text-white">{label}</span>
            <div className="h-px flex-1 bg-border-main" />
            <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">{assets.length} média{assets.length > 1 ? 's' : ''}</span>
          </div>

          <div className="grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
            {assets.map((asset) => (
              <article key={asset.id} className="min-w-0 overflow-hidden rounded-2xl border border-border-main bg-card-bg shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-elite">
                <button type="button" onClick={() => void openAsset(asset)} className="block w-full text-left" aria-label={`Ouvrir ${assetTypeLabel[asset.asset_type] || 'média'} ${asset.timepoint || ''}`.trim()}>
                  <div className="relative aspect-[16/10] overflow-hidden bg-slate-50">
                    {asset.thumbnail_asset_id ? (
                      <AuthenticatedThumbnail patientId={patientId} assetId={asset.thumbnail_asset_id} />
                    ) : (
                      <div className="absolute inset-0 flex items-center justify-center text-slate-300">
                        {asset.asset_type === 'DOCUMENT' ? <FileText size={40} /> : <ImageIcon size={40} />}
                      </div>
                    )}
                    <span className="absolute left-3 top-3 rounded-lg bg-white/95 px-2 py-1 text-[10px] font-black uppercase tracking-wider text-primary shadow-sm">{asset.timepoint || 'Sans repère'}</span>
                  </div>
                  <div className="space-y-2 p-4">
                    <div className="flex items-center justify-between gap-2">
                      <span className="truncate text-sm font-black text-main">{assetTypeLabel[asset.asset_type] || asset.asset_type}</span>
                      <Eye size={16} className="shrink-0 text-text-muted" />
                    </div>
                    <div className="flex items-center justify-between gap-2 text-[11px] font-bold text-text-muted">
                      <span>{formatDate(asset.captured_at || asset.created_at)}</span>
                      <span>{asset.mime_type === 'application/pdf' ? 'PDF' : 'Image'}</span>
                    </div>
                  </div>
                </button>
              </article>
            ))}
          </div>
        </section>
      ))}

      {viewer && (
        <div className="fixed inset-0 z-[700] flex items-center justify-center bg-slate-950/75 p-3 backdrop-blur-sm sm:p-6" role="dialog" aria-modal="true" aria-label="Visionneuse média clinique">
          <div className="flex h-[92vh] w-full max-w-6xl flex-col overflow-hidden rounded-[1.75rem] bg-white shadow-2xl">
            <div className="flex items-center justify-between gap-3 border-b border-slate-200 px-4 py-3 sm:px-5">
              <div className="min-w-0">
                <p className="text-xs font-black uppercase tracking-widest text-primary">{viewer.asset.timepoint || 'Sans repère'}</p>
                <h3 className="truncate text-base font-black text-slate-900">{assetTypeLabel[viewer.asset.asset_type] || viewer.asset.asset_type}</h3>
              </div>
              <button type="button" onClick={closeViewer} className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50" aria-label="Fermer la visionneuse"><X size={20} /></button>
            </div>
            <div className="min-h-0 flex-1 bg-slate-100 p-2 sm:p-4">
              {viewer.asset.mime_type === 'application/pdf' ? (
                <iframe src={viewer.url} title="Document clinique" className="h-full w-full rounded-xl bg-white" />
              ) : (
                <div className="flex h-full w-full items-center justify-center overflow-auto rounded-xl bg-slate-950">
                  <img src={viewer.url} alt="Média clinique" className="max-h-full max-w-full object-contain" />
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
