import React from 'react';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { CabinetTwoViewsPilot, type CabinetTwoViewsPatient } from './CabinetTwoViewsPilot';

vi.mock('../patients/components/PatientMediaTimeline', () => ({
  PatientMediaTimeline: ({ patientId, compactHeader }: { patientId: number; compactHeader?: boolean }) => (
    <div data-testid="module-mediatheque-reel" data-compact-header={String(Boolean(compactHeader))}>Médias du patient {patientId}</div>
  ),
}));
vi.mock('../ortho/OrthoLongitudinalComparePanel', () => ({
  OrthoLongitudinalComparePanel: ({ patientId, embedded }: { patientId: number; embedded?: boolean }) => (
    <div data-testid="module-suivi-reel" data-embedded={String(Boolean(embedded))}>Comparaison longitudinale du patient {patientId}</div>
  ),
}));

const listeners = new Set<() => void>();
let desktop = false;
const patient: CabinetTwoViewsPatient = {
  id: 17, numero_dossier: 'DOS-17', nom: 'DEMONSTRATION', prenom: 'Patient',
  date_naissance: '2001-01-01', telephone: '00 00 00 00', assurance: 'Non spécifiée',
  antecedents_medicaux: 'Aucun renseignement', dossier: { is_ortho_active: true },
};

beforeEach(() => {
  desktop = false;
  listeners.clear();
  Object.defineProperty(window, 'matchMedia', { configurable:true, value:vi.fn(() => ({
    get matches() { return desktop; },
    media:'(min-width: 1280px)',
    addEventListener: (_:string, cb:() => void) => listeners.add(cb),
    removeEventListener: (_:string, cb:() => void) => listeners.delete(cb),
  })) });
});
afterEach(() => cleanup());

describe('Vues multiples Cabinet — deux véritables modules liés à un patient', () => {
  it('conserve une seule médiathèque originale sur petit écran', () => {
    render(<CabinetTwoViewsPilot patient={patient} canCephalo />);
    expect(screen.queryByRole('region',{name:'Vues multiples du patient actif'})).toBeNull();
    expect(screen.getAllByTestId('module-mediatheque-reel')).toHaveLength(1);
    expect(screen.getByTestId('module-mediatheque-reel').getAttribute('data-compact-header')).toBe('false');
    expect(screen.queryByTestId('module-suivi-reel')).toBeNull();
  });
  it('charge le dossier réel déjà reçu et exactement une médiathèque du même patient', () => {
    desktop = true;
    render(<CabinetTwoViewsPilot patient={patient} canCephalo />);
    expect(screen.getByRole('region',{name:'Vues multiples du patient actif'})).toBeTruthy();
    expect(screen.getByText('DOS-17')).toBeTruthy();
    expect(screen.getByText('Patient DEMONSTRATION')).toBeTruthy();
    expect(screen.getByText('01/01/2001')).toBeTruthy();
    expect(screen.queryByText('2001-01-01')).toBeNull();
    expect(screen.getByRole('region', { name: 'Médiathèque clinique' })).toBeTruthy();
    expect(screen.getAllByTestId('module-mediatheque-reel')).toHaveLength(1);
    expect(screen.getByTestId('module-mediatheque-reel').getAttribute('data-compact-header')).toBe('true');
    expect(screen.queryAllByTestId('module-suivi-reel')).toHaveLength(0);
  });
  it('présente le vrai comparateur T0/T1 uniquement si Céphalo est autorisée', () => {
    desktop = true;
    const {rerender}=render(<CabinetTwoViewsPilot patient={patient} canCephalo={false}/>);
    expect(screen.queryByRole('option',{name:'Suivi T0 / T1'})).toBeNull();
    rerender(<CabinetTwoViewsPilot patient={patient} canCephalo/>);
    fireEvent.change(screen.getByRole('combobox',{name:'Contenu du premier panneau'}),{target:{value:'suivi'}});
    expect(screen.getByTestId('module-suivi-reel').textContent).toContain('17');
    expect(screen.getByTestId('module-suivi-reel').getAttribute('data-embedded')).toBe('true');
    expect(screen.getAllByTestId('module-mediatheque-reel')).toHaveLength(1);
    rerender(<CabinetTwoViewsPilot patient={patient} canCephalo={false}/>);
    expect(screen.queryByTestId('module-suivi-reel')).toBeNull();
    expect(screen.getByText('DOS-17')).toBeTruthy();
  });
  it('formate un horodatage ISO sans décaler la date civile', () => {
    desktop = true;
    render(<CabinetTwoViewsPilot patient={{ ...patient, date_naissance: '2001-01-01T00:00:00' }} canCephalo />);
    expect(screen.getByText('01/01/2001')).toBeTruthy();
    expect(screen.queryByText('2001-01-01T00:00:00')).toBeNull();
  });
  it('affiche une date invalide comme non renseignée, sans fabriquer une naissance', () => {
    desktop = true;
    render(<CabinetTwoViewsPilot patient={{ ...patient, date_naissance: '2001-02-31T00:00:00' }} canCephalo />);
    const birth = screen.getByText('Naissance').closest('div');
    expect(birth?.querySelector('dd')?.textContent).toBe('Non renseigné');
    expect(screen.queryByText('03/03/2001')).toBeNull();
  });
  it('redimensionne au clavier, échange les panneaux et permet de tout rétablir', () => {
    desktop = true;
    render(<CabinetTwoViewsPilot patient={patient} canCephalo/>);
    const sep=screen.getByRole('separator',{name:'Redimensionner les vues'});
    expect(sep.getAttribute('aria-valuenow')).toBe('45');
    fireEvent.keyDown(sep,{key:'ArrowRight'});
    expect(sep.getAttribute('aria-valuenow')).toBe('50');
    fireEvent.keyDown(sep,{key:'End'});
    expect(sep.getAttribute('aria-valuenow')).toBe('63');
    fireEvent.click(screen.getByRole('button',{name:'Échanger les vues'}));
    const surface=document.querySelector('[data-v15-07-split-container]') as HTMLDivElement;
    expect(surface.style.flexDirection).toBe('row-reverse');
    fireEvent.click(screen.getByRole('button',{name:'Réinitialiser'}));
    expect(sep.getAttribute('aria-valuenow')).toBe('45');
    expect(surface.style.flexDirection).toBe('row');
  });
  it('ne garde aucune donnée du patient précédent après changement de contexte', () => {
    desktop = true;
    const {rerender}=render(<CabinetTwoViewsPilot patient={patient} canCephalo/>);
    rerender(<CabinetTwoViewsPilot patient={{...patient,id:22,nom:'AUTRE',numero_dossier:'DOS-22'}} canCephalo/>);
    expect(screen.queryByText('DOS-17')).toBeNull();
    expect(screen.getByText('DOS-22')).toBeTruthy();
    expect(screen.getAllByTestId('module-mediatheque-reel')).toHaveLength(1);
    expect(screen.getByTestId('module-mediatheque-reel').textContent).toContain('22');
    act(() => { desktop=false; listeners.forEach(cb=>cb()); });
    expect(screen.queryByRole('region',{name:'Vues multiples du patient actif'})).toBeNull();
    expect(screen.getAllByTestId('module-mediatheque-reel')).toHaveLength(1);
  });
});
