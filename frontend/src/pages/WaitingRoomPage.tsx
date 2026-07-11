import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { cn } from '../utils/cn';
import { Clock, Users, CheckCircle2, ChevronRight, User, RefreshCw, Timer, Loader2 } from 'lucide-react';
import { useState } from 'react';
import toast from 'react-hot-toast';

interface Appointment {
  id: number;
  patient_id: number | null;
  patient_name: string | null;
  datetime_start: string;
  duration_minutes: number;
  motif: string | null;
  status: string;
  scheduling_type: string;
  notes: string | null;
  ticket_number: number | null;
  phone: string | null;
}

const STATUS_FLOW: Record<string, { next: string; nextLabel: string; color: string; bg: string; border: string; label: string }> = {
  'PRÉVU':    { next: 'EN_S_ATTENTE', nextLabel: 'Patient arrivé',    color: 'text-slate-600',   bg: 'bg-slate-50',      border: 'border-slate-200',  label: 'Prévu' },
  'CONFIRMÉ': { next: 'EN_S_ATTENTE', nextLabel: 'Patient arrivé',    color: 'text-blue-600',    bg: 'bg-blue-50',       border: 'border-blue-200',   label: 'Confirmé' },
  'EN_S_ATTENTE': { next: 'EN_FAUTEUIL', nextLabel: 'Appeler en fauteuil', color: 'text-amber-700', bg: 'bg-amber-50',  border: 'border-amber-200',  label: 'En salle d\'attente' },
  'EN_FAUTEUIL':  { next: 'TERMINÉ',    nextLabel: 'Terminer',            color: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200', label: 'En fauteuil' },
  'TERMINÉ':      { next: '',           nextLabel: '',                    color: 'text-slate-400',   bg: 'bg-slate-50',   border: 'border-slate-200',  label: 'Terminé' },
  'ANNULÉ':       { next: '',           nextLabel: '',                    color: 'text-red-400',     bg: 'bg-red-50',     border: 'border-red-200',    label: 'Annulé' },
};

const formatTime = (iso: string) => new Date(iso).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
const formatEndTime = (iso: string, duration: number) => {
  const d = new Date(iso);
  d.setMinutes(d.getMinutes() + duration);
  return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
};

const displayName = (appt: Appointment) =>
  appt.patient_name || `Patient ${appt.ticket_number ?? appt.id}`;

export const WaitingRoomPage = () => {
  const qc = useQueryClient();
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  const todayStart = new Date();
  todayStart.setHours(0, 0, 0, 0);
  const todayEnd = new Date();
  todayEnd.setHours(23, 59, 59, 999);

  const { data: appointments = [], isFetching } = useQuery<Appointment[]>({
    queryKey: ['waiting-room', todayStart.toISOString()],
    queryFn: async () => {
      const res = await api.get(`/appointments/?start_date=${todayStart.toISOString()}&end_date=${todayEnd.toISOString()}`);
      return res.data;
    },
    refetchInterval: 30_000,
  });

  const advance = async (appt: Appointment) => {
    const next = STATUS_FLOW[appt.status]?.next;
    if (!next) return;
    setUpdatingId(appt.id);
    try {
      await api.put(`/appointments/${appt.id}`, { status: next });
      await qc.invalidateQueries({ queryKey: ['waiting-room'] });
    } catch {
      toast.error('Erreur lors de la mise à jour du statut');
    } finally {
      setUpdatingId(null);
    }
  };

  const waiting  = appointments.filter(a => a.status === 'EN_S_ATTENTE');
  const inChair  = appointments.filter(a => a.status === 'EN_FAUTEUIL');
  const upcoming = appointments.filter(a => a.status === 'PRÉVU' || a.status === 'CONFIRMÉ');
  const done     = appointments.filter(a => a.status === 'TERMINÉ');
  const total    = appointments.filter(a => a.status !== 'ANNULÉ' && a.status !== 'REFUSÉ' && a.status !== 'EXPIRÉ' && a.status !== 'ABSENT').length;

  const ApptCard = ({ appt }: { appt: Appointment }) => {
    const meta = STATUS_FLOW[appt.status] || STATUS_FLOW['PRÉVU'];
    const isUpdating = updatingId === appt.id;
    const canAdvance = !!meta.next && appt.status !== 'TERMINÉ';

    return (
      <div className={cn(
        "rounded-2xl border p-4 space-y-2 transition-all",
        meta.bg, meta.border,
        canAdvance && "hover:shadow-md cursor-default"
      )}>
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className={cn("w-8 h-8 rounded-xl flex items-center justify-center shrink-0", meta.bg, "border", meta.border)}>
              <User size={15} className={meta.color} />
            </div>
            <div className="min-w-0">
              <p className="font-black text-sm text-slate-800 truncate">{displayName(appt)}</p>
              {appt.motif && <p className="text-[11px] text-slate-500 font-medium truncate">{appt.motif}</p>}
            </div>
          </div>
          <div className="text-right shrink-0">
            <p className="text-xs font-black text-slate-700">{formatTime(appt.datetime_start)}</p>
            <p className="text-[10px] text-slate-400 font-medium">→ {formatEndTime(appt.datetime_start, appt.duration_minutes)}</p>
          </div>
        </div>

        {appt.phone && (
          <p className="text-[10px] text-slate-400 font-medium">{appt.phone}</p>
        )}

        {canAdvance && (
          <button
            onClick={() => advance(appt)}
            disabled={isUpdating}
            className={cn(
              "w-full flex items-center justify-center gap-1.5 py-2 rounded-xl text-[11px] font-black uppercase tracking-wider transition-all border",
              "bg-white hover:shadow-sm",
              meta.color, meta.border
            )}
          >
            {isUpdating ? (
              <Loader2 size={12} className="animate-spin" />
            ) : (
              <>
                {meta.nextLabel}
                <ChevronRight size={13} />
              </>
            )}
          </button>
        )}

        {appt.status === 'TERMINÉ' && (
          <div className="flex items-center gap-1.5 justify-center py-1">
            <CheckCircle2 size={13} className="text-emerald-500" />
            <span className="text-[10px] font-black text-emerald-600">Consultation terminée</span>
          </div>
        )}
      </div>
    );
  };

  const Column = ({ title, count, icon, children, accent }: {
    title: string; count: number; icon: React.ReactNode;
    children: React.ReactNode; accent: string;
  }) => (
    <div className="flex flex-col gap-3">
      <div className={cn("flex items-center gap-2.5 px-4 py-3 rounded-2xl border", accent)}>
        {icon}
        <h2 className="text-[11px] font-black uppercase tracking-widest">{title}</h2>
        <span className="ml-auto text-lg font-black">{count}</span>
      </div>
      <div className="space-y-2.5">
        {count === 0 ? (
          <div className="py-8 text-center text-text-muted">
            <p className="text-sm font-bold">Aucun</p>
          </div>
        ) : children}
      </div>
    </div>
  );

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-slate-800 tracking-tight">Salle d'attente</h1>
          <p className="text-sm text-slate-500 font-medium mt-0.5">
            {new Date().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })}
          </p>
        </div>
        <div className="flex items-center gap-4">
          {/* KPIs rapides */}
          <div className="flex items-center gap-3">
            <div className="px-4 py-2.5 bg-amber-50 border border-amber-200 rounded-2xl text-center">
              <p className="text-[9px] font-black uppercase tracking-widest text-amber-500 mb-0.5">En attente</p>
              <p className="text-xl font-black text-amber-700">{waiting.length}</p>
            </div>
            <div className="px-4 py-2.5 bg-emerald-50 border border-emerald-200 rounded-2xl text-center">
              <p className="text-[9px] font-black uppercase tracking-widest text-emerald-500 mb-0.5">En fauteuil</p>
              <p className="text-xl font-black text-emerald-700">{inChair.length}</p>
            </div>
            <div className="px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-2xl text-center">
              <p className="text-[9px] font-black uppercase tracking-widest text-slate-400 mb-0.5">Total jour</p>
              <p className="text-xl font-black text-slate-700">{total}</p>
            </div>
          </div>
          <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400">
            <RefreshCw size={12} className={isFetching ? 'animate-spin text-primary' : ''} />
            Auto 30s
          </div>
        </div>
      </div>

      {/* Kanban 4 colonnes */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5">
        <Column
          title="À venir"
          count={upcoming.length}
          icon={<Clock size={14} className="text-slate-500" />}
          accent="bg-slate-50 border-slate-200 text-slate-600"
        >
          {upcoming.sort((a, b) => a.datetime_start.localeCompare(b.datetime_start)).map(a => (
            <ApptCard key={a.id} appt={a} />
          ))}
        </Column>

        <Column
          title="En salle d'attente"
          count={waiting.length}
          icon={<Timer size={14} className="text-amber-600" />}
          accent="bg-amber-50 border-amber-200 text-amber-700"
        >
          {waiting.sort((a, b) => a.datetime_start.localeCompare(b.datetime_start)).map(a => (
            <ApptCard key={a.id} appt={a} />
          ))}
        </Column>

        <Column
          title="En fauteuil"
          count={inChair.length}
          icon={<Users size={14} className="text-emerald-600" />}
          accent="bg-emerald-50 border-emerald-200 text-emerald-700"
        >
          {inChair.sort((a, b) => a.datetime_start.localeCompare(b.datetime_start)).map(a => (
            <ApptCard key={a.id} appt={a} />
          ))}
        </Column>

        <Column
          title="Terminés"
          count={done.length}
          icon={<CheckCircle2 size={14} className="text-slate-400" />}
          accent="bg-slate-50 border-slate-200 text-slate-500"
        >
          {done.sort((a, b) => a.datetime_start.localeCompare(b.datetime_start)).map(a => (
            <ApptCard key={a.id} appt={a} />
          ))}
        </Column>
      </div>

    </div>
  );
};
