# DIGITAL CROWN — CÉPHALOMÉTRIE — R15 STUDIO CLINIQUE UX/UI

**Date :** 2026-09-12  
**Statut :** R15 ACTIF — non certifié, non mergé  
**Base R15 vérifiée :** `36091c89a6f4ae0679f40980e9f7f3e5e143d6be`  
**Branche :** `feat/cephalo-r15-clinical-studio-ux`  
**Canonique parent :** `docs/CEPHALO_DIAGNOSTIC_SPEC.md`  
**Déploiement :** aucun ; aucun déploiement Vercel sans autorisation explicite.

## GOAL R15

Construire le Studio clinique UX/UI Digital Crown qui rend les états scientifiques R11/R12/R13/R14 immédiatement compréhensibles et actionnables par le praticien, sans inventer, masquer ou auto-sélectionner de contenu clinique.

### Succès observable

- lecture explicite et continue `R11 → R12 → R13 → R14` ;
- provenance, missing data, contradictions, contre-indications et blocking gates visibles ;
- `EVALUABLE` présenté comme évaluable, jamais comme prescription ou sélection ;
- `BLOCKED != DROPPED` visible dans l'interface ;
- toute action praticien affichée est soit réellement disponible avec preuve backend traçable, soit explicitement indisponible avec sa raison ;
- les anciens champs libres sont clairement distingués des objets autoritaires R11–R14 ;
- archivage documentaire et validation clinique R14 ne sont jamais confondus ;
- BEFORE/AFTER sur les mêmes surfaces et viewports 390 / 768 / 1280+ ;
- CI exact-head + T2 verts avant merge ;
- reviews/threads clean ;
- aucun déploiement.

## EXTENSION DE MISSION AJOUTÉE LE 2026-09-12

Les constats de l'audit initial deviennent des exigences R15 obligatoires :

1. **Remplacer la lecture clinique legacy** : le workflow actuel `Céphalométrie → Moulages → Synthèse clinique → Documents & stratégie` ne suffit pas pour exprimer l'autorité scientifique R11–R14. Les étapes métier existantes peuvent rester comme navigation de travail, mais la décision clinique doit être lue explicitement comme `R11 → R12 → R13 → R14`.
2. **Exposer l'état scientifique réel** : provenance, missing data, contradictions, blockers, `EVALUABLE`, validation/rejet praticien et absence de snapshot autoritaire doivent être visibles sans embellissement trompeur.
3. **Aucune validation décorative** : aucune action ou libellé local ne doit simuler une validation R11/R13/R14. Toute validation visible doit être reliée à une preuve backend réelle avec cible, action, acteur et horodatage cohérents.
4. **Séparer notes et autorité** : les textes libres diagnostiques/thérapeutiques legacy restent au mieux des notes praticien clairement étiquetées hors preuve R11/R13/R14.
5. **Séparer archive et validation** : `Prévisualiser`, `Brouillon PDF`, `Archiver` sont des actions documentaires et ne valent jamais validation R14.
6. **Réparer la certification visuelle préexistante** : `.github/workflows/document-history-actions-visual-cert.yml` était réellement corrompu sur master et produisait des échecs immédiats. Il ne peut servir de preuve tant qu'il n'est pas réparé et revalidé.
7. **BEFORE/AFTER étendu** : couvrir les surfaces Étape 3 et Étape 4, mêmes viewports 390 / 768 / 1280+, avec absence d'overflow, erreur runtime et confusion sémantique.

## CHRONOLOGIE DE PREUVE — NE PAS RÉÉCRIRE L'HISTOIRE

- Le Goal R15 et les contraintes UX/UI ont été fournis avant toute implémentation R15.
- Le premier commit de branche après master est `21eff261a7128ef733936569dc42d533f832da2e` et ajoute uniquement le harness BEFORE ; aucune UI n'y est modifiée.
- Le workflow BEFORE est ensuite ajouté par `b6efb79bb821ad6c3c6e6ac85ec90433f175c799`.
- La dette du workflow visuel corrompu est réparée sur la branche par `5abebf9f26b25d622b7e5fde8ca4073952b55005` avant l'implémentation R15.
- Le premier code de projection R15 arrive ensuite (`249cf53564b414d895047fc675ea429b694f2c58`).
- **Écart documentaire identifié :** la référence/mockup structurée n'avait pas été enregistrée dans un fichier dédié avant les premiers changements UI. Ce document formalise cet élément ; aucune nouvelle modification visuelle ne doit être faite avant validation de cette référence et obtention d'un BEFORE propre.

## BEFORE RÉEL — ÉTAT ACTUEL DE LA PREUVE

Workflow : `Cephalo R15 BEFORE`.

Dernier artefact disponible :
- run `34718890021` ;
- HEAD harness `27f6763e439a3453a1e0080852ed13003b64386c` ;
- artefact `cephalo-r15-before` ;
- digest `sha256:47cee55bfc90240d8a6271695d868c3816cd32f94de732c041f869e18f724a60` ;
- 12 captures produites : Step 3 top + décision et Step 4 top + action, chacune en 390x844 / 768x1024 / 1280x900.

