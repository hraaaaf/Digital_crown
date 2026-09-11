# CLOSEOUT — Digital Crown Céphalométrie R2

Date : 2026-09-11

## Goal

Fermer R2 avec une chaîne scientifique runtime active unique et vérifiable :

`SourceEvidence → LandmarkEvidence → ConstructionEvidence → MeasurementEvidence`

La chaîne doit rester la même à travers création, correction, calibration, recalcul et GET, et échouer fermement dès qu'une référence active devient incohérente.

## État final vérifié

- repo : `hraaaaf/Digital_crown`
- PR : `#408` — `feat(cephalo): enforce R2 active runtime evidence chain`
- branche : `feat/cephalo-r2-runtime-evidence-chain`
- HEAD PR certifié : `5e98c364e095b966d4349b9791792f2bdbed1e95`
- merge squash master : `7108ac75aa130868fe1826979697257e45d1daf3`
- master vérifié après merge : `7108ac75aa130868fe1826979697257e45d1daf3`
- merge commit GitHub : signature vérifiée
- Vercel : aucun déploiement effectué

## Preuves exact-head

- CI `#3229` / run `34582517244` : **SUCCESS**
- T2 Runtime Browser Certification `#2234` / run `34582517253` : **SUCCESS**
- M6-I `#1034` / run `34582517269` : **SKIPPED** attendu
- Frontend tests & build : **SUCCESS**
- backend `Tests & durcissement` : **SUCCESS**
- production safety checks : **SUCCESS**
- M4-A / M4-B / M4-C AFTER : **SUCCESS**

## Contrat R2 fermé

- le graphe peut conserver des objets historiques pour audit ;
- `current_landmark_refs` exprime explicitement le jeu de landmarks actif ;
- la persistence canonise ce jeu actif lorsque l'autorité est non ambiguë ;
- un ancien snapshot sans `current_landmark_refs` reste lisible uniquement si chaque landmark n'a qu'une preuve non ambiguë ;
- une construction qui référence un landmark historique non actif bloque la lecture scientifique ;
- une mesure qui référence un landmark historique non actif bloque la lecture scientifique ;
- une mesure qui référence une calibration non courante bloque la lecture scientifique ;
- le GET canonique n'expose les valeurs CRANIOM typées qu'après validation de la chaîne active ;
- le marqueur obsolète `PERSISTED_NOT_YET_READ_PATH` est retiré avant persistence canonique ;
- aucune norme, interprétation, diagnostic, indication ou traitement n'a été ajouté ;
- ZERO LLM préservé.

## Test traversant

La suite R2 couvre explicitement :

`création → persistence canonique → correction landmark → calibration manuelle → recalcul → GET scientifique`

et les chemins négatifs d'autorité ambiguë / référence stale.

## Limites connues

R2 garantit la continuité de provenance et d'autorité des objets géométriques déjà versionnés. Il ne résout pas les ambiguïtés scientifiques de définition de certaines constructions ou conventions CRANIOM ; celles-ci relèvent du lot R3.

## Next exact

Ouvrir R3 depuis le master courant après ce closeout.

### R3 — Conventions géométriques / CRANIOM

Goal : supprimer toute ambiguïté avant extension des analyses.

Succès : chaque mesure possède des landmarks, une construction, une convention, une formule et une source versionnés sans convention implicite.

Points ouverts canoniques :
- plan mandibulaire propre à chaque analyse ;
- ambiguïté `Go` ;
- `Gi/Gs` CRANIOM ;
- `A''B''` sans protocole NHP / regard horizontal.

## Avis expert

R2 ferme correctement le risque d'autorité runtime divergente. Le prochain risque n'est plus informatique mais scientifique : deux chaînes techniquement cohérentes peuvent encore produire des résultats différents si leurs constructions ou conventions géométriques ne sont pas définies de façon univoque. R3 doit donc verrouiller les définitions avant toute extension de couverture analytique.
