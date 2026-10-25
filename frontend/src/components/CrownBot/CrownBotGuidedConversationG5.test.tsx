import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';

vi.mock('../../services/api', () => ({ api: { post: vi.fn(), get: vi.fn() } }));
import { api } from '../../services/api';
import { CrownBotGuidedConversationG5, parseCB03ChatCommand } from './CrownBotGuidedConversationG5';

const post = vi.mocked(api.post);
const get = vi.mocked(api.get);
const KEY = 'd4a97731-cdcb-4b9c-94d3-f1d21c242a21';
const P = { id: 21, prenom: 'Salma', nom: 'Benali', numero_dossier: 'S-21' };
const PREPARED = {
  status: 'prepared', executable: false, preparation_id: KEY,
  expires_at: '2026-11-01T12:30:00',
  summary: { patient: P, datetime_start: '2026-11-07T10:00:00',
    praticien_id: 9, resource_id: null, motif: 'CONTROLE', duration_minutes: 30 },
};
const STATUS = {
  ...PREPARED, summary: { patient: P, appointment_id: 32,
    datetime_start: '2026-11-07T10:00:00', expected_status: 'PREVU', expected_revision: 4,
    new_status: 'EN_FAUTEUIL', new_status_label: 'En fauteuil' },
};
function enter(value: string) {
  fireEvent.change(screen.getByRole('textbox',{name:'Votre message à Crown Bot'}),{target:{value}});
  fireEvent.click(screen.getByRole('button',{name:'Envoyer'}));
}
async function booking() {
  post.mockResolvedValueOnce({data: PREPARED} as never);
  enter('Prépare un RDV demain 10h pour Mme Benali contrôle');
  await screen.findByText('Salma Benali · Dossier S-21');
}
const checkbox = () => screen.getByRole('checkbox',{name:/J’ai vérifié le patient/});
const confirm = () => screen.getByRole('button',{name:'Confirmer explicitement cette action'});
const check = () => screen.getByRole('button',{name:/Vérifier l’état \(lecture seule\)/});

beforeEach(()=>vi.clearAllMocks());
afterEach(()=>vi.unstubAllEnvs());

