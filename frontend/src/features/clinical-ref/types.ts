export interface ChecklistItem {
  id: string;
  label: string;
  critical: boolean;
}

export interface StepItem {
  order: number;
  label: string;
  tip?: string;
}

export interface PitfallItem {
  risk: string;
  mitigation: string;
}

export interface DrugItem {
  category: "anesthesia" | "antibiotic" | "analgesic" | "antiseptic";
  name: string;
  dose_adult: string;
  dose_child?: string;
  indication?: string;
}

export interface PatientInstructionItem {
  timing: "immediately" | "day1" | "week1";
  instruction: string;
}

export interface ClinicalProtocol {
  act_code: string;
  act_names: string[];
  difficulty: "routine" | "complex" | "specialist";
  duration_min: number;
  checklist: ChecklistItem[];
  steps: StepItem[];
  pitfalls: PitfallItem[];
  drugs: DrugItem[];
  patient_instructions: PatientInstructionItem[];
}
