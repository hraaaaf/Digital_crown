import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import type { AppUser } from '../../types';

const hook=vi.hoisted(()=>vi.fn());
vi.mock('../dashboard/hooks/useTodayAppointments',()=>({useTodayAppointments:hook}));
import { R3AgendaReadonlyPanel } from './R3AgendaReadonlyPanel';

const actor=(permissions:Record<string,boolean>)=>({
  id:'synthetic-user',role:'SECRETAIRE',employer_id:11,permissions,
} as unknown as AppUser);
const appointment={
  id:123,start_time:'2026-10-26T09:30:00',status:'CONFIRMÉ',
  patient:{id:99,nom:'Synthetic',prenom:'A'},
};
beforeEach(()=>hook.mockReturnValue({
  appointmentsState:'ready',appointments:[appointment],refreshAppointments:vi.fn(),
}));
afterEach(()=>{cleanup();hook.mockReset();});

describe('LOT07 R3 real authenticated Cabinet agenda — R-only',()=>{
  it('projects a real verified appointment without exposing any write action',()=>{
    const {container}=render(<R3AgendaReadonlyPanel user={actor({agenda:true,patients:true})}/>);
    expect(screen.getByTestId('r3-real-agenda')).toBeTruthy();
    expect(screen.getByText('A Synthetic')).toBeTruthy();
    expect(screen.getByText('09:30')).toBeTruthy();
    expect(screen.getByText('CONFIRMÉ')).toBeTruthy();
    expect(container.querySelectorAll('button')).toHaveLength(1);
    fireEvent.click(screen.getByRole('button',{name:"Actualiser l'agenda"}));
    expect(hook.mock.results[0].value.refreshAppointments).toHaveBeenCalledTimes(1);
  });

  it('redacts appointment identities when Agenda is allowed but Patients is denied',()=>{
    render(<R3AgendaReadonlyPanel user={actor({agenda:true,patients:false})}/>);
    expect(screen.queryByText('A Synthetic')).toBeNull();
    expect(screen.getByText('Rendez-vous')).toBeTruthy();
  });

  it('refuses absent Agenda permission, and never presents malformed API data as empty',()=>{
    const no=render(<R3AgendaReadonlyPanel user={actor({agenda:false,patients:true})}/>);
    expect(screen.getByRole('alert').textContent).toContain('refusé');
    expect(screen.queryByText('Synthetic')).toBeNull();
    no.unmount();
    hook.mockReturnValue({
      appointmentsState:'ready',appointments:[{id:'unsafe',start_time:null}],refreshAppointments:vi.fn(),
    });
    render(<R3AgendaReadonlyPanel user={actor({agenda:true,patients:true})}/>);
    expect(screen.getByRole('alert').textContent).toContain('indisponible');
    expect(screen.queryByText("Aucun rendez-vous aujourd'hui.")).toBeNull();
  });

  it('does not manufacture empty state during loading or failed request',()=>{
    hook.mockReturnValue({appointmentsState:'loading',appointments:null,refreshAppointments:vi.fn()});
    const v=render(<R3AgendaReadonlyPanel user={actor({agenda:true,patients:true})}/>);
    expect(screen.getByRole('status').textContent).toContain('Chargement');
    v.unmount();
    hook.mockReturnValue({appointmentsState:'error',appointments:null,refreshAppointments:vi.fn()});
    render(<R3AgendaReadonlyPanel user={actor({agenda:true,patients:true})}/>);
    expect(screen.getByRole('alert').textContent).toContain('indisponible');
  });
});
