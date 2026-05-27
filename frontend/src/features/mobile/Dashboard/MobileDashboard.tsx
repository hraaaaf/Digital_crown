import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Calendar, TrendingUp, ShieldCheck, Phone, MessageSquare,
  Clock, Wallet, ArrowUpRight, ArrowDownRight, RefreshCw,
  Wifi, WifiOff, LogOut, Users, AlertTriangle, CheckCircle2,
  PlayCircle, XCircle, ChevronRight, ChevronLeft, Download, Stethoscope, FileText, Trash2, Plus
} from 'lucide-react';
import { AreaChart, Area, XAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { MobileStorage } from '../../../services/zka/MobileStorage';
import { cn } from '../../../utils/cn';
import Logo from '../../../assets/logo.png';
import toast from 'react-hot-toast';

type Tab = 'agenda' | 'finance' | 'securite';
type SyncStatus = 'idle' | 'loading' | 'success' | 'error';
type ApptStatus = 'PLANIFIE' | 'EN_COURS' | 'TERMINE' | 'ANNULE';

interface WeekDay { date: string; amount: number }
interface Appointment {
  id: number;
  patient_id?: number | null;
  time: string;
  patient_name: string;
  date?: string;
  phone: string | null;
  motif: string;
  status: ApptStatus | null;
  duration_minutes: number;
}
interface Snapshot {
  generated_at: string;
  role?: string;
  is_superadmin?: boolean;
  appointments: Appointment[];
  finance: {
    today_revenue: number; month_revenue: number;
    month_variation: number | null; appointments_count: number;
    weekly_revenue: WeekDay[]; total_patients: number; total_debt: number;
  };
  debtors: { id: number; name: string; amount: number; phone: string | null }[];
}

// ── HELPERS ──────────────────────────────────────────────────────────────────

function greeting(): string {
  const h = new Date().getHours();
  if (h < 12) return 'Bonjour';
  if (h < 18) return 'Bon après-midi';
  return 'Bonsoir';
}

function fmt(n: number) { return new Intl.NumberFormat('fr-FR').format(Math.round(n)); }

function dayLabel(dateStr: string, idx: number, total: number): string {
  if (idx === total - 1) return 'Auj.';
  const d = new Date(dateStr);
  return ['D', 'L', 'M', 'M', 'J', 'V', 'S'][d.getDay()];
}

const STATUS_META: Record<ApptStatus, { label: string; className: string; icon: React.ReactNode }> = {
  PLANIFIE: {
    label: 'Planifié',
    className: 'bg-slate-100 text-slate-600 border-slate-200',
    icon: <Clock size={11} />,
  },
  EN_COURS: {
    label: 'En cours',
    className: 'bg-primary/10 text-primary border-primary/20 animate-pulse',
    icon: <PlayCircle size={11} />,
  },
  TERMINE: {
    label: 'Terminé',
    className: 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20',
    icon: <CheckCircle2 size={11} />,
  },
  ANNULE: {
    label: 'Annulé',
    className: 'bg-rose-500/10 text-rose-500 border-rose-500/20',
    icon: <XCircle size={11} />,
  },
};

// ── APPOINTMENT CARD ──────────────────────────────────────────────────────────

function ApptCard({
  apt, onStatusChange, onWhatsApp, onDelete, onSign
}: {
  apt: Appointment;
  onStatusChange: (id: number, status: ApptStatus) => void;
  onWhatsApp: (apt: Appointment) => void;
  onDelete?: (id: number) => void;
  onSign?: (patientId: number, patientName: string) => void;
}) {
  const meta = STATUS_META[apt.status as ApptStatus] ?? STATUS_META.PLANIFIE;
  const [expanded, setExpanded] = useState(false);

  const nextStatuses: ApptStatus[] = apt.status === 'PLANIFIE'
    ? ['EN_COURS', 'ANNULE']
    : apt.status === 'EN_COURS'
    ? ['TERMINE', 'ANNULE']
    : [];

  return (
    <div className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[24px] overflow-hidden shadow-elite transition-all duration-300">
      <button
        className="w-full flex items-center gap-4 p-5 text-left hover:bg-primary/[0.02] transition-colors"
        onClick={() => setExpanded(e => !e)}
      >
        {/* Time bubble */}
        <div className="w-14 h-14 bg-primary/5 border border-primary/10 rounded-[16px] flex flex-col items-center justify-center shrink-0">
          <Stethoscope size={12} className="text-primary mb-0.5" />
          <span className="text-[11px] font-black text-primary leading-none">{apt.time}</span>
        </div>

        <div className="flex-1 min-w-0">
          <p className="font-black text-text-main font-outfit truncate leading-tight">{apt.patient_name}</p>
          <p className="text-[10px] text-text-muted font-bold mt-0.5 uppercase tracking-wider truncate">
            {apt.motif} · {apt.duration_minutes}min
          </p>
        </div>

        <div className="flex flex-col items-end gap-2 shrink-0">
          <span className={cn(
            'flex items-center gap-1 px-2 py-1 rounded-lg border text-[9px] font-black uppercase tracking-widest',
            meta.className
          )}>
            {meta.icon} {meta.label}
          </span>
          <ChevronRight size={14} className={cn('text-text-muted transition-transform', expanded ? 'rotate-90' : '')} />
        </div>
      </button>

      {expanded && (
        <div className="px-5 pb-5 space-y-3 border-t border-border-main pt-4">
          {nextStatuses.length > 0 && (
            <div className="flex gap-2">
              {nextStatuses.map(s => {
                const sm = STATUS_META[s];
                return (
                  <button
                    key={s}
                    onClick={() => onStatusChange(apt.id, s)}
                    className={cn(
                      'flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-[16px] border text-[10px] font-black uppercase tracking-widest transition-all active:scale-95',
                      sm.className
                    )}
                  >
                    {sm.icon} {sm.label}
                  </button>
                );
              })}
              {onDelete && (
                <button
                  onClick={() => onDelete(apt.id)}
                  className="flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-[16px] border text-[10px] font-black uppercase tracking-widest transition-all active:scale-95 bg-rose-500/10 text-rose-500 border-rose-500/20"
                >
                  <Trash2 size={12} /> Supprimer
                </button>
              )}
            </div>
          )}

          <div className="flex flex-col gap-2">
            {apt.phone && (
              <div className="flex gap-2">
                <a
                  href={`tel:${apt.phone}`}
                  className="flex-1 flex items-center justify-center gap-1.5 py-2.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 rounded-[16px] text-[10px] font-black uppercase tracking-widest"
                >
                  <Phone size={12} /> Appeler
                </a>
                <button
                  onClick={() => onWhatsApp(apt)}
                  className="flex-1 flex items-center justify-center gap-1.5 py-2.5 bg-primary/5 border border-primary/10 text-primary rounded-[16px] text-[10px] font-black uppercase tracking-widest"
                >
                  <MessageSquare size={12} /> WhatsApp
                </button>
              </div>
            )}

            {apt.patient_id && onSign && (
              <button
                onClick={() => onSign(apt.patient_id!, apt.patient_name)}
                className="w-full flex items-center justify-center gap-1.5 py-2.5 bg-indigo-500/10 border border-indigo-500/20 text-indigo-600 rounded-[16px] text-[10px] font-black uppercase tracking-widest transition-all active:scale-95"
              >
                <FileText size={12} /> Signature au Fauteuil
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ── SIGNATURE PAD ───────────────────────────────────────────────────────────

interface SignaturePadProps {
  onSave: (dataUrl: string) => void;
  onCancel: () => void;
}

function SignaturePad({ onSave, onCancel }: SignaturePadProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.strokeStyle = '#1e1b4b'; // Deep Indigo
    ctx.lineWidth = 3.5;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
  }, []);

  const startDrawing = (e: React.MouseEvent | React.TouchEvent) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const rect = canvas.getBoundingClientRect();
    const x = ('touches' in e) ? e.touches[0].clientX - rect.left : e.clientX - rect.left;
    const y = ('touches' in e) ? e.touches[0].clientY - rect.top : e.clientY - rect.top;

    ctx.beginPath();
    ctx.moveTo(x, y);
    setIsDrawing(true);
  };

  const draw = (e: React.MouseEvent | React.TouchEvent) => {
    if (!isDrawing) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const rect = canvas.getBoundingClientRect();
    const x = ('touches' in e) ? e.touches[0].clientX - rect.left : e.clientX - rect.left;
    const y = ('touches' in e) ? e.touches[0].clientY - rect.top : e.clientY - rect.top;

    ctx.lineTo(x, y);
    ctx.stroke();
  };

  const stopDrawing = () => {
    setIsDrawing(false);
  };

  const clear = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  };

  const save = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    onSave(canvas.toDataURL());
  };

  return (
    <div className="space-y-4">
      <div className="border border-border-main rounded-2xl bg-white overflow-hidden shadow-inner relative">
        <canvas
          ref={canvasRef}
          width={300}
          height={180}
          className="w-full h-[180px] bg-slate-50 touch-none cursor-crosshair"
          onMouseDown={startDrawing}
          onMouseMove={draw}
          onMouseUp={stopDrawing}
          onMouseLeave={stopDrawing}
          onTouchStart={startDrawing}
          onTouchMove={draw}
          onTouchEnd={stopDrawing}
        />
        <div className="absolute bottom-2 left-4 right-4 pointer-events-none text-center">
          <p className="text-[9px] font-black uppercase tracking-widest text-slate-400">Signez avec votre doigt ici</p>
        </div>
      </div>
      <div className="flex gap-2">
        <button onClick={clear} className="flex-1 py-3 border border-border-main text-xs font-bold rounded-xl active:scale-95 transition-transform text-slate-600 bg-white">Effacer</button>
        <button onClick={save} className="flex-1 py-3 bg-primary text-white text-xs font-bold rounded-xl active:scale-95 transition-transform shadow-md">Enregistrer</button>
      </div>
    </div>
  );
}

// ── SKELETON ──────────────────────────────────────────────────────────────────

function Skeleton({ className = '' }: { className?: string }) {
  return <div className={cn('bg-border-main/40 rounded-[16px] animate-pulse', className)} />;
}

// ── MAIN COMPONENT ────────────────────────────────────────────────────────────

export const MobileDashboard = () => {
  const [activeTab, setActiveTab] = useState<Tab>('agenda');
  const [syncStatus, setSyncStatus] = useState<SyncStatus>('idle');
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [now, setNow] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<string>(() => new Date().toISOString().split('T')[0]);
  const [patients, setPatients] = useState<{id: number, name: string, phone: string | null}[]>([]);
  const credsRef = useRef<{ access_token: string; api_base_url: string } | null>(null);
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
    // Forcer le thème clair pour l'interface mobile (Désactive complètement le dark mode)
    document.documentElement.dataset.theme = '';
    document.body.dataset.theme = '';
    
    const t = setInterval(() => setNow(new Date()), 30000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    const on = () => setIsOnline(true);
    const off = () => setIsOnline(false);
    window.addEventListener('online', on);
    window.addEventListener('offline', off);
    return () => { window.removeEventListener('online', on); window.removeEventListener('offline', off); };
  }, []);

  const fetchSnapshot = useCallback(async () => {
    try {
      setSyncStatus('loading');
      const creds = await MobileStorage.getCredentials();
      if (!creds) throw new Error('Non appairé');
      credsRef.current = creds;

      const res = await fetch(`${creds.api_base_url}/api/mobile/snapshot?target_date=${selectedDate}`, {
        headers: { Authorization: `Bearer ${creds.access_token}` },
        signal: AbortSignal.timeout(8000),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail ?? `Erreur ${res.status}`);

      const data: Snapshot = await res.json();
      setSnapshot(data);
      await MobileStorage.saveLastSnapshot(data);
      setError(null);
      setSyncStatus('success');
    } catch {
      const cached = await MobileStorage.getLastSnapshot();
      if (cached) { setSnapshot(cached); setSyncStatus('error'); setError('Hors réseau — données en cache'); }
      else { setError('Impossible de joindre le cabinet'); setSyncStatus('error'); }
    }
  }, [selectedDate]);

  const fetchPatients = useCallback(async () => {
    try {
      const creds = credsRef.current || await MobileStorage.getCredentials();
      if (!creds) return;
      const res = await fetch(`${creds.api_base_url}/api/mobile/patients`, {
        headers: { Authorization: `Bearer ${creds.access_token}` },
        signal: AbortSignal.timeout(5000),
      });
      if (res.ok) setPatients(await res.json());
    } catch { /* silent */ }
  }, []);

  useEffect(() => {
    MobileStorage.getLastSnapshot().then(c => { if (c) { setSnapshot(c); setSyncStatus('success'); } });
    fetchSnapshot();
    fetchPatients();
  }, [fetchSnapshot, fetchPatients]);

  const handleStatusChange = async (id: number, status: ApptStatus) => {
    const creds = credsRef.current || await MobileStorage.getCredentials();
    if (!creds) return;
    try {
      await fetch(`${creds.api_base_url}/api/mobile/appointments/${id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${creds.access_token}` },
        body: JSON.stringify({ status }),
      });
      setSnapshot(prev => prev ? {
        ...prev,
        appointments: prev.appointments.map(a => a.id === id ? { ...a, status } : a),
      } : prev);
    } catch { /* silent */ }
  };

  const handleDeleteAppt = async (id: number) => {
    if (!window.confirm("Supprimer ce rendez-vous ?")) return;
    const creds = credsRef.current || await MobileStorage.getCredentials();
    if (!creds) return;
    try {
      await fetch(`${creds.api_base_url}/api/mobile/appointments/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${creds.access_token}` }
      });
      fetchSnapshot();
      toast.success("Rendez-vous supprimé");
    } catch (err) {
      toast.error("Erreur de suppression");
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
    
    // Simplification : si le motif contient "prothèse", "empreinte", "taille", "armature" etc.
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

  const fetchSignatureDocs = useCallback(async (patientId: number) => {
    setIsLoadingDocs(true);
    try {
      const creds = credsRef.current || await MobileStorage.getCredentials();
      if (!creds) return;
      const res = await fetch(`${creds.api_base_url}/api/mobile/patients/${patientId}/documents`, {
        headers: { Authorization: `Bearer ${creds.access_token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setSigDocs(data);
        if (data.length > 0) {
          const unsigned = data.find((d: any) => !d.signed);
          setSelectedDocId(unsigned ? unsigned.id : data[0].id);
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
      const res = await fetch(`${creds.api_base_url}/api/mobile/documents/${selectedDocId}/sign`, {
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
    if (window.confirm('Révoquer cet accès ? La clé sera supprimée de ce téléphone.')) {
      await MobileStorage.clearAll();
      window.location.replace('/mobile/onboarding');
    }
  };

  const handleExportPDF = async () => {
    const creds = credsRef.current || await MobileStorage.getCredentials();
    if (!creds) return;
    try {
      const d = new Date(selectedDate);
      const res = await fetch(`${creds.api_base_url}/api/mobile/accounting/export-pdf?year=${d.getFullYear()}&month=${d.getMonth() + 1}`, {
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

  const f = snapshot?.finance;
  const todayStr = new Date(selectedDate).toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });
  const timeStr = now.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });

  const termineCount = snapshot?.appointments.filter(a => a.status === 'TERMINE').length ?? 0;
  const totalCount = snapshot?.appointments.length ?? 0;

  // ── AGENDA VIEW ──────────────────────────────────────────────────────────────
  const [showAddModal, setShowAddModal] = useState(false);
  const [newApt, setNewApt] = useState({ patient_name: '', motif: 'Consultation', isCustomMotif: false, time: '09:00', duration_minutes: 30 });
  const [isCreatingPatient, setIsCreatingPatient] = useState(false);
  const [newPt, setNewPt] = useState({ nom: '', prenom: '', telephone: '' });

  const handleCreatePatient = async () => {
    if (!newPt.nom || !newPt.prenom) return toast.error("Nom et prénom requis");
    const creds = credsRef.current || await MobileStorage.getCredentials();
    if (!creds) return;
    try {
      const res = await fetch(`${creds.api_base_url}/api/mobile/patients`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${creds.access_token}` },
        body: JSON.stringify({ nom: newPt.nom, prenom: newPt.prenom, telephone: newPt.telephone, sexe: 'M' })
      });
      if (!res.ok) throw new Error("Erreur serveur");
      const created = await res.json();
      // Mettre à jour la liste des patients locaux
      setPatients(prev => [...prev, created]);
      setNewApt({...newApt, patient_name: created.name});
      setIsCreatingPatient(false);
      setNewPt({ nom: '', prenom: '', telephone: '' });
      toast.success("Patient ajouté !");
    } catch (e) {
      toast.error("Erreur d'ajout du patient");
    }
  };

  const handleAddAppt = async () => {
    const creds = credsRef.current || await MobileStorage.getCredentials();
    if (!creds) return;
    try {
      await fetch(`${creds.api_base_url}/api/mobile/appointments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${creds.access_token}` },
        body: JSON.stringify({
          datetime_start: `${selectedDate}T${newApt.time}:00`,
          patient_name: newApt.patient_name,
          motif: newApt.motif,
          duration_minutes: newApt.duration_minutes
        })
      });
      fetchSnapshot();
      setShowAddModal(false);
      toast.success("Rendez-vous ajouté");
    } catch (err) {
      toast.error("Erreur d'ajout");
    }
  };

  const renderAgendaView = () => {
    const dayAppointments = snapshot?.appointments.filter(a => !a.date || a.date === selectedDate) || [];
    return (
    <div className="space-y-4">
      {/* Progress bar */}
      {totalCount > 0 && (
        <div className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[20px] p-4 shadow-elite">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-black text-text-muted uppercase tracking-widest flex items-center gap-1.5">
              <Clock size={12} /> Progression du jour
            </span>
            <span className="text-[10px] font-black text-primary">{termineCount}/{totalCount} terminés</span>
          </div>
          <div className="h-1.5 bg-border-main rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary to-secondary rounded-full transition-all duration-700"
              style={{ width: `${(termineCount / totalCount) * 100}%` }}
            />
          </div>
        </div>
      )}

      {syncStatus === 'loading' && !snapshot ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => <Skeleton key={i} className="h-24" />)}
        </div>
      ) : !dayAppointments.length ? (
        <div className="bg-card border border-border-main rounded-[24px] py-20 text-center shadow-elite relative overflow-hidden">
          <div className="w-16 h-16 bg-primary/5 border border-primary/10 rounded-[20px] flex items-center justify-center mx-auto mb-4 text-primary">
            <Calendar size={32} />
          </div>
          <h4 className="font-black text-primary font-outfit">Aucun RDV aujourd'hui</h4>
          <p className="text-text-muted text-[11px] font-medium mt-1">L'agenda est libre.</p>
        </div>
      ) : (
        dayAppointments.map(apt => (
          <ApptCard key={apt.id} apt={apt} onStatusChange={handleStatusChange} onWhatsApp={openApptWhatsApp} onDelete={handleDeleteAppt} onSign={handleOpenSignature} />
        ))
      )}

      {/* Bouton d'ajout de RDV */}
      <div className="fixed bottom-28 right-6 z-40">
        <button onClick={() => setShowAddModal(true)} className="w-14 h-14 bg-primary text-white rounded-full shadow-[0_8px_30px_rgba(var(--primary-rgb),0.4)] flex items-center justify-center hover:scale-105 active:scale-95 transition-transform border border-white/20">
          <Plus size={24} />
        </button>
      </div>

      {showAddModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-card border border-glass-border rounded-[24px] w-full max-w-sm overflow-hidden shadow-elite animate-in fade-in zoom-in-95 duration-200 p-5 space-y-4">
            <h3 className="font-black font-outfit text-primary flex items-center gap-2"><Calendar size={18}/> Ajouter un RDV</h3>
            <div className="space-y-3">
              <div>
                <div className="flex items-center justify-between">
                  <label className="text-[10px] font-black uppercase text-text-muted">Patient</label>
                  <button onClick={() => setIsCreatingPatient(!isCreatingPatient)} className="text-[10px] font-black uppercase text-primary tracking-widest flex items-center gap-1">
                    {isCreatingPatient ? 'Annuler' : '+ Nouveau'}
                  </button>
                </div>
                {isCreatingPatient ? (
                  <div className="mt-2 space-y-2 bg-primary/5 p-3 rounded-xl border border-primary/10">
                    <input type="text" placeholder="Nom" className="w-full bg-glass-bg border border-glass-border rounded-lg px-3 py-1.5 text-xs outline-none focus:border-primary" value={newPt.nom} onChange={e => setNewPt({...newPt, nom: e.target.value})} />
                    <input type="text" placeholder="Prénom" className="w-full bg-glass-bg border border-glass-border rounded-lg px-3 py-1.5 text-xs outline-none focus:border-primary" value={newPt.prenom} onChange={e => setNewPt({...newPt, prenom: e.target.value})} />
                    <input type="tel" placeholder="Téléphone" className="w-full bg-glass-bg border border-glass-border rounded-lg px-3 py-1.5 text-xs outline-none focus:border-primary" value={newPt.telephone} onChange={e => setNewPt({...newPt, telephone: e.target.value})} />
                    <button onClick={handleCreatePatient} className="w-full py-2 mt-1 bg-primary text-white font-bold text-[11px] rounded-lg shadow-sm">Créer le patient</button>
                  </div>
                ) : (
                  <select className="w-full mt-1 bg-glass-bg border border-glass-border rounded-xl px-3 py-2 text-sm outline-none focus:border-primary" value={newApt.patient_name} onChange={e => setNewApt({...newApt, patient_name: e.target.value})}>
                    <option value="" disabled>Sélectionner un patient...</option>
                    {patients.map(p => <option key={p.id} value={p.name}>{p.name}</option>)}
                  </select>
                )}
              </div>
              <div>
                <label className="text-[10px] font-black uppercase text-text-muted">Motif</label>
                {newApt.isCustomMotif ? (
                  <div className="flex gap-2 mt-1 items-center">
                    <input type="text" className="w-full bg-glass-bg border border-glass-border rounded-xl px-3 py-2 text-sm outline-none focus:border-primary" placeholder="Nouveau motif..." value={newApt.motif} onChange={e => setNewApt({...newApt, motif: e.target.value})} autoFocus />
                    <button onClick={() => setNewApt({...newApt, isCustomMotif: false, motif: 'Consultation'})} className="p-1 text-text-muted hover:text-primary"><XCircle size={18} /></button>
                  </div>
                ) : (
                  <select className="w-full mt-1 bg-glass-bg border border-glass-border rounded-xl px-3 py-2 text-sm outline-none focus:border-primary" value={newApt.motif} onChange={e => {
                    if (e.target.value === 'Autre...') {
                      setNewApt({...newApt, isCustomMotif: true, motif: ''});
                    } else {
                      setNewApt({...newApt, motif: e.target.value});
                    }
                  }}>
                    <option value="Consultation">Consultation</option>
                    <option value="Contrôle">Contrôle</option>
                    <option value="Détartrage">Détartrage</option>
                    <option value="Urgence">Urgence</option>
                    <option value="Soins">Soins</option>
                    <option value="Extraction">Extraction</option>
                    <option value="Orthodontie">Orthodontie</option>
                    <option disabled>--- Prothèse ---</option>
                    <option value="Prothèse">Prothèse</option>
                    <option value="Taille">Taille</option>
                    <option value="Empreinte">Empreinte</option>
                    <option value="Essayage armature">Essayage armature</option>
                    <option value="Essayage biscuit">Essayage biscuit</option>
                    <option value="Pose de prothèse">Pose de prothèse</option>
                    <option disabled>--- Prothèse Adjointe ---</option>
                    <option value="Prothèse adjointe (PEI)">PEI</option>
                    <option value="Prothèse adjointe (RIM)">RIM</option>
                    <option value="Prothèse adjointe (Montage)">Montage</option>
                    <option value="Prothèse adjointe (Finition)">Finition</option>
                    <option value="Autre...">Autre...</option>
                  </select>
                )}
              </div>
              <div className="flex gap-3">
                <div className="flex-1"><label className="text-[10px] font-black uppercase text-text-muted">Heure</label><input type="time" className="w-full mt-1 bg-glass-bg border border-glass-border rounded-xl px-3 py-2 text-sm outline-none focus:border-primary" value={newApt.time} onChange={e => setNewApt({...newApt, time: e.target.value})} /></div>
                <div className="flex-1"><label className="text-[10px] font-black uppercase text-text-muted">Durée (min)</label><input type="number" className="w-full mt-1 bg-glass-bg border border-glass-border rounded-xl px-3 py-2 text-sm outline-none focus:border-primary" value={newApt.duration_minutes} onChange={e => setNewApt({...newApt, duration_minutes: Number(e.target.value)})} /></div>
              </div>
            </div>
            <div className="flex gap-2 pt-2">
              <button onClick={() => setShowAddModal(false)} className="flex-1 py-2.5 rounded-xl border border-glass-border font-bold text-xs text-text-main active:scale-95 transition-all">Annuler</button>
              <button onClick={handleAddAppt} disabled={!newApt.patient_name} className="flex-1 py-2.5 rounded-xl bg-primary text-white font-bold text-xs shadow-md active:scale-95 transition-all disabled:opacity-50">Ajouter</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
  };

  // ── FINANCE VIEW ─────────────────────────────────────────────────────────────
  const renderFinanceView = () => (
    <div className="space-y-6">
      {/* KPI grid */}
      <div className="grid grid-cols-2 gap-3">
        {/* Today */}
        <div className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[24px] p-5 shadow-elite" style={{ background: 'linear-gradient(135deg, var(--primary), var(--secondary))' }}>
          <div className="w-8 h-8 bg-white/20 backdrop-blur-md rounded-[12px] flex items-center justify-center text-white mb-3 border border-white/30">
            <Wallet size={16} />
          </div>
          {syncStatus === 'loading' && !f
            ? <Skeleton className="h-8 w-24 bg-white/20" />
            : <>
                <p className="text-xl font-black tracking-tight text-white font-outfit">{fmt(f?.today_revenue ?? 0)}</p>
                <p className="text-[9px] font-black text-white/70 uppercase tracking-widest mt-1">Recettes Jour</p>
              </>
          }
        </div>
        {/* Month */}
        <div className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[24px] p-5 shadow-elite">
          <div className="w-8 h-8 bg-amber-500/10 rounded-[12px] flex items-center justify-center text-amber-600 mb-3 border border-amber-500/20">
            <TrendingUp size={16} />
          </div>
          {syncStatus === 'loading' && !f
            ? <Skeleton className="h-8 w-24" />
            : <>
                <div className="flex items-baseline gap-1.5">
                  <p className="text-xl font-black tracking-tight text-text-main font-outfit">{fmt(f?.month_revenue ?? 0)}</p>
                  {f?.month_variation != null && (
                    <span className={cn('text-[9px] font-black flex items-center', f.month_variation >= 0 ? 'text-emerald-500' : 'text-rose-500')}>
                      {f.month_variation >= 0 ? <ArrowUpRight size={9} /> : <ArrowDownRight size={9} />}
                      {Math.abs(f.month_variation)}%
                    </span>
                  )}
                </div>
                <p className="text-[9px] font-black text-text-muted uppercase tracking-widest mt-1">Recettes Mois</p>
              </>
          }
        </div>
        {/* Patients */}
        <div className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[24px] p-5 shadow-elite">
          <div className="w-8 h-8 bg-emerald-500/10 rounded-[12px] flex items-center justify-center text-emerald-600 mb-3 border border-emerald-500/20">
            <Users size={16} />
          </div>
          <p className="text-xl font-black tracking-tight text-text-main font-outfit">{f?.total_patients ?? '—'}</p>
          <p className="text-[9px] font-black text-text-muted uppercase tracking-widest mt-1">Patients</p>
        </div>
        {/* Total debt */}
        <div className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[24px] p-5 shadow-elite">
          <div className="w-8 h-8 bg-rose-500/10 rounded-[12px] flex items-center justify-center text-rose-500 mb-3 border border-rose-500/20">
            <AlertTriangle size={16} />
          </div>
          <p className="text-xl font-black tracking-tight text-rose-500 font-outfit">{fmt(f?.total_debt ?? 0)}</p>
          <p className="text-[9px] font-black text-text-muted uppercase tracking-widest mt-1">Créances</p>
        </div>
      </div>

      {/* 7-day chart */}
      {f?.weekly_revenue && f.weekly_revenue.length > 0 && (
        <div className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[24px] p-6 shadow-elite">
          <div className="flex items-center justify-between mb-6 border-b border-border-main pb-4">
            <div>
              <p className="text-[9px] font-black text-text-muted uppercase tracking-[0.2em]">Intelligence Analytique</p>
              <h4 className="text-lg font-black text-primary font-outfit mt-0.5">Activité 7 Jours</h4>
            </div>
            <span className="text-[9px] font-black text-text-muted uppercase tracking-wider">MAD</span>
          </div>
          <div className="h-[140px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={f.weekly_revenue}>
                <defs>
                  <linearGradient id="colorAmountMobile" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="var(--primary)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis 
                  dataKey="date" 
                  axisLine={false} 
                  tickLine={false} 
                  tickFormatter={(val, i) => dayLabel(val, i, f.weekly_revenue.length)}
                  tick={{ fontSize: 9, fontWeight: 900, fill: '#94a3b8' }} 
                  dy={10} 
                />
                <Tooltip
                  cursor={{ stroke: 'var(--primary)', strokeWidth: 1, strokeDasharray: '4 4', opacity: 0.2 }}
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="bg-white/95 backdrop-blur-md p-3 rounded-[16px] border border-border-main shadow-elite">
                          <p className="text-[9px] font-black text-text-muted uppercase tracking-widest mb-1">
                            {new Date(payload[0].payload.date).toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric', month: 'short' })}
                          </p>
                          <p className="text-sm font-black text-primary">{(payload[0].value as number).toLocaleString('fr-FR')} MAD</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Area type="monotone" dataKey="amount" stroke="var(--primary)" strokeWidth={3} fillOpacity={1} fill="url(#colorAmountMobile)" animationDuration={1000} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Debtors */}
      <div>
        <h2 className="text-[10px] font-black text-text-muted uppercase tracking-widest mb-3 px-1 flex items-center gap-2">
          <AlertTriangle size={14} className="text-rose-500" /> Liste Rouge
          <span className="ml-auto">{snapshot?.debtors.length ?? 0} dossiers</span>
        </h2>
        {!snapshot?.debtors.length ? (
          <div className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[24px] py-12 text-center shadow-elite">
            <CheckCircle2 size={32} className="mx-auto mb-3 text-emerald-500" />
            <p className="text-sm font-black text-text-main font-outfit">Aucun impayé</p>
            <p className="text-text-muted text-[11px] mt-1">Tous les comptes sont à jour.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {snapshot.debtors.map(d => (
              <div
                key={d.id}
                className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[20px] p-4 flex items-center justify-between shadow-elite hover:border-rose-200 transition-all"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-primary/10 border border-primary/20 rounded-[12px] flex items-center justify-center font-black text-primary font-outfit">
                    {d.name.charAt(0)}
                  </div>
                  <div>
                    <p className="text-sm font-black text-text-main">{d.name}</p>
                    <p className="text-[10px] font-black text-rose-500 mt-0.5">{fmt(d.amount)} MAD</p>
                  </div>
                </div>
                {d.phone && (
                  <button
                    onClick={() => openWhatsApp(d.phone, `Bonjour ${d.name}, nous vous contactons concernant un solde en attente de ${fmt(d.amount)} MAD.`)}
                    className="w-10 h-10 bg-primary/5 border border-primary/10 rounded-[12px] flex items-center justify-center text-primary hover:bg-primary hover:text-white transition-all active:scale-95"
                  >
                    <MessageSquare size={16} />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <button
        onClick={handleExportPDF}
        className="w-full py-4 bg-primary border border-primary/20 text-white rounded-[24px] font-black text-[11px] uppercase tracking-widest flex items-center justify-center gap-2 active:scale-95 transition-all shadow-elite hover:bg-primary/90"
      >
        <Download size={16} /> Exporter le Bilan PDF du Mois
      </button>
    </div>
  );

  // ── SECURITE VIEW ─────────────────────────────────────────────────────────────
  const renderSecuriteView = () => (
    <div className="space-y-5">
      {/* Shield card */}
      <div className="relative overflow-hidden rounded-[32px] p-8 flex flex-col items-center text-center gap-5 shadow-elite-hover" style={{ backgroundImage: 'linear-gradient(135deg, var(--primary), var(--secondary))' }}>
        <div className="absolute top-0 right-0 w-48 h-48 bg-white/10 rounded-full -mr-24 -mt-24 blur-3xl" />
        <div className="w-20 h-20 bg-white/20 backdrop-blur-md border border-white/30 rounded-[24px] flex items-center justify-center text-white shadow-xl z-10">
          <ShieldCheck size={40} />
        </div>
        <div className="z-10">
          <p className="font-black text-white text-xl font-outfit">Terminal Appairé</p>
          <p className="text-[11px] text-white/70 mt-2 leading-relaxed max-w-xs">
            Accès direct au cabinet via réseau local. Aucune donnée ne transite par un serveur cloud.
          </p>
        </div>
        <div className="w-full flex items-center justify-center gap-2 py-2.5 bg-white/10 border border-white/20 rounded-[16px] z-10">
          <div className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
          <span className="text-[10px] font-black text-white uppercase tracking-widest">Zero-Knowledge · AES-256</span>
        </div>
      </div>

      {/* Status cards */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[20px] p-4 shadow-elite">
          <div className="flex items-center gap-2 mb-3">
            {isOnline
              ? <Wifi size={14} className="text-emerald-500" />
              : <WifiOff size={14} className="text-rose-500" />
            }
            <span className="text-[9px] font-black text-text-muted uppercase tracking-widest">Réseau</span>
          </div>
          <p className={cn('text-xs font-black', isOnline ? 'text-emerald-600' : 'text-rose-500')}>
            {isOnline ? 'En ligne' : 'Hors ligne'}
          </p>
          <p className="text-[9px] text-text-muted mt-0.5 font-bold">
            {isOnline ? 'Temps réel' : 'Cache local'}
          </p>
        </div>
        <div className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[20px] p-4 shadow-elite">
          <div className="flex items-center gap-2 mb-3">
            <RefreshCw size={14} className="text-primary" />
            <span className="text-[9px] font-black text-text-muted uppercase tracking-widest">Sync</span>
          </div>
          <p className="text-xs font-black text-text-main">
            {syncStatus === 'success' ? 'À jour' : syncStatus === 'loading' ? 'En cours…' : 'En attente'}
          </p>
          <p className="text-[9px] text-text-muted mt-0.5 font-bold">
            {snapshot ? new Date(snapshot.generated_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : '—'}
          </p>
        </div>
      </div>

      {/* Status system pill */}
      <div className="bg-glass-bg border border-glass-border backdrop-blur-md rounded-[20px] p-4 shadow-elite flex items-center gap-3">
        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
        <div>
          <p className="text-[10px] font-black text-text-muted uppercase tracking-widest">Status Système</p>
          <p className="text-sm font-black text-text-main">Elite Cloud Connecté</p>
        </div>
        <FileText size={16} className="ml-auto text-text-muted" />
      </div>

      {/* Logout */}
      <button
        onClick={handleLogout}
        className="w-full py-5 bg-rose-500/5 border border-rose-200 text-rose-500 rounded-[24px] font-black text-xs uppercase tracking-widest flex items-center justify-center gap-3 active:scale-95 transition-all hover:bg-rose-50"
      >
        <LogOut size={16} /> Révoquer cet accès
      </button>
    </div>
  );

  // ── MAIN LAYOUT ───────────────────────────────────────────────────────────────
  return (
    <div className="min-h-[100dvh] bg-background text-text-main flex flex-col font-outfit pb-28 select-none relative" style={{ backgroundColor: 'var(--bg-medical-pearl)' }}>
      <div className="document-watermark absolute inset-0 z-0 pointer-events-none opacity-50" />

      {/* ── HEADER ── */}
      <div className="px-6 pt-14 pb-6 relative z-10">
        {/* Top row */}
        <div className="flex items-center justify-between mb-8">
          <img src={Logo} alt="Digital Crown" className="w-36 h-auto object-contain drop-shadow-sm origin-left" />

          <button
            onClick={fetchSnapshot}
            disabled={syncStatus === 'loading'}
            className="flex items-center gap-1.5 px-3 py-2 bg-card border border-glass-border rounded-[12px] shadow-elite disabled:opacity-40 active:scale-95 transition-all hover:bg-primary/5 backdrop-blur-md"
            style={{ backgroundColor: 'var(--glass-bg)' }}
          >
            <div className={cn(
              'w-1.5 h-1.5 rounded-full',
              syncStatus === 'loading' ? 'bg-primary animate-pulse'
              : syncStatus === 'error' ? 'bg-rose-500'
              : 'bg-emerald-500'
            )} />
            <RefreshCw size={10} className={cn('text-text-muted', syncStatus === 'loading' ? 'animate-spin' : '')} />
            <span className="text-[9px] font-black text-text-muted uppercase tracking-widest">
              {syncStatus === 'loading' ? 'Sync…' : syncStatus === 'error' ? 'Offline' : 'Live'}
            </span>
          </button>
        </div>

        {/* Header Title / Greeting */}
        <div>
          {(activeTab === 'agenda' || activeTab === 'finance') && (
            <div className="flex items-center gap-2 mb-2">
              <Calendar size={12} className="text-primary shrink-0" />
              <button 
                onClick={() => {
                  const d = new Date(selectedDate);
                  d.setDate(d.getDate() - 1);
                  setSelectedDate(d.toISOString().split('T')[0]);
                }} 
                className="p-1 text-primary bg-primary/10 rounded-full active:scale-90 transition-transform"
              >
                <ChevronLeft size={12} />
              </button>
              <input 
                type="date" 
                value={selectedDate} 
                onChange={(e) => setSelectedDate(e.target.value)} 
                className="bg-transparent border-none text-text-muted font-bold text-xs capitalize outline-none p-0 cursor-pointer text-center min-w-min"
              />
              <button 
                onClick={() => {
                  const d = new Date(selectedDate);
                  d.setDate(d.getDate() + 1);
                  setSelectedDate(d.toISOString().split('T')[0]);
                }} 
                className="p-1 text-primary bg-primary/10 rounded-full active:scale-90 transition-transform"
              >
                <ChevronRight size={12} />
              </button>
            </div>
          )}
          
          <h1 className="text-4xl font-black tracking-tight text-primary font-outfit leading-none">
            {activeTab === 'agenda' ? `${greeting()},` : 
             activeTab === 'finance' ? 'Finances' : 
             activeTab === 'securite' ? 'Sécurité' : ''}
          </h1>

          {snapshot?.is_superadmin && (
            <button 
              onClick={() => window.location.href = '/super-admin'}
              className="mt-4 px-4 py-2 bg-amber-400 hover:bg-amber-500 text-amber-950 rounded-full font-black text-xs shadow-md uppercase tracking-widest flex items-center gap-2 transition-all active:scale-95"
            >
              <ShieldCheck size={16} /> Gestion des dentistes
            </button>
          )}
          
          {activeTab === 'agenda' && totalCount > 0 && (
            <div className="flex items-center gap-2 mt-4">
              <div className="flex items-center gap-1.5 px-3 py-1.5 bg-primary/5 border border-primary/10 rounded-full shadow-sm">
                <span className="text-[10px] font-black text-primary">{totalCount} RDV aujourd'hui</span>
              </div>
              {termineCount > 0 && (
                <div className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/5 border border-emerald-500/20 rounded-full shadow-sm">
                  <span className="text-[10px] font-black text-emerald-600">{termineCount} terminé{termineCount > 1 ? 's' : ''}</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Error banner */}
      {error && syncStatus === 'error' && (
        <div className="mx-6 mb-4 p-3 bg-amber-500/5 border border-amber-200 rounded-[16px] flex items-center gap-3 relative z-10 shadow-sm">
          <WifiOff size={14} className="text-amber-500 shrink-0" />
          <p className="text-[10px] font-black text-amber-600 uppercase tracking-widest">{error}</p>
        </div>
      )}

      {/* Content */}
      <main ref={mainRef} className="flex-1 px-6 overflow-y-auto">
        {activeTab === 'agenda'   && renderAgendaView()}
        {activeTab === 'finance'  && renderFinanceView()}
        {activeTab === 'securite' && renderSecuriteView()}
      </main>

      {/* ── BOTTOM NAV ── */}
      <nav className="fixed bottom-6 left-6 right-6 h-[68px] backdrop-blur-2xl border rounded-[32px] flex items-center justify-around px-6 shadow-elite-hover z-50" style={{ backgroundColor: 'var(--glass-bg)', borderColor: 'var(--glass-border)' }}>
        {([
          {
            id: 'agenda' as Tab,
            icon: Calendar,
            label: 'Agenda',
            dot: totalCount > 0 && termineCount < totalCount,
            allowedRoles: ['DENTISTE', 'ADMIN', 'SECRETAIRE']
          },
          {
            id: 'finance' as Tab,
            icon: TrendingUp,
            label: 'Finance',
            dot: false,
            allowedRoles: ['DENTISTE', 'ADMIN']
          },
          {
            id: 'securite' as Tab,
            icon: ShieldCheck,
            label: 'Sécurité',
            dot: false,
            allowedRoles: ['DENTISTE', 'ADMIN']
          },
        ]).filter(t => t.allowedRoles.includes(snapshot?.role ?? 'DENTISTE')).map(({ id, icon: Icon, label, dot }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={cn(
              'relative flex flex-col items-center gap-1 transition-all duration-200',
              activeTab === id ? 'text-primary scale-105' : 'text-text-muted'
            )}
          >
            {dot && (
              <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 bg-primary rounded-full animate-pulse" />
            )}
            <Icon size={21} />
            <span className="text-[9px] font-black uppercase tracking-widest">{label}</span>
          </button>
        ))}
      </nav>

      {/* ── MODAL WHATSAPP ── */}
      {whatsappApt && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-card border border-glass-border rounded-[24px] w-full max-w-sm overflow-hidden shadow-elite animate-in fade-in zoom-in-95 duration-200 p-5 space-y-4">
            <h3 className="font-outfit font-black text-primary flex items-center gap-2">
              <MessageSquare size={18} /> Rappel WhatsApp
            </h3>
            
            <div className="space-y-3">
              <div>
                <label className="text-[10px] font-black uppercase text-text-muted">Modèle de message</label>
                <div className="flex gap-2 mt-1">
                  <button 
                    onClick={() => setWhatsappTemplate('rappel')}
                    className={cn(
                      "flex-1 py-2 text-[10px] font-black uppercase tracking-wider rounded-lg border transition-all",
                      whatsappTemplate === 'rappel' ? "bg-primary text-white border-primary" : "bg-white text-slate-600 border-slate-200"
                    )}
                  >
                    Rappel RDV
                  </button>
                  <button 
                    onClick={() => setWhatsappTemplate('confirmation')}
                    className={cn(
                      "flex-1 py-2 text-[10px] font-black uppercase tracking-wider rounded-lg border transition-all",
                      whatsappTemplate === 'confirmation' ? "bg-primary text-white border-primary" : "bg-white text-slate-600 border-slate-200"
                    )}
                  >
                    Confirmation
                  </button>
                </div>
              </div>

              <div>
                <label className="text-[10px] font-black uppercase text-text-muted">Message à envoyer</label>
                <textarea 
                  value={customMessage}
                  onChange={e => setCustomMessage(e.target.value)}
                  className="w-full mt-1 bg-glass-bg border border-glass-border rounded-xl px-3 py-2 text-xs outline-none focus:border-primary h-24 resize-none font-medium text-slate-800"
                />
              </div>
            </div>

            <div className="flex gap-2 pt-2">
              <button 
                onClick={() => setWhatsappApt(null)} 
                className="flex-1 py-2.5 rounded-xl border border-glass-border font-bold text-xs text-text-main active:scale-95 transition-all"
              >
                Annuler
              </button>
              <button 
                onClick={handleSendWhatsApp} 
                className="flex-1 py-2.5 rounded-xl bg-primary text-white font-bold text-xs shadow-md active:scale-95 transition-all flex items-center justify-center gap-1.5"
              >
                <MessageSquare size={14} /> Envoyer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── MODAL SIGNATURE AU FAUTEUIL ── */}
      {sigPatientId && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-card border border-glass-border rounded-[24px] w-full max-w-sm overflow-hidden shadow-elite animate-in fade-in zoom-in-95 duration-200 p-5 space-y-4">
            <div className="flex justify-between items-start">
              <h3 className="font-outfit font-black text-primary flex items-center gap-2">
                <FileText size={18} /> Signature au Fauteuil
              </h3>
              <button onClick={() => setSigPatientId(null)} className="text-text-muted hover:text-rose-500">
                <XCircle size={18} />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <p className="text-xs text-text-muted">
                  Patient : <span className="font-black text-text-main">{sigPatientName}</span>
                </p>
              </div>

              {isLoadingDocs ? (
                <div className="py-6 flex flex-col items-center justify-center gap-2">
                  <RefreshCw className="animate-spin text-primary" size={24} />
                  <p className="text-[10px] font-black uppercase text-text-muted">Chargement des documents...</p>
                </div>
              ) : sigDocs.length === 0 ? (
                <div className="py-6 text-center border border-dashed border-border-main rounded-2xl bg-slate-50/50">
                  <AlertTriangle className="mx-auto text-amber-500 mb-1" size={24} />
                  <p className="text-xs font-bold text-slate-600">Aucun devis trouvé pour ce patient</p>
                  <p className="text-[10px] text-text-muted mt-0.5">Veuillez d'abord générer un devis sur le PC.</p>
                </div>
              ) : (
                <>
                  <div>
                    <label className="text-[10px] font-black uppercase text-text-muted">Document à signer</label>
                    <select 
                      className="w-full mt-1 bg-glass-bg border border-glass-border rounded-xl px-3 py-2 text-xs outline-none focus:border-primary font-bold text-slate-800"
                      value={selectedDocId || ''}
                      onChange={e => setSelectedDocId(Number(e.target.value))}
                    >
                      {sigDocs.map(d => (
                        <option key={d.id} value={d.id}>
                          {d.filename} ({d.signed ? 'SIGNÉ' : 'Non signé'})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="pt-2 border-t border-border-main">
                    <label className="text-[10px] font-black uppercase text-text-muted block mb-2 font-black">Signature du Patient</label>
                    {isSigning ? (
                      <div className="py-12 flex flex-col items-center justify-center gap-2">
                        <RefreshCw className="animate-spin text-primary" size={24} />
                        <p className="text-[10px] font-black uppercase text-text-muted">Enregistrement et génération du PDF...</p>
                      </div>
                    ) : (
                      <SignaturePad 
                        onSave={handleSaveSignature} 
                        onCancel={() => setSigPatientId(null)} 
                      />
                    )}
                  </div>
                </>
              )}
            </div>

            <div className="pt-2">
              <button 
                onClick={() => setSigPatientId(null)} 
                className="w-full py-2.5 rounded-xl border border-glass-border font-bold text-xs text-text-muted active:scale-95 transition-all bg-white"
              >
                Fermer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
