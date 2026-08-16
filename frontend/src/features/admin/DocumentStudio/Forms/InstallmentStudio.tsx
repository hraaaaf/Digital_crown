import React, { useEffect } from 'react';
import { api } from '../../../../services/api';
import { InstallmentStudio as InstallmentStudioInner } from './InstallmentStudioInner';
import { isInstallmentDirty, setInstallmentDirty } from '../InstallmentDirtyState';

type InstallmentStudioProps = React.ComponentProps<typeof InstallmentStudioInner>;

const isUnsavedDraftMutation = (target: EventTarget | null): boolean => {
  if (!(target instanceof HTMLInputElement || target instanceof HTMLSelectElement)) return false;
  if (target.disabled) return false;

  if (target instanceof HTMLSelectElement || target.type === 'checkbox') return false;

  const row = target.closest('tr');
  if (!row) return true;

  const amountInput = row.querySelector<HTMLInputElement>('input[type="number"]');
  return !amountInput?.disabled;
};

export const InstallmentStudio: React.FC<InstallmentStudioProps> = props => {
  useEffect(() => {
    setInstallmentDirty(false);
  }, [props.patientId]);

  useEffect(() => {
    const beforeUnload = (event: BeforeUnloadEvent) => {
      if (!isInstallmentDirty()) return;
      event.preventDefault();
      event.returnValue = '';
    };

    const responseInterceptors = api.interceptors?.response;
    const responseInterceptor = responseInterceptors?.use(response => {
      const method = response.config?.method?.toLowerCase();
      const url = response.config?.url || '';
      if (method === 'post' && url === '/installments/') {
        setInstallmentDirty(false);
      }
      return response;
    });

    window.addEventListener('beforeunload', beforeUnload);
    return () => {
      window.removeEventListener('beforeunload', beforeUnload);
      if (responseInterceptor !== undefined) {
        responseInterceptors?.eject(responseInterceptor);
      }
      setInstallmentDirty(false);
    };
  }, []);

  return (
    <div
      className="contents"
      onChangeCapture={event => {
        if (isUnsavedDraftMutation(event.target)) setInstallmentDirty(true);
      }}
      onClickCapture={event => {
        const button = (event.target as HTMLElement).closest('button');
        if (!button) return;

        const text = button.textContent?.trim() || '';
        const ariaLabel = button.getAttribute('aria-label') || '';

        if (text === 'Nouveau plan') {
          if (isInstallmentDirty()) {
            const confirmed = window.confirm('Abandonner le brouillon d’échéancier en cours ?');
            if (!confirmed) {
              event.preventDefault();
              event.stopPropagation();
              return;
            }
          }
          setInstallmentDirty(false);
          return;
        }

        if (
          text.includes('Générer le tableau') ||
          text.includes('Ajouter manuellement') ||
          ariaLabel.startsWith('Supprimer ')
        ) {
          setInstallmentDirty(true);
        }
      }}
    >
      <InstallmentStudioInner {...props} />
    </div>
  );
};