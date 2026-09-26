import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { StudioTabs } from './StudioTabs';
import { StudioFooter } from './StudioFooter';
import { useAccountingStore } from '../store/useAccountingStore';

afterEach(() => {
  cleanup();
  useAccountingStore.getState().reset();
});

describe('Document Studio G4 shell controls', () => {
  it('routes every allowed document tab through the canonical tab-change boundary', () => {
    const onTabChange=vi.fn();
    render(
      <StudioTabs
        activeTab="ordonnance"
        onTabChange={onTabChange}
        allowedTabs={['ordonnance','certificat','devis','honoraires','echeancier','libre']}
      />,
    );

    for (const [name,tab] of [
      ['Ordonnance','ordonnance'],
      ['Certificat','certificat'],
      ['Devis','devis'],
      ['Note Honoraires','honoraires'],
      ['Suivi Paiement','echeancier'],
      ['Document Libre','libre'],
    ] as const) {
      fireEvent.click(screen.getByRole('button',{name:new RegExp(name,'i')}));
      expect(onTabChange).toHaveBeenLastCalledWith(tab);
    }
  });

  it('hides disallowed document tabs rather than exposing inert controls', () => {
    render(
      <StudioTabs activeTab="ordonnance" onTabChange={vi.fn()} allowedTabs={['ordonnance','certificat']} />,
    );
    expect(screen.getByRole('button',{name:/Ordonnance/i})).toBeTruthy();
    expect(screen.getByRole('button',{name:/Certificat/i})).toBeTruthy();
    expect(screen.queryByRole('button',{name:/Honoraires/i})).toBeNull();
    expect(screen.queryByRole('button',{name:/Devis/i})).toBeNull();
  });

  it('maps preview/save/print buttons to distinct generation contracts for accounting documents', () => {
    const onGenerate=vi.fn();
    const onTogglePreview=vi.fn();
    render(
      <StudioFooter
        loading={false}
        activeTab="honoraires"
        onGenerate={onGenerate}
        showPrintWarning={false}
        onCloseWarning={vi.fn()}
        hasChanges
        total={1250}
        sideStudioType="NONE"
        onTogglePreview={onTogglePreview}
      />,
    );

    const totalLabel=screen.getByText('Total', { exact: true });
    expect(totalLabel.parentElement?.textContent?.replace(/\s/g,'')).toContain('1250MAD');
    fireEvent.click(screen.getByRole('button',{name:/Aperçu/i}));
    expect(onTogglePreview).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole('button',{name:/Enregistrer/i}));
    expect(onGenerate).toHaveBeenCalledWith(true,false,false,false);

    fireEvent.click(screen.getByRole('button',{name:/Imprimer/i}));
    expect(onGenerate).toHaveBeenCalledWith(false,true,false,false);

    fireEvent.click(screen.getByRole('button',{name:'Payé'}));
    fireEvent.click(screen.getByRole('button',{name:'TPE'}));
    expect(useAccountingStore.getState().paymentStatus).toBe('PAYE');
    expect(useAccountingStore.getState().paymentMode).toBe('TPE');

    fireEvent.click(screen.getByRole('button',{name:'Partiel'}));
    expect(useAccountingStore.getState().paymentStatus).toBe('PAYE');
    expect(screen.getByRole('alert').textContent).toMatch(/montant encaissé explicite/i);

    fireEvent.click(screen.getByRole('button',{name:'Compris'}));
    fireEvent.click(screen.getByRole('button',{name:'À régler'}));
    expect(useAccountingStore.getState().paymentStatus).toBe('EN_ATTENTE');
  });

  it('uses fresh-PDF generation for certificate/libre print preparation', () => {
    const onGenerate=vi.fn();
    render(
      <StudioFooter
        loading={false}
        activeTab="certificat"
        onGenerate={onGenerate}
        showPrintWarning={false}
        onCloseWarning={vi.fn()}
        hasChanges
        sideStudioType="NONE"
        onTogglePreview={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole('button',{name:/Préparer impression/i}));
    expect(onGenerate).toHaveBeenCalledWith(true,false,false,true);
  });

  it('requires explicit confirmation when the direct-print warning is shown', () => {
    const onGenerate=vi.fn();
    const onCloseWarning=vi.fn();
    render(
      <StudioFooter
        loading={false}
        activeTab="honoraires"
        onGenerate={onGenerate}
        showPrintWarning
        onCloseWarning={onCloseWarning}
        hasChanges
        total={100}
        sideStudioType="NONE"
        onTogglePreview={vi.fn()}
      />,
    );

    const dialog=screen.getByRole('dialog');
    fireEvent.click(screen.getByRole('button',{name:'Annuler'}));
    expect(onCloseWarning).toHaveBeenCalledTimes(1);
    expect(onGenerate).not.toHaveBeenCalledWith(true,true,false,true);

    fireEvent.click(screen.getByRole('button',{name:'Confirmer'}));
    expect(onGenerate).toHaveBeenCalledWith(true,true,false,true);
    expect(dialog).toBeTruthy();
  });
});
