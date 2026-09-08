# DIGITAL CROWN — UX CONTINUITY / FLOW HANDOFF — CANONICAL HANDOVER

Status: VALIDATION GREEN — CLOSEOUT DOCUMENTÉ — MERGE RESTANT

## Goal

Garantir qu’après toute action exigeant une interaction suivante, cette interaction soit immédiatement visible, identifiable et utilisable sans scroll manuel de recherche.

## Success

Critères observables :
- suppression Patient depuis haut / milieu / bas → confirmation immédiatement visible ;
- CTA de confirmation accessibles sur petits viewports ;
- fond verrouillé pendant la confirmation ;
- focus initial logique + restauration du focus ;
- Wizard N → N+1 → nouvelle étape immédiatement visible ;
- PatientDetails → nouvelle surface automatiquement visible et focus utile ;
- BEFORE / AFTER mêmes viewports ;
- tests ciblés + build + CI verts ;
- aucun changement backend, RBAC ou capacité métier ;
- aucun déploiement Vercel.

## Cause racine

La confirmation Patient était rendue localement sous un ancêtre Framer Motion transformé. Un descendant `position: fixed` pouvait alors être positionné relativement à ce containing block plutôt qu’au viewport. Le Wizard et PatientDetails changeaient d’étape / surface sans handoff explicite du viewport ni du focus.

## Implémentation

### `CrownDialog`

`frontend/src/components/CrownDialog.tsx`

- portal vers `document.body` ;
- couverture viewport `100dvh` ;
- scroll arrière-plan verrouillé ;
- hauteur interne bornée ;
- focus initial ;
- focus trap ;
- Escape ;
- restauration du focus.

### `useFlowHandoff`

`frontend/src/hooks/useFlowHandoff.ts`

- mesure de visibilité ;
- scroll uniquement si nécessaire ;
- focus utile avec `preventScroll` ;
- marge compatible avec headers sticky.

### Flows migrés

1. `frontend/src/features/patients/PatientList.tsx` — suppression Patient.
2. `frontend/src/features/admin/SetupWizard/SetupWizard.tsx` — transitions N → N+1.
3. `frontend/src/features/patients/PatientDetailsInner.tsx` — changement automatique de surface / onglet.

## BEFORE certifié

Base produit intacte :
`2926c06166e4d765451bb47e04214508ef4b439c`

Run :
`34170349446` — SUCCESS

Artifact :
- nom : `ux-continuity-before-2926c061`
- id : `10035543779`
- digest : `sha256:c124fba3bbee21dd18b90a3397f5c43d07efaf71e0e1ba8c8e060a13c62484e3`

Résultat BEFORE :
- suppression Patient : 15/15 dialogues hors viewport ;
- Wizard : étape 2 hors viewport à 390×844 et 1366×700 ;
- absence de scroll lock confirmée.

## AFTER certifié

PR candidate : `#370`

HEAD produit certifié avant closeout doc :
`dc05a974135e7eacedc655ef1822a088f60c357f`

GitHub PR synthetic merge commit exécuté par les workflows :
`9d7305a464b2d47af3eb5d5e23cd61d24e814b50`

### Confirmation Patient + Wizard

Run :
`34171720396` — SUCCESS

Artifact :
- nom : `ux-continuity-after`
- id : `10035963637`
- digest : `sha256:1b075a706ca1827ba3a0f06ac87caf860621ef53b8614a319d816d74c8c3dedc`

Résultats :
- 15/15 confirmations entièrement visibles ;
- 15/15 avec `bodyOverflow=hidden` et `htmlOverflow=hidden` ;
- 15/15 focus logique actif ;
- 15/15 focus restauré après fermeture ;
- 0 erreur runtime ;
- Wizard 390×844 : scroll 646 → 143, titre étape 2 visible, focus dans la nouvelle étape ;
- Wizard 1366×700 : scroll 718 → 155, titre étape 2 visible, focus dans la nouvelle étape.

### PatientDetails

Run :
`34171720389` — SUCCESS

Artifact :
- nom : `ux-continuity-patientdetails-after`
- id : `10035962593`
- digest : `sha256:d3997252e91f615cb541ca64961049f90e540ce23e88f4b9a0cf045fcae3fd42`

Résultats :
- 390×844 : scroll 715 → 106, nouvelle surface visible, focus utile ;
- 1366×700 : scroll 408 → 194, nouvelle surface visible, focus utile ;
- 0 erreur runtime.

## Comparaison visuelle

Viewports verrouillés :
- 390×844
- 430×932
- 768×1024
- 1366×700
- 1440×900

Inspection manuelle des captures AFTER :
- modale mobile centrée et contenue dans le viewport ;
- aucune action critique coupée ;
- contexte arrière-plan conservé et neutralisé visuellement ;
- Wizard étape 2 repositionné directement sur son contenu utile ;
- PatientDetails repositionné directement sur la nouvelle surface.

Score visuel du lot : **9.6/10**.

La marge restante est cosmétique et n’affecte ni continuité, ni accessibilité de l’action suivante, ni capacité métier.

## Validation CI

Sur le HEAD produit `dc05a974135e7eacedc655ef1822a088f60c357f` :
- CI `34171720392` — SUCCESS ;
- UX Continuity AFTER `34171720396` — SUCCESS ;
- UX Continuity PatientDetails AFTER `34171720389` — SUCCESS ;
- Patient Indicators Truth Certification `34171720378` — SUCCESS ;
- Patient P1 Architecture After `34171720390` — SUCCESS ;
- T2 Runtime Browser Certification `34171720408` — SUCCESS ;
- Patient P7 Final Certification `34171720413` — SUCCESS ;
- Onboarding Settings P2 Visual Certification `34171720399` — SUCCESS.

## Scope / sécurité

- aucun backend modifié ;
- aucun RBAC modifié ;
- aucune prérogative SuperAdmin supprimée ;
- aucune donnée cabinet réelle utilisée pour la certification ;
- aucun déploiement Vercel.

## Git / PR

Repo : `hraaaaf/Digital_crown`

Branche : `ux/continuity-flow-handoff-runner`

PR : `#370` — `UX: continuity flow handoff`

Le closeout documentaire est le seul changement après le HEAD produit certifié ; il doit recevoir les checks GitHub requis avant merge.

## Next exact

1. Vérifier les checks déclenchés par ce commit documentaire.
2. Si verts : passer PR #370 ready for review.
3. Merge PR #370.
4. Vérifier le merge commit exact et la CI post-merge.
5. Marquer ce chantier CLOSED uniquement après preuve post-merge.

## Séquence restante

`CI closeout doc → ready for review → merge → post-merge CI → CLOSED`

## Repères de reprise

- chantier/lot : Digital Crown — UX Continuity / Flow Handoff
- Goal : prochaine interaction visible immédiatement sans recherche manuelle
- repo : `hraaaaf/Digital_crown`
- branche : `ux/continuity-flow-handoff-runner`
- PR : `#370` draft au moment de ce closeout documentaire
- HEAD produit certifié : `dc05a974135e7eacedc655ef1822a088f60c357f`
- CI produit : `34171720392` SUCCESS
- AFTER principal : `34171720396` SUCCESS
- AFTER PatientDetails : `34171720389` SUCCESS
- deployment : aucun Vercel
- dernière preuve : artifacts AFTER inspectés + score visuel 9.6/10
- blocage réel : checks du commit documentaire puis merge/post-merge
- Next exact : vérifier les checks du commit documentaire
- effort suivant : ⚡ instantané

---

Ce fichier reste le point de reprise canonique jusqu’au closeout post-merge.