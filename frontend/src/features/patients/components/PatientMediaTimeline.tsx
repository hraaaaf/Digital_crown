import { useCallback, useEffect, useMemo, useRef, useState, type ChangeEvent } from 'react';
import { Eye, FileText, Image as ImageIcon, Images, Loader2, Maximize2, RefreshCcw, Upload, X } from 'lucide-react';
import toast from 'react-hot-toast';

import { api } from '../../../services/api';
import { cn } from '../../../utils/cn';

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
        <Images size={30} strokeWidth={1.6} />
      </div>
    );
  }

  return <img src={url} alt="Aperçu clinique" className="absolute inset-0 h-full w-full object-cover" />;
};

const AuthenticatedAssetPreview = ({ patientId, asset }: { patientId: number; asset: ClinicalAsset | null }) => {
  const [url, setUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let disposed = false;
    let objectUrl: string | null = null;

    setUrl(null);
    if (!asset) return () => undefined;

    setLoading(true);
    api.get(`/patients/${patientId}/assets/${asset.id}/content`, { responseType: 'blob' })
      .then((response) => {
        if (disposed) return;
        objectUrl = URL.createObjectURL(response.data);
        setUrl(objectUrl);
      })
      .catch(() => {
        if (!disposed) setUrl(null);
      })
      .finally(() => {
        if (!disposed) setLoading(false);
      });

    return () => {
      disposed = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [asset, patientId]);

  if (!asset) {
    return (
      <div className="flex min-h-[220px] items-center justify-center bg-slate-950 text-slate-500 sm:min-h-[280px] md:min-h-[390px] lg:min-h-[470px]">
        <Images size={44} strokeWidth={1.4} />
      </div>
    );
  }

  if (loading || !url) {
    return (
      <div className="flex min-h-[220px] items-center justify-center bg-slate-950 text-slate-300 sm:min-h-[280px] md:min-h-[390px] lg:min-h-[470px]">
        <Loader2 size={26} className="animate-spin" />
      </div>
    );
  }

  if (asset.mime_type === 'application/pdf') {
    return <iframe src={url} title="Aperçu document clinique" className="min-h-[260px] w-full bg-white sm:min-h-[320px] md:min-h-[390px] lg:min-h-[470px]" />;
  }

  return (
    <div className="flex min-h-[220px] items-center justify-center overflow-hidden bg-slate-950 sm:min-h-[280px] md:min-h-[390px] lg:min-h-[470px]">
      <img src={url} alt="Média clinique sélectionné" className="max-h-[470px] max-w-full object-contain" />
    </div>
  );
};

export const PatientMediaTimeline = ({ patientId }: PatientMediaTimelineProps) => {
  const [items, setItems] = useState<ClinicalAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [assetType, setAssetType] = useState<'PHOTO' | 'RADIOGRAPH' | 'DOCUMENT'>('PHOTO');
  const [timepoint, setTimepoint] = useState('T0');
  const [viewer, setViewer] = useState<ViewerState | null>(null);
  const [selectedAssetId, setSelectedAssetId] = useState<number | null>(null);
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

  useEffect(() => {
    setSelectedAssetId((current) => {
      if (items.length === 0) return null;
      if (current && items.some((item) => item.id === current)) return current;
      return items[0].id;
    });
  }, [items]);

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

  const selectedAsset = useMemo(
    () => items.find((item) => item.id === selectedAssetId) || items[0] || null,
    [items, selectedAssetId],
  );

  const openAsset = async (asset: ClinicalAsset) => {
    setSelectedAssetId(asset.id);
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
    <div data-testid="patient-media-timeline" className="min-w-0 space-y-2.5 sm:space-y-3">
      <div className="rounded-[1.25rem] border border-border-main bg-card-bg px-2.5 py-2.5 sm:px-3 sm:py-3 lg:px-4">
        <div className="flex flex-col gap-2.5 lg:flex-row lg:items-center lg:justify-between">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-primary">
              <Images size={18} />
              <h2 className="text-base font-black tracking-tight text-main sm:text-lg lg:text-xl">Médiathèque clinique</h2>
            </div>
            <p className="mt-0.5 text-[11px] font-medium leading-snug text-text-muted sm:text-xs lg:text-sm">
              Suivi longitudinal T0, T1, T2… des médias cliniques.
            </p>
            {grouped.length > 0 && (
              <div className="mt-1.5 flex max-w-full gap-1.5 overflow-x-auto pb-0.5 scrollbar-none" aria-label="Repères longitudinaux">
                {grouped.map(([label, assets]) => (
                  <span key={label} className="inline-flex shrink-0 items-center gap-1 rounded-full border border-primary/10 bg-primary/5 px-2 py-0.5 text-[9px] font-black uppercase tracking-wide text-primary sm:py-1 sm:text-[10px]">
                    {label} <span className="text-text-muted">{assets.length}</span>
                  </span>
                ))}
              </div>
            )}
          </div>

          <div className="grid w-full grid-cols-2 gap-1.5 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] sm:gap-2 lg:w-auto" aria-label="Import média clinique">
            <select
              aria-label="Type de média"
              value={assetType}
              onChange={(event) => setAssetType(event.target.value as 'PHOTO' | 'RADIOGRAPH' | 'DOCUMENT')}
              className="h-8 min-w-0 rounded-lg border border-border-main bg-card-bg px-2.5 text-[10px] font-black uppercase tracking-wide text-main outline-none focus:border-primary sm:h-9 sm:rounded-xl sm:px-3 sm:text-[11px]"
            >
              <option value="PHOTO">Photo</option>
              <option value="RADIOGRAPH">Radiographie</option>
              <option value="DOCUMENT">Document PDF</option>
            </select>
            <select
              aria-label="Repère temporel"
              value={timepoint}
              onChange={(event) => setTimepoint(event.target.value)}
              className="h-8 min-w-0 rounded-lg border border-border-main bg-card-bg px-2.5 text-[10px] font-black uppercase tracking-wide text-main outline-none focus:border-primary sm:h-9 sm:rounded-xl sm:px-3 sm:text-[11px]"
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
              className="col-span-2 inline-flex h-8 items-center justify-center gap-1.5 rounded-lg bg-primary px-3 text-[10px] font-black uppercase tracking-wider text-white shadow-sm transition-all hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-50 sm:col-span-1 sm:h-9 sm:rounded-xl sm:px-4 sm:text-[11px] sm:tracking-widest"
            >
              {uploading ? <Loader2 size={13} className="animate-spin" /> : <Upload size={13} />}
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
      </div>

      {loading && (
        <div className="flex min-h-[220px] items-center justify-center text-text-muted sm:min-h-[280px]">
          <Loader2 size={28} className="animate-spin" />
        </div>
      )}

      {!loading && loadError && (
        <div className="flex min-h-[220px] flex-col items-center justify-center gap-4 rounded-[1.25rem] border border-border-main bg-card-bg p-6 text-center sm:min-h-[280px] sm:p-8">
          <RefreshCcw size={30} className="text-text-muted" />
          <div>
            <h3 className="font-black text-main">Médiathèque indisponible</h3>
            <p className="mt-1 text-sm text-text-muted">La liste des médias n’a pas pu être chargée.</p>
          </div>
          <button type="button" onClick={() => void loadAssets()} className="rounded-xl border border-border-main px-4 py-2 text-xs font-black uppercase tracking-widest text-primary">Réessayer</button>
        </div>
      )}

      {!loading && !loadError && items.length === 0 && (
        <div className="flex min-h-[220px] flex-col items-center justify-center rounded-[1.25rem] border border-dashed border-border-main bg-card-bg/60 p-6 text-center sm:min-h-[280px] sm:p-8">
          <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/5 text-primary sm:mb-4 sm:h-16 sm:w-16"><Images size={28} /></div>
          <h3 className="text-base font-black text-main sm:text-lg">Aucun média longitudinal</h3>
          <p className="mt-1.5 max-w-md text-xs text-text-muted sm:mt-2 sm:text-sm">Importez un premier média et associez-lui un repère T0, T1 ou T2 pour démarrer le suivi.</p>
        </div>
      )}

      {!loading && !loadError && items.length > 0 && (
        <div className="grid min-w-0 gap-2.5 md:grid-cols-[minmax(190px,0.31fr)_minmax(0,1fr)] lg:grid-cols-[minmax(250px,0.34fr)_minmax(0,1fr)] lg:gap-3">
          <div data-testid="media-asset-rail" className="order-2 min-w-0 space-y-2.5 md:order-1 md:max-h-[460px] md:overflow-y-auto md:pr-1 lg:max-h-[545px] lg:space-y-3">
            {grouped.map(([label, assets]) => (
              <section key={label} aria-label={`Temps ${label}`} className="space-y-1.5 sm:space-y-2">
                <div className="flex items-center gap-2 px-0.5">
                  <span className="inline-flex h-6 min-w-6 items-center justify-center rounded-lg bg-primary px-2 text-[9px] font-black tracking-wider text-white sm:h-7 sm:min-w-7 sm:text-[10px]">{label}</span>
                  <div className="h-px flex-1 bg-border-main" />
                  <span className="text-[9px] font-black uppercase tracking-widest text-text-muted">{assets.length}</span>
                </div>

                <div className="space-y-1.5 sm:space-y-2">
                  {assets.map((asset) => {
                    const selected = selectedAsset?.id === asset.id;
                    return (
                      <article key={asset.id} className={cn('min-w-0 overflow-hidden rounded-xl border bg-card-bg transition-all', selected ? 'border-primary/40 shadow-sm ring-2 ring-primary/5' : 'border-border-main hover:border-primary/20')}>
                        <button
                          type="button"
                          onClick={() => void openAsset(asset)}
                          className="flex w-full min-w-0 items-center gap-2 p-1.5 text-left sm:gap-3 sm:p-2"
                          aria-label={`Ouvrir ${assetTypeLabel[asset.asset_type] || 'média'} ${asset.timepoint || ''}`.trim()}
                        >
                          <div className="relative h-14 w-20 shrink-0 overflow-hidden rounded-lg bg-slate-50 sm:h-16 sm:w-24 md:h-14 md:w-20 lg:h-16 lg:w-24">
                            {asset.thumbnail_asset_id ? (
                              <AuthenticatedThumbnail patientId={patientId} assetId={asset.thumbnail_asset_id} />
                            ) : (
                              <div className="absolute inset-0 flex items-center justify-center text-slate-300">
                                {asset.asset_type === 'DOCUMENT' ? <FileText size={26} /> : <ImageIcon size={26} />}
                              </div>
                            )}
                          </div>
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center justify-between gap-2">
                              <span className="truncate text-[11px] font-black text-main sm:text-xs">{assetTypeLabel[asset.asset_type] || asset.asset_type}</span>
                              <Eye size={13} className="shrink-0 text-text-muted" />
                            </div>
                            <p className="mt-0.5 truncate text-[9px] font-bold text-text-muted sm:mt-1 sm:text-[10px]">{formatDate(asset.captured_at || asset.created_at)}</p>
                            <p className="mt-0.5 text-[8px] font-black uppercase tracking-wider text-primary sm:mt-1 sm:text-[9px]">{asset.mime_type === 'application/pdf' ? 'PDF' : 'Image'} · {asset.timepoint || 'Sans repère'}</p>
                          </div>
                        </button>
                      </article>
                    );
                  })}
                </div>
              </section>
            ))}
          </div>

          <section data-testid="media-inline-viewer" aria-label="Aperçu média clinique" className="order-1 min-w-0 overflow-hidden rounded-[1.25rem] border border-border-main bg-card-bg shadow-sm md:order-2 sm:rounded-[1.5rem]">
            <div className="flex min-h-[44px] items-center justify-between gap-2 border-b border-border-main px-2.5 py-2 sm:min-h-[48px] sm:px-3 md:px-4">
              <div className="min-w-0">
                <p className="text-[8px] font-black uppercase tracking-[0.16em] text-primary sm:text-[9px]">{selectedAsset?.timepoint || 'Sans repère'}</p>
                <div className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-0.5">
                  <h3 className="truncate text-xs font-black text-main sm:text-sm">{selectedAsset ? (assetTypeLabel[selectedAsset.asset_type] || selectedAsset.asset_type) : 'Aucun média'}</h3>
                  {selectedAsset && <span className="text-[9px] font-bold text-text-muted sm:text-[10px]">{formatDate(selectedAsset.captured_at || selectedAsset.created_at)}</span>}
                </div>
              </div>
              {selectedAsset && (
                <button
                  type="button"
                  onClick={() => void openAsset(selectedAsset)}
                  className="inline-flex h-8 shrink-0 items-center justify-center gap-1.5 rounded-lg border border-border-main bg-card-bg px-2 text-[9px] font-black uppercase tracking-wider text-primary transition hover:bg-primary/5 sm:h-9 sm:rounded-xl sm:px-3 sm:text-[10px] sm:tracking-widest"
                  aria-label="Ouvrir le média sélectionné en plein écran"
                >
                  <Maximize2 size={13} /> <span className="hidden sm:inline">Plein écran</span>
                </button>
              )}
            </div>
            <AuthenticatedAssetPreview patientId={patientId} asset={selectedAsset} />
          </section>
        </div>
      )}

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