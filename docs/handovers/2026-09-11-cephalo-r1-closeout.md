# CLOSEOUT — Digital Crown Céphalométrie R1

Date : 2026-09-11

## Goal

Fermer R1 — calibration céphalométrique assistée par fiducial — avec preuve backend, runtime, provenance et UX responsive, sans inventer d’échelle physique et sans réintroduire de logique diagnostique ou thérapeutique.

## État final vérifié

- repo : `hraaaaf/Digital_crown`
- PR : `#406` — `feat(cephalo): assisted fiducial calibration provenance`
- branche PR : `feat/cephalo-auto-fiducial-calibration`
- HEAD PR certifié : `3f8c72082b61e9a9ec2f23316a325995a172b8e4`
- merge squash master : `ac858696a734cf04fcf2797ebd0bf53b0caaac25`
- master vérifié après merge : `ac858696a734cf04fcf2797ebd0bf53b0caaac25`
- reviews : 0
- review threads : 0
- Vercel : aucun déploiement effectué

## Preuves exact-head

- CI `#3220` / run `34580727939` : **SUCCESS**
- T2 Runtime Browser Certification `#2227` / run `34580727944` : **SUCCESS**
- Patient P7 Final Certification `#1194` / run `34580727985` : **SUCCESS**
- Cephalo R1 AFTER `#4` / run `34580727933` : **SUCCESS**
- M6-I `#1027` : **SKIPPED** attendu

Artefact AFTER :
- nom : `cephalo-r1-after`
- artifact ID : `10191532363`
- SHA-256 : `84ea4876c88d738fb216c7c22428b037188b3a1ae8a1b0fc905a5d74bcc2c586`
- produit : `3f8c72082b61e9a9ec2f23316a325995a172b8e4`
- viewports : `390x844`, `768x1024`, `1280x900`
- rapport : `invalidCount = 0`
- egress externe bloqué : aucun

## Validation visuelle

Les trois PNG AFTER ont été inspectés humainement :

- 390 : aucun overflow document, aucun clipping assistant/header ; le badge affiche intégralement `RÉGLETTE À VÉRIFIER` ;
- 768 : rendu cohérent, provenance et actions visibles ;
- 1280 : rendu non blanc et cohérent sur l’essai final certifié.

Le harness lance un Chromium frais par viewport. Un seul retry frais est autorisé après un premier rendu invalide ; l’essai final doit satisfaire indépendamment tous les gates. Le viewport 1280 a utilisé ce retry sur le run final. Ce comportement est tracé et n’est pas masqué.

Score visuel interne : **9,8/10**. Le score n’est pas 10/10 à cause du flake de premier rendu 1280 observé dans le harness, malgré une capture finale certifiée propre.

## Contrat R1 fermé

- détection image → `CANDIDATE_UNVERIFIED` tant qu’aucune preuve physique déterministe n’existe ;
- aucun fallback implicite `0.1 mm/px` ;
- aucun `10 mm` hardcodé promu en vérité physique ;
- `AUTO_VERIFIED` seulement si profil physique validé/versionné + gates objectifs ;
- le client ne peut pas choisir `profile_id`, `profile_version` ou `validation_reference` ;
- binding profil résolu côté serveur depuis la preuve persistée ;
- `AUTO_VERIFIED` et `CLINICIAN_CONFIRMED` restent des provenances distinctes ;
- confirmation praticien recommandée mais non obligatoire ;
- confirmation praticien ne modifie ni ratio ni mesures, seulement la provenance ;
- calibration manuelle `MANUAL_TWO_POINT` reste distincte ;
- mesures millimétriques restent `NOT_COMPUTABLE` sans calibration vérifiée ;
- sauvegardes ordinaires préservent candidat/décision/statut de calibration ;
- aucune norme, diagnostic, indication ou traitement n’a été ajouté ;
- ZERO LLM conservé.

## Limite connue

Le registre `validated_fiducial_profiles` reste vide par défaut. L’architecture R1 autorise l’auto-vérification lorsqu’un profil physique validé sera explicitement introduit, mais aucun profil de test ou implicite n’active `AUTO_VERIFIED` en production.

## Next exact

Ouvrir R2 — chaîne runtime scientifique traversante — à partir du master `ac858696a734cf04fcf2797ebd0bf53b0caaac25`.

Goal R2 : une chaîne unique `SourceEvidence → LandmarkEvidence → ConstructionEvidence → MeasurementEvidence` pour création, correction, calibration, recalcul et GET, avec fail-closed sur toute référence incohérente.

## Avis expert

R1 est suffisamment prouvé pour être fermé. Le principal résiduel n’est plus la calibration elle-même mais la robustesse transversale de la chaîne de preuve lorsque plusieurs transitions se succèdent. R2 doit donc viser la continuité d’autorité des objets, pas ajouter de nouvelles heuristiques cliniques.
