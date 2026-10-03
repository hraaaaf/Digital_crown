import React, { ChangeEvent, useEffect, useMemo, useRef, useState } from 'react';
import { Camera, Check, Cuboid, Loader2, Upload } from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '../../../services/api';

export const ORTHO_PHOTO_SLOTS = [
  ['EXTRA_FRONTAL_REPOSE', 'Face — repos', 'extraoral'],
  ['EXTRA_PROFILE', 'Profil', 'extraoral'],
  ['EXTRA_SMILE', 'Sourire', 'extraoral'],
  ['INTRA_FRONTAL', 'Intra — frontal', 'intraoral'],
  ['INTRA_RIGHT', 'Intra — droit', 'intraoral'],
  ['INTRA_LEFT', 'Intra — gauche', 'intraoral'],
  ['INTRA_OCCLUSAL_MAXILLARY', 'Occlusal maxillaire', 'intraoral'],
  ['INTRA_OCCLUSAL_MANDIBULAR', 'Occlusal mandibulaire', 'intraoral'],
] as const;

const TIMEPOINTS = ['T0', 'T1', 'T2', 'T3', 'OTHER'] as const;

type Asset = { asset_id: number; mime_type?: string | null; captured_at?: string | null };
type PhotoSlot = { slot_id: string; state: 'EMPTY' | 'FILLED'; asset: Asset | null };
type ModelHook = { hook_id: string; accepted_formats: string[]; state: string; measurement_authority: string };
type OrthoMediaRecord = {
  schema_version: 'ORTHO_MEDIA_RECORD_V1';
  patient_id: number;
  timepoint: string;
  photo_slots: PhotoSlot[];
  photo_complete: boolean;
  model_hooks: ModelHook[];
};

const nowLocalInput = () => {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 16);
};

const AssetPreview: React.FC<{ patientId: number; asset: Asset | null }> = ({ patientId, asset }) => {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    let revoked = false;
    let objectUrl: string | null = null;
    setUrl(null);
    if (!asset) return;
    void api.get(`/patients/${patientId}/assets/${asset.asset_id}/content`, { responseType: 'blob' })
      .then(({ data }) => {
        if (revoked) return;
        objectUrl = URL.createObjectURL(data as Blob);
        setUrl(objectUrl);
      })
      .catch(() => setUrl(null));
    return () => {
      revoked = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [asset?.asset_id, patientId]);
  if (!url) return <Camera size={24} className="opacity-35" aria-hidden="true" />;
  return <img src={url} alt="Vue orthodontique" className="h-full w-full object-cover" />;
};

