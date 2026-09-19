import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { AgendaView } from './AgendaView';

vi.mock('@dnd-kit/core', () => ({
  DndContext: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  TouchSensor: function TouchSensor() {},
  MouseSensor: function MouseSensor() {},
  useSensor: () => ({}),
  useSensors: () => [],
}));
vi.mock('../components/DraggableApptCard', () => ({
  DraggableApptCard: ({ apt, onStatusChange, openApptWhatsApp, handleDeleteAppt, handleOpenSignature }: any) => (
    <div>
      <span>{apt.patient_name}</span>
      <button onClick={() => onStatusChange(apt.id, 'EN_ATTENTE')}>Set waiting</button>
      <button onClick={() => openApptWhatsApp(apt)}>WhatsApp</button>
      <button onClick={() => handleDeleteAppt(apt.id)}>Delete appt</button>
      <button onClick={() => handleOpenSignature(apt.patient_id, apt.patient_name)}>Signature</button>
    </div>
  ),
}));
vi.mock('../components/DroppableDay', () => ({
  DroppableDay: ({ label, onClick }: any) => <button onClick={onClick}>Day {label}</button>,
}));
vi.mock('../components/AddApptModal', () => ({
  AddApptModal: ({ onClose, onSuccess }: any) => (
    <div>
      <span>Add appointment modal</span>
      <button onClick={onSuccess}>Save appointment</button>
      <button onClick={onClose}>Close appointment</button>
    </div>
  ),
}));

const snapshot:any = {
  generated_at:'2026-09-19T00:00:00Z',
  appointments:[{
    id:1, patient_id:7, time:'10:15', date:'2026-09-19', patient_name:'Sara BENALI',
    phone:'0612345678', motif:'Contrôle', status:'PLANIFIE', duration_minutes:30
  }],
  finance:{today_revenue:0,month_revenue:0,month_variation:0,appointments_count:1,weekly_revenue:[],total_patients:1,total_debt:0},
  debtors:[]
};

const props = {
  snapshot,
  syncStatus:'success' as const,
  selectedDate:'2026-09-19',
  setSelectedDate:vi.fn(),
  patients:[],
  onStatusChange:vi.fn(),
  onRescheduleAppt:vi.fn(),
  openApptWhatsApp:vi.fn(),
  handleDeleteAppt:vi.fn(),
  handleOpenSignature:vi.fn(),
  onRefresh:vi.fn(),
  onPatientCreated:vi.fn(),
};

afterEach(() => { cleanup(); vi.clearAllMocks(); });

describe('AgendaView G3 mobile interactive matrix', () => {
  it('switches day/week/month views and changes selected calendar date', () => {
    render(<AgendaView {...props} />);

    expect(screen.getByText('Sara BENALI')).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'semaine' }));
    expect(screen.getByText(/^Day /)).toBeTruthy();

    fireEvent.click(screen.getAllByText(/^Day /)[0]);
    expect(props.setSelectedDate).toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'mois' }));
    expect(screen.getByText(/septembre 2026/i)).toBeTruthy();
  });

  it('opens/closes the add appointment modal and refreshes after success', () => {
    render(<AgendaView {...props} />);

    fireEvent.click(screen.getByRole('button', { name: 'Ajouter un rendez-vous' }));
    expect(screen.getByText('Add appointment modal')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Save appointment' }));
    expect(props.onRefresh).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole('button', { name: 'Close appointment' }));
    expect(screen.queryByText('Add appointment modal')).toBeNull();
  });

  it('delegates appointment status, WhatsApp, delete and signature buttons to canonical handlers', () => {
    render(<AgendaView {...props} />);

    fireEvent.click(screen.getByRole('button', { name: 'Set waiting' }));
    expect(props.onStatusChange).toHaveBeenCalledWith(1, 'EN_ATTENTE');

    fireEvent.click(screen.getByRole('button', { name: 'WhatsApp' }));
    expect(props.openApptWhatsApp).toHaveBeenCalledWith(snapshot.appointments[0]);

    fireEvent.click(screen.getByRole('button', { name: 'Delete appt' }));
    expect(props.handleDeleteAppt).toHaveBeenCalledWith(1);

    fireEvent.click(screen.getByRole('button', { name: 'Signature' }));
    expect(props.handleOpenSignature).toHaveBeenCalledWith(7, 'Sara BENALI');
  });

  it('distinguishes loading, hard error and truthful empty agenda states', () => {
    const a=render(<AgendaView {...props} snapshot={null} syncStatus="loading" />);
    expect(a.container.querySelectorAll('.h-24').length).toBeGreaterThan(0);
    a.unmount();

    render(<AgendaView {...props} snapshot={null} syncStatus="error" />);
    expect(screen.getByText('Données indisponibles')).toBeTruthy();
    cleanup();

    render(<AgendaView {...props} snapshot={{...snapshot,appointments:[]}} />);
    expect(screen.getByText('Aucun RDV')).toBeTruthy();
  });
});
