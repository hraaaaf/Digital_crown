import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const read = (path: string) => readFileSync(resolve(process.cwd(), path), 'utf8');
const quickPay = read('src/features/patients/components/QuickPayModal.tsx');
const paymentApi = read('src/services/paymentApi.ts');
const finances = read('src/features/patients/components/PatientFinances.tsx');

describe('P6 canonical patient payment contract', () => {
  it('requires a positive amount and an explicit payment method in QuickPay', () => {
    expect(quickPay).toContain("type PaymentMethod = 'ESPECES' | 'CARTE' | 'VIREMENT' | 'CHEQUE'");
    expect(quickPay).toContain('useState<PaymentMethod | null>(null)');
    expect(quickPay).toContain('if (!amount || parseFloat(amount) <= 0 || !method) return');
    expect(quickPay).toContain('disabled={isSubmitting || !amount || parseFloat(amount) <= 0 || !method}');
  });

  it('writes patient payments through the canonical accounting endpoint only', () => {
    expect(quickPay).toContain('paymentApi.recordPayment');
    expect(quickPay).not.toContain("api.post('/accounting/payments'");
    expect(paymentApi).toContain("api.post('/accounting/payments', payment)");
  });

  it('keeps acte and installment targets on the same Payment payload contract', () => {
    expect(paymentApi).toContain('acte_id?: number');
    expect(paymentApi).toContain('installment_id?: number');
    expect(paymentApi).toContain("payment_method: 'ESPECES' | 'CARTE' | 'VIREMENT' | 'CHEQUE'");
  });

  it('does not introduce a second payment write endpoint in PatientFinances', () => {
    expect(finances).not.toContain("api.post('/payments'");
    expect(finances).not.toContain("api.post('/patient-payments'");
  });
});
