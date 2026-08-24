import { Calendar, X, XCircle } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { MobileStorage } from '../../../../services/zka/MobileStorage';
import { mobileFetch } from '../../../../services/zka/mobileFetch';

type MobilePatient = { id: number; name: string; phone: string | null };

type CanonicalPatient = {
  id: number;
  nom: string;
  prenom: string;
  telephone?: string | null;
};

function patientToMobile(patient: CanonicalPatient): MobilePatient {
  return {
    id: patient.id,
    name: `${patient.prenom ?? ''} ${patient.nom ?? ''}`.trim(),
    phone: patient.telephone ?? null,
  };
}

function apiErrorMessage(payload: any, fallback: string): string {
  const detail = payload?.detail;
  if (typeof detail === 'string') return detail;
  if (typeof detail?.message === 'string') return detail.message;
  if (typeof payload?.message === 'string') return payload.message;
  return fallback;
}

export function AddApptModal({
  selectedDate,
  patients,
  onClose,
  onSuccess,
  onPatientCreated,
}: {
  selectedDate: string;
  patients: MobilePatient[];
  onClose: () => void;
  onSuccess: () => void;
  onPatientCreated: (pt: MobilePatient) => void;
}) {
  const [newApt, setNewApt] = useState({
    patient_id: '',
    motif: 'Consultation',
    isCustomMotif: false,
    time: '09:00',
    duration_minutes: 30,
  });
  const [isCreatingPatient, setIsCreatingPatient] = useState(false);
  const [newPt, setNewPt] = useState({
    nom: '',
    prenom: '',
    date_naissance: '',
    sexe: '' as '' | 'F' | 'M',
    telephone: '',
  });
  const [canonicalPatients, setCanonicalPatients] = useState<MobilePatient[]>(patients);
  const [isLoadingPatients, setIsLoadingPatients] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [patientLoadError, setPatientLoadError] = useState<string | null>(null);

  const loadCanonicalPatients = useCallback(async (): Promise<MobilePatient[]> => {
    const creds = await MobileStorage.getCredentials();
    if (!creds) throw new Error('Session mobile indisponible');
    const res = await mobileFetch(`${creds.api_base_url}/api/patients/`, {
      signal: AbortSignal.timeout(5000),
    });
    if (!res.ok) {
      const payload = await res.json().catch(() => ({}));
      throw new Error(apiErrorMessage(payload, 'Impossible de charger les patients'));
    }
    const data = await res.json() as CanonicalPatient[];
    const mapped = data.map(patientToMobile);
    setCanonicalPatients(mapped);
    setPatientLoadError(null);
    return mapped;
  }, []);

  const refreshPatients = useCallback(async () => {
    setIsLoadingPatients(true);
    try {
      await loadCanonicalPatients();
    } catch (error) {
      setCanonicalPatients([]);
      setPatientLoadError(error instanceof Error ? error.message : 'Patients indisponibles');
    } finally {
      setIsLoadingPatients(false);
    }
  }, [loadCanonicalPatients]);

  useEffect(() => {
    void refreshPatients();
  }, [refreshPatients]);

  const resetPatientForm = () => {
    setNewPt({ nom: '', prenom: '', date_naissance: '', sexe: '', telephone: '' });
  };

  const selectExistingPatient = async (patientId: number) => {
    const refreshed = await loadCanonicalPatients();
    const existing = refreshed.find(patient => patient.id === patientId);
    if (!existing) throw new Error('Dossier patient existant introuvable');
    setNewApt(current => ({ ...current, patient_id: String(existing.id) }));
    setIsCreatingPatient(false);
    resetPatientForm();
    toast.success('Dossier existant sélectionné');
  };

  const handleCreatePatient = async () => {
    if (!newPt.nom.trim() || !newPt.prenom.trim()) {
      toast.error('Nom et prénom requis');
      return;
    }
    if (!newPt.date_naissance) {
      toast.error('Date de naissance requise');
      return;
    }
    if (!newPt.sexe) {
      toast.error('Sexe F ou M requis');
      return;
    }

    const creds = await MobileStorage.getCredentials();
    if (!creds) {
      toast.error('Session mobile indisponible');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await mobileFetch(`${creds.api_base_url}/api/patients/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nom: newPt.nom.trim(),
          prenom: newPt.prenom.trim(),
          date_naissance: newPt.date_naissance,
          sexe: newPt.sexe,
          telephone: newPt.telephone.trim() || null,
        }),
      });
      const payload = await res.json().catch(() => ({}));

      if (res.status === 409) {
        const existingId = payload?.detail?.existing_patient?.id;
        if (typeof existingId === 'number') {
          await selectExistingPatient(existingId);
          return;
        }
        throw new Error('Doublon détecté sans dossier réutilisable');
      }
      if (!res.ok) {
        throw new Error(apiErrorMessage(payload, 'Création patient refusée'));
      }

      const created = patientToMobile(payload as CanonicalPatient);
      setCanonicalPatients(current => [created, ...current.filter(patient => patient.id !== created.id)]);
      onPatientCreated(created);
      setNewApt(current => ({ ...current, patient_id: String(created.id) }));
      setIsCreatingPatient(false);
      resetPatientForm();
      toast.success('Patient créé et sélectionné');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Erreur de création patient');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAddAppt = async () => {
    const patientId = Number(newApt.patient_id);
    if (!Number.isInteger(patientId) || patientId <= 0) {
      toast.error('Sélectionnez un patient');
      return;
    }
    if (!newApt.motif.trim()) {
      toast.error('Motif requis');
      return;
    }
    if (!newApt.time) {
      toast.error('Heure requise');
      return;
    }
    if (!Number.isFinite(newApt.duration_minutes) || newApt.duration_minutes <= 0) {
      toast.error('Durée invalide');
      return;
    }

    const creds = await MobileStorage.getCredentials();
    if (!creds) {
      toast.error('Session mobile indisponible');
      return;
    }
    const selectedPatient = canonicalPatients.find(patient => patient.id === patientId);
    if (!selectedPatient) {
      toast.error('Patient introuvable, rechargez la liste');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await mobileFetch(`${creds.api_base_url}/api/appointments/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_id: patientId,
          patient_name: selectedPatient.name,
          datetime_start: `${selectedDate}T${newApt.time}:00`,
          motif: newApt.motif.trim(),
          duration_minutes: newApt.duration_minutes,
          scheduling_type: 'EXACT_TIME',
        }),
      });
      const payload = await res.json().catch(() => ({}));
      if (res.status === 409) {
        throw new Error('Ce créneau chevauche déjà un autre rendez-vous');
      }
      if (!res.ok) {
        throw new Error(apiErrorMessage(payload, 'Création du rendez-vous refusée'));
      }
      onSuccess();
      onClose();
      toast.success('Rendez-vous créé');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Erreur de création du rendez-vous');
    } finally {
      setIsSubmitting(false);
    }
  };

  const controlClass = 'w-full min-h-12 bg-glass-bg border border-glass-border rounded-xl px-3 text-sm outline-none focus:border-primary';

  return (
    <div className="fixed inset-0 z-[100] flex items-end sm:items-center sm:justify-center bg-black/60 backdrop-blur-sm sm:p-4">
      <div className="bg-card border border-glass-border rounded-t-[28px] sm:rounded-[28px] w-full sm:max-w-md max-h-[92dvh] overflow-y-auto shadow-elite animate-in fade-in slide-in-from-bottom-4 sm:zoom-in-95 duration-200 p-5 pb-[max(1.25rem,env(safe-area-inset-bottom))] space-y-5">
        <div className="sm:hidden w-10 h-1 rounded-full bg-border-main mx-auto" aria-hidden="true" />

        <div className="flex items-center justify-between gap-3">
          <h3 className="font-black font-outfit text-primary flex items-center gap-2 text-base">
            <Calendar size={20} /> Nouveau rendez-vous
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="min-w-11 min-h-11 rounded-xl border border-glass-border flex items-center justify-center text-text-muted active:scale-95"
            aria-label="Fermer"
          >
            <X size={20} />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between gap-3 mb-1.5">
              <label className="text-[11px] font-black uppercase tracking-wider text-text-muted">Patient</label>
              <button
                type="button"
                onClick={() => setIsCreatingPatient(value => !value)}
                className="min-h-11 px-3 rounded-xl text-xs font-black uppercase text-primary tracking-wide border border-primary/15 bg-primary/5"
              >
                {isCreatingPatient ? 'Revenir à la liste' : '+ Nouveau patient'}
              </button>
            </div>

            {isCreatingPatient ? (
              <div className="space-y-3 bg-primary/5 p-3 rounded-2xl border border-primary/10">
                <div className="grid grid-cols-2 gap-2">
                  <input type="text" placeholder="Nom" autoComplete="family-name" className={controlClass} value={newPt.nom} onChange={event => setNewPt({ ...newPt, nom: event.target.value })} />
                  <input type="text" placeholder="Prénom" autoComplete="given-name" className={controlClass} value={newPt.prenom} onChange={event => setNewPt({ ...newPt, prenom: event.target.value })} />
                </div>
                <div>
                  <label className="text-[11px] font-black uppercase tracking-wider text-text-muted">Date de naissance</label>
                  <input type="date" className={`${controlClass} mt-1`} value={newPt.date_naissance} onChange={event => setNewPt({ ...newPt, date_naissance: event.target.value })} />
                </div>
                <div>
                  <label className="text-[11px] font-black uppercase tracking-wider text-text-muted">Sexe</label>
                  <div className="grid grid-cols-2 gap-2 mt-1">
                    {(['F', 'M'] as const).map(sexe => (
                      <button
                        type="button"
                        key={sexe}
                        onClick={() => setNewPt({ ...newPt, sexe })}
                        className={`min-h-12 rounded-xl border text-sm font-black transition-colors ${newPt.sexe === sexe ? 'bg-primary text-white border-primary' : 'bg-glass-bg text-text-main border-glass-border'}`}
                        aria-pressed={newPt.sexe === sexe}
                      >
                        {sexe === 'F' ? 'Féminin (F)' : 'Masculin (M)'}
                      </button>
                    ))}
                  </div>
                </div>
                <input type="tel" placeholder="Téléphone (optionnel)" autoComplete="tel" className={controlClass} value={newPt.telephone} onChange={event => setNewPt({ ...newPt, telephone: event.target.value })} />
                <button
                  type="button"
                  onClick={handleCreatePatient}
                  disabled={isSubmitting}
                  className="w-full min-h-[52px] bg-primary text-white font-black text-sm rounded-xl shadow-sm disabled:opacity-50"
                >
                  Créer et sélectionner ce patient
                </button>
              </div>
            ) : (
              <>
                <select
                  className={controlClass}
                  value={newApt.patient_id}
                  onChange={event => setNewApt({ ...newApt, patient_id: event.target.value })}
                  disabled={isLoadingPatients || Boolean(patientLoadError)}
                >
                  <option value="" disabled>{isLoadingPatients ? 'Chargement des patients…' : 'Sélectionner un patient…'}</option>
                  {canonicalPatients.map(patient => <option key={patient.id} value={patient.id}>{patient.name}</option>)}
                </select>
                {patientLoadError && (
                  <div className="mt-2 flex items-center justify-between gap-2 text-xs text-rose-500">
                    <span>{patientLoadError}</span>
                    <button type="button" onClick={() => void refreshPatients()} className="min-h-11 px-3 rounded-xl border border-rose-500/20 font-bold">Réessayer</button>
                  </div>
                )}
              </>
            )}
          </div>

          <div>
            <label className="text-[11px] font-black uppercase tracking-wider text-text-muted">Motif</label>
            {newApt.isCustomMotif ? (
              <div className="flex gap-2 mt-1 items-center">
                <input type="text" className={controlClass} placeholder="Nouveau motif…" value={newApt.motif} onChange={event => setNewApt({ ...newApt, motif: event.target.value })} autoFocus />
                <button type="button" onClick={() => setNewApt({ ...newApt, isCustomMotif: false, motif: 'Consultation' })} className="min-w-12 min-h-12 rounded-xl border border-glass-border text-text-muted flex items-center justify-center" aria-label="Annuler le motif personnalisé"><XCircle size={20} /></button>
              </div>
            ) : (
              <select className={`${controlClass} mt-1`} value={newApt.motif} onChange={event => {
                if (event.target.value === 'Autre...') {
                  setNewApt({ ...newApt, isCustomMotif: true, motif: '' });
                } else {
                  setNewApt({ ...newApt, motif: event.target.value });
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
                <option value="Autre...">Autre…</option>
              </select>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[11px] font-black uppercase tracking-wider text-text-muted">Heure</label>
              <input type="time" className={`${controlClass} mt-1`} value={newApt.time} onChange={event => setNewApt({ ...newApt, time: event.target.value })} />
            </div>
            <div>
              <label className="text-[11px] font-black uppercase tracking-wider text-text-muted">Durée (min)</label>
              <input type="number" min="5" step="5" className={`${controlClass} mt-1`} value={newApt.duration_minutes} onChange={event => setNewApt({ ...newApt, duration_minutes: Number(event.target.value) })} />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 pt-1">
          <button type="button" onClick={onClose} className="min-h-[52px] rounded-xl border border-glass-border font-black text-sm text-text-main active:scale-95 transition-all">Annuler</button>
          <button type="button" onClick={handleAddAppt} disabled={!newApt.patient_id || isSubmitting || isCreatingPatient || Boolean(patientLoadError)} className="min-h-[52px] rounded-xl bg-primary text-white font-black text-sm shadow-md active:scale-95 transition-all disabled:opacity-50">Créer le RDV</button>
        </div>
      </div>
    </div>
  );
}
