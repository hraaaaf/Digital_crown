import extractionMolaire from './extraction-molaire.json';
import traitementEndodontique from './traitement-endodontique.json';
import poseImplant from './pose-implant.json';
import detartrageSurfacage from './detartrage-surfacage.json';
import scellementComposite from './scellement-composite.json';
import alveoliteTraitement from './alveolite-traitement.json';
import collageOrtho from './collage-ortho.json';
import blanchimentFauteuil from './blanchiment-fauteuil.json';
import pulpotomiePedo from './pulpotomie-pedodontie.json';
import preparationCouronne from './preparation-couronne.json';
// CONSERVATRICE
import composite1Face from './composite-1-face.json';
import composite2Faces from './composite-2-faces.json';
import composite3Faces from './composite-3-faces.json';
import reconstitutionCoronaire from './reconstitution-coronaire.json';
import dentineHypersensible from './dentine-hypersensible.json';
import coiffagePulpaire from './coiffage-pulpaire.json';
// PRÉVENTION
import examenBuccodentaire from './examen-buccodentaire.json';
import vernisFluore from './vernis-fluore.json';
import radioRetroalveolaire from './radio-retroalveolaire.json';
import radioPanoramique from './radio-panoramique.json';
import radioBitewing from './radio-bitewing.json';
import cbctDentaire from './cbct-dentaire.json';
// ENDODONTIE
import pulpotomieUrgence from './pulpotomie-urgence.json';
import canalaireMonoradiculaire from './canalaire-monoradiculaire.json';
import canalairePremolaireJSON from './canalaire-premolaire.json';
import retraitementEndodontique from './retraitement-endodontique.json';
// CHIRURGIE
import avulsionSimple from './avulsion-simple.json';
import avulsionSagesseincluse from './avulsion-sagesse-incluse.json';
import germectomie from './germectomie.json';
import apicectomie from './apicectomie.json';
import frenectomie from './frenectomie.json';
// PARODONTOLOGIE
import surfacageRadiculaireQuadrant from './surfacage-radiculaire-quadrant.json';
import gingivectomie from './gingivectomie.json';
import greffeGingivaleConjonctive from './greffe-gingivale-conjonctive.json';
import chirurgieLambeauWidman from './chirurgie-lambeau-widman.json';
// PROTHÈSE
import couronnesCeramiqueZircone from './couronne-ceramique-zircone.json';
import bridge3Elements from './bridge-3-elements.json';
import inlayOnlayCeramique from './inlay-onlay-ceramique.json';
import tenonFibreRcr from './tenon-fibre-rcr.json';
import prothesePartielleResine from './prothese-partielle-resine.json';
import prothesePartielleChassis from './prothese-partielle-chassis.json';
import prostheseTotaleAmovible from './prothese-totale-amovible.json';
// IMPLANTOLOGIE
import couronneSurImplant from './couronne-sur-implant.json';
import sinusLift from './sinus-lift.json';
import greffeOsseuse from './greffe-osseuse.json';
// ORTHODONTIE
import bilanOrthodontique from './bilan-orthodontique.json';
import aligneursTransparents from './aligneurs-transparents.json';
// ESTHÉTIQUE
import facetteCompositeDirecte from './facette-composite-directe.json';
// PÉDIATRIE
import couronnesPediatriquesAcier from './couronne-pediatrique-acier.json';
import avulsionDentLacteale from './avulsion-dent-lacteale.json';

import type { ClinicalProtocol } from '../../features/clinical-ref/types';

export const CLINICAL_PROTOCOLS: ClinicalProtocol[] = [
  // Originaux (10)
  extractionMolaire as ClinicalProtocol,
  traitementEndodontique as ClinicalProtocol,
  poseImplant as ClinicalProtocol,
  detartrageSurfacage as ClinicalProtocol,
  scellementComposite as ClinicalProtocol,
  alveoliteTraitement as ClinicalProtocol,
  collageOrtho as ClinicalProtocol,
  blanchimentFauteuil as ClinicalProtocol,
  pulpotomiePedo as ClinicalProtocol,
  preparationCouronne as ClinicalProtocol,
  // CONSERVATRICE (6)
  composite1Face as ClinicalProtocol,
  composite2Faces as ClinicalProtocol,
  composite3Faces as ClinicalProtocol,
  reconstitutionCoronaire as ClinicalProtocol,
  dentineHypersensible as ClinicalProtocol,
  coiffagePulpaire as ClinicalProtocol,
  // PRÉVENTION (6)
  examenBuccodentaire as ClinicalProtocol,
  vernisFluore as ClinicalProtocol,
  radioRetroalveolaire as ClinicalProtocol,
  radioPanoramique as ClinicalProtocol,
  radioBitewing as ClinicalProtocol,
  cbctDentaire as ClinicalProtocol,
  // ENDODONTIE (4)
  pulpotomieUrgence as ClinicalProtocol,
  canalaireMonoradiculaire as ClinicalProtocol,
  canalairePremolaireJSON as ClinicalProtocol,
  retraitementEndodontique as ClinicalProtocol,
  // CHIRURGIE (5)
  avulsionSimple as ClinicalProtocol,
  avulsionSagesseincluse as ClinicalProtocol,
  germectomie as ClinicalProtocol,
  apicectomie as ClinicalProtocol,
  frenectomie as ClinicalProtocol,
  // PARODONTOLOGIE (4)
  surfacageRadiculaireQuadrant as ClinicalProtocol,
  gingivectomie as ClinicalProtocol,
  greffeGingivaleConjonctive as ClinicalProtocol,
  chirurgieLambeauWidman as ClinicalProtocol,
  // PROTHÈSE (7)
  couronnesCeramiqueZircone as ClinicalProtocol,
  bridge3Elements as ClinicalProtocol,
  inlayOnlayCeramique as ClinicalProtocol,
  tenonFibreRcr as ClinicalProtocol,
  prothesePartielleResine as ClinicalProtocol,
  prothesePartielleChassis as ClinicalProtocol,
  prostheseTotaleAmovible as ClinicalProtocol,
  // IMPLANTOLOGIE (3)
  couronneSurImplant as ClinicalProtocol,
  sinusLift as ClinicalProtocol,
  greffeOsseuse as ClinicalProtocol,
  // ORTHODONTIE (2)
  bilanOrthodontique as ClinicalProtocol,
  aligneursTransparents as ClinicalProtocol,
  // ESTHÉTIQUE (1)
  facetteCompositeDirecte as ClinicalProtocol,
  // PÉDIATRIE (2)
  couronnesPediatriquesAcier as ClinicalProtocol,
  avulsionDentLacteale as ClinicalProtocol,
];

export const getProtocolByActName = (actName: string): ClinicalProtocol | undefined => {
  if (!actName || actName.trim().length < 3) return undefined;

  const normalizedSearch = actName.toLowerCase().trim();

  // 1. Essayer une correspondance exacte en premier
  const exactMatch = CLINICAL_PROTOCOLS.find(p =>
    p.act_names.some(name => name.toLowerCase() === normalizedSearch)
  );
  if (exactMatch) return exactMatch;

  // 2. Sinon essayer une correspondance par préfixe ou mot-clé propre
  return CLINICAL_PROTOCOLS.find(p =>
    p.act_names.some(name => {
      const lowerName = name.toLowerCase();
      return lowerName.startsWith(normalizedSearch) || 
             (normalizedSearch.length >= 4 && lowerName.includes(normalizedSearch));
    })
  );
};
