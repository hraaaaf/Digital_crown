import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { api } from '../../../services/api';

export interface DocumentHubPatientDetails {
  id: number;
  nom: string;
  prenom: string;
  date_naissance?: string;
  genre?: string;
}

export function useDocumentHubPatient(patientId: string | undefined) {
  const [patientDetails, setPatientDetails] = useState<DocumentHubPatientDetails | null>(null);

  useEffect(() => {
    if (!patientId) {
      setPatientDetails(null);
      return;
    }

    let cancelled = false;
    setPatientDetails(null);

    api.get(`/patients/${patientId}`)
      .then(res => {
        if (!cancelled) setPatientDetails(res.data);
      })
      .catch((err) => {
        if (cancelled) return;
        console.error('DocumentHub: patient fetch failed', err);
        const status = err.response?.status;
        if (status === 403 || status === 404) {
          setPatientDetails(null);
          toast.error('Dossier patient introuvable ou accès non autorisé.');
        }
      });

    return () => {
      cancelled = true;
    };
  }, [patientId]);

  return patientDetails;
}
