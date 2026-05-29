import type { LabJob } from "../types/labJob";

/**
 * Encode a LabJob into the WhatsApp message format required by the mobile flow.
 *
 * Output format (before encoding):
 *   Patient: [Initiale]
 *   Dent: [Tooth]
 *   Travail: [Type] - [Shade]
 *   Deadline: [Date formatted]
 */
export const formatLabJobMessage = (job: LabJob): string => {
  // Human‑readable plain text (no URL encoding)
  const patientInitial = job.patient_id ? `P${job.patient_id}` : "?";
  const tooth = job.tooth_number ?? "?";
  const shade = job.shade ?? "?";
  const deadline = new Date(job.deadline).toLocaleString();

  const raw = `Patient: ${patientInitial}\nDent: ${tooth}\nTravail: ${job.type} - ${shade}\nDeadline: ${deadline}`;
  return raw;
};
