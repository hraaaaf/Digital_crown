export interface HonoraireItem {
  id: number | string;
  patient_id: number;
  patient_name: string;
  assurance: string;
  date: string;
  title: string;
  amount: number;
  file_url: string;
  payment_status?: string;
  is_collected?: boolean;
  validated_by?: string;
}

export interface GroupedItem {
  key: string;
  patient_id: number;
  patient_name: string;
  assurance: string;
  date: string;
  total: number;
  notes: HonoraireItem[];
}
