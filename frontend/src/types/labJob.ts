export enum LabJobStatus {
  PRESCRIPTION = "PRESCRIPTION",
  SENT = "SENT",
  IN_PROGRESS = "IN_PROGRESS",
  TRY_IN = "TRY_IN",
  READY = "READY",
  DELIVERED = "DELIVERED"
}

export interface LabJob {
  id: number;
  patient_id: number;
  act_id: number;
  lab_id?: number;
  material: string;
  shade?: string;
  type: string;
  tooth_number?: string;
  notes?: string;
  deadline: string; // ISO string
  status: LabJobStatus;
  is_remake: boolean;
  is_late: boolean;
  created_at: string;
  updated_at: string;
}
