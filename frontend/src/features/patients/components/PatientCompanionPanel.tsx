import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Copy,
  FileText,
  Images,
  Link2,
  Link2Off,
  Loader2,
  Mail,
  QrCode,
  RefreshCcw,
  ShieldCheck,
  Smartphone,
  Unlink,
} from 'lucide-react';
import toast from 'react-hot-toast';

import { api } from '../../../services/api';
import { cn } from '../../../utils/cn';

type ResourceType = 'document' | 'media';

type Share = {
  share_id: string;
  resource_type: ResourceType;
  resource_id: number;
  created_at: string;
};

type CompanionStatus = {
  patient_id: number;
  active_accesses: Array<{
    access_id: string;
    relationship_type: string;
    created_at: string;
  }>;
  pending_invitation: null | {
    invitation_id: string;
    relationship_type: string;
    recipient_type: 'email' | 'phone';
    created_at: string;
    expires_at: string;
  };
  shares: Share[];
};

type DocumentItem = {
  id: string;
  name: string;
  type: string;
  date: string;
};

type MediaItem = {
  id: number;
  asset_type: string;
  source_kind: string;
  timepoint?: string | null;
  captured_at?: string | null;
  created_at: string;
};

type EphemeralInvitation = {
  invitationId: string;
  manualCode: string;
  qrDataUrl: string;
  expiresAt: string;
};

interface PatientCompanionPanelProps {
  patientId: number;
  patientEmail?: string;
}

const relationshipLabels: Record<string, string> = {
  SELF: 'Patient',
  PARENT: 'Parent',
  GUARDIAN: 'Tuteur',
  CAREGIVER: 'Aidant',
};

