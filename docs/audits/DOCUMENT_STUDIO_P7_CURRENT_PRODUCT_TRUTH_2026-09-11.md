# P7 — Compagnon Diagnostique : vérité produit actuelle

Date : 2026-09-11

## Verdict

**P7 n'est pas une page active du Document Studio certifiable actuel.**

Le Compagnon Diagnostique a été retiré volontairement du contrat produit actif. Le code historique `TreatmentPlanStudio` et ses tests subsistent dans le dépôt, mais ils sont dormants et ne doivent pas être présentés comme une page runtime actuellement certifiable.

## Preuves vérifiées sur `master`

HEAD de référence après fermeture P6 : `e5a9f37fe33690759124cadb18d672d756647578`.

- `frontend/src/features/admin/DocumentStudio/StudioTabs.tsx` n'expose que : Ordonnance, Certificat, Devis, Note Honoraires, Suivi Paiement, Document Libre.
- `frontend/src/features/admin/DocumentStudio/DocumentStudioVocabulary.ts` ne contient que ces six tabs ; `plan` n'appartient plus à `CertifiableDocumentStudioTab`.
- `frontend/scripts/certify-document-studio-browser.mjs` certifie ces six pages et contient un gate explicite `assertCompanionAbsent(...)` qui échoue si le label ou le tab Compagnon Diagnostique est visible.
- commit `a294dacc428d7bee43f910bcb3e71bd8bc6f3496` : `refactor(documents): remove diagnostic companion tab`.
- commit `8e8bb2c245e5b742a37ac29d9b0b6a9aec9e4481` : `refactor(documents): keep only document-producing tabs`, avec suppression de `plan` du vocabulaire certifiable.

## Code dormant restant

`TreatmentPlanStudio.tsx` existe encore dans le dépôt. Il conserve une logique déterministe de questionnaire avec des sorties cliniques et thérapeutiques spécifiques, notamment des diagnostics nommés et des actes pouvant inclure antibiothérapie, antalgiques ou anti-inflammatoires.

Les lots historiques P7-A/B/D/F/G ont durci certaines frontières (warning-only ATCD, reset patient, dirty-state, wording moins prescriptif, responsive/a11y), mais leur présence dans le dépôt **ne prouve pas une page produit active** et ne constitue pas une certification scientifique ou clinique.

Le harness `scripts/certify_document_studio_p7.sh` reste une régression de code historique. Il ne doit pas être utilisé pour revendiquer un runtime P7 actif tant que le produit n'expose pas explicitement cette surface.

## Décision canonique

1. Ne pas réactiver silencieusement `plan` dans Document Studio.
2. Ne pas lancer une certification runtime P7 comme si la page était actuellement active.
3. Conserver le code dormant jusqu'à décision produit/clinique dédiée ou suppression explicite.
4. Toute réactivation future devient un **nouveau chantier produit + clinique**, avec :
   - Goal produit écrit ;
   - frontière clinique structurée ;
   - provenance/version/evidence ;
   - validation scientifique humaine ;
   - BEFORE/mockup/AFTER si UI réintroduite ;
   - runtime authentifié patient A→B ;
   - responsive/clavier ;
   - full-regression avant exposition.
5. Pour le Document Studio certifiable actuel, le prochain lot transversal exécutable après P6 est **T1**, pas P7 runtime.

## Limite

Ce document ne décide pas que le concept de compagnon diagnostique doit être supprimé définitivement. Il fixe uniquement la vérité actuelle : **surface retirée du produit certifiable, code dormant, aucune certification runtime/scientifique P7 active revendiquée**.
