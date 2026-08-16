import { create } from 'zustand';
import { PARTIAL_PAYMENT_DISABLED_REASON } from '../DocumentStudio/AccountingPaymentPolicy';

export type PaymentMode = '' | 'Espèces' | 'Chèque' | 'TPE' | 'Virement';

export interface PriceItem {
  id: number;
  description: string;
  dent: string;
  price: number;
  toothNumbers?: number[];
  _odontogramKey?: string;
  category?: string;
  odontogramSurfaces?: string[];
  odontogramNotes?: string;
  odontogramTreatmentCode?: string;
}

export interface InstallmentItem {
  id: number;
  date: string;
  amount: number;
  label: string;
}

interface AccountingState {
  items: PriceItem[];
  paymentMode: PaymentMode;
  installments: InstallmentItem[];
  isAccounted: boolean;
  paymentStatus: string;
  paymentStatusGuardMessage: string | null;
  isGlobalNote: boolean;

  groupTreatmentName: string;
  groupTreatmentPrice: number | '';

  showOdontoPanoramique: boolean;
  odontogramMode: 'individual' | 'group' | 'ortho';
  groupSelectedTeeth: number[];

  actSuggestions: any[];
  activeActSearchId: number | null;

  setItems: (items: PriceItem[] | ((prev: PriceItem[]) => PriceItem[])) => void;
  setPaymentMode: (mode: PaymentMode) => void;
  setInstallments: (installments: InstallmentItem[]) => void;
  setIsAccounted: (val: boolean) => void;
  setPaymentStatus: (status: string) => void;
  clearPaymentStatusGuard: () => void;
  setIsGlobalNote: (val: boolean) => void;

  setGroupTreatmentName: (name: string) => void;
  setGroupTreatmentPrice: (price: number | '') => void;
  setShowOdontoPanoramique: (val: boolean | ((prev: boolean) => boolean)) => void;
  setOdontogramMode: (mode: 'individual' | 'group' | 'ortho') => void;
  setGroupSelectedTeeth: (teeth: number[] | ((prev: number[]) => number[])) => void;

  setActSuggestions: (suggestions: any[]) => void;
  setActiveActSearchId: (id: number | null) => void;

  reset: () => void;
}

const initialState = {
  items: [],
  paymentMode: '' as PaymentMode,
  installments: [],
  isAccounted: true,
  paymentStatus: 'EN_ATTENTE',
  paymentStatusGuardMessage: null as string | null,
  isGlobalNote: false,
  groupTreatmentName: '',
  groupTreatmentPrice: '' as number | '',
  showOdontoPanoramique: true,
  odontogramMode: 'individual' as const,
  groupSelectedTeeth: [],
  actSuggestions: [],
  activeActSearchId: null,
};

export const useAccountingStore = create<AccountingState>((set) => ({
  ...initialState,

  setItems: (val) => set((state) => ({ items: typeof val === 'function' ? val(state.items) : val })),
  setPaymentMode: (paymentMode) => set({ paymentMode }),
  setInstallments: (installments) => set({ installments }),
  setIsAccounted: (isAccounted) => set({ isAccounted }),
  setPaymentStatus: (paymentStatus) => {
    if (paymentStatus === 'PARTIEL') {
      set({ paymentStatusGuardMessage: PARTIAL_PAYMENT_DISABLED_REASON });
      return;
    }
    if (paymentStatus !== 'EN_ATTENTE' && paymentStatus !== 'PAYE') {
      set({ paymentStatusGuardMessage: 'Statut de paiement invalide.' });
      return;
    }
    set({ paymentStatus, paymentStatusGuardMessage: null });
  },
  clearPaymentStatusGuard: () => set({ paymentStatusGuardMessage: null }),
  setIsGlobalNote: (isGlobalNote) => set({ isGlobalNote }),

  setGroupTreatmentName: (groupTreatmentName) => set({ groupTreatmentName }),
  setGroupTreatmentPrice: (groupTreatmentPrice) => set({ groupTreatmentPrice }),
  setShowOdontoPanoramique: (val) => set((state) => ({ showOdontoPanoramique: typeof val === 'function' ? val(state.showOdontoPanoramique) : val })),
  setOdontogramMode: (odontogramMode) => set({ odontogramMode }),
  setGroupSelectedTeeth: (val) => set((state) => ({ groupSelectedTeeth: typeof val === 'function' ? val(state.groupSelectedTeeth) : val })),

  setActSuggestions: (actSuggestions) => set({ actSuggestions }),
  setActiveActSearchId: (activeActSearchId) => set({ activeActSearchId }),

  reset: () => set(initialState),
}));