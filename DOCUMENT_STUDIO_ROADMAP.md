# Document Studio — roadmap canonique page par page

Date de référence : 2026-08-16

## Objectif

Auditer, corriger et recertifier le Studio documentaire de Digital Crown **page par page, dans l’ordre visuel réel de l’interface**, sans confondre engineering, runtime, validation clinique/financière et production.

Ordre canonique (`StudioTabs.tsx`) :

1. **P1 — Ordonnance**
2. **P2 — Certificat**
3. **P3 — Devis**
4. **P4 — Note Honoraires**
5. **P5 — Suivi Paiement**
6. **P6 — Document Libre**
7. **P7 — Compagnon Diagnostique**
8. **T1 — Audit transversal premium**
9. **T2 — Refonte intelligente finale / recertification globale**

## Règle de preuve

- **CODE VÉRIFIÉ** : comportement démontré par le code courant.
- **TEST EXÉCUTÉ** : résultat réellement observé.
- **INTERACTION EXÉCUTÉE** : parcours réellement observé dans l’application.
- **CERTIFICATION** : séparée et jamais déduite automatiquement d’un test local ou d’une CI.

Aucun pourcentage global n’est déduit de cette roadmap : aucune pondération officielle des pages/gates n’a été définie. **Avancement global chiffré : indéterminé.**

---

## P1 — Ordonnance

**État : ✅ engineering fermé + recertification visuelle réalisée ; gates clinique/runtime séparés.**

Rapport : `docs/audits/DOCUMENT_STUDIO_P1_ORDONNANCE_AUDIT.md`.

Gates séparés : interaction authentifiée finale et validation clinique/pharmacologique humaine.

---

## P2 — Certificat

**État : ✅ engineering convergé ; ⏳ runtime/PDF final différé.**

Rapport historique : `docs/audits/DOCUMENT_STUDIO_P3_CERTIFICAT_AUDIT.md`.

T1 a rétabli un dirty-state Certificat explicite et intégré la date commune à la protection de brouillon.

---

## P3 — Devis

**État : ⏸ CLOSED / PAUSED UNTIL FURTHER NOTICE — décision produit du 16 août 2026.**

Rapports :
- `docs/audits/DOCUMENT_STUDIO_P3_DEVIS_AUDIT.md`
- `docs/audits/DOCUMENT_STUDIO_P3_DEVIS_INTEGRATION_STATUS.md`

PR : **#77**, open + draft.

Preuves locales P3-H conservées : backend **26/26 PASS**, frontend policies `tsc --strict` PASS, frontend ciblé **39/39 PASS**, PDF long lisible floor >=7 pt.

---

## P4 — Note Honoraires

**État : ✅ engineering local convergé ; ⏳ full-app/browser/PDF cabinet différés.**

Rapport : `docs/audits/DOCUMENT_STUDIO_P4_NOTE_HONORAIRES_AUDIT.md`.
PR : **#90**, draft.

Preuves locales : backend **13/13 PASS**, échéancier **4/4 PASS**, archive hydration **1/1 PASS**, PDF long **36/36 lignes / 6 pages / header 6/6 / floor 7 pt**.

---

## P5 — Suivi Paiement

**État : ✅ engineering local convergé ; ⏳ certification financière/full-app différée.**

Rapport : `docs/audits/DOCUMENT_STUDIO_P5_SUIVI_PAIEMENT_AUDIT.md`.
Handover : `docs/audits/DOCUMENT_STUDIO_P5_HANDOVER_2026-08-16.md`.
PR : **#95**, draft.

Preuves locales : backend **15/15 PASS**, summary **4/4 PASS**, create payload `tsc --strict` + **8/8 PASS**.

T1 a en plus :
- rendu le contrat d’impression explicite : PDF brouillon ≠ sauvegarde ;
- supprimé le stale-print P5 en armant l’impression seulement après nouveau `pdf_url` ;
- désactivé le vieux second moteur `/documents/generate` pour `echeancier`.

---

## P6 — Document Libre

**État : ✅ engineering local convergé ; ⏳ runtime/PDF cabinet différés.**

Rapport : `docs/audits/DOCUMENT_STUDIO_P6_DOCUMENT_LIBRE_AUDIT.md`.
PR : **#96**, draft.

Preuve P6-R1 : `tsc --strict` PASS + **11/11 assertions PASS**.

