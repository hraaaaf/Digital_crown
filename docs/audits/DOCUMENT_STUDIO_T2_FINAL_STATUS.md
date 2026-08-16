# Document Studio — T2 final engineering status

Date : 2026-08-16
Branche : `agent/t2-document-studio-final-recertification`

## Verdict

**Closeout engineering local convergé. Certification full-app / production non revendiquée.**

Le chantier page-par-page P1→P7, puis T1 transversal, a été consolidé par T2 avec un certificateur unique et un dernier durcissement accessibilité. Les preuves runtime authentifiées, PDF cabinet réels, browser/responsive et validation clinique/scientifique humaine restent des gates séparés.

## État des pages

- P1 Ordonnance : engineering fermé ; recertification visuelle historique acquise ; gates clinique/runtime séparés.
- P2 Certificat : engineering convergé ; dirty-state transversal rétabli par T1 ; runtime/PDF final différé.
- P3 Devis : **CLOSED / PAUSED jusqu'à nouvel ordre** par décision produit ; PR #77 draft conservée comme restart point.
- P4 Note Honoraires : engineering local convergé ; PR #90 draft.
- P5 Suivi Paiement : engineering local convergé ; PR #95 draft.
- P6 Document Libre : engineering local convergé ; PR #96 draft.
- P7 Compagnon Diagnostique : frontière non-prescriptive rétablie ; PR #97 draft.
- T1 transversal : navigation/dirty/archive/print/ghost cleanup convergés localement ; PR #101 draft.

## T2 — actions exécutées

### 1. Certificateur unique

`scripts/certify_document_studio.sh` couvre désormais :
- prérequis Python >=3.12 et Node >=20 ;
- worktree propre ;
- garde de sécurité développement ;
- régression backend ciblée Document Studio P1→P7 ;
- suite backend complète ;
- tests frontend ciblés `src/features/admin/DocumentStudio` ;
- suite frontend complète ;
- build production frontend ;
- invariants source Document Studio : pas de `/ai-diagnostic`, pas de route `ai`, pas de libellé `Diagnostic Établi` ;
- garde production négative.

Preuve réellement exécutée dans le Linux disponible :
- `bash -n scripts/certify_document_studio.sh` reconstruit localement : **PASS** ;
- environnement disponible : Python **3.13.5**, Node **22.16.0**, npm **10.9.2**.

Limite : le dépôt complet et ses dépendances ne sont pas montés dans ce Linux ; le script complet n'a donc pas été exécuté ici. Aucun faux PASS full-suite n'est revendiqué.

### 2. Accessibilité LivePreview

`LivePreview` non-inline reçoit désormais :
- `role="dialog"` ;
- `aria-modal="true"` ;
- titre lié par `aria-labelledby` ;
- focus initial sur le bouton Fermer ;
- fermeture Escape ;
- label explicite du bouton Fermer ;
- statut de chargement `aria-live`.

Le test `LivePreview.r7.test.tsx` a été étendu pour couvrir dialog / focus / Escape. Ce test est versionné mais **non exécuté dans un vrai Vitest full-project dans l'environnement courant**.

### 3. Legacy cleanup — décision fail-closed

Des fichiers historiques lourds (`EliteAssistant`, `EliteDock`, `DiagnosticEngine`, etc.) semblent potentiellement orphelins, mais la recherche GitHub a retourné `incomplete_results=true`. Ils ne sont donc **pas supprimés sans preuve exhaustive d'absence de référence**.

Même doctrine pour `DocumentFactory.create_installment_plan()` : le chemin public `/documents/generate` `echeancier` est déjà bloqué par le contrat exporté, mais la suppression physique de la méthode reste une dette de quarantaine si l'absence de tout appel est certifiée plus tard.

## Preuves locales consolidées conservées

- P3 : backend 26/26 PASS ; frontend ciblé 39/39 PASS ; policies `tsc --strict` ; PDF multipage ciblé PASS.
- P4 : backend 13/13 PASS ; échéancier 4/4 ; archive hydration 1/1 ; PDF long 36/36 lignes, 6 pages.
- P5 : backend 15/15 PASS ; summary 4/4 ; create payload `tsc --strict` + 8/8.
- P6 : dirty/archive `tsc --strict` + 11/11.
- P7 : safety `tsc --strict` + 8/8 ; P7→P3 + dirty `tsc --strict` + 12/12.
- T1 : navigation dernier rerun `tsc --strict` + **9/9** ; contrat legacy échéancier helper 4/4.

## Gates externes / différés

Avant toute revendication de certification complète ou production-ready :
1. checkout complet du head final avec dépendances installées ;
2. exécution complète de `bash scripts/certify_document_studio.sh` ;
3. smoke authentifié P1→P7 ;
4. archive/reopen/duplicate/print/payment réels selon page ;
5. PDF cabinet branding/signature/long/multipage ;
6. browser 390 / 768 / desktop + clavier/focus/touch ;
7. validation clinique/scientifique/réglementaire humaine où applicable ;
8. résolution/merge ordonné des PR stackées ;
9. recertification post-merge.

## Règle de merge

Les PR stackées restent draft. T2 n'autorise pas implicitement un merge tant que les gates exigés ne sont pas réellement exécutés ou explicitement différés par une nouvelle décision produit.

## Avancement

La roadmap ne définit aucune pondération officielle. **Pourcentage global : indéterminé.**
