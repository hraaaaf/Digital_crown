import { Clock, PlayCircle, CheckCircle2, XCircle, UsersRound } from 'lucide-react';

export type Tab = 'agenda' | 'waiting-room' | 'patients' | 'finance' | 'bot' | 'lab' | 'securite' | 'dentists' | 'frontdesk' | 'notifications' | 'stock' | 'library' | 'marketplace';
export type SyncStatus = 'idle' | 'loading' | 'success' | 'error';
export type ApptStatus = 'PLANIFIE' | 'EN_ATTENTE' | 'EN_COURS' | 'TERMINE' | 'ANNULE';

export interface WeekDay { date: string; amount: number }
export interface Appointment {
  id: number;
  patient_id?: number | null;
  time: string;
  patient_name: string;
  date?: string;
  phone: string | null;
  motif: string;
  status: ApptStatus | null;
  duration_minutes: number;
  ticket_number?: number | null;
}
export interface Snapshot {
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

export const STATUS_META: Record<ApptStatus, { label: string; className: string; icon: any }> = {
  PLANIFIE: {
    label: 'Planifié',
    className: 'bg-slate-100 text-slate-600 border-slate-200',
    icon: <Clock size={11} />,
  },
  EN_ATTENTE: {
    label: 'En salle d’attente',
    className: 'bg-amber-500/10 text-amber-700 border-amber-500/20',
    icon: <UsersRound size={11} />,
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