const formatDate = (value?: string | null) => {
  if (!value) return '—';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return '—';
  return parsed.toLocaleString('fr-MA', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const PatientCompanionPanel = ({ patientId, patientEmail }: PatientCompanionPanelProps) => {
  const [status, setStatus] = useState<CompanionStatus | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [media, setMedia] = useState<MediaItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [recipient, setRecipient] = useState(patientEmail || '');
  const [relationshipType, setRelationshipType] = useState('SELF');
  const [expiresInMinutes, setExpiresInMinutes] = useState(15);
  const [ephemeralInvitation, setEphemeralInvitation] = useState<EphemeralInvitation | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [statusResponse, docsResponse, mediaResponse] = await Promise.all([
        api.get(`/patient-companion/admin/patients/${patientId}/status`),
        api.get(`/patients/${patientId}/documents`),
        api.get(`/patients/${patientId}/assets`, { params: { limit: 200, offset: 0 } }),
      ]);
      setStatus(statusResponse.data);
      setDocuments(Array.isArray(docsResponse.data) ? docsResponse.data : []);
      setMedia(Array.isArray(mediaResponse.data?.items) ? mediaResponse.data.items : []);
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      toast.error(typeof detail === 'string' ? detail : 'Impossible de charger Patient Companion');
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    setRecipient(patientEmail || '');
    setEphemeralInvitation(null);
    void load();
  }, [load, patientEmail, patientId]);

  useEffect(() => {
    if (!ephemeralInvitation) return undefined;
    const expiresAt = new Date(ephemeralInvitation.expiresAt).getTime();
    const delay = Math.max(0, expiresAt - Date.now());
    const timer = window.setTimeout(() => setEphemeralInvitation(null), delay);
    return () => window.clearTimeout(timer);
  }, [ephemeralInvitation]);

  useEffect(() => () => setEphemeralInvitation(null), []);

  const shareByResource = useMemo(() => {
    const map = new Map<string, Share>();
    for (const share of status?.shares || []) {
      map.set(`${share.resource_type}:${share.resource_id}`, share);
    }
    return map;
  }, [status?.shares]);

  const canonicalDocuments = useMemo(
    () => documents.filter(document => /^\d+$/.test(document.id)),
    [documents],
  );

  const createInvitation = async () => {
    const email = recipient.trim();
    if (!email) return void toast.error("Renseignez l'e-mail vérifié du patient");
    setBusyKey('invite');
    try {
      const response = await api.post(`/patient-companion/admin/patients/${patientId}/invitation`, {
        recipient_type: 'email',
        recipient: email,
        relationship_type: relationshipType,
        expires_in_minutes: expiresInMinutes,
      });
      setEphemeralInvitation({
        invitationId: response.data.invitation_id,
        manualCode: response.data.manual_code,
        qrDataUrl: response.data.qr_data_url,
        expiresAt: response.data.expires_at,
      });
      toast.success('Invitation Companion générée');
      await load();
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      toast.error(typeof detail === 'string' ? detail : "Impossible de générer l'invitation");
    } finally {
      setBusyKey(null);
    }
  };

  const revokePendingInvitation = async () => {
    if (!status?.pending_invitation) return;
    setBusyKey('pending-invite');
    try {
      await api.post(`/patient-companion/admin/invitations/${status.pending_invitation.invitation_id}/revoke`);
      setEphemeralInvitation(null);
      await load();
      toast.success('Invitation révoquée');
    } catch {
      toast.error("Impossible de révoquer l'invitation");
    } finally {
      setBusyKey(null);
    }
  };

  const setShare = async (resourceType: ResourceType, resourceId: number, share?: Share) => {
    const key = `${resourceType}:${resourceId}`;
    setBusyKey(key);
    try {
      if (share) {
        await api.delete(`/patient-companion/admin/patients/${patientId}/shares/${share.share_id}`);
      } else {
        await api.post(`/patient-companion/admin/patients/${patientId}/shares`, {
          resource_type: resourceType,
          resource_id: resourceId,
        });
      }
      await load();
      toast.success(share ? 'Partage retiré' : 'Partage activé');
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      toast.error(typeof detail === 'string' ? detail : 'Action de partage impossible');
    } finally {
      setBusyKey(null);
    }
  };

  const revokeAllAccess = async () => {
    if (!status || (status.active_accesses.length === 0 && !status.pending_invitation)) return;
    if (!window.confirm("Révoquer tous les accès Patient Companion actifs et l'invitation en attente ?")) return;
    setBusyKey('revoke-all');
    try {
      const results = await Promise.allSettled([
        ...status.active_accesses.map(access => api.post(`/patient-companion/admin/accesses/${access.access_id}/revoke`)),
        ...(status.pending_invitation
          ? [api.post(`/patient-companion/admin/invitations/${status.pending_invitation.invitation_id}/revoke`)]
          : []),
      ]);
      setEphemeralInvitation(null);
      await load();
      if (results.some(result => result.status === 'rejected')) {
        toast.error('Révocation partielle : état actualisé, réessayez les éléments restants.');
      } else {
        toast.success('Accès Companion révoqué');
      }
    } finally {
      setBusyKey(null);
    }
  };

  const copyCode = async () => {
    if (!ephemeralInvitation?.manualCode) return;
    try {
      await navigator.clipboard.writeText(ephemeralInvitation.manualCode);
      toast.success('Code copié');
    } catch {
      toast.error('Copie impossible');
    }
  };

  if (loading && !status) {
    return <div className="min-h-[50vh] flex items-center justify-center text-text-muted"><Loader2 className="animate-spin" size={30} /></div>;
  }

  const activeCount = status?.active_accesses.length || 0;
  const pending = status?.pending_invitation;

  return (
    <div className="space-y-4 sm:space-y-5 scroll-mt-28" data-patient-companion-admin>
      <section className="grid grid-cols-1 lg:grid-cols-[1.15fr_0.85fr] gap-3 sm:gap-4">
        <div className="bg-card-bg rounded-2xl sm:rounded-[1.75rem] border border-border-main shadow-elite p-4 sm:p-5 md:p-6">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-primary"><ShieldCheck size={20} /><span className="text-[11px] font-black uppercase tracking-[0.16em]">Accès patient</span></div>
              <h2 className="mt-1.5 text-xl sm:mt-2 sm:text-2xl font-black text-main">Patient Companion</h2>
              <p className="hidden sm:block mt-1 text-sm font-medium text-text-muted">Administration sécurisée de l’accès mobile, sans dupliquer le dossier patient.</p>
            </div>
            <button type="button" onClick={() => void load()} className="h-10 px-3 rounded-xl border border-border-main bg-card-bg text-text-muted hover:text-primary transition-colors flex items-center gap-2 text-xs font-black uppercase tracking-wider">
              <RefreshCcw size={15} /><span className="hidden sm:inline">Actualiser</span>
            </button>
          </div>

          <div className="mt-4 grid grid-cols-3 gap-2 sm:mt-5 sm:gap-3">
            <StatusMetric icon={<Smartphone size={18} />} label="Accès actifs" value={String(activeCount)} tone={activeCount ? 'good' : 'neutral'} />
            <StatusMetric icon={<Clock3 size={18} />} label="Invitation" value={pending ? 'En attente' : 'Aucune'} tone={pending ? 'warn' : 'neutral'} />
            <StatusMetric icon={<Link2 size={18} />} label="Partages" value={String(status?.shares.length || 0)} tone={(status?.shares.length || 0) ? 'good' : 'neutral'} />
          </div>

          {status?.active_accesses.map(access => (
            <div key={access.access_id} className="mt-3 flex items-center justify-between gap-3 rounded-2xl border border-emerald-200 bg-emerald-50/70 px-4 py-3">
              <div className="flex items-center gap-3 min-w-0"><CheckCircle2 className="text-emerald-600 shrink-0" size={18} /><div className="min-w-0"><p className="text-sm font-black text-emerald-900">Accès actif · {relationshipLabels[access.relationship_type] || access.relationship_type}</p><p className="text-xs font-medium text-emerald-700">Activé depuis {formatDate(access.created_at)}</p></div></div>
            </div>
          ))}
        </div>

        <div className="bg-card-bg rounded-2xl sm:rounded-[1.75rem] border border-border-main shadow-elite p-4 sm:p-5 md:p-6">
          <div className="flex items-center gap-2 text-primary"><Mail size={19} /><span className="text-[11px] font-black uppercase tracking-[0.16em]">Invitation</span></div>
          <div className="mt-4 space-y-3">
            <label className="block"><span className="text-[10px] font-black uppercase tracking-widest text-text-muted">E-mail Firebase vérifié</span><input value={recipient} onChange={event => setRecipient(event.target.value)} type="email" autoComplete="off" className="mt-1.5 w-full h-11 px-3 rounded-xl border border-border-main bg-background text-main font-bold text-sm outline-none focus:ring-2 focus:ring-primary/20" placeholder="patient@email.com" /></label>
            <div className="grid grid-cols-2 gap-3">
              <label><span className="text-[10px] font-black uppercase tracking-widest text-text-muted">Lien</span><select value={relationshipType} onChange={event => setRelationshipType(event.target.value)} className="mt-1.5 w-full h-11 px-3 rounded-xl border border-border-main bg-background text-main font-bold text-sm"><option value="SELF">Patient</option><option value="PARENT">Parent</option><option value="GUARDIAN">Tuteur</option><option value="CAREGIVER">Aidant</option></select></label>
              <label><span className="text-[10px] font-black uppercase tracking-widest text-text-muted">Validité</span><select value={expiresInMinutes} onChange={event => setExpiresInMinutes(Number(event.target.value))} className="mt-1.5 w-full h-11 px-3 rounded-xl border border-border-main bg-background text-main font-bold text-sm"><option value={15}>15 min</option><option value={30}>30 min</option><option value={60}>60 min</option></select></label>
            </div>
            <button type="button" disabled={busyKey === 'invite'} onClick={() => void createInvitation()} className="w-full h-11 rounded-xl bg-primary text-white font-black text-xs uppercase tracking-widest flex items-center justify-center gap-2 disabled:opacity-60">{busyKey === 'invite' ? <Loader2 className="animate-spin" size={16} /> : <QrCode size={16} />}{pending ? 'Réémettre une invitation' : 'Créer une invitation'}</button>
          </div>

          {pending && !ephemeralInvitation && (
            <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 p-4">
              <p className="text-sm font-black text-amber-900">Invitation active jusqu’au {formatDate(pending.expires_at)}</p>
              <p className="mt-1 text-xs font-medium text-amber-800">Le secret n’est pas récupérable après rechargement. Réémettez l’invitation pour afficher un nouveau QR/code.</p>
              <button type="button" onClick={() => void revokePendingInvitation()} disabled={busyKey === 'pending-invite'} className="mt-3 text-xs font-black text-amber-900 underline underline-offset-4">Révoquer l’invitation</button>
            </div>
          )}
        </div>
      </section>

      {ephemeralInvitation && (
        <section className="scroll-mt-28 sm:scroll-mt-36 bg-card-bg rounded-2xl sm:rounded-[1.75rem] border border-primary/20 shadow-elite p-4 sm:p-5 md:p-6" data-ephemeral-invitation>
          <div className="flex items-start gap-3"><div className="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center shrink-0"><QrCode size={20} /></div><div><h3 className="text-lg font-black text-main">Invitation à remettre au patient</h3><p className="text-sm text-text-muted font-medium">Visible uniquement dans cette session jusqu’au {formatDate(ephemeralInvitation.expiresAt)}.</p></div></div>
          <div className="mt-5 grid grid-cols-1 md:grid-cols-[220px_1fr] gap-5 items-center">
            <div className="rounded-2xl border border-border-main bg-white p-3 flex items-center justify-center min-h-[180px] sm:min-h-[220px]">{ephemeralInvitation.qrDataUrl ? <img src={ephemeralInvitation.qrDataUrl} alt="QR d’activation Patient Companion" className="w-40 h-40 sm:w-48 sm:h-48 object-contain" /> : <QrCode size={96} className="text-slate-300" />}</div>
            <div className="space-y-3"><div className="rounded-2xl border border-border-main bg-background p-4"><p className="text-[10px] font-black uppercase tracking-widest text-text-muted">Code manuel</p><div className="mt-2 flex items-center gap-3"><code className="text-xl sm:text-2xl font-black tracking-[0.14em] text-main break-all">{ephemeralInvitation.manualCode}</code><button type="button" onClick={() => void copyCode()} aria-label="Copier le code" className="w-10 h-10 rounded-xl border border-border-main bg-card-bg flex items-center justify-center text-text-muted hover:text-primary"><Copy size={16} /></button></div></div><p className="text-xs font-medium text-text-muted">Le QR et le code portent le même secret à usage unique. Ils ne sont pas stockés dans le navigateur.</p></div>
          </div>
        </section>
      )}

      <section className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <ResourceCard title="Documents" icon={<FileText size={18} />} empty="Aucun document canonique partageable">
          {canonicalDocuments.map(document => {
            const resourceId = Number(document.id);
            const share = shareByResource.get(`document:${resourceId}`);
            return <ResourceRow key={document.id} title={document.name || document.type} subtitle={`${document.type} · ${document.date}`} shared={Boolean(share)} busy={busyKey === `document:${resourceId}`} onToggle={() => void setShare('document', resourceId, share)} />;
          })}
        </ResourceCard>
        <ResourceCard title="Médias" icon={<Images size={18} />} empty="Aucun média clinique partageable">
          {media.map(asset => {
            const share = shareByResource.get(`media:${asset.id}`);
            return <ResourceRow key={asset.id} title={asset.asset_type === 'RADIOGRAPH' ? 'Radiographie' : asset.asset_type === 'PHOTO' ? 'Photo' : 'Document média'} subtitle={`${asset.timepoint || asset.source_kind} · ${formatDate(asset.captured_at || asset.created_at)}`} shared={Boolean(share)} busy={busyKey === `media:${asset.id}`} onToggle={() => void setShare('media', asset.id, share)} />;
          })}
        </ResourceCard>
      </section>

      <section className="rounded-2xl sm:rounded-[1.75rem] border border-rose-200 bg-rose-50/70 p-4 sm:p-5 md:p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"><div className="flex items-start gap-3"><AlertTriangle size={20} className="text-rose-600 mt-0.5 shrink-0" /><div><h3 className="font-black text-rose-950">Révoquer complètement l’accès Companion</h3><p className="mt-1 text-sm font-medium text-rose-800">Révoque les accès actifs et l’invitation en attente. Les données patient, documents et médias restent intacts.</p></div></div><button type="button" onClick={() => void revokeAllAccess()} disabled={busyKey === 'revoke-all' || (activeCount === 0 && !pending)} className="h-11 px-4 rounded-xl border border-rose-300 bg-white text-rose-700 font-black text-xs uppercase tracking-widest flex items-center justify-center gap-2 disabled:opacity-50"><Unlink size={16} /> Révoquer l’accès</button></div>
      </section>
    </div>
  );
};

