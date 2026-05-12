import { api } from './api';

export interface PaymentCreate {
  patient_id: number;
  amount: number;
  payment_method: 'ESPECES' | 'CARTE' | 'VIREMENT' | 'CHEQUE';
  payment_date?: string;
  notes?: string;
  acte_id?: number;
  installment_id?: number;
}

export interface PaymentOut {
  id: number;
  patient_id: number;
  amount: number;
  payment_method: string;
  payment_date: string;
  notes?: string;
  acte_id?: number;
  installment_id?: number;
}

export const paymentApi = {
  /**
   * Enregistrer un nouvel encaissement réel
   */
  recordPayment: async (payment: PaymentCreate): Promise<PaymentOut> => {
    const { data } = await api.post('/accounting/payments', payment);
    return data;
  },

  /**
   * Récupérer l'historique des paiements d'un patient
   */
  getPatientPayments: async (patientId: number): Promise<PaymentOut[]> => {
    const { data } = await api.get(`/accounting/payments/patient/${patientId}`);
    return data;
  }
};
