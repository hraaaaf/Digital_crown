import { useState, useEffect, useCallback, useRef } from 'react';
import toast from 'react-hot-toast';
import { MobileStorage } from '../../../../services/zka/MobileStorage';
import { mobileFetch } from '../../../../services/zka/mobileFetch';
import { CryptoService } from '../../../../services/zka/CryptoService';
import { fetchLabJobs, patchLabJobStatus } from '../../../../services/labJobService';
import type { LabJob } from '../../../../types/labJob';
import { formatLabJobMessage } from '../../../../services/whatsappService';
import type { Tab, SyncStatus, Snapshot, Appointment, ApptStatus } from '../types';
import { LabJobStatus } from '../../../../types/labJob';

function resolveApiBaseUrl(stored: string): string {
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') return stored;
  if (stored.includes('localhost') || stored.includes('127.0.0.1')) {
    return `${window.location.protocol}//${hostname}:8005`;
  }
  return stored;
}


function isQueueableNetworkError(error: unknown): boolean {
  if (error instanceof TypeError) return true;
  const name = error && typeof error === 'object' && 'name' in error
    ? String((error as { name?: unknown }).name ?? '')
    : '';
  return name === 'AbortError' || name === 'TimeoutError';
}

export function useMobileDashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('agenda');
  const [syncStatus, setSyncStatus] = useState<SyncStatus>('idle');
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [queuedActionsCount, setQueuedActionsCount] = useState(0);
  const [now, setNow] = useState(new Date());
  const [labJobs, setLabJobs] = useState<LabJob[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>(() => new Date().toISOString().split('T')[0]);
  const [patients, setPatients] = useState<{id: number, name: string, phone: string | null}[]>([]);
  const credsRef = useRef<{ access_token: string; api_base_url: string; masterKey: string } | null>(null);
  const mainRef = useRef<HTMLElement>(null);

  // Signature au Fauteuil states
  const [sigPatientId, setSigPatientId] = useState<number | null>(null);
  const [sigPatientName, setSigPatientName] = useState<string>('');
  const [sigDocs, setSigDocs] = useState<any[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<number | null>(null);
  const [isSigning, setIsSigning] = useState(false);
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);

  // WhatsApp states
  const [whatsappApt, setWhatsappApt] = useState<Appointment | null>(null);
  const [customMessage, setCustomMessage] = useState<string>('');
  const [whatsappTemplate, setWhatsappTemplate] = useState<'rappel' | 'confirmation'>('rappel');

  useEffect(() => {
    if (mainRef.current) {
      mainRef.current.scrollTo({ top: 0, behavior: 'instant' as any });
    }
  }, [activeTab]);

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 30000);
    // Pré-charger le token mobile dans localStorage pour que l'intercepteur api le retrouve
    MobileStorage.getCredentials().then(creds => {
      if (creds?.access_token) {
        try { localStorage.setItem('token', creds.access_token); } catch { /* ignore */ }
      }
    });
    return () => clearInterval(t);
  }, []);

  const fetchSnapshot = useCallback(async () => {
    try {
      setSyncStatus('loading');
      const creds = await MobileStorage.getCredentials();
      if (!creds) throw new Error('Non appairé');
      credsRef.current = creds;

      // Sync mobile JWT into localStorage so the standard api interceptor
      // (used by CrownBotChat and other shared components) sends Authorization headers.
      try { localStorage.setItem('token', creds.access_token); } catch { /* ignore */ }

      const res = await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/snapshot?target_date=${selectedDate}`, {
        signal: AbortSignal.timeout(8000),
      });
      if (!res.ok) {
        const detail = (await res.json().catch(() => ({}))).detail ?? `Erreur ${res.status}`;
        if (res.status === 401 || res.status === 403) {
          setError('Session mobile expirée ou révoquée');
          setSyncStatus('error');
          return;
        }
        setError(detail);
        setSyncStatus('error');
        return;
      }

      const rawRes = await res.json();
      const data: Snapshot = rawRes.payload 
        ? await CryptoService.decryptPayload(rawRes.payload, creds.masterKey) 
        : rawRes;

      setSnapshot(data);
      await MobileStorage.saveLastSnapshot(data);
      setError(null);
      setSyncStatus('success');
    } catch (err) {
      console.error('[MobileDashboard] fetchSnapshot failed:', err);
      const notPaired = err instanceof Error && err.message === 'Non appairé';
      if (notPaired) {
        setError('Session mobile expirée ou révoquée');
        setSyncStatus('error');
        return;
      }
      if (!isQueueableNetworkError(err)) {
        setError(err instanceof Error ? err.message : 'Erreur de synchronisation mobile');
        setSyncStatus('error');
        return;
      }
      const cached = await MobileStorage.getLastSnapshot();
      if (cached) {
        setSnapshot(cached);
        setSyncStatus('error');
        setError('Hors réseau — données en cache');
      } else {
        setError('Impossible de joindre le cabinet');
        setSyncStatus('error');
      }
    }
  }, [selectedDate]);

  const fetchPatients = useCallback(async () => {
    try {
      const creds = credsRef.current || await MobileStorage.getCredentials();
      if (!creds) return;
      const res = await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/patients`, {
        headers: { Authorization: `Bearer ${creds.access_token}` },
        signal: AbortSignal.timeout(5000),
      });
      if (res.ok) {
        const rawRes = await res.json();
        const data = rawRes.payload 
          ? await CryptoService.decryptPayload(rawRes.payload, creds.masterKey)
          : rawRes;
        setPatients(data.data || data);
      }
    } catch { /* silent */ }
  }, []);

  const syncQueue = useCallback(async () => {
    if (!navigator.onLine) return;
    const creds = await MobileStorage.getCredentials();
    if (!creds) return;
    
    const queue = await MobileStorage.getActionQueue();
    if (queue.length === 0) {
      setQueuedActionsCount(0);
      return;
    }

    setSyncStatus('loading');
    let hasError = false;

    for (const action of queue) {
      try {
        const res = await mobileFetch(action.url, {
          method: action.method,
          headers: {
            'Content-Type': 'application/json',
            'X-Mobile-Action-Id': action.id,
          },
          body: action.body ? JSON.stringify(action.body) : undefined,
        });
        if (!res.ok) {
          hasError = true;
          toast.error(`Synchronisation refusée (${res.status})`);
          break;
        }
        await MobileStorage.removeActionFromQueue(action.id);
      } catch {
        hasError = true;
        break;
      }
    }

    const remaining = await MobileStorage.getActionQueue();
    setQueuedActionsCount(remaining.length);
    if (!hasError) {
      toast.success('Données synchronisées');
      fetchSnapshot();
    }
  }, [fetchSnapshot]);

  useEffect(() => {
    MobileStorage.getActionQueue().then(q => setQueuedActionsCount(q.length));
    const on = () => { setIsOnline(true); syncQueue(); };
    const off = () => setIsOnline(false);
    window.addEventListener('online', on);
    window.addEventListener('offline', off);
    return () => { window.removeEventListener('online', on); window.removeEventListener('offline', off); };
  }, [syncQueue]);

  useEffect(() => { 
    MobileStorage.getLastSnapshot().then(c => { if (c) { setSnapshot(c); setSyncStatus('success'); } }); 
    fetchSnapshot(); 
    fetchPatients(); 
    fetchLabJobs().then(setLabJobs).catch(err => console.error(err)); 
  }, [fetchSnapshot, fetchPatients]);

  const handleStatusChange = async (id: number, status: ApptStatus) => {
    const creds = credsRef.current || await MobileStorage.getCredentials();
    if (!creds) return;
    const actionId = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${id}-status`;
    try {
      const res = await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/appointments/${id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', 'X-Mobile-Action-Id': actionId },
        body: JSON.stringify({ status }),
      });
      if (!res.ok) {
        toast.error(`Mise à jour refusée (${res.status})`);
        return;
      }
      setSnapshot(prev => prev ? {
        ...prev,
        appointments: prev.appointments.map(a => a.id === id ? { ...a, status } : a),
      } : prev);
    } catch (err) {
      if (!isQueueableNetworkError(err)) {
        toast.error(err instanceof Error && err.message === 'Non appairé'
          ? 'Session mobile expirée ou révoquée'
          : 'Erreur lors de la mise à jour');
        return;
      }
      await MobileStorage.enqueueAction(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/appointments/${id}/status`, 'PATCH', { status }, actionId);
      setQueuedActionsCount((await MobileStorage.getActionQueue()).length);
      toast('Mise à jour mise en attente (hors ligne)', { icon: '🔄' });
      setSnapshot(prev => prev ? {
        ...prev,
        appointments: prev.appointments.map(a => a.id === id ? { ...a, status } : a),
      } : prev);
    }
  };

  const handleDeleteAppt = async (id: number) => {
    if (!window.confirm("Supprimer ce rendez-vous ?")) return;
    const creds = credsRef.current || await MobileStorage.getCredentials();
    if (!creds) return;
    const actionId = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${id}-delete`;
    try {
      const res = await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/appointments/${id}`, {
        method: 'DELETE',
        headers: { 'X-Mobile-Action-Id': actionId },
      });
      if (!res.ok) {
        toast.error(`Suppression refusée (${res.status})`);
        return;
      }
      fetchSnapshot();
      toast.success("Rendez-vous supprimé");
    } catch (err) {
      if (!isQueueableNetworkError(err)) {
        toast.error(err instanceof Error && err.message === 'Non appairé'
          ? 'Session mobile expirée ou révoquée'
          : 'Erreur lors de la suppression');
        return;
      }
      await MobileStorage.enqueueAction(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/appointments/${id}`, 'DELETE', undefined, actionId);
      setQueuedActionsCount((await MobileStorage.getActionQueue()).length);
      toast('Suppression mise en attente (hors ligne)', { icon: '🔄' });
      setSnapshot(prev => prev ? {
        ...prev,
        appointments: prev.appointments.filter(a => a.id !== id),
      } : prev);
    }
  };

  const handleRescheduleAppt = async (id: number, newDate: string, newTime: string) => {
    const creds = credsRef.current || await MobileStorage.getCredentials();
    if (!creds) return;
    try {
      const res = await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/appointments/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ datetime_start: `${newDate}T${newTime}:00` }),
      });
      if (!res.ok) {
        toast.error('Déplacement mobile indisponible — utilisez l’agenda principal.');
        return;
      }
      fetchSnapshot();
      toast.success("Rendez-vous déplacé");
    } catch {
      // La route de déplacement mobile n'est pas encore canonique (M6.3) :
      // ne jamais mettre en queue une opération que le serveur ne sait pas rejouer.
      toast.error('Déplacement impossible hors ligne.');
    }
  };

  const openWhatsApp = (phone: string | null, msg: string) => {
    if (!phone) return;
    window.open(`https://wa.me/${phone.replace(/\D/g, '')}?text=${encodeURIComponent(msg)}`, '_blank');
  };

  const openApptWhatsApp = (apt: Appointment) => {
    setWhatsappApt(apt);
    setWhatsappTemplate('rappel');
  };

  useEffect(() => {
    if (!whatsappApt) return;
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const dateFormatted = tomorrow.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });
    
    const motifLower = (whatsappApt.motif || "").toLowerCase();
    let motifStr = "votre consultation";
    if (motifLower) {
      if (motifLower.includes("empreinte") || motifLower.includes("taille") || motifLower.includes("armature") || motifLower.includes("biscuit") || motifLower.includes("prothèse")) {
        motifStr = `l'essayage / l'étape ${motifLower}`;
      } else {
        motifStr = `votre séance de ${motifLower}`;
      }
    }
    
    if (whatsappTemplate === 'rappel') {
      setCustomMessage(`Bonjour, n'oubliez pas votre rdv de demain à ${whatsappApt.time} pour ${motifStr}.`);
    } else {
      setCustomMessage(`Bonjour ${whatsappApt.patient_name}, nous vous confirmons votre rendez-vous du ${dateFormatted} à ${whatsappApt.time} pour ${whatsappApt.motif || 'votre consultation'}.`);
    }
  }, [whatsappApt, whatsappTemplate]);

  const handleSendWhatsApp = () => {
    if (!whatsappApt || !whatsappApt.phone) return;
    const phoneClean = whatsappApt.phone.replace(/\D/g, '');
    window.open(`https://wa.me/${phoneClean}?text=${encodeURIComponent(customMessage)}`, '_blank');
    setWhatsappApt(null);
  };

  const handleWhatsAppSend = async (job: LabJob) => {
    const plainText = formatLabJobMessage(job);
    const whatsappUri = `whatsapp://send?phone=${''}&text=${encodeURIComponent(plainText)}`;

    try {
      await navigator.clipboard.writeText(plainText);
    } catch (c) {
      console.warn('Échec silencieux du presse‑papier', c);
    }

    try {
      window.location.href = whatsappUri;
      await patchLabJobStatus(job.id, { status: LabJobStatus.SENT });
      setLabJobs(prev => prev.map(j => j.id === job.id ? { ...j, status: LabJobStatus.SENT } : j));
    } catch (e) {
      console.error('Échec WhatsApp ou persistance Labo', e);
      toast.error('WhatsApp ouvert, mais statut Labo non confirmé.');
    }
  };

  const fetchSignatureDocs = useCallback(async (patientId: number) => {
    setIsLoadingDocs(true);
    try {
      const creds = credsRef.current || await MobileStorage.getCredentials();
      if (!creds) return;
      const res = await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/patients/${patientId}/documents`, {
        headers: { Authorization: `Bearer ${creds.access_token}` },
      });
      if (res.ok) {
        const rawRes = await res.json();
        const data = rawRes.payload 
          ? await CryptoService.decryptPayload(rawRes.payload, creds.masterKey)
          : rawRes;
        const docs = data.data || data;
        setSigDocs(docs);
        if (docs.length > 0) {
          const unsigned = docs.find((d: any) => !d.signed);
          setSelectedDocId(unsigned ? unsigned.id : docs[0].id);
        } else {
          setSelectedDocId(null);
        }
      }
    } catch (e) {
      toast.error("Erreur lors du chargement des documents");
    } finally {
      setIsLoadingDocs(false);
    }
  }, []);

  const handleOpenSignature = (patientId: number, patientName: string) => {
    setSigPatientId(patientId);
    setSigPatientName(patientName);
    setSigDocs([]);
    setSelectedDocId(null);
    setIsSigning(false);
    fetchSignatureDocs(patientId);
  };

  const handleSaveSignature = async (dataUrl: string) => {
    if (!selectedDocId) return toast.error("Veuillez sélectionner un document.");
    setIsSigning(true);
    try {
      const creds = credsRef.current || await MobileStorage.getCredentials();
      if (!creds) return;
      const res = await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/documents/${selectedDocId}/sign`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${creds.access_token}`
        },
        body: JSON.stringify({ signature_base64: dataUrl })
      });
      if (res.ok) {
        toast.success("Document signé et PDF régénéré !");
        fetchSignatureDocs(sigPatientId!);
      } else {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? "Erreur lors de la signature");
      }
    } catch (e: any) {
      toast.error(`Erreur : ${e.message}`);
    } finally {
      setIsSigning(false);
    }
  };

  const handleLogout = async () => {
    await MobileStorage.clearAll();
    window.location.replace('/mobile/onboarding');
  };

  const handleExportPDF = async () => {
    const creds = credsRef.current || await MobileStorage.getCredentials();
    if (!creds) return;
    try {
      const d = new Date(selectedDate);
      const res = await mobileFetch(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/accounting/export-pdf?year=${d.getFullYear()}&month=${d.getMonth() + 1}`, {
        headers: { Authorization: `Bearer ${creds.access_token}` },
      });
      if (!res.ok) throw new Error('Erreur export');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      
      if (navigator.share && navigator.canShare) {
        const file = new File([blob], `Compta_${d.getFullYear()}_${d.getMonth() + 1}.pdf`, { type: 'application/pdf' });
        if (navigator.canShare({ files: [file] })) {
          await navigator.share({
            files: [file],
            title: `Comptabilité ${d.getMonth() + 1}/${d.getFullYear()}`,
          });
          return;
        }
      }

      const a = document.createElement('a');
      a.href = url;
      a.download = `Compta_${d.getFullYear()}_${d.getMonth() + 1}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert("Erreur lors de l'export PDF");
    }
  };

  return {
    state: {
      activeTab,
      syncStatus,
      snapshot,
      error,
      isOnline,
      now,
      labJobs,
      selectedDate,
      patients,
      sigPatientId,
      sigPatientName,
      sigDocs,
      selectedDocId,
      isSigning,
      isLoadingDocs,
      whatsappApt,
      customMessage,
      whatsappTemplate,
      queuedActionsCount,
    },
    actions: {
      setActiveTab,
      setSelectedDate,
      fetchSnapshot,
      fetchPatients,
      handleStatusChange,
      handleDeleteAppt,
      handleRescheduleAppt,
      openWhatsApp,
      openApptWhatsApp,
      handleSendWhatsApp,
      handleWhatsAppSend,
      handleOpenSignature,
      handleSaveSignature,
      handleLogout,
      handleExportPDF,
      setSigPatientId,
      setSelectedDocId,
      setWhatsappApt,
      setWhatsappTemplate,
      setCustomMessage,
    },
    refs: {
      mainRef,
    }
  };
}
