import { useEffect, useMemo, useRef, useState, type ChangeEvent } from 'react';
import { AlertTriangle, ArrowLeft, Calendar, Camera, CheckCircle2, Download, ExternalLink, FileText, Image as ImageIcon, Loader2, MessageCircle, Phone, Plus, RefreshCcw, Share2, ShieldCheck, Trash2, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { MobileStorage, type MobileBridgeContext } from '../../../services/zka/MobileStorage';
import { buildTelHref, buildWhatsAppHref } from './mobilePatientContact';
import { buildDocumentShareData, canNativeShareDocument, isShareAbortError } from './mobileDocumentShare';
import { MobilePanoramicViewer } from './MobilePanoramicViewer';

interface MobilePatient {
  id: number;
  numero_dossier?: string | null;
  nom: string;
  prenom: string;
  date_naissance?: string | null;
  telephone?: string | null;
  assurance?: string | null;
  has_medical_alert: boolean;
  motif_consultation?: string | null;
}

interface MobilePanoramic {
  patient_name: string;
  created_at?: string | null;
  landmarks_count: number;
  report_saved: boolean;
}

interface MobileDocument {
  patient_name: string;
  document_type: string;
  name: string;
  filename: string;
  created_at?: string | null;
  mime_type?: string | null;
}

interface MobileAppointment {
  patient_name: string;
  datetime_start?: string | null;
  duration_minutes: number;
  motif: string;
  status: string;
  scheduling_type: string;
  notes?: string | null;
}

interface DocumentScanPage {
  key: string;
  file: File;
  previewUrl: string;
}

function ageFromBirth(value?: string | null): number | null {
  if (!value) return null;
  const birth = new Date(value);
  if (Number.isNaN(birth.getTime())) return null;
  const now = new Date();
  let age = now.getFullYear() - birth.getFullYear();
  const beforeBirthday = now.getMonth() < birth.getMonth() || (now.getMonth() === birth.getMonth() && now.getDate() < birth.getDate());
  if (beforeBirthday) age -= 1;
  return age >= 0 && age < 130 ? age : null;
}

function formatDate(value?: string | null): string {
  if (!value) return 'Date non renseignée';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Date non renseignée';
  return date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export const MobileContext = () => {
  const navigate = useNavigate();
  const [context, setContext] = useState<MobileBridgeContext | null>(null);
  const [patient, setPatient] = useState<MobilePatient | null>(null);
  const [panoramic, setPanoramic] = useState<MobilePanoramic | null>(null);
  const [documentData, setDocumentData] = useState<MobileDocument | null>(null);
  const [appointment, setAppointment] = useState<MobileAppointment | null>(null);
  const [mediaUrl, setMediaUrl] = useState<string | null>(null);
  const [mediaType, setMediaType] = useState<string>('');
  const [mediaBlob, setMediaBlob] = useState<Blob | null>(null);
  const [shareError, setShareError] = useState('');
  const mediaUrlRef = useRef<string | null>(null);
  const [phase, setPhase] = useState<'loading' | 'ready' | 'error'>('loading');
  const [error, setError] = useState('');
  const photoInputRef = useRef<HTMLInputElement | null>(null);
  const photoPreviewUrlRef = useRef<string | null>(null);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoPreviewUrl, setPhotoPreviewUrl] = useState<string | null>(null);
  const [photoPhase, setPhotoPhase] = useState<'idle' | 'preview' | 'uploading' | 'saved'>('idle');
  const [photoError, setPhotoError] = useState('');
  const scanInputRef = useRef<HTMLInputElement | null>(null);
  const scanPagesRef = useRef<DocumentScanPage[]>([]);
  const [scanPages, setScanPages] = useState<DocumentScanPage[]>([]);
  const [scanActiveIndex, setScanActiveIndex] = useState(0);
  const [scanPhase, setScanPhase] = useState<'idle' | 'preview' | 'uploading' | 'saved'>('idle');
  const [scanError, setScanError] = useState('');

  const clearMedia = () => {
    if (mediaUrlRef.current) URL.revokeObjectURL(mediaUrlRef.current);
    mediaUrlRef.current = null;
    setMediaUrl(null);
    setMediaType('');
    setMediaBlob(null);
    setShareError('');
  };

  const clearClinicalPhoto = () => {
    if (photoPreviewUrlRef.current) URL.revokeObjectURL(photoPreviewUrlRef.current);
    photoPreviewUrlRef.current = null;
    setPhotoPreviewUrl(null);
    setPhotoFile(null);
    setPhotoPhase('idle');
    setPhotoError('');
    if (photoInputRef.current) photoInputRef.current.value = '';
  };

  const setDocumentScanPages = (pages: DocumentScanPage[]) => {
    scanPagesRef.current = pages;
    setScanPages(pages);
  };

  const clearDocumentScan = () => {
    scanPagesRef.current.forEach(page => URL.revokeObjectURL(page.previewUrl));
    setDocumentScanPages([]);
    setScanActiveIndex(0);
    setScanPhase('idle');
    setScanError('');
    if (scanInputRef.current) scanInputRef.current.value = '';
  };


  const load = async () => {
    setPhase('loading');
    setError('');
    setPatient(null);
    setPanoramic(null);
    setDocumentData(null);
    setAppointment(null);
    clearMedia();
    clearClinicalPhoto();
    clearDocumentScan();
    const stored = await MobileStorage.getBridgeContext().catch(() => null);
    setContext(stored);
    if (!stored || !['patient', 'panoramic', 'document', 'appointment'].includes(stored.type)) {
      setError('Aucun contexte clinique compatible n’est disponible sur cet appareil.');
      setPhase('error');
      return;
    }
    if (stored.state !== 'ready') {
      setError(stored.reason || 'Ce contexte clinique n’est plus disponible.');
      setPhase('error');
      return;
    }

    let creds = await MobileStorage.getCredentials();
    if (!creds?.access_token) {
      setError('Session mobile non disponible. Régénérez le pont depuis le poste cabinet.');
      setPhase('error');
      return;
    }

    const request = async (path: string, accessToken: string) => fetch(`${creds!.api_base_url.replace(/\/$/, '')}/api/mobile/${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${accessToken}` },
      body: JSON.stringify({ context_key: stored.key }),
    });

    const loadMedia = async () => {
      if (!creds?.access_token) throw new Error('Session mobile expirée.');
      let mediaResponse = await request('resource-context-media', creds.access_token);
      if (mediaResponse.status === 401) {
        creds = await MobileStorage.refreshCredentials();
        if (creds?.access_token) mediaResponse = await request('resource-context-media', creds.access_token);
      }
      if (!mediaResponse.ok) {
        const mediaError = await mediaResponse.json().catch(() => ({}));
        throw new Error(mediaError.detail || `Média indisponible (${mediaResponse.status}).`);
      }
      const blob = await mediaResponse.blob();
      if (!blob.size) throw new Error('Le média reçu est vide.');
      if (stored.type === 'panoramic' && !blob.type.startsWith('image/')) {
        throw new Error('Média panoramique invalide.');
      }
      const nextUrl = URL.createObjectURL(blob);
      mediaUrlRef.current = nextUrl;
      setMediaUrl(nextUrl);
      setMediaType(blob.type || 'application/octet-stream');
      setMediaBlob(blob);
    };

    try {
      let response = await request('resource-context', creds.access_token);
      if (response.status === 401) {
        creds = await MobileStorage.refreshCredentials();
        if (creds?.access_token) response = await request('resource-context', creds.access_token);
      }
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || `Contexte indisponible (${response.status}).`);
      }
      const payload = await response.json();

      if (payload.type === 'patient' && payload.patient && stored.type === 'patient') {
        setPatient(payload.patient as MobilePatient);
        setPhase('ready');
        return;
      }

      if (payload.type === 'panoramic' && payload.panoramic && stored.type === 'panoramic') {
        await loadMedia();
        setPanoramic(payload.panoramic as MobilePanoramic);
        setPhase('ready');
        return;
      }

      if (payload.type === 'document' && payload.document && stored.type === 'document') {
        await loadMedia();
        setDocumentData(payload.document as MobileDocument);
        setPhase('ready');
        return;
      }

      if (payload.type === 'appointment' && payload.appointment && stored.type === 'appointment') {
        setAppointment(payload.appointment as MobileAppointment);
        setPhase('ready');
        return;
      }

      throw new Error('Réponse de contexte mobile invalide.');
    } catch (err: unknown) {
      setError(err instanceof TypeError
        ? 'Serveur du cabinet inaccessible. Vérifiez que le poste cabinet est démarré et accessible sur ce réseau, puis réessayez.'
        : err instanceof Error
          ? err.message
          : 'Impossible de charger le contexte clinique.');
      setPhase('error');
    }
  };

  useEffect(() => {
    void load();
    return () => {
      if (mediaUrlRef.current) URL.revokeObjectURL(mediaUrlRef.current);
      if (photoPreviewUrlRef.current) URL.revokeObjectURL(photoPreviewUrlRef.current);
      scanPagesRef.current.forEach(page => URL.revokeObjectURL(page.previewUrl));
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const age = useMemo(() => ageFromBirth(patient?.date_naissance), [patient?.date_naissance]);
  const callHref = buildTelHref(patient?.telephone);
  const whatsappHref = buildWhatsAppHref(patient?.telephone);
  const whatsappHint = !patient?.telephone
    ? 'WhatsApp indisponible : aucun numéro patient.'
    : !whatsappHref
      ? 'WhatsApp : indicatif international requis.'
      : null;

  const openDocument = () => {
    if (!mediaUrl) return;
    window.open(mediaUrl, '_blank', 'noopener,noreferrer');
  };

  const downloadDocument = () => {
    if (!mediaUrl || !documentData) return;
    const anchor = document.createElement('a');
    anchor.href = mediaUrl;
    anchor.download = documentData.filename || documentData.name || 'document';
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
  };

  const shareDocument = () => {
    setShareError('');
    if (!mediaBlob || !documentData) return;
    const shareData = buildDocumentShareData(mediaBlob, documentData.mime_type || mediaType);
    if (!canNativeShareDocument(navigator, shareData)) {
      setShareError('Partage système indisponible. Utilisez Télécharger.');
      return;
    }
    const sharePromise = navigator.share(shareData);
    void sharePromise.catch((shareFailure: unknown) => {
      if (!isShareAbortError(shareFailure)) setShareError('Le partage système n’a pas pu s’ouvrir. Utilisez Télécharger.');
    });
  };

  const openClinicalPhotoPicker = () => {
    clearDocumentScan();
    setPhotoError('');
    photoInputRef.current?.click();
  };

  const handleClinicalPhotoSelected = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] || null;
    if (!file) return;
    if (file.type && !file.type.startsWith('image/')) {
      setPhotoError('Sélectionnez une image JPEG, PNG ou WebP.');
      event.target.value = '';
      return;
    }
    if (file.size > 12 * 1024 * 1024) {
      setPhotoError('La photo dépasse la limite de 12 MiB.');
      event.target.value = '';
      return;
    }
    if (photoPreviewUrlRef.current) URL.revokeObjectURL(photoPreviewUrlRef.current);
    const nextUrl = URL.createObjectURL(file);
    photoPreviewUrlRef.current = nextUrl;
    setPhotoFile(file);
    setPhotoPreviewUrl(nextUrl);
    setPhotoError('');
    setPhotoPhase('preview');
  };

  const uploadClinicalPhoto = async () => {
    if (!photoFile || !context || context.type !== 'patient') return;
    setPhotoPhase('uploading');
    setPhotoError('');
    try {
      let creds = await MobileStorage.getCredentials();
      if (!creds?.access_token) throw new Error('Session mobile non disponible. Régénérez le pont depuis le poste cabinet.');

      const request = async (accessToken: string) => {
        const form = new FormData();
        form.append('context_key', context.key);
        form.append('file', photoFile, photoFile.name || 'photo-clinique.jpg');
        return fetch(`${creds!.api_base_url.replace(/\/$/, '')}/api/mobile/resource-context-photo`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${accessToken}` },
          body: form,
        });
      };

      let response = await request(creds.access_token);
      if (response.status === 401) {
        creds = await MobileStorage.refreshCredentials();
        if (creds?.access_token) response = await request(creds.access_token);
      }
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || `Photo clinique non enregistrée (${response.status}).`);
      }
      const payload = await response.json();
      if (!payload?.success || payload?.document?.document_type !== 'PHOTO_CLINIQUE') {
        throw new Error('Réponse d’enregistrement de photo invalide.');
      }
      setPhotoPhase('saved');
    } catch (err: unknown) {
      setPhotoError(err instanceof TypeError
        ? 'Serveur du cabinet inaccessible. La photo reste en aperçu : vérifiez le poste cabinet puis réessayez.'
        : err instanceof Error
          ? err.message
          : 'Impossible d’enregistrer la photo clinique.');
      setPhotoPhase('preview');
    }
  };

  const startDocumentScan = () => {
    clearClinicalPhoto();
    clearDocumentScan();
    scanInputRef.current?.click();
  };

  const addDocumentScanPage = () => {
    setScanError('');
    if (scanPagesRef.current.length >= 8) {
      setScanError('Le document est limité à 8 pages.');
      return;
    }
    scanInputRef.current?.click();
  };

  const handleDocumentScanSelected = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] || null;
    if (!file) return;
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (file.type && !allowedTypes.includes(file.type)) {
      setScanError('Sélectionnez une page JPEG, PNG ou WebP.');
      event.target.value = '';
      return;
    }
    if (file.size > 12 * 1024 * 1024) {
      setScanError('Une page dépasse la limite de 12 MiB.');
      event.target.value = '';
      return;
    }
    if (scanPagesRef.current.reduce((total, page) => total + page.file.size, 0) + file.size > 48 * 1024 * 1024) {
      setScanError('Le scan dépasse la limite cumulée de 48 MiB.');
      event.target.value = '';
      return;
    }
    if (scanPagesRef.current.length >= 8) {
      setScanError('Le document est limité à 8 pages.');
      event.target.value = '';
      return;
    }
    const previewUrl = URL.createObjectURL(file);
    const next = [...scanPagesRef.current, {
      key: `${Date.now()}-${scanPagesRef.current.length}-${file.name}`,
      file,
      previewUrl,
    }];
    setDocumentScanPages(next);
    setScanActiveIndex(next.length - 1);
    setScanPhase('preview');
    setScanError('');
    event.target.value = '';
  };

  const removeDocumentScanPage = (index: number) => {
    const current = scanPagesRef.current;
    const removed = current[index];
    if (removed) URL.revokeObjectURL(removed.previewUrl);
    const next = current.filter((_page, pageIndex) => pageIndex !== index);
    setDocumentScanPages(next);
    if (!next.length) {
      setScanActiveIndex(0);
      setScanPhase('idle');
      setScanError('');
      return;
    }
    setScanActiveIndex(Math.min(index, next.length - 1));
    setScanPhase('preview');
    setScanError('');
  };

  const uploadDocumentScan = async () => {
    if (!scanPagesRef.current.length || !context || context.type !== 'patient') return;
    setScanPhase('uploading');
    setScanError('');
    try {
      let creds = await MobileStorage.getCredentials();
      if (!creds?.access_token) throw new Error('Session mobile non disponible. Régénérez le pont depuis le poste cabinet.');
      const request = async (accessToken: string) => {
        const form = new FormData();
        form.append('context_key', context.key);
        scanPagesRef.current.forEach((page, index) => form.append('pages', page.file, page.file.name || `scan-page-${index + 1}.jpg`));
        return fetch(`${creds!.api_base_url.replace(/\/$/, '')}/api/mobile/resource-context-document-scan`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${accessToken}` },
          body: form,
        });
      };
      let response = await request(creds.access_token);
      if (response.status === 401) {
        creds = await MobileStorage.refreshCredentials();
        if (creds?.access_token) response = await request(creds.access_token);
      }
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || `Document non enregistré (${response.status}).`);
      }
      const payload = await response.json();
      if (!payload?.success || payload?.document?.document_type !== 'AUTRE' || payload?.pages !== scanPagesRef.current.length) {
        throw new Error('Réponse d’enregistrement du document invalide.');
      }
      setScanPhase('saved');
    } catch (err: unknown) {
      setScanError(err instanceof TypeError
        ? 'Serveur du cabinet inaccessible. Les pages restent en aperçu : vérifiez le poste cabinet puis réessayez.'
        : err instanceof Error
          ? err.message
          : 'Impossible d’enregistrer le document scanné.');
      setScanPhase('preview');
    }
  };


  if (phase === 'loading') {
    return (
      <div data-mobile-context className="min-h-[100dvh] bg-background text-text-main flex flex-col items-center justify-center gap-4 p-6 font-outfit relative" style={{ backgroundColor: 'var(--bg-medical-pearl)' }}><div className="document-watermark absolute inset-0 pointer-events-none opacity-40" />
        <Loader2 size={38} className="animate-spin text-primary relative z-10" />
        <p className="relative z-10 text-xs font-black uppercase tracking-widest text-text-muted">Ouverture sécurisée du contexte…</p>
      </div>
    );
  }

  if (phase === 'error' || (!patient && !panoramic && !documentData && !appointment)) {
    return (
      <div data-mobile-context className="min-h-[100dvh] bg-background text-text-main p-5 font-outfit flex items-center justify-center relative" style={{ backgroundColor: 'var(--bg-medical-pearl)' }}><div className="document-watermark absolute inset-0 pointer-events-none opacity-40" />
        <div className="w-full max-w-md bg-card-bg border border-rose-200 rounded-[2rem] p-6 shadow-elite text-center relative z-10">
          <AlertTriangle className="mx-auto text-rose-500" size={42} />
          <h1 className="mt-4 text-xl font-black text-text-main">Contexte indisponible</h1>
          <p className="mt-2 text-sm font-bold leading-relaxed text-text-muted">{error || context?.reason}</p>
          <button data-m4-touch type="button" onClick={() => void load()} className="mt-5 w-full min-h-[52px] rounded-2xl border border-border-main bg-card-bg font-black text-xs uppercase tracking-widest text-text-main inline-flex items-center justify-center gap-2"><RefreshCcw size={16} /> Réessayer</button>
          <button data-m4-touch type="button" onClick={() => navigate('/mobile/dashboard?tab=agenda', { replace: true })} className="mt-3 w-full min-h-[52px] rounded-2xl bg-primary text-white font-black text-xs uppercase tracking-widest">Retour au mobile</button>
        </div>
      </div>
    );
  }

  if (appointment) {
    const schedulingLabels: Record<string, string> = { EXACT_TIME: 'Heure précise', MORNING: 'Matin', AFTERNOON: 'Après-midi', FULL_DAY: 'Toute la journée' };
    return (
      <div data-m4d-context className="min-h-[100dvh] bg-background text-text-main font-outfit relative px-5 pt-[max(1.25rem,env(safe-area-inset-top))] pb-[max(1.5rem,env(safe-area-inset-bottom))]" style={{ backgroundColor: 'var(--bg-medical-pearl)' }}>
        <div className="document-watermark absolute inset-0 pointer-events-none opacity-40" />
        <div className="max-w-md mx-auto relative z-10">
          <button data-m4d-touch type="button" onClick={() => navigate('/mobile/dashboard?tab=agenda')} className="min-h-11 inline-flex items-center gap-2 text-sm font-black text-text-muted"><ArrowLeft size={17} /> Retour</button>
          <div className="mt-4 flex items-center gap-2 text-primary"><ShieldCheck size={18} /><p className="text-[10px] font-black uppercase tracking-[0.18em]">Contexte cabinet vérifié</p></div>
          <h1 className="mt-2 text-3xl font-black tracking-tight text-text-main">Rendez-vous</h1>
          <p className="mt-1 text-lg font-black text-text-main">{appointment.patient_name}</p>
          <section className="mt-5 rounded-[1.75rem] bg-card-bg border border-border-main p-5 shadow-elite space-y-5">
            <div><p className="text-[10px] font-black uppercase tracking-widest text-text-muted">Date & heure</p><p className="mt-1 text-lg font-black text-text-main">{formatDate(appointment.datetime_start)}</p><p className="mt-1 text-sm font-bold text-text-muted">{appointment.duration_minutes} min · {schedulingLabels[appointment.scheduling_type] || appointment.scheduling_type}</p></div>
            <div className="pt-4 border-t border-border-main"><p className="text-[10px] font-black uppercase tracking-widest text-text-muted">Motif</p><p className="mt-1 text-base font-black text-text-main">{appointment.motif || 'Non renseigné'}</p></div>
            <div className="pt-4 border-t border-border-main"><p className="text-[10px] font-black uppercase tracking-widest text-text-muted">Statut</p><p className="mt-1 inline-flex min-h-11 items-center rounded-xl bg-primary/10 px-3 text-sm font-black text-primary">{appointment.status}</p></div>
            {appointment.notes && <div className="pt-4 border-t border-border-main"><p className="text-[10px] font-black uppercase tracking-widest text-text-muted">Notes</p><p className="mt-1 text-sm font-bold text-text-main whitespace-pre-wrap">{appointment.notes}</p></div>}
          </section>
          <p className="mt-4 text-[11px] font-bold text-text-muted text-center">Contexte résolu côté serveur · aucun identifiant rendez-vous dans l’URL</p>
          <button data-m4d-touch type="button" onClick={() => navigate('/mobile/dashboard?tab=agenda', { replace: true })} className="mt-6 w-full min-h-[54px] rounded-2xl bg-primary text-white font-black text-xs uppercase tracking-widest">Retour au mobile</button>
        </div>
      </div>
    );
  }

  if (documentData) {
    const isImage = mediaType.startsWith('image/');
    const shareData = mediaBlob ? buildDocumentShareData(mediaBlob, documentData.mime_type || mediaType) : null;
    const shareSupported = !!shareData && canNativeShareDocument(navigator, shareData);
    return (
      <div data-m4c-context className="min-h-[100dvh] bg-background text-text-main font-outfit relative px-5 pt-[max(1.25rem,env(safe-area-inset-top))] pb-[max(1.5rem,env(safe-area-inset-bottom))]" style={{ backgroundColor: 'var(--bg-medical-pearl)' }}>
        <div className="document-watermark absolute inset-0 pointer-events-none opacity-40" />
        <div className="max-w-md mx-auto relative z-10">
          <button data-m4c-touch type="button" onClick={() => navigate('/mobile/dashboard?tab=agenda')} className="min-h-11 inline-flex items-center gap-2 text-sm font-black text-text-muted"><ArrowLeft size={17} /> Retour</button>
          <div className="mt-4 flex items-center gap-2 text-primary"><ShieldCheck size={18} /><p className="text-[10px] font-black uppercase tracking-[0.18em]">Contexte cabinet vérifié</p></div>
          <h1 className="mt-2 text-3xl font-black tracking-tight text-text-main">Document</h1>
          <p className="mt-1 text-base font-black text-text-main">{documentData.patient_name}</p>
          <p className="mt-1 text-sm font-bold text-text-muted">{documentData.document_type} · {formatDate(documentData.created_at)}</p>

          <section className="mt-5 rounded-[1.75rem] bg-card-bg border border-border-main p-5 shadow-elite">
            {isImage && mediaUrl ? <img src={mediaUrl} alt="Document contextuel" className="block w-full max-h-[48dvh] object-contain rounded-2xl border border-border-main bg-white" /> : <div className="min-h-[230px] rounded-2xl border border-border-main bg-background/60 flex flex-col items-center justify-center text-center p-5"><FileText size={64} className="text-primary"/><p className="mt-5 font-black text-text-main break-all">{documentData.name}</p><p className="mt-2 text-xs font-bold text-text-muted">Document chargé depuis le serveur sécurisé</p></div>}
          </section>

          <div className="mt-4 grid grid-cols-2 gap-3">
            <button data-m4c-touch type="button" onClick={openDocument} disabled={!mediaUrl} className="min-h-[54px] rounded-2xl bg-card-bg border border-border-main text-text-main inline-flex items-center justify-center gap-2 font-black text-sm disabled:opacity-40"><ExternalLink size={18}/> Ouvrir</button>
            <button data-m4c-touch type="button" onClick={downloadDocument} disabled={!mediaUrl} className="min-h-[54px] rounded-2xl bg-card-bg border border-border-main text-text-main inline-flex items-center justify-center gap-2 font-black text-sm disabled:opacity-40"><Download size={18}/> Télécharger</button>
          </div>
          {shareSupported ? <button data-m4c-touch data-m6f-touch data-m6f-share type="button" onClick={shareDocument} className="mt-3 w-full min-h-[58px] rounded-2xl bg-primary text-white inline-flex items-center justify-center gap-2 font-black text-sm"><Share2 size={19}/> Partager le document</button> : <p data-m6f-share-fallback className="mt-3 text-center text-[11px] font-bold text-text-muted">Partage système indisponible · Télécharger reste disponible.</p>}
          {shareSupported && <p data-m6f-share-privacy className="mt-3 text-center text-[11px] font-bold text-text-muted">Fichier uniquement · aucun lien ou token partagé</p>}
          {shareError && <p data-m6f-share-error role="alert" className="mt-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-center text-xs font-bold text-amber-800">{shareError}</p>}
          <p className="mt-4 text-[11px] font-bold text-text-muted text-center">Média chargé par contexte serveur · aucun identifiant document dans l’URL</p>
          <button data-m4c-touch type="button" onClick={() => navigate('/mobile/dashboard?tab=agenda', { replace: true })} className="mt-6 w-full min-h-[54px] rounded-2xl bg-card-bg border border-border-main text-text-main font-black text-xs uppercase tracking-widest">Retour au mobile</button>
        </div>
      </div>
    );
  }

  if (panoramic) {
    return (
      <div data-m4b-context className="min-h-[100dvh] bg-background text-text-main font-outfit relative px-5 pt-[max(1.25rem,env(safe-area-inset-top))] pb-[max(1.5rem,env(safe-area-inset-bottom))]" style={{ backgroundColor: 'var(--bg-medical-pearl)' }}>
        <div className="document-watermark absolute inset-0 pointer-events-none opacity-40" />
        <div className="max-w-md mx-auto relative z-10">
          <button data-m4b-touch type="button" onClick={() => navigate('/mobile/dashboard?tab=agenda')} className="min-h-11 inline-flex items-center gap-2 text-sm font-black text-text-muted"><ArrowLeft size={17} /> Retour</button>
          <div className="mt-4 flex items-center gap-2 text-primary"><ShieldCheck size={18} /><p className="text-[10px] font-black uppercase tracking-[0.18em]">Contexte cabinet vérifié</p></div>
          <h1 className="mt-2 text-3xl font-black tracking-tight text-text-main">Radio panoramique</h1>
          <p className="mt-1 text-base font-black text-text-main">{panoramic.patient_name}</p>
          <p className="mt-1 text-sm font-bold text-text-muted">{formatDate(panoramic.created_at)}</p>
          <section className="mt-5 rounded-[1.75rem] overflow-hidden bg-slate-950 border border-slate-800 shadow-elite min-h-[230px] flex items-center justify-center">
            {mediaUrl ? <MobilePanoramicViewer src={mediaUrl} alt="Radio panoramique contextuelle" /> : <div className="text-slate-400 flex items-center gap-2 text-sm font-bold"><ImageIcon size={18} /> Image indisponible</div>}
          </section>
          {mediaUrl && <p data-m6h-hint className="mt-3 text-center text-[10px] font-black uppercase tracking-[0.12em] text-text-muted">Agrandir pour examiner · zoom 1×–4×</p>}
          <section className="mt-4 rounded-[1.5rem] bg-card-bg border border-border-main p-4 shadow-elite"><div className="flex items-center justify-between gap-4"><div><p className="text-[10px] font-black uppercase tracking-widest text-text-muted">Statut</p><p className="mt-1 font-black text-text-main">{panoramic.report_saved ? 'Rapport enregistré' : 'Rapport non finalisé'}</p></div><FileText size={20} className="text-primary" /></div><p className="mt-3 pt-3 border-t border-border-main text-[11px] font-bold text-text-muted">{panoramic.landmarks_count} repère{panoramic.landmarks_count > 1 ? 's' : ''} dentaire{panoramic.landmarks_count > 1 ? 's' : ''} · média chargé depuis le serveur sans identifiant dans l’URL</p></section>
          <button data-m4b-touch type="button" onClick={() => navigate('/mobile/dashboard?tab=agenda', { replace: true })} className="mt-6 w-full min-h-[54px] rounded-2xl bg-card-bg border border-border-main text-text-main font-black text-xs uppercase tracking-widest">Retour au mobile</button>
        </div>
      </div>
    );
  }

  const displayName = `${patient!.nom.toUpperCase()} ${patient!.prenom}`;
  return (
    <div data-m4a-context className="min-h-[100dvh] bg-background text-text-main font-outfit relative px-5 pt-[max(1.25rem,env(safe-area-inset-top))] pb-[max(1.5rem,env(safe-area-inset-bottom))]" style={{ backgroundColor: 'var(--bg-medical-pearl)' }}>
      <div className="document-watermark absolute inset-0 pointer-events-none opacity-40" />
      <div className="max-w-md mx-auto relative z-10">
        <button data-m4a-touch type="button" onClick={() => navigate('/mobile/dashboard?tab=agenda')} className="min-h-11 inline-flex items-center gap-2 text-sm font-black text-text-muted"><ArrowLeft size={17} /> Retour</button>
        <div className="mt-4 flex items-center gap-2 text-primary"><ShieldCheck size={18} /><p className="text-[10px] font-black uppercase tracking-[0.18em]">Contexte cabinet vérifié</p></div>
        <h1 className="mt-2 text-3xl font-black tracking-tight text-text-main">Dossier patient</h1>
        <section className="mt-5 rounded-[1.75rem] bg-card-bg border border-border-main p-5 shadow-elite"><h2 className="text-2xl font-black tracking-tight text-text-main">{displayName}</h2><p className="mt-1 text-sm font-bold text-text-muted">Dossier {patient!.numero_dossier || 'sans numéro'}</p><div className="mt-3 flex flex-wrap gap-x-4 gap-y-2 text-sm font-bold text-text-muted">{age !== null && <span>{age} ans</span>}{patient!.telephone && <span>{patient!.telephone}</span>}</div>{patient!.has_medical_alert && <div className="mt-4 inline-flex min-h-11 items-center gap-2 px-3 rounded-xl border border-rose-200 bg-rose-50 text-rose-700 text-xs font-black uppercase tracking-wide"><AlertTriangle size={15} /> Alerte médicale</div>}</section>
        <p className="mt-7 mb-3 text-sm font-black text-text-main">Actions rapides</p>
        <div data-m6e-actions className="grid grid-cols-3 gap-2">
          {callHref ? <a data-m4a-touch data-m6e-touch data-m6e-contact data-m6e-call href={callHref} className="min-h-[64px] rounded-2xl bg-card-bg border border-border-main inline-flex flex-col items-center justify-center gap-1 font-black text-xs text-text-main"><Phone size={18} /> Appeler</a> : <button data-m4a-touch data-m6e-touch data-m6e-contact data-m6e-call type="button" disabled className="min-h-[64px] rounded-2xl bg-card-bg border border-border-main inline-flex flex-col items-center justify-center gap-1 font-black text-xs text-text-main opacity-40"><Phone size={18} /> Appeler</button>}
          {whatsappHref ? <a data-m4a-touch data-m6e-touch data-m6e-contact data-m6e-whatsapp href={whatsappHref} target="_blank" rel="noopener noreferrer" className="min-h-[64px] rounded-2xl bg-card-bg border border-primary/20 inline-flex flex-col items-center justify-center gap-1 font-black text-xs text-text-main"><MessageCircle size={18} className="text-primary" /> WhatsApp</a> : <button data-m4a-touch data-m6e-touch data-m6e-contact data-m6e-whatsapp type="button" disabled className="min-h-[64px] rounded-2xl bg-card-bg border border-border-main inline-flex flex-col items-center justify-center gap-1 font-black text-xs text-text-main opacity-40"><MessageCircle size={18} /> WhatsApp</button>}
          <button data-m4a-touch data-m6e-touch data-m6e-contact type="button" onClick={() => navigate('/mobile/dashboard?tab=agenda')} className="min-h-[64px] rounded-2xl bg-primary text-white inline-flex flex-col items-center justify-center gap-1 font-black text-xs"><Calendar size={18} /> Agenda</button>
        </div>
        {whatsappHint && <p data-m6e-whatsapp-hint className="mt-2 text-center text-[10px] font-bold text-text-muted">{whatsappHint}</p>}
        <input ref={photoInputRef} data-m6a-photo-input type="file" accept="image/jpeg,image/png,image/webp" capture="environment" onChange={handleClinicalPhotoSelected} className="sr-only" tabIndex={-1} aria-hidden="true" />
        <button data-m6a-photo-action data-m6a-touch type="button" onClick={openClinicalPhotoPicker} className="mt-3 w-full min-h-[66px] rounded-2xl bg-primary text-white inline-flex items-center justify-start gap-3 px-4 text-left shadow-elite active:scale-[0.99] transition-transform focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-white/15"><Camera size={20} /></span>
          <span><span className="block font-black text-sm">Photo clinique</span><span className="mt-0.5 block text-[11px] font-bold text-white/80">Prendre une photo au fauteuil</span></span>
        </button>

        <input ref={scanInputRef} data-m6b-scan-input type="file" accept="image/jpeg,image/png,image/webp" capture="environment" onChange={handleDocumentScanSelected} className="sr-only" tabIndex={-1} aria-hidden="true" />
        <button data-m6b-scan-action data-m6b-touch type="button" onClick={startDocumentScan} className="mt-3 w-full min-h-[66px] rounded-2xl bg-card-bg border border-primary/25 text-text-main inline-flex items-center justify-start gap-3 px-4 text-left shadow-elite active:scale-[0.99] transition-transform focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary"><FileText size={20} /></span>
          <span><span className="block font-black text-sm">Scanner un document</span><span className="mt-0.5 block text-[11px] font-bold text-text-muted">Créer un PDF dans le dossier</span></span>
          <span aria-hidden="true" className="ml-auto text-xl font-black text-text-muted/70">›</span>
        </button>
        <section className="mt-6 rounded-[1.75rem] bg-card-bg border border-border-main p-5 shadow-elite space-y-4"><div><p className="text-[10px] font-black uppercase tracking-widest text-text-muted">Assurance</p><p className="mt-1 font-black text-text-main">{patient!.assurance || 'Non renseignée'}</p></div><div><p className="text-[10px] font-black uppercase tracking-widest text-text-muted">Motif</p><p className="mt-1 font-bold text-text-main">{patient!.motif_consultation || 'Non renseigné'}</p></div><p className="pt-2 border-t border-border-main text-[11px] font-bold text-text-muted">Contexte chargé depuis le serveur · aucun identifiant patient dans l’URL</p></section>
        <button data-m4a-touch type="button" onClick={() => navigate('/mobile/dashboard?tab=agenda', { replace: true })} className="mt-6 w-full min-h-[54px] rounded-2xl bg-card-bg border border-border-main text-text-main font-black text-xs uppercase tracking-widest">Retour au mobile</button>
      </div>


      {scanPages.length > 0 && (
        <div data-m6b-scan-sheet className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/30 backdrop-blur-sm sm:p-4">
          <section role="dialog" aria-modal="true" aria-labelledby="m6b-scan-title" className="w-full max-w-md rounded-t-[2rem] sm:rounded-[2rem] bg-card-bg border border-border-main shadow-elite p-5 pb-[max(1.25rem,env(safe-area-inset-bottom))] relative">
            <div className="mx-auto mb-4 h-1.5 w-12 rounded-full bg-text-muted/20 sm:hidden" />
            <button data-m6b-touch type="button" aria-label="Annuler le scan" onClick={clearDocumentScan} className="absolute right-4 top-4 min-h-[52px] min-w-[52px] rounded-2xl inline-flex items-center justify-center text-text-muted hover:bg-primary/5"><X size={20} /></button>
            <p className="text-[10px] font-black uppercase tracking-[0.16em] text-primary">Scan document</p>
            <h2 id="m6b-scan-title" className="mt-1 pr-14 text-xl font-black text-text-main">{scanPhase === 'saved' ? 'Document enregistré' : `${scanPages.length} page${scanPages.length > 1 ? 's' : ''} prête${scanPages.length > 1 ? 's' : ''}`}</h2>
            <p className="mt-1 text-xs font-bold text-text-muted">{displayName} · Dossier {patient!.numero_dossier || 'sans numéro'}</p>

            {scanPhase === 'saved' ? (
              <div data-m6b-scan-success className="mt-5">
                <div className="min-h-[72px] rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 flex items-center gap-3 text-emerald-800"><CheckCircle2 size={22} className="shrink-0" /><div><p className="text-sm font-black">Document scanné enregistré</p><p className="mt-0.5 text-xs font-bold">{scanPages.length} page{scanPages.length > 1 ? 's' : ''} · PDF dans le dossier</p></div></div>
                <button data-m6b-touch type="button" onClick={startDocumentScan} className="mt-4 w-full min-h-[54px] rounded-2xl bg-primary text-white inline-flex items-center justify-center gap-2 font-black text-sm"><FileText size={18} /> Scanner un autre document</button>
              </div>
            ) : (
              <>
                {scanPages[scanActiveIndex] && <img data-m6b-scan-preview src={scanPages[scanActiveIndex].previewUrl} alt={`Page ${scanActiveIndex + 1} du document de ${displayName}`} className="mt-4 block w-full max-h-[36dvh] aspect-[4/3] object-contain rounded-2xl border border-border-main bg-slate-950/5" />}
                <div className="mt-3 flex items-center justify-between gap-3"><p className="text-xs font-black text-text-main">Page {scanActiveIndex + 1} sur {scanPages.length}</p><p className="text-[10px] font-bold text-text-muted">8 pages max.</p></div>
                <div data-m6b-scan-thumbnails className="mt-3 flex gap-2 overflow-x-auto pb-1">
                  {scanPages.map((page, index) => <button data-m6b-touch data-m6b-scan-thumbnail key={page.key} type="button" onClick={() => setScanActiveIndex(index)} aria-label={`Voir la page ${index + 1}`} className={`min-w-[56px] min-h-[56px] w-14 h-14 overflow-hidden rounded-xl border-2 ${scanActiveIndex === index ? 'border-primary' : 'border-border-main'}`}><img src={page.previewUrl} alt="" className="w-full h-full object-cover" /></button>)}
                  {scanPages.length < 8 && <button data-m6b-touch data-m6b-add-page type="button" onClick={addDocumentScanPage} className="min-w-[56px] min-h-[56px] w-14 h-14 rounded-xl border border-primary/30 bg-primary/5 text-primary inline-flex items-center justify-center" aria-label="Ajouter une page"><Plus size={20} /></button>}
                </div>
                <button data-m6b-touch type="button" disabled={scanPhase === 'uploading'} onClick={() => removeDocumentScanPage(scanActiveIndex)} className="mt-3 min-h-[52px] w-full rounded-2xl border border-rose-200 bg-rose-50 text-rose-700 inline-flex items-center justify-center gap-2 font-black text-xs disabled:opacity-50"><Trash2 size={16} /> Supprimer cette page</button>
                {scanError && <div role="alert" className="mt-3 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-xs font-bold text-rose-700">{scanError}</div>}
                <button data-m6b-touch type="button" disabled={scanPhase === 'uploading'} onClick={() => void uploadDocumentScan()} className="mt-4 w-full min-h-[56px] rounded-2xl bg-primary text-white inline-flex items-center justify-center gap-2 font-black text-sm disabled:opacity-60">{scanPhase === 'uploading' ? <><Loader2 size={17} className="animate-spin" /> Enregistrement…</> : `Enregistrer le PDF · ${scanPages.length} page${scanPages.length > 1 ? 's' : ''}`}</button>
                <p className="mt-3 text-center text-[10px] font-bold text-text-muted">Aucune page n’est archivée avant confirmation.</p>
              </>
            )}
          </section>
        </div>
      )}

      {photoPreviewUrl && photoFile && (
        <div data-m6a-photo-sheet className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/30 backdrop-blur-sm sm:p-4">
          <section role="dialog" aria-modal="true" aria-labelledby="m6a-photo-title" className="w-full max-w-md rounded-t-[2rem] sm:rounded-[2rem] bg-card-bg border border-border-main shadow-elite p-5 pb-[max(1.25rem,env(safe-area-inset-bottom))] relative">
            <div className="mx-auto mb-4 h-1.5 w-12 rounded-full bg-text-muted/20 sm:hidden" />
            <button data-m6a-touch type="button" aria-label="Fermer la photo clinique" onClick={clearClinicalPhoto} className="absolute right-4 top-4 min-h-[52px] min-w-[52px] rounded-2xl inline-flex items-center justify-center text-text-muted hover:bg-primary/5"><X size={20} /></button>
            <p className="text-[10px] font-black uppercase tracking-[0.16em] text-primary">Photo clinique</p>
            <h2 id="m6a-photo-title" className="mt-1 pr-14 text-xl font-black text-text-main">{photoPhase === 'saved' ? 'Photo enregistrée' : 'Nouvelle photo clinique'}</h2>
            <p className="mt-1 text-xs font-bold text-text-muted">{displayName} · Dossier {patient!.numero_dossier || 'sans numéro'}</p>
            <img data-m6a-photo-preview src={photoPreviewUrl} alt={`Aperçu de la photo clinique de ${displayName}`} className="mt-4 block w-full max-h-[42dvh] aspect-[4/3] object-contain rounded-2xl border border-border-main bg-slate-950/5" />

            {photoPhase === 'saved' ? (
              <div data-m6a-photo-success className="mt-4">
                <div className="min-h-[52px] rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 flex items-center gap-3 text-emerald-800"><CheckCircle2 size={20} className="shrink-0" /><p className="text-sm font-black">Photo clinique enregistrée dans le dossier</p></div>
                <button data-m6a-touch type="button" onClick={() => { clearClinicalPhoto(); setTimeout(() => photoInputRef.current?.click(), 0); }} className="mt-3 w-full min-h-[54px] rounded-2xl bg-primary text-white inline-flex items-center justify-center gap-2 font-black text-sm"><Camera size={18} /> Prendre une autre photo</button>
              </div>
            ) : (
              <>
                <p className="mt-3 text-[11px] font-bold text-text-muted">La photo n’est pas enregistrée avant votre confirmation.</p>
                {photoError && <div role="alert" className="mt-3 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-xs font-bold text-rose-700">{photoError}</div>}
                <div className="mt-4 grid grid-cols-2 gap-3">
                  <button data-m6a-touch type="button" disabled={photoPhase === 'uploading'} onClick={openClinicalPhotoPicker} className="min-h-[54px] rounded-2xl bg-card-bg border border-border-main text-text-main inline-flex items-center justify-center gap-2 font-black text-sm disabled:opacity-50"><RefreshCcw size={17} /> Reprendre</button>
                  <button data-m6a-touch type="button" disabled={photoPhase === 'uploading'} onClick={() => void uploadClinicalPhoto()} className="min-h-[54px] rounded-2xl bg-primary text-white inline-flex items-center justify-center gap-2 font-black text-sm disabled:opacity-60">{photoPhase === 'uploading' ? <><Loader2 size={17} className="animate-spin" /> Enregistrement…</> : 'Enregistrer'}</button>
                </div>
              </>
            )}
          </section>
        </div>
      )}
    </div>
  );
};