export const OrthoMediaRecordPanel: React.FC<{ patientId: number; P: any }> = ({ patientId, P }) => {
  const [timepoint, setTimepoint] = useState<(typeof TIMEPOINTS)[number]>('T0');
  const [acquiredAt, setAcquiredAt] = useState(nowLocalInput);
  const [record, setRecord] = useState<OrthoMediaRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploadingSlot, setUploadingSlot] = useState<string | null>(null);
  const requestSequence = useRef(0);

  const load = async () => {
    const sequence = ++requestSequence.current;
    setLoading(true);
    try {
      const { data } = await api.get(`/patients/${patientId}/ortho-media-record`, { params: { timepoint } });
      if (sequence !== requestSequence.current) return;
      const next = data as OrthoMediaRecord;
      if (next.patient_id !== patientId || next.timepoint !== timepoint || next.schema_version !== 'ORTHO_MEDIA_RECORD_V1') {
        throw new Error('Orthodontic media record identity mismatch');
      }
      setRecord(next);
    } catch {
      if (sequence !== requestSequence.current) return;
      setRecord(null);
      toast.error('Dossier m?dia orthodontique indisponible');
    } finally {
      if (sequence === requestSequence.current) setLoading(false);
    }
  };

  useEffect(() => {
    void load();
    return () => { requestSequence.current += 1; };
  }, [patientId, timepoint]);

  const bySlot = useMemo(() => new Map((record?.photo_slots ?? []).map(item => [item.slot_id, item])), [record]);

  const upload = async (slotId: string, event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      toast.error('Format photo attendu : JPEG, PNG ou WebP');
      return;
    }
    const acquisitionDate = new Date(acquiredAt);
    if (!acquiredAt || Number.isNaN(acquisitionDate.getTime())) {
      toast.error('Date de prise de vue requise');
      return;
    }
    const body = new FormData();
    body.append('file', file);
    body.append('timepoint', timepoint);
    body.append('acquired_at', acquisitionDate.toISOString());
    try {
      setUploadingSlot(slotId);
      await api.post(`/patients/${patientId}/ortho-media-record/photos/${slotId}`, body);
      toast.success('Vue orthodontique enregistrée');
      await load();
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      toast.error(typeof detail === 'string' ? detail : "Échec de l'import orthodontique");
    } finally {
      setUploadingSlot(null);
    }
  };

  const renderGroup = (kind: 'extraoral' | 'intraoral', title: string) => {
    const groupSlots = ORTHO_PHOTO_SLOTS.filter(([, , group]) => group === kind);
    const groupFilled = groupSlots.filter(([slotId]) => bySlot.get(slotId)?.state === 'FILLED').length;
    return (
    <section>
      <div className="mb-2 flex items-center justify-between">
        <h4 className="text-[11px] font-black uppercase tracking-[0.14em]" style={{ color: P.textMuted }}>{title}</h4>
        <span className="text-[10px] font-bold" style={{ color: P.textDim }}>{groupFilled}/{groupSlots.length}</span>
      </div>
      <div className={kind === 'extraoral' ? 'grid gap-3 sm:grid-cols-3' : 'grid gap-3 sm:grid-cols-2 xl:grid-cols-5'}>
        {groupSlots.map(([slotId, label]) => {
          const slot = bySlot.get(slotId);
          const filled = slot?.state === 'FILLED' && slot.asset;
          return (
            <label key={slotId} data-ortho-photo-slot={slotId} className="group relative min-h-[138px] cursor-pointer overflow-hidden rounded-2xl border transition hover:-translate-y-0.5" style={{ borderColor: filled ? P.accentSuccess : P.border, background: P.bgCard }}>
              <input type="file" accept="image/jpeg,image/png,image/webp" className="sr-only" onChange={(event) => void upload(slotId, event)} />
              <div className="absolute inset-0 flex items-center justify-center" style={{ color: P.textMuted }}>
                {uploadingSlot === slotId ? <Loader2 size={22} className="animate-spin" /> : <AssetPreview patientId={patientId} asset={slot?.asset ?? null} />}
              </div>
              <div className="absolute inset-x-0 bottom-0 flex items-center justify-between gap-2 bg-black/55 px-3 py-2 text-white backdrop-blur-sm">
                <span className="truncate text-[10px] font-black">{label}</span>
                {filled ? <Check size={14} /> : <Upload size={13} />}
              </div>
            </label>
          );
        })}
      </div>
    </section>
    );
  };

  const filledCount = record?.photo_slots.filter(slot => slot.state === 'FILLED').length ?? 0;

  return (
    <div data-testid="ortho-media-record" className="mb-6 rounded-3xl border p-4 sm:p-5" style={{ borderColor: P.border, background: P.bgPanel }}>
      <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Camera size={18} style={{ color: P.accent }} />
            <h3 className="text-sm font-black" style={{ color: P.text }}>Dossier photographique orthodontique</h3>
          </div>
          <p className="mt-1 text-[11px]" style={{ color: P.textMuted }}>8 vues standardisées · dossier Patient local · {filledCount}/8 renseignées</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <label className="text-[10px] font-bold" style={{ color: P.textMuted }}>
            Temps
            <select aria-label="Temps orthodontique" value={timepoint} onChange={e => setTimepoint(e.target.value as any)} className="ml-2 rounded-xl border px-3 py-2" style={{ borderColor: P.border, background: P.bgInput, color: P.text }}>
              {TIMEPOINTS.map(tp => <option key={tp} value={tp}>{tp}</option>)}
            </select>
          </label>
          <label className="text-[10px] font-bold" style={{ color: P.textMuted }}>
            Prise de vue
            <input aria-label="Date de prise de vue" type="datetime-local" value={acquiredAt} onChange={e => setAcquiredAt(e.target.value)} className="ml-2 rounded-xl border px-3 py-2" style={{ borderColor: P.border, background: P.bgInput, color: P.text }} />
          </label>
        </div>
      </div>
      {loading ? <div className="flex min-h-32 items-center justify-center"><Loader2 className="animate-spin" style={{ color: P.accent }} /></div> : (
        <div className="space-y-5">
          {renderGroup('extraoral', 'Extra-orales · 3 vues')}
          {renderGroup('intraoral', 'Intra-orales · 5 vues')}
          <section>
            <h4 className="mb-2 text-[11px] font-black uppercase tracking-[0.14em]" style={{ color: P.textMuted }}>Modèles numériques</h4>
            <div className="grid gap-3 sm:grid-cols-3">
              {(record?.model_hooks ?? []).map(hook => (
                <div key={hook.hook_id} data-ortho-model-hook={hook.hook_id} className="rounded-2xl border border-dashed p-4" style={{ borderColor: P.border, background: P.bgCard }}>
                  <div className="flex items-center gap-2"><Cuboid size={16} style={{ color: P.textDim }} /><span className="text-[11px] font-black" style={{ color: P.text }}>{hook.hook_id.replaceAll('_', ' ')}</span></div>
                  <p className="mt-2 text-[10px] leading-relaxed" style={{ color: P.textMuted }}>{hook.accepted_formats.join(' / ')} · connecteur réservé</p>
                  <p className="mt-1 text-[9px] font-bold" style={{ color: P.textDim }}>Import désactivé jusqu'au validateur 3D.</p>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}
    </div>
  );
};