Constats vérifiés :
- 390 et 1280 sont exploitables ;
- 768 Step 3 a subi un rendu transitoire vide ;
- `invalidCount = 1` ;
- aucune surface explicite R11/R12/R13/R14 dans le BEFORE legacy ;
- Step 3 utilise encore les libellés de diagnostic/plan thérapeutique libre ;
- Step 4 présente encore une checklist de « validation », un plan de traitement libre et `Valider & Archiver` ;
- aucun overflow horizontal sur les captures rendues correctement.

**Conclusion :** le BEFORE existe et prouve le problème, mais n'est pas encore une preuve visuelle certifiable à 3/3 viewports. Une recapture propre sur la base exacte `36091c89…` est obligatoire avant certification R15.

## GOAL VISUEL ÉCRIT

Le praticien doit comprendre en moins d'un écran :

- où se situe le dossier dans la chaîne R11→R14 ;
- ce qui est autoritaire versus simple note ;
- pourquoi un étage est bloqué ;
- quelles données/preuves manquent ou se contredisent ;
- quelle provenance soutient l'état ;
- si une action praticien est réellement disponible ;
- qu'une action documentaire n'est pas une validation clinique.

Aucun code couleur ne doit transformer une valeur brute ou une hypothèse non validée en diagnostic implicite.

## RÉFÉRENCE / MOCKUP R15

Référence visuelle : identité Digital Crown céphalométrique existante et certification R1, sans introduire un design générique externe.

Structure cible :

```text
┌ Chaîne clinique scientifique ───────────── R11 → R14 ── N blocages ┐
│ Une mesure calculable ≠ diagnostic ≠ indication ≠ traitement        │
├────────────┬────────────┬────────────┬────────────┤
│ R11        │ R12        │ R13        │ R14        │
│ Diagnostic │ Problèmes  │ Options    │ Final      │
│ [ÉTAT]     │ [ÉTAT]     │ [ÉTAT]     │ [ÉTAT]     │
├─────────────────────────────────────────────────────────────────────┤
│ Étage sélectionné                                                   │
│ Résumé autoritaire / état                                           │
│ ┌ Blocages / missing / contradictions ┐ ┌ Provenance ┐             │
│ │ ...                                  │ │ ...        │             │
│ └──────────────────────────────────────┘ └────────────┘             │
│ ┌ Action praticien ───────────────────────────────────────────────┐ │
│ │ disponible uniquement si backend + preuve traçable le permettent│ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘

[Notes praticien — hors preuve scientifique autoritaire]
[Actions documentaires — ne valent jamais validation R14]
```

Sur mobile : cartes R11–R14 en grille 1 colonne ou 2 colonnes selon largeur, détails empilés, aucun élément critique masqué horizontalement.

## TOKENS VÉRIFIÉS

Source unique : `frontend/src/features/ortho/cephaloTheme.ts`.

Règles :
- fonds/panels/cards/borders/textes depuis `PALETTE` ;
- `accentSuccess` réservé à un état réellement validé ;
- `accentWarning` pour attente/action requise/évaluable non sélectionné ;
- `accentError` pour rejet ou blocage réel ;
- aucune couleur clinique diagnostique ajoutée hors tokens ;
- conserver l'identité sombre/glassmorphisme existante et sa variante light.

## CONTRAT D'IMPLÉMENTATION

Le Studio R15 est une **projection clinique**, pas un moteur supplémentaire :

- il lit l'autorité existante ;
- il ne crée aucune règle, norme, diagnostic, objectif, option ou plan ;
- si les snapshots R11–R14 ne sont pas persistés, il doit afficher exactement cette absence comme blocker ;
- une action praticien non implémentée côté backend doit rester désactivée ;
- l'UI ne peut pas promouvoir un état local en validation clinique ;
- toute future action activée doit produire la preuve conforme au contrat backend concerné.

## NON-GOALS R15

- aucune activation de nouvelle norme ou règle scientifique ;
- aucune création de vraie option thérapeutique ;
- aucune auto-sélection R13 ;
- aucun contournement des gates R11–R14 ;
- aucun PDF/restitution R16 ;
- aucun déploiement Vercel.

## PREUVES REQUISES AVANT CERTIFICATION R15

1. BEFORE propre sur base exacte `36091c89…`, 390/768/1280+, mêmes scènes Step 3/4 ;
2. comparaison BEFORE/AFTER sur les mêmes viewports et mêmes zones ;
3. AFTER sans overflow, erreur runtime ni egress externe inattendu ;
4. tests backend de projection fail-closed + tenant guard ;
5. tests frontend des états R11–R14, visibilité blockers/provenance et absence de validation simulée ;
6. build frontend ;
7. workflow visuel réparé réellement vert ou explicitement non utilisé comme preuve ;
8. CI exact-head verte ;
9. T2 verte ;
10. reviews/threads clean ;
11. diff final propre et limité au scope R15 ;
12. canonical + handover R16 seulement après preuves.

## NEXT EXACT

Produire un BEFORE propre et déterministe sur la base exacte `36091c89a6f4ae0679f40980e9f7f3e5e143d6be`, puis auditer l'implémentation R15 actuelle contre ce Goal/mockup avant toute nouvelle retouche visuelle.
