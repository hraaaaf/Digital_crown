# CUST-04 — Practitioner prescription presets — Goal

Date: 2026-09-22

## Goal
Permettre au praticien d'enregistrer et de réutiliser ses propres brouillons d'ordonnance, sans transformer un preset en recommandation clinique automatique.

## Vérité actuelle vérifiée
- Le studio actif est `PrescriptionAgenticStudioV1.tsx`, réexporté via `PrescriptionAgenticStudio.tsx`.
- Le studio actif marque explicitement les règles/suggestions cliniques comme bloquées :
  - `data-clinical-rule-status="blocked"`
  - `data-safety-status="blocked"`
  - les suggestions cliniques bloquées sont masquées.
- Le formulaire legacy `PrescriptionForm.tsx` contient encore 4 protocoles rapides codés en dur et une détection de contexte par libellé, mais il ne doit pas être utilisé comme base tant que son usage actif n'est pas prouvé.
- `useDocumentGenerator.ts` valide la présence d'au moins un médicament et la posologie des lignes médicament avant génération.
- Le moteur actuel ne prétend pas vérifier interactions, contre-indications ou doses : il limite l'analyse de cohérence à la complétude tant qu'une règle clinique sourcée/versionnée/testée n'existe pas.
- Le payload final d'ordonnance conserve les valeurs explicites du praticien.

## Principe de sécurité CUST-04
Un preset praticien est un **brouillon réutilisable**, jamais :
- une recommandation clinique ;
- une adaptation automatique au patient ;
- une déduction depuis le diagnostic, l'acte ou le libellé ;
- une validation de dose, indication, interaction ou contre-indication ;
- une prescription appliquée sans clic explicite.

L'application d'un preset doit remplir un brouillon éditable et rester soumise aux validations existantes avant génération.

## Audit à compléter avant code
1. identifier le parent actif qui monte `PrescriptionAgenticStudioV1` ;
2. identifier la persistance existante la plus proche (`DocumentTemplate`, habitudes praticien, autre modèle) ;
3. vérifier si `onSaveHabit` est réellement branché ou dormant ;
4. cartographier les frontières tenant/praticien ;
5. décider si CUST-04 réutilise une primitive existante ou nécessite un stockage dédié ;
6. vérifier les tests et garde-fous existants avant toute mutation UI.

## Target fonctionnel provisoire
Dans le studio actif :
- zone discrète « Mes presets » ;
- action « Enregistrer ce brouillon comme preset » ;
- clic explicite sur un preset pour charger les lignes ;
- confirmation si le brouillon courant contient déjà des lignes différentes ;
- toutes les lignes restent éditables après chargement ;
- indication/patient/date ne sont jamais capturés silencieusement ;
- aucun preset appliqué automatiquement.

## Succès observable
1. aucun changement clinique automatique ;
2. un preset n'est appliqué qu'après action explicite du praticien ;
3. aucune donnée patient n'est stockée dans le preset ;
4. aucun libellé clinique n'active automatiquement un preset ;
5. les validations de l'ordonnance restent actives après chargement ;
6. isolation tenant/praticien vérifiée ;
7. BEFORE/AFTER 390×844, 768×1024, 1280×900 ;
8. tests fonctionnels + CI + T2 verts avant merge.

## Hors scope
- moteur de recommandation thérapeutique ;
- calcul ou validation de dose ;
- interactions médicamenteuses automatiques ;
- contre-indications automatisées ;
- prescription automatique depuis diagnostic/acte ;
- déploiement Vercel.