T1 a centralisé la décision de navigation et l'archive-success au niveau du Hub. Les anciens listeners locaux encore présents restent redondants mais fail-closed ; T2 ne revendique pas leur suppression.

---

## P7 — Compagnon Diagnostique

**État : ✅ engineering safety local convergé ; ⏳ full-app + validation clinique/scientifique différés.**

Rapport : `docs/audits/DOCUMENT_STUDIO_P7_COMPAGNON_DIAGNOSTIQUE_AUDIT.md`.
PR : **#97**, draft.

Preuves locales : policy P7 `tsc --strict` + **8/8 PASS** ; chaîne P7→P3 + dirty `tsc --strict` + **12/12 PASS**.

---

## T1 — Audit transversal premium

**État : ✅ engineering transversal local convergé ; ⏳ full-app/browser différés.**

Rapport : `docs/audits/DOCUMENT_STUDIO_T1_TRANSVERSAL_AUDIT.md`.
PR : **#101**, draft.

### Fermetures T1

- navigation clic/query-param/programmée centralisée ;
- dirty-state Certificat rétabli ;
- date commune intégrée aux dirty-state concernés ;
- archive-success rendu explicite, sans déduction via simple changement de `pdfUrl` ;
- preview/erreur/409 ne nettoient plus les brouillons ;
- P5 impression non persistante rendue explicite et stale-print supprimé ;
- branche ghost `ai` retirée du Document Studio et appel `/ai-diagnostic` supprimé du hook ;
- ancien `/documents/generate` `echeancier` désactivé ;
- header partagé nettoyé des raccourcis de navigation directs ;
- permissions partagées relues et accès patient conservé.

### Preuves T1

- `DocumentNavigationPolicy` : `tsc --strict` PASS + **9/9 scénarios PASS** au dernier rerun local ;
- contrat legacy échéancier : **4/4 PASS** sous Linux ;
- tests `DocumentRequest` versionnés ;
- inspection statique des composants/routeurs partagés.

### Gates différés

- vrai `npm test` / `npm run build` full-project ;
- suite backend full-repo ;
- runtime authentifié navigation/dirty/archive/preview/409/print ;
- browser 390/768/desktop ;
- PDF cabinet ;
- merge/post-merge.

---

## T2 — Refonte intelligente finale / recertification globale

**État : ✅ engineering local convergé ; ⏳ certification full-app / humaine différée.**

Rapports :
- `docs/audits/DOCUMENT_STUDIO_T2_FINAL_STATUS.md`
- `docs/audits/DOCUMENT_STUDIO_T2_FINAL_RECERTIFICATION.md`
- `docs/audits/DOCUMENT_STUDIO_T2_HANDOVER_2026-08-16.md`

PR : **#102**, draft.

### Acquis T2

- certificateur unifié `scripts/certify_document_studio.sh` couvrant targeted backend P1→P7, full backend, targeted DocumentStudio Vitest, full frontend, build, invariants source et prod-safety ;
- prérequis du harness : Python >=3.12, Node >=20, worktree propre ;
- `LivePreview` non-inline durci : `role=dialog`, `aria-modal`, titre lié, focus initial, Escape, loading `aria-live` ;
- test LivePreview étendu pour dialog/focus/Escape ;
- fichiers legacy potentiellement orphelins non supprimés sans scan complet fiable (`incomplete_results=true`).

### Preuves T2 réellement exécutées

- `bash -n scripts/certify_document_studio.sh` reconstruit sous Linux : **PASS** ;
- environnement local : Python **3.13.5**, Node **22.16.0**, npm **10.9.2**.

Le harness complet n'est pas revendiqué PASS dans cette session : le checkout full-repository avec dépendances installées n'est pas monté dans cet environnement.

### Gates finaux différés

1. exécution complète de `bash scripts/certify_document_studio.sh` sur le head candidat exact ;
2. runtime authentifié P1→P7 ;
3. archive/reopen/duplicate/print/payment réels ;
4. PDF cabinet branding/signature/long/multipage ;
5. browser 390 / 768 / desktop + clavier/touch/focus ;
6. validations humaines clinique/scientifique/réglementaire/financière applicables ;
7. ready/merge ordonné des PR stackées puis post-merge recertification.

**Verdict global Document Studio : engineering local connu convergé ; certification complète non revendiquée. Pourcentage global indéterminé faute de pondération officielle.**
