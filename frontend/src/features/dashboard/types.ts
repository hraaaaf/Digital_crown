export interface RecentPatient {
  id: number;
  nom: string;
  prenom: string;
  acte: string;
  time: string;
  type: string;
}

export interface DashboardStats {
  total_patients: number;
  total_analyses: number;
  in_waiting: number;
  recent_patients: RecentPatient[];
  weekly_activity: number[];
  weekly_patient_counts?: number[];
  weekly_patients?: number;
}

export interface DashboardAppointment {
  id: number;
  start_time: string;
  status: string;
  description?: string | null;
  patient?: {
    nom: string;
    prenom: string;
  } | null;
}

export interface ProactiveAlert {
  id: number;
  patient_id: number | null;
  nom: string | null;
  prenom: string | null;
  type: string;
  title: string;
  message: string;
  action: string;
  priority: number;
}

export interface ForecastData {
  week_start: string;
  week_end: string;
  rdv_count: number;
  forecast_revenue: number;
  avg_per_rdv: number;
}

export interface ConversionData {
  devis_count: number;
  converted_count: number;
  taux: number;
  avg_days: number | null;
}

export interface ProjectionEntry {
  month: string;
  revenue: number;
  type: 'actual' | 'forecast';
}

export interface ProjectionData {
  historical: ProjectionEntry[];
  projections: ProjectionEntry[];
  avg_monthly: number;
}

export interface LatentCashOpportunity {
  patient_id: number;
  patient_name: string;
  telephone?: string | null;
  date_devis: string;
  montant: number;
  type: string;
}

export interface LatentCashData {
  total_opportunites: number;
  valeur_totale_latente: number;
  opportunites: LatentCashOpportunity[];
}

export interface FinanceToday {
  today_revenue: number;
  month_revenue: number;
  total_debt: number;
}

export interface SearchPatientResult {
  id: number;
  nom?: string | null;
  prenom?: string | null;
  numero_dossier?: string | null;
}

export type DataState = 'idle' | 'loading' | 'ready' | 'error';
