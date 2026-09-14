import { useCallback, useEffect, useMemo, useRef, useState, type ChangeEvent } from 'react';
import { Check, Eye, FileText, Image as ImageIcon, Images, Loader2, Maximize2, RefreshCcw, Search, Upload, X } from 'lucide-react';
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
    return <div className="absolute inset-0 flex items-center justify-center bg-slate-50 text-slate-300"><Images size={30} strokeWidth={1.6} /></div>;
  }
  return <img src={url} alt="Aperçu clinique" className="absolute inset-0 h-full w-full object-cover" />;
};

const AuthenticatedAssetPreview = ({ patientId, asset, compact = false }: { patientId: number; asset: ClinicalAsset | null; compact?: boolean }) => {
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

  const minHeight = compact ? 'min-h-[220px] sm:min-h-[280px] lg:min-h-[360px]' : 'min-h-[220px] sm:min-h-[280px] md:min-h-[390px] lg:min-h-[470px]';

  if (!asset) return <div className={cn('flex items-center justify-center bg-slate-950 text-slate-500', minHeight)}><Images size={44} strokeWidth={1.4} /></div>;
  if (loading || !url) return <div className={cn('flex items-center justify-center bg-slate-950 text-slate-300', minHeight)}><Loader2 size={26} className="animate-spin" /></div>;
  if (asset.mime_type === 'application/pdf') return <iframe src={url} title="Aperçu document clinique" className={cn('w-full bg-white', minHeight)} />;

  return <div className={cn('flex items-center justify-center overflow-hidden bg-slate-950', minHeight)}><img src={url} alt="Média clinique sélectionné" className="max-h-[470px] max-w-full object-contain" /></div>;
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
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [timepointFilter, setTimepointFilter] = useState('ALL');
  const [compareIds, setCompareIds] = useState<number[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const workspaceRef = useRef<HTMLDivElement>(null);
  const workspaceTopBeforeCompareRef = useRef<number | null>(null);

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
    setCompareIds((current) => current.filter((id) => items.some((item) => item.id === id)).slice(0, 2));
  }, [items]);

  const availableTimepoints = useMemo(() => Array.from(new Set(items.map((item) => item.timepoint || 'Sans repère'))).sort((a, b) => timepointOrder(a) - timepointOrder(b)), [items]);

  const filteredItems = useMemo(() => {
    const query = searchTerm.trim().toLocaleLowerCase('fr');
    return items.filter((item) => {
      if (typeFilter !== 'ALL' && item.asset_type !== typeFilter) return false;
      const itemTimepoint = item.timepoint || 'Sans repère';
      if (timepointFilter !== 'ALL' && itemTimepoint !== timepointFilter) return false;
      if (!query) return true;
      const haystack = [assetTypeLabel[item.asset_type] || item.asset_type, item.asset_type, item.source_kind, itemTimepoint, formatDate(item.captured_at || item.created_at)].join(' ').toLocaleLowerCase('fr');
      return haystack.includes(query);
    });
  }, [items, searchTerm, timepointFilter, typeFilter]);

  const grouped = useMemo(() => {
    const groups = new Map<string, ClinicalAsset[]>();
    for (const item of filteredItems) {
      const key = item.timepoint || 'Sans repère';
      const bucket = groups.get(key) || [];
      bucket.push(item);
      groups.set(key, bucket);
    }
    return Array.from(groups.entries()).sort(([left], [right]) => {
      const delta = timepointOrder(left) - timepointOrder(right);
      return delta !== 0 ? delta : left.localeCompare(right, 'fr');
    });
  }, [filteredItems]);

  const selectedAsset = useMemo(() => filteredItems.find((item) => item.id === selectedAssetId) || filteredItems[0] || null, [filteredItems, selectedAssetId]);
  const comparedAssets = useMemo(() => compareIds.map((id) => items.find((item) => item.id === id)).filter((item): item is ClinicalAsset => Boolean(item)), [compareIds, items]);

  useEffect(() => {
    if (comparedAssets.length !== 2) return undefined;

    const frame = window.requestAnimationFrame(() => {
      const workspace = workspaceRef.current;
      if (!workspace) return;

      const workspaceTop = workspace.getBoundingClientRect().top;
      const recordedTargetTop = workspaceTopBeforeCompareRef.current;
      workspaceTopBeforeCompareRef.current = null;
      if (recordedTargetTop == null) return;

      const stickyHeader = document.querySelector<HTMLElement>('header.sticky');
      const isMobile = window.innerWidth < 768;
      const targetTop = isMobile && stickyHeader
        ? Math.max(recordedTargetTop, stickyHeader.getBoundingClientRect().bottom + 8)
        : recordedTargetTop;
      const delta = workspaceTop - targetTop;
      if (Math.abs(delta) < 1) return;

      let scrollParent: HTMLElement | null = workspace.parentElement;
      while (scrollParent && scrollParent !== document.body) {
        const { overflowY } = window.getComputedStyle(scrollParent);
        if (/(auto|scroll|overlay)/.test(overflowY) && scrollParent.scrollHeight > scrollParent.clientHeight + 1) break;
        scrollParent = scrollParent.parentElement;
      }

      if (scrollParent && scrollParent !== document.body) {
        scrollParent.scrollBy({ top: delta, behavior: 'auto' });
      } else {
        window.scrollBy({ top: delta, behavior: 'auto' });
      }
    });

    return () => window.cancelAnimationFrame(frame);
  }, [comparedAssets.length]);

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

  const closeViewer = () => setViewer((current) => {
    if (current?.url) URL.revokeObjectURL(current.url);
    return null;
  });

  const toggleCompare = (assetId: number) => {
    setCompareIds((current) => {
      if (current.includes(assetId)) return current.filter((id) => id !== assetId);
      if (current.length === 0 && workspaceRef.current) {
        workspaceTopBeforeCompareRef.current = workspaceRef.current.getBoundingClientRect().top;
      }
      if (current.length >= 2) return [current[1], assetId];
      return [...current, assetId];
    });
  };

  const handleFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    const expectedDocument = file.type === 'application/pdf';
    if (expectedDocument && assetType !== 'DOCUMENT') return void toast.error('Un PDF doit être importé comme Document');
    if (!expectedDocument && assetType === 'DOCUMENT') return void toast.error('Le type Document attend un PDF');

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
    <div ref={workspaceRef} data-testid="patient-media-timeline" className="min-w-0 space-y-2">
      <div className="rounded-xl border border-border-main bg-card-bg px-2 py-2 sm:px-2.5 sm:py-2.5 lg:px-3">
        <div className="flex flex-col gap-2 xl:flex-row xl:items-center xl:justify-between">
          <div className="min-w-0">
            <div className="flex max-w-full flex-wrap items-center gap-x-2 gap-y-1 text-primary">
              <Images size={17} className="shrink-0" />
              <h2 className="text-base font-black tracking-tight text-main sm:text-lg">Médiathèque clinique</h2>
              {items.length > 0 && <span className="rounded-full bg-primary/5 px-2 py-0.5 text-[9px] font-black text-primary">{filteredItems.length}/{items.length}</span>}
            </div>
            <p className="mt-0.5 hidden text-[11px] font-medium leading-snug text-text-muted md:block lg:text-xs">Recherche, filtres et comparaison longitudinale T0/T1/T2.</p>
          </div>

          <div className="grid w-full gap-1.5 sm:grid-cols-2 xl:w-auto xl:min-w-[650px] xl:grid-cols-[minmax(180px,1.3fr)_minmax(120px,.8fr)_minmax(120px,.8fr)_auto]" aria-label="Recherche et filtres médias">
            <label className="relative block min-w-0">
              <Search size={14} className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-text-muted" />
              <input value={searchTerm} onChange={(event) => setSearchTerm(event.target.value)} placeholder="Rechercher média…" aria-label="Rechercher un média" className="h-8 w-full rounded-lg border border-border-main bg-card-bg pl-8 pr-2 text-[11px] font-bold text-main outline-none focus:border-primary" />
            </label>
            <select aria-label="Filtrer par type" value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)} className="h-8 min-w-0 rounded-lg border border-border-main bg-card-bg px-2 text-[10px] font-black uppercase tracking-wide text-main outline-none focus:border-primary">
              <option value="ALL">Tous types</option><option value="PHOTO">Photos</option><option value="RADIOGRAPH">Radios</option><option value="DOCUMENT">Documents</option>
            </select>
            <select aria-label="Filtrer par repère" value={timepointFilter} onChange={(event) => setTimepointFilter(event.target.value)} className="h-8 min-w-0 rounded-lg border border-border-main bg-card-bg px-2 text-[10px] font-black uppercase tracking-wide text-main outline-none focus:border-primary">
              <option value="ALL">Tous repères</option>{availableTimepoints.map((label) => <option key={label} value={label}>{label}</option>)}
            </select>
            <button type="button" onClick={() => setCompareIds([])} disabled={compareIds.length === 0} className="inline-flex h-8 items-center justify-center rounded-lg border border-border-main px-3 text-[10px] font-black uppercase tracking-wider text-primary disabled:opacity-40">Réinitialiser compare</button>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-border-main bg-card-bg px-2 py-2 sm:px-2.5">
        <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]" aria-label="Import média clinique">
          <select aria-label="Type de média" value={assetType} onChange={(event) => setAssetType(event.target.value as 'PHOTO' | 'RADIOGRAPH' | 'DOCUMENT')} className="h-8 min-w-0 rounded-lg border border-border-main bg-card-bg px-2.5 text-[10px] font-black uppercase tracking-wide text-main outline-none focus:border-primary"><option value="PHOTO">Photo</option><option value="RADIOGRAPH">Radiographie</option><option value="DOCUMENT">Document PDF</option></select>
          <select aria-label="Repère temporel" value={timepoint} onChange={(event) => setTimepoint(event.target.value)} className="h-8 min-w-0 rounded-lg border border-border-main bg-card-bg px-2.5 text-[10px] font-black uppercase tracking-wide text-main outline-none focus:border-primary"><option value="">Sans repère</option><option value="T0">T0</option><option value="T1">T1</option><option value="T2">T2</option></select>
          <button type="button" onClick={() => fileInputRef.current?.click()} disabled={uploading} className="col-span-2 inline-flex h-8 items-center justify-center gap-1.5 rounded-lg bg-primary px-3 text-[10px] font-black uppercase tracking-wider text-white shadow-sm transition-all hover:opacity-95 disabled:opacity-50 sm:col-span-1">{uploading ? <Loader2 size={13} className="animate-spin" /> : <Upload size={13} />}Importer</button>
          <input ref={fileInputRef} type="file" accept="image/jpeg,image/png,image/webp,application/pdf" className="hidden" onChange={handleFile} />
        </div>
      </div>

      {loading && <div className="flex min-h-[220px] items-center justify-center text-text-muted"><Loader2 size={28} className="animate-spin" /></div>}
      {!loading && loadError && <div className="flex min-h-[220px] flex-col items-center justify-center gap-4 rounded-[1.25rem] border border-border-main bg-card-bg p-6 text-center"><RefreshCcw size={30} className="text-text-muted" /><div><h3 className="font-black text-main">Médiathèque indisponible</h3><p className="mt-1 text-sm text-text-muted">La liste des médias n’a pas pu être chargée.</p></div><button type="button" onClick={() => void loadAssets()} className="rounded-xl border border-border-main px-4 py-2 text-xs font-black uppercase tracking-widest text-primary">Réessayer</button></div>}
      {!loading && !loadError && items.length === 0 && <div className="flex min-h-[220px] flex-col items-center justify-center rounded-[1.25rem] border border-dashed border-border-main bg-card-bg/60 p-6 text-center"><Images size={34} className="mb-3 text-primary" /><h3 className="text-base font-black text-main">Aucun média longitudinal</h3></div>}
      {!loading && !loadError && items.length > 0 && filteredItems.length === 0 && <div className="flex min-h-[160px] flex-col items-center justify-center rounded-[1.25rem] border border-dashed border-border-main bg-card-bg/60 p-6 text-center"><Search size={28} className="mb-2 text-text-muted" /><h3 className="font-black text-main">Aucun média ne correspond aux filtres</h3></div>}

      {!loading && !loadError && filteredItems.length > 0 && (
        <>
          {comparedAssets.length === 2 && (
            <section data-testid="media-compare-panel" aria-label="Comparaison de médias" className="overflow-hidden rounded-[1.25rem] border border-primary/20 bg-card-bg shadow-sm">
              <div className="flex items-center justify-between border-b border-border-main px-3 py-2.5"><div><p className="text-[9px] font-black uppercase tracking-[0.16em] text-primary">Comparaison</p><h3 className="text-sm font-black text-main">{comparedAssets[0].timepoint || 'Sans repère'} ↔ {comparedAssets[1].timepoint || 'Sans repère'}</h3></div><button type="button" onClick={() => setCompareIds([])} className="rounded-lg border border-border-main p-2 text-text-muted hover:text-main" aria-label="Fermer la comparaison"><X size={15} /></button></div>
              <div className="grid gap-px bg-border-main md:grid-cols-2">
                {comparedAssets.map((asset) => <div key={asset.id} className="min-w-0 bg-card-bg"><div className="flex items-center justify-between gap-2 px-3 py-2"><div className="min-w-0"><p className="text-[9px] font-black uppercase tracking-wider text-primary">{asset.timepoint || 'Sans repère'}</p><p className="truncate text-xs font-black text-main">{assetTypeLabel[asset.asset_type] || asset.asset_type} · {formatDate(asset.captured_at || asset.created_at)}</p></div><button type="button" onClick={() => void openAsset(asset)} className="rounded-lg border border-border-main p-2 text-primary" aria-label="Ouvrir ce média en plein écran"><Maximize2 size={14} /></button></div><AuthenticatedAssetPreview patientId={patientId} asset={asset} compact /></div>)}
              </div>
            </section>
          )}

          <div className="grid min-w-0 gap-2.5 md:grid-cols-[minmax(210px,0.32fr)_minmax(0,1fr)] lg:grid-cols-[minmax(260px,0.34fr)_minmax(0,1fr)] lg:gap-3">
            <div data-testid="media-asset-rail" className="order-2 min-w-0 space-y-2.5 md:order-1 md:max-h-[545px] md:overflow-y-auto md:pr-1">
              {grouped.map(([label, assets]) => <section key={label} aria-label={`Temps ${label}`} className="space-y-1.5"><div className="flex items-center gap-2 px-0.5"><span className="inline-flex h-6 min-w-6 items-center justify-center rounded-lg bg-primary px-2 text-[9px] font-black tracking-wider text-white">{label}</span><div className="h-px flex-1 bg-border-main" /><span className="text-[9px] font-black uppercase tracking-widest text-text-muted">{assets.length}</span></div><div className="space-y-1.5">{assets.map((asset) => {
                const selected = selectedAsset?.id === asset.id;
                const compared = compareIds.includes(asset.id);
                return <article key={asset.id} className={cn('min-w-0 overflow-hidden rounded-xl border bg-card-bg transition-all', selected ? 'border-primary/40 shadow-sm ring-2 ring-primary/5' : 'border-border-main hover:border-primary/20')}><div className="flex w-full min-w-0 items-center gap-2 p-1.5"><button type="button" onClick={() => void openAsset(asset)} className="flex min-w-0 flex-1 items-center gap-2 text-left" aria-label={`Ouvrir ${assetTypeLabel[asset.asset_type] || 'média'} ${asset.timepoint || ''}`.trim()}><div className="relative h-14 w-20 shrink-0 overflow-hidden rounded-lg bg-slate-50">{asset.thumbnail_asset_id ? <AuthenticatedThumbnail patientId={patientId} assetId={asset.thumbnail_asset_id} /> : <div className="absolute inset-0 flex items-center justify-center text-slate-300">{asset.asset_type === 'DOCUMENT' ? <FileText size={26} /> : <ImageIcon size={26} />}</div>}</div><div className="min-w-0 flex-1"><div className="flex items-center justify-between gap-2"><span className="truncate text-[11px] font-black text-main">{assetTypeLabel[asset.asset_type] || asset.asset_type}</span><Eye size={13} className="shrink-0 text-text-muted" /></div><p className="mt-0.5 truncate text-[9px] font-bold text-text-muted">{formatDate(asset.captured_at || asset.created_at)}</p><p className="mt-0.5 text-[8px] font-black uppercase tracking-wider text-primary">{asset.mime_type === 'application/pdf' ? 'PDF' : 'Image'} · {asset.timepoint || 'Sans repère'}</p></div></button><button type="button" onClick={() => toggleCompare(asset.id)} className={cn('flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border transition', compared ? 'border-primary bg-primary text-white' : 'border-border-main text-text-muted hover:border-primary/30 hover:text-primary')} aria-pressed={compared} aria-label={compared ? 'Retirer de la comparaison' : 'Ajouter à la comparaison'}>{compared ? <Check size={14} /> : <span className="text-[10px] font-black">1/2</span>}</button></div></article>;
              })}</div></section>)}
            </div>

            <section data-testid="media-inline-viewer" aria-label="Aperçu média clinique" className="order-1 min-w-0 overflow-hidden rounded-[1.25rem] border border-border-main bg-card-bg shadow-sm md:order-2">
              <div className="flex min-h-[44px] items-center justify-between gap-2 border-b border-border-main px-2.5 py-2 sm:px-3 md:px-4"><div className="min-w-0"><p className="text-[8px] font-black uppercase tracking-[0.16em] text-primary">{selectedAsset?.timepoint || 'Sans repère'}</p><div className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-0.5"><h3 className="truncate text-xs font-black text-main sm:text-sm">{selectedAsset ? (assetTypeLabel[selectedAsset.asset_type] || selectedAsset.asset_type) : 'Aucun média'}</h3>{selectedAsset && <span className="text-[9px] font-bold text-text-muted">{formatDate(selectedAsset.captured_at || selectedAsset.created_at)}</span>}</div></div>{selectedAsset && <div className="flex shrink-0 items-center gap-1.5"><button type="button" onClick={() => toggleCompare(selectedAsset.id)} className={cn('inline-flex h-8 items-center justify-center rounded-lg border px-2 text-[9px] font-black uppercase tracking-wider', compareIds.includes(selectedAsset.id) ? 'border-primary bg-primary text-white' : 'border-border-main text-primary')} aria-pressed={compareIds.includes(selectedAsset.id)}>{compareIds.includes(selectedAsset.id) ? 'Ajouté' : 'Comparer'}</button><button type="button" onClick={() => void openAsset(selectedAsset)} className="inline-flex h-8 items-center justify-center gap-1.5 rounded-lg border border-border-main bg-card-bg px-2 text-[9px] font-black uppercase tracking-wider text-primary" aria-label="Ouvrir le média sélectionné en plein écran"><Maximize2 size={13} /><span className="hidden sm:inline">Plein écran</span></button></div>}</div>
              <AuthenticatedAssetPreview patientId={patientId} asset={selectedAsset} />
            </section>
          </div>
        </>
      )}

      {viewer && <div className="fixed inset-0 z-[700] flex items-center justify-center bg-slate-950/75 p-3 backdrop-blur-sm sm:p-6" role="dialog" aria-modal="true" aria-label="Visionneuse média clinique"><div className="flex h-[92vh] w-full max-w-6xl flex-col overflow-hidden rounded-[1.75rem] bg-white shadow-2xl"><div className="flex items-center justify-between gap-3 border-b border-slate-200 px-4 py-3 sm:px-5"><div className="min-w-0"><p className="text-xs font-black uppercase tracking-widest text-primary">{viewer.asset.timepoint || 'Sans repère'}</p><h3 className="truncate text-base font-black text-slate-900">{assetTypeLabel[viewer.asset.asset_type] || viewer.asset.asset_type}</h3></div><button type="button" onClick={closeViewer} className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50" aria-label="Fermer la visionneuse"><X size={20} /></button></div><div className="min-h-0 flex-1 bg-slate-100 p-2 sm:p-4">{viewer.asset.mime_type === 'application/pdf' ? <iframe src={viewer.url} title="Document clinique" className="h-full w-full rounded-xl bg-white" /> : <div className="flex h-full w-full items-center justify-center overflow-auto rounded-xl bg-slate-950"><img src={viewer.url} alt="Média clinique" className="max-h-full max-w-full object-contain" /></div>}</div></div></div>}
    </div>
  );
};
