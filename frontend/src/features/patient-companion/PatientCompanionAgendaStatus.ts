/** Patient-facing appointment states; never invent a confirmation from an API row. */
export type AppointmentPresentation = {
  label: string;
  canManage: boolean;
  isUpcoming: boolean;
  style: 'positive' | 'neutral' | 'warning' | 'negative';
};

export function appointmentPresentation(raw: string | undefined | null): AppointmentPresentation {
  const status = (raw || '').trim().toUpperCase();
  switch (status) {
    case 'CONFIRMÉ':
    case 'CONFIRME':
      return { label: 'Confirmé', canManage: true, isUpcoming: true, style: 'positive' };
    case 'PRÉVU':
    case 'PREVU':
      return { label: 'Prévu', canManage: true, isUpcoming: true, style: 'neutral' };
    case 'EN_ATTENTE_DEMANDE':
    case 'EN_ATTENTE_CONFIRM':
      return { label: 'En attente de confirmation', canManage: false, isUpcoming: false, style: 'warning' };
    case 'REFUSÉ':
    case 'REFUSE':
      return { label: 'Refusé', canManage: false, isUpcoming: false, style: 'negative' };
    case 'EXPIRÉ':
    case 'EXPIRE':
      return { label: 'Expiré', canManage: false, isUpcoming: false, style: 'negative' };
    case 'ANNULÉ':
    case 'ANNULE':
      return { label: 'Annulé', canManage: false, isUpcoming: false, style: 'neutral' };
    case 'TERMINÉ':
    case 'TERMINE':
      return { label: 'Terminé', canManage: false, isUpcoming: false, style: 'neutral' };
    case 'EN_S_ATTENTE':
    case 'EN_SALLE_ATTENTE':
      return { label: 'En salle d’attente', canManage: false, isUpcoming: false, style: 'neutral' };
    case 'EN_FAUTEUIL':
      return { label: 'En soin', canManage: false, isUpcoming: false, style: 'neutral' };
    case 'ABSENT':
      return { label: 'Absent', canManage: false, isUpcoming: false, style: 'neutral' };
    default:
      return { label: 'Statut à vérifier auprès du cabinet', canManage: false, isUpcoming: false, style: 'warning' };
  }
}