const StatusMetric = ({ icon, label, value, tone }: { icon: React.ReactNode; label: string; value: string; tone: 'good' | 'warn' | 'neutral' }) => (
  <div className={cn('rounded-xl sm:rounded-2xl border px-2.5 py-2.5 sm:px-4 sm:py-3', tone === 'good' ? 'border-emerald-200 bg-emerald-50/70' : tone === 'warn' ? 'border-amber-200 bg-amber-50/70' : 'border-border-main bg-background')}><div className="flex items-center gap-1.5 text-text-muted"><span className="hidden sm:inline-flex">{icon}</span><span className="text-[8px] sm:text-[10px] font-black uppercase tracking-[0.04em] sm:tracking-widest">{label}</span></div><p className="mt-1 text-sm sm:mt-2 sm:text-lg font-black leading-tight text-main">{value}</p></div>
);

const ResourceCard = ({ title, icon, empty, children }: { title: string; icon: React.ReactNode; empty: string; children: React.ReactNode }) => {
  const hasChildren = Array.isArray(children) ? children.length > 0 : Boolean(children);
  return <div className="bg-card-bg rounded-2xl sm:rounded-[1.75rem] border border-border-main shadow-elite p-4 sm:p-5 md:p-6"><div className="flex items-center gap-2 text-primary">{icon}<h3 className="font-black text-main">{title}</h3></div><div className="mt-4 max-h-[420px] overflow-y-auto space-y-2 pr-1">{hasChildren ? children : <p className="py-8 text-center text-sm font-medium text-text-muted">{empty}</p>}</div></div>;
};

const ResourceRow = ({ title, subtitle, shared, busy, onToggle }: { title: string; subtitle: string; shared: boolean; busy: boolean; onToggle: () => void }) => (
  <div className="flex items-center justify-between gap-3 rounded-2xl border border-border-main bg-background px-3.5 py-3"><div className="min-w-0"><p className="truncate text-sm font-black text-main">{title}</p><p className="mt-0.5 truncate text-xs font-medium text-text-muted">{subtitle}</p></div><button type="button" onClick={onToggle} disabled={busy} className={cn('shrink-0 h-9 px-3 rounded-xl border text-[10px] font-black uppercase tracking-wider flex items-center gap-1.5 transition-colors disabled:opacity-60', shared ? 'border-rose-200 bg-rose-50 text-rose-700' : 'border-primary/20 bg-primary/5 text-primary')}>{busy ? <Loader2 className="animate-spin" size={14} /> : shared ? <Link2Off size={14} /> : <Link2 size={14} />}{shared ? 'Retirer' : 'Partager'}</button></div>
);
