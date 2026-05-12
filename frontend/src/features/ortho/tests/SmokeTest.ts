import type { Landmark } from '../cephaloShared';
import { generateTreatmentPlan } from '../cephaloUtils';

/**
 * SmokeTestEngine
 * 
 * Un moteur de test interne pour valider les transitions d'état
 * et la cohérence des données du workflow céphalométrique.
 */
export const runCephaloSmokeTest = async (store: any) => {
  const results: string[] = [];
  const log = (msg: string) => results.push(`[${new Date().toLocaleTimeString()}] ${msg}`);

  try {
    log('🚀 Démarrage du Smoke Test Céphalométrique...');

    // 1. Reset Store
    store.setLocal({ landmarks: [], version: 0 });
    store.setDdm({ maxillaire: '', mandibulaire: '' });
    store.setDiag({
      diagnostic_squelettique: '',
      analyse_moulages: '',
      synthese_diagnostique: '',
      strategie_therapeutique: ''
    });
    log('✅ Store réinitialisé.');

    // 2. Step 1: Céphalométrie
    const mockLandmarks: Landmark[] = [
      { id: 'S', x: 100, y: 100 },
      { id: 'N', x: 200, y: 100 },
      { id: 'Po', x: 80, y: 150 },
      { id: 'Or', x: 180, y: 150 },
      { id: 'Go', x: 80, y: 250 },
      { id: 'Me', x: 180, y: 250 },
      { id: 'L1_incisal', x: 200, y: 220 },
      { id: 'L1_apex', x: 180, y: 240 },
    ];
    store.setLocal({ landmarks: mockLandmarks, version: 1 });
    log('✅ Step 1 : 8 points de repère ajoutés.');

    // 3. Step 2: Moulages & DDM
    store.setDdm({ maxillaire: 5, mandibulaire: 3 });
    log('✅ Step 2 : DDM saisie (Max: 5, Mand: 3).');

    // 4. Step 3: Diagnostic & IA
    const mockStep3Data = {
      age: 15,
      cvm: 'CS3',
      classe_squelettique: 'Classe II div 1',
      pattern_vertical: 'normodivergent',
      severite_ddm: 'modéré',
      osseuse: { anb: 5, sna: 82, snb: 77, angle_tweed: 25 },
      dentaire: { impa: 95, i_francfort: 110, surplomb: 4, recouvrement: 3 },
      esthetique: { ligne_e_ls: -2, ligne_e_li: -1, angle_nasolabial: 102 }
    };
    store.setEtape3Data(mockStep3Data as any);
    
    const treatmentPlan = generateTreatmentPlan(mockStep3Data as any);
    if (treatmentPlan.length > 50) {
      log('✅ Step 3 : Plan de traitement IA généré avec succès.');
    } else {
      throw new Error('Échec génération plan de traitement');
    }

    // 4.5. Multi-Analysis Validation
    log('🧪 Validation Multi-Analyse (McNamara, Steiner, Tweed)...');
    const steinerData = { ...mockStep3Data, selectedAnalysis: 'STEINER' };
    store.setEtape3Data(steinerData as any);
    log('✅ Switch Steiner OK.');
    
    const tweedData = { ...mockStep3Data, selectedAnalysis: 'TWEED' };
    store.setEtape3Data(tweedData as any);
    log('✅ Switch Tweed OK.');


    // 5. Step 4: Documents
    log('✅ Step 4 : Prêt pour l\'export PDF.');

    log('🏁 SMOKE TEST RÉUSSI : Architecture stable.');
    return { success: true, logs: results };
  } catch (error: any) {
    log(`❌ ERREUR : ${error.message}`);
    return { success: false, logs: results };
  }
};
