import { Calendar, XCircle } from 'lucide-react';
import { useState, useRef } from 'react';
import toast from 'react-hot-toast';
import { MobileStorage } from '../../../../services/zka/MobileStorage';

export function AddApptModal({
  selectedDate,
  patients,
  onClose,
  onSuccess,
  onPatientCreated,
}: {
  selectedDate: string;
  patients: { id: number; name: string; phone: string | null }[];
  onClose: () => void;
  onSuccess: () => void;
  onPatientCreated: (pt: { id: number; name: string; phone: string | null }) => void;
}) {
  const [newApt, setNewApt] = useState({ patient_name: '', motif: 'Consultation', isCustomMotif: false, time: '09:00', duration_minutes: 30 });
  const [isCreatingPatient, setIsCreatingPatient] = useState(false);
  const [newPt, setNewPt] = useState({ nom: '', prenom: '', telephone: '' });
  
  const handleCreatePatient = async () => {
    if (!newPt.nom || !newPt.prenom) return toast.error("Nom et prénom requis");
    const creds = await MobileStorage.getCredentials();
    if (!creds) return;
    try {
      const res = await fetch(`${creds.api_base_url}/api/mobile/patients`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${creds.access_token}` },
        body: JSON.stringify({ nom: newPt.nom, prenom: newPt.prenom, telephone: newPt.telephone, sexe: 'M' })
      });
      if (!res.ok) throw new Error("Erreur serveur");
      const created = await res.json();
      onPatientCreated(created);
      setNewApt({...newApt, patient_name: created.name});
      setIsCreatingPatient(false);
      setNewPt({ nom: '', prenom: '', telephone: '' });
      toast.success("Patient ajouté !");
    } catch (e) {
      toast.error("Erreur d'ajout du patient");
    }
  };

  const handleAddAppt = async () => {
    const creds = await MobileStorage.getCredentials();
    if (!creds) return;
    try {
      await fetch(`${creds.api_base_url}/api/mobile/appointments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${creds.access_token}` },
        body: JSON.stringify({
          datetime_start: `${selectedDate}T${newApt.time}:00`,
          patient_name: newApt.patient_name,
          motif: newApt.motif,
          duration_minutes: newApt.duration_minutes
        })
      });
      onSuccess();
      onClose();
      toast.success("Rendez-vous ajouté");
    } catch (err) {
      toast.error("Erreur d'ajout");
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-card border border-glass-border rounded-[24px] w-full max-w-sm overflow-hidden shadow-elite animate-in fade-in zoom-in-95 duration-200 p-5 space-y-4">
        <h3 className="font-black font-outfit text-primary flex items-center gap-2"><Calendar size={18}/> Ajouter un RDV</h3>
        <div className="space-y-3">
          <div>
            <div className="flex items-center justify-between">
              <label className="text-[10px] font-black uppercase text-text-muted">Patient</label>
              <button onClick={() => setIsCreatingPatient(!isCreatingPatient)} className="text-[10px] font-black uppercase text-primary tracking-widest flex items-center gap-1">
                {isCreatingPatient ? 'Annuler' : '+ Nouveau'}
              </button>
            </div>
            {isCreatingPatient ? (
              <div className="mt-2 space-y-2 bg-primary/5 p-3 rounded-xl border border-primary/10">
                <input type="text" placeholder="Nom" className="w-full bg-glass-bg border border-glass-border rounded-lg px-3 py-1.5 text-xs outline-none focus:border-primary" value={newPt.nom} onChange={e => setNewPt({...newPt, nom: e.target.value})} />
                <input type="text" placeholder="Prénom" className="w-full bg-glass-bg border border-glass-border rounded-lg px-3 py-1.5 text-xs outline-none focus:border-primary" value={newPt.prenom} onChange={e => setNewPt({...newPt, prenom: e.target.value})} />
                <input type="tel" placeholder="Téléphone" className="w-full bg-glass-bg border border-glass-border rounded-lg px-3 py-1.5 text-xs outline-none focus:border-primary" value={newPt.telephone} onChange={e => setNewPt({...newPt, telephone: e.target.value})} />
                <button onClick={handleCreatePatient} className="w-full py-2 mt-1 bg-primary text-white font-bold text-[11px] rounded-lg shadow-sm">Créer le patient</button>
              </div>
            ) : (
              <select className="w-full mt-1 bg-glass-bg border border-glass-border rounded-xl px-3 py-2 text-sm outline-none focus:border-primary" value={newApt.patient_name} onChange={e => setNewApt({...newApt, patient_name: e.target.value})}>
                <option value="" disabled>Sélectionner un patient...</option>
                {patients.map(p => <option key={p.id} value={p.name}>{p.name}</option>)}
              </select>
            )}
          </div>
          <div>
            <label className="text-[10px] font-black uppercase text-text-muted">Motif</label>
            {newApt.isCustomMotif ? (
              <div className="flex gap-2 mt-1 items-center">
                <input type="text" className="w-full bg-glass-bg border border-glass-border rounded-xl px-3 py-2 text-sm outline-none focus:border-primary" placeholder="Nouveau motif..." value={newApt.motif} onChange={e => setNewApt({...newApt, motif: e.target.value})} autoFocus />
                <button onClick={() => setNewApt({...newApt, isCustomMotif: false, motif: 'Consultation'})} className="p-1 text-text-muted hover:text-primary"><XCircle size={18} /></button>
              </div>
            ) : (
              <select className="w-full mt-1 bg-glass-bg border border-glass-border rounded-xl px-3 py-2 text-sm outline-none focus:border-primary" value={newApt.motif} onChange={e => {
                if (e.target.value === 'Autre...') {
                  setNewApt({...newApt, isCustomMotif: true, motif: ''});
                } else {
                  setNewApt({...newApt, motif: e.target.value});
                }
              }}>
                <option value="Consultation">Consultation</option>
                <option value="Contrôle">Contrôle</option>
                <option value="Détartrage">Détartrage</option>
                <option value="Urgence">Urgence</option>
                <option value="Soins">Soins</option>
                <option value="Extraction">Extraction</option>
                <option value="Orthodontie">Orthodontie</option>
                <option disabled>--- Prothèse ---</option>
                <option value="Prothèse">Prothèse</option>
                <option value="Taille">Taille</option>
                <option value="Empreinte">Empreinte</option>
                <option value="Essayage armature">Essayage armature</option>
                <option value="Essayage biscuit">Essayage biscuit</option>
                <option value="Pose de prothèse">Pose de prothèse</option>
                <option disabled>--- Prothèse Adjointe ---</option>
                <option value="Prothèse adjointe (PEI)">PEI</option>
                <option value="Prothèse adjointe (RIM)">RIM</option>
                <option value="Prothèse adjointe (Montage)">Montage</option>
                <option value="Prothèse adjointe (Finition)">Finition</option>
                <option value="Autre...">Autre...</option>
              </select>
            )}
          </div>
          <div className="flex gap-3">
            <div className="flex-1"><label className="text-[10px] font-black uppercase text-text-muted">Heure</label><input type="time" className="w-full mt-1 bg-glass-bg border border-glass-border rounded-xl px-3 py-2 text-sm outline-none focus:border-primary" value={newApt.time} onChange={e => setNewApt({...newApt, time: e.target.value})} /></div>
            <div className="flex-1"><label className="text-[10px] font-black uppercase text-text-muted">Durée (min)</label><input type="number" className="w-full mt-1 bg-glass-bg border border-glass-border rounded-xl px-3 py-2 text-sm outline-none focus:border-primary" value={newApt.duration_minutes} onChange={e => setNewApt({...newApt, duration_minutes: Number(e.target.value)})} /></div>
          </div>
        </div>
        <div className="flex gap-2 pt-2">
          <button onClick={onClose} className="flex-1 py-2.5 rounded-xl border border-glass-border font-bold text-xs text-text-main active:scale-95 transition-all">Annuler</button>
          <button onClick={handleAddAppt} disabled={!newApt.patient_name} className="flex-1 py-2.5 rounded-xl bg-primary text-white font-bold text-xs shadow-md active:scale-95 transition-all disabled:opacity-50">Ajouter</button>
        </div>
      </div>
    </div>
  );
}