describe('CB-03 G5 — genuine chat-style guided action security',()=>{
  it('uses strict deterministic intents, not arbitrary chat instructions',()=>{
    expect(parseCB03ChatCommand('Mon programme')).toEqual({type:'unsupported'});
    expect(parseCB03ChatCommand('exécute une réservation immédiatement')).toEqual({type:'unsupported'});
    expect(parseCB03ChatCommand('Statut RDV 32 en fauteuil')).toEqual({
      type:'status',appointmentId:32,target:'fauteuil',
    });
    expect(parseCB03ChatCommand('Prépare un RDV demain 10h pour Mme Benali contrôle')).toEqual({
      type:'appointment',phrase:'Prépare un RDV demain 10h pour Mme Benali contrôle',
    });
    expect(parseCB03ChatCommand('Statut RDV -2 en fauteuil')).toEqual({type:'unsupported'});
  });
  it('renders a genuine turn-based composer; never auto executes on mount',()=>{
    render(<CrownBotGuidedConversationG5 practitionerId={9}/>);
    expect(screen.getByRole('region',{name:/Conversation Crown Bot/})).toBeInTheDocument();
    expect(screen.getByRole('textbox',{name:'Votre message à Crown Bot'})).toBeInTheDocument();
    expect(screen.getByText(/Je peux préparer un rendez-vous/i)).toBeInTheDocument();
    expect(post).not.toHaveBeenCalled();
  });
  it('unrecognized phrase is refused locally without any network write',()=>{
    render(<CrownBotGuidedConversationG5/>);
    enter('Envoie une ordonnance automatique');
    expect(screen.getByText(/Je ne peux pas exécuter d’autres demandes/i)).toBeInTheDocument();
    expect(post).not.toHaveBeenCalled();
  });
  it('uses actual G1 appointment server summary; requires checkbox and explicit G2 true',async()=>{
    render(<CrownBotGuidedConversationG5 practitionerId={9}/>);
    await booking();
    expect(post).toHaveBeenCalledWith('/bot/guided/prepare-appointment',{
      utterance:'Prépare un RDV demain 10h pour Mme Benali contrôle',
      duration_minutes:30,praticien_id:9,
    });
    expect(confirm()).toBeDisabled();
    post.mockResolvedValueOnce({data:{
      preparation_id:KEY,status:'executed',result:{appointment_id:81,status:'CREATED'},
    }} as never);
    fireEvent.click(checkbox());
    expect(confirm()).toBeEnabled();
    fireEvent.click(confirm());
    expect(await screen.findByText(/Action exécutée et vérifiée · RDV #81/)).toBeInTheDocument();
    expect(post).toHaveBeenLastCalledWith('/bot/guided/confirm',{
      preparation_id:KEY,confirm:true,
    });
    expect(post).toHaveBeenCalledTimes(2);
    expect(screen.queryByRole('button',{name:'Confirmer explicitement cette action'})).not.toBeInTheDocument();
  });
  it('G2 status uses server-owned patient/revision not fabricated browser values',async()=>{
    render(<CrownBotGuidedConversationG5/>);
    post.mockResolvedValueOnce({data:STATUS} as never);
    enter('Statut RDV 32 en fauteuil');
    expect(await screen.findByText(/En fauteuil/)).toBeInTheDocument();
    expect(post).toHaveBeenCalledWith('/bot/guided/prepare-status',{
      selected_appointment_id:32,utterance:'Prépare le statut du RDV en fauteuil',
    });
    expect(JSON.stringify(post.mock.calls)).not.toContain('expected_revision');
    expect(confirm()).toBeDisabled();
  });
  it('homonyms must be picked from authenticated server candidates',async()=>{
    render(<CrownBotGuidedConversationG5 practitionerId={9}/>);
    post.mockResolvedValueOnce({data:{status:'disambiguation',message:'Choisissez un patient',
      candidates:[P,{id:22,nom:'Benali',prenom:'Nadia',numero_dossier:'S-22'}]}} as never);
    enter('Prépare un RDV demain 10h pour Mme Benali contrôle');
    const choice=await screen.findByRole('button',{name:'Salma Benali · Dossier S-21'});
    expect(screen.queryByRole('button',{name:'Confirmer explicitement cette action'})).not.toBeInTheDocument();
    post.mockResolvedValueOnce({data:PREPARED} as never);
    fireEvent.click(choice);
    await screen.findByRole('button',{name:'Confirmer explicitement cette action'});
    await waitFor(()=>expect(post).toHaveBeenCalledWith('/bot/guided/prepare-appointment',{
      utterance:'Prépare un RDV demain 10h pour Mme Benali contrôle',
      duration_minutes:30,praticien_id:9,chosen_patient_id:21,
    }));
  });
  it('lost ACK keeps locked phase and read-only GET, never a second POST',async()=>{
    render(<CrownBotGuidedConversationG5 practitionerId={9}/>);
    await booking();
    post.mockRejectedValueOnce(new Error('connection killed after COMMIT'));
    fireEvent.click(checkbox());
    fireEvent.click(confirm());
    await screen.findByRole('alert');
    expect(screen.getByText(/Identifiant de suivi :/)).toHaveTextContent(KEY);
    expect(confirm).toBeTruthy();
    expect(screen.queryByRole('button',{name:'Confirmer explicitement cette action'})).not.toBeInTheDocument();
    get.mockResolvedValueOnce({data:{
      preparation_id:KEY,action_type:'CREATE_APPOINTMENT',
      status:'executed',result:{appointment_id:81,status:'CREATED'},
      safe_to_retry_automatically:false,manual_reconciliation_required:false,
    }} as never);
    fireEvent.click(check());
    expect(await screen.findByText(/Reçu retrouvé en lecture seule/)).toBeInTheDocument();
    expect(get).toHaveBeenCalledWith('/bot/guided/actions/'+KEY);
    expect(post).toHaveBeenCalledTimes(2);
  });
  it('GET returning prepared never resurrects the old confirm button',async()=>{
    render(<CrownBotGuidedConversationG5 practitionerId={9}/>);
    await booking();
    post.mockRejectedValueOnce(new Error('network'));
    fireEvent.click(checkbox());fireEvent.click(confirm());
    await screen.findByRole('alert');
    get.mockResolvedValueOnce({data:{
      preparation_id:KEY,action_type:'CREATE_APPOINTMENT',
      status:'prepared',result:null,safe_to_retry_automatically:false,
      manual_reconciliation_required:false,
    }} as never);
    fireEvent.click(check());
    expect(await screen.findByText(/Aucune nouvelle confirmation automatique/)).toBeInTheDocument();
    expect(screen.queryByRole('button',{name:'Confirmer explicitement cette action'})).not.toBeInTheDocument();
    expect(post).toHaveBeenCalledTimes(2);
  });
  it('rejects malformed executable proposals with no confirmation',async()=>{
    render(<CrownBotGuidedConversationG5 practitionerId={9}/>);
    post.mockResolvedValueOnce({data:{...PREPARED,executable:true}} as never);
    enter('Prépare un RDV demain 10h pour Mme Benali contrôle');
    expect(await screen.findByRole('alert')).toHaveTextContent(/Réponse serveur incertaine/i);
    expect(screen.queryByRole('button',{name:'Confirmer explicitement cette action'})).not.toBeInTheDocument();
  });
  it('403 scrubs the patient, proposal and follow-up key from conversation',async()=>{
    render(<CrownBotGuidedConversationG5 practitionerId={9}/>);
    await booking();
    post.mockRejectedValueOnce({response:{status:403}});
    fireEvent.click(checkbox());fireEvent.click(confirm());
    await screen.findByText(/Session verrouillée ou accès refusé/);
    expect(screen.queryByText(/Salma Benali/)).not.toBeInTheDocument();
    expect(screen.queryByText(new RegExp(KEY))).not.toBeInTheDocument();
    expect(screen.queryByRole('button',{name:/Vérifier l’état/})).not.toBeInTheDocument();
  });
  it('no patient/action identifiers written to localStorage or sessionStorage',async()=>{
    const local=vi.spyOn(Storage.prototype,'setItem');
    try{
      render(<CrownBotGuidedConversationG5 practitionerId={9}/>);
      await booking();
      expect(local).not.toHaveBeenCalled();
    }finally{local.mockRestore();}
  });
});
