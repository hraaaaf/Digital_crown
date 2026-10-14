import { Clock, PlayCircle, CheckCircle2, XCircle, UsersRound } from 'lucide-react';

export type Tab = 'today' | 'agenda' | 'waiting-room' | 'patients' | 'finance' | 'bot' | 'lab' | 'securite' | 'dentists' | 'frontdesk' | 'notifications' | 'stock' | 'library' | 'marketplace';
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
    className: 'bg-background text-text-muted border-border-main',
    icon: <Clock size={11} />,
  },
  EN_ATTENTE: {
    label: 'En salle d’attente',
    className: 'bg-warning-surface text-warning border-warning-border',
    icon: <UsersRound size={11} />,
  },
  EN_COURS: {
    label: 'En cours',
    className: 'bg-primary/10 text-primary border-primary/20 animate-pulse',
    icon: <PlayCircle size={11} />,
  },
  TERMINE: {
    label: 'Terminé',
    className: 'bg-success-surface text-success border-success-border',
    icon: <CheckCircle2 size={11} />,
  },
  ANNULE: {
    label: 'Annulé',
    className: 'bg-danger-surface text-danger border-danger-border',
    icon: <XCircle size={11} />,
  },
};