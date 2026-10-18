import { describe, expect, it } from 'vitest';
import { appointmentPresentation } from './PatientCompanionAgendaStatus';

describe('Patient Companion genuine appointment state', () => {
  it.each([
    ['CONFIRMÉ', 'Confirmé', true, true],
    ['PRÉVU', 'Prévu', true, true],
    ['EN_ATTENTE_DEMANDE', 'En attente de confirmation', false, false],
    ['EN_ATTENTE_CONFIRM', 'En attente de confirmation', false, false],
    ['REFUSÉ', 'Refusé', false, false],
    ['EXPIRÉ', 'Expiré', false, false],
    ['ANNULÉ', 'Annulé', false, false],
    ['TERMINÉ', 'Terminé', false, false],
    ['EN_S_ATTENTE', 'En salle d’attente', false, false],
    ['EN_FAUTEUIL', 'En soin', false, false],
    ['ABSENT', 'Absent', false, false],
    ['UNRECOGNIZED', 'Statut à vérifier auprès du cabinet', false, false],
  ])('preserves API state %s instead of inventing confirmation', (status, label, canManage, isUpcoming) => {
    const result = appointmentPresentation(status);
    expect(result.label).toBe(label);
    expect(result.canManage).toBe(canManage);
    expect(result.isUpcoming).toBe(isUpcoming);
  });
});
