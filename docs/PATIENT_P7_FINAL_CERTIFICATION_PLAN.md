# Patient P7 — Certification finale Page Patient

## Goal
Fermer le chantier Page Patient uniquement sur un HEAD consolidé qui contient réellement les lots P0→P6 et qui passe les preuves fonctionnelles, visuelles, de persistance, d'isolation et de permissions sur ce même HEAD.

## Succès observable
1. Le HEAD P7 contient P6 final et réintègre le delta Clinique P3 final perdu dans la stack, sans régression P4/P5/P6.
2. CI globale et T2 Runtime Browser Certification sont SUCCESS sur le HEAD P7 exact.
3. Le gate P7 dédié est SUCCESS sur le même HEAD.
4. Matrice visuelle : 10 surfaces × 4 viewports = 40 captures, zéro overflow horizontal, zéro runtime error, zéro HTTP 5xx.
5. Persistance backend relue après mutation : odontogramme, conclusion praticien, Master Plan, RVG, paiement explicite.
6. Documents : création/historique présents, Compagnon absent, ancien `documentTab=plan` normalisé ; PDF/impression certifiés par T2 exact-HEAD.
7. Finances : Facturé / Encaissé / Reste dû / Prochaine échéance, sans faux zéro ni taux de recouvrement sur la fiche.
8. Identité : Add/Edit partagent le contrat canonique, aucun sexe implicite, contrôles fail-closed.
9. Aucun déploiement Vercel.

## Consolidation de stack vérifiée avant commit
- P6 final : `2a0ac2ade90f2bae99c6e7c11302755d856a730e`.
- P5 courant est déjà ancêtre de P6 final.
- P2 product code est déjà présent dans P6 ; son delta hors stack est documentaire/test.
- P3 courant `02126a646322d1c1d98351ea33489384be49ab57` contient un delta produit réel absent de P6, notamment `ClinicalHub.tsx` et trois assistants proposition-only.
- P4 courant `27f55a6e807c2c59b444f5c4356388043d284cfa` porte l'imagerie finalisée et resynchronise l'essentiel du delta P3, mais reste derrière P3 d'un commit ; P7 conserve donc P3 et P4 comme ascendance explicite.
- `PatientDetailsInner.tsx` P6 est conservé car il contient le RBAC strict Imagerie de P4/P3 plus le RBAC Finances P6.

## Matrice visuelle finale
Sur 390×844, 430×932, 768×1024 et 1280×900 :
1. Vue d’ensemble / Patient Journey
2. Clinique
3. Imagerie / RVG
4. Imagerie / Panoramique
5. Imagerie / Céphalométrie
6. Documents / Créer
7. Documents / Historique
8. Finances
9. Nouveau Patient
10. Modifier Patient

## Preuves attendues
- Workflow `Patient P7 Final Certification` : tests P0→P6 ciblés + build + round-trips backend + 40 captures.
- Workflow `CI` : régression globale backend/frontend.
- Workflow `T2 Runtime Browser Certification` : PDF strict, reconciliation financière persistée, Document Studio navigateur/impression.
- Artefact `patient-p7-final-certification` : `summary.json`, `persistence.json`, `evidence.json`, 40 captures.

## Règles de fermeture
P7 reste ouvert tant que les trois gates exact-HEAD ne sont pas verts et que l'artefact visuel n'est pas inspecté. Le certificat/roadmap de closeout ne doit enregistrer que les résultats réellement obtenus et doit lui-même repasser les gates exact-HEAD proportionnels au risque.

Aucun Vercel.
