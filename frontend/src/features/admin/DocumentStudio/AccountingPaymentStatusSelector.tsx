import React from 'react';
import { cn } from '../../../utils/cn';
import {
  getDocumentPaymentStatusOptions,
  type DocumentPaymentStatus,
} from './AccountingPaymentPolicy';

interface AccountingPaymentStatusSelectorProps {
  value: DocumentPaymentStatus;
  onChange: (status: DocumentPaymentStatus) => void;
}

const activeClasses: Record<DocumentPaymentStatus, string> = {
  EN_ATTENTE: 'text-amber-600 bg-white shadow-sm border border-slate-100',
  PARTIEL: 'text-blue-600 bg-white shadow-sm border border-slate-100',
  PAYE: 'text-emerald-600 bg-white shadow-sm border border-slate-100',
};

export const AccountingPaymentStatusSelector: React.FC<AccountingPaymentStatusSelectorProps> = ({
  value,
  onChange,
}) => {
  const options = getDocumentPaymentStatusOptions();

  return (
    <div className="space-y-2">
      <div className="flex bg-slate-50/50 p-1.5 rounded-[1.5rem] border border-slate-100 gap-1">
        {options.map(option => (
          <button
            key={option.id}
            type="button"
            disabled={!option.enabled}
            aria-disabled={!option.enabled}
            aria-describedby={!option.enabled ? `payment-status-${option.id}-reason` : undefined}
            onClick={() => option.enabled && onChange(option.id)}
            className={cn(
              'flex-1 py-3.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all',
              value === option.id && option.enabled
                ? activeClasses[option.id]
                : 'text-slate-400 hover:text-slate-600',
              !option.enabled && 'cursor-not-allowed opacity-45 hover:text-slate-400',
            )}
            title={option.reason}
          >
            {option.label}
          </button>
        ))}
      </div>
      {options.filter(option => !option.enabled && option.reason).map(option => (
        <p
          key={option.id}
          id={`payment-status-${option.id}-reason`}
          className="px-2 text-[10px] font-semibold text-slate-500"
        >
          {option.reason}
        </p>
      ))}
    </div>
  );
};
