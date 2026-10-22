# CEPH-UXCLIN-01 — R23-I : audit clinique de provenance après FUE-H

**Date :** 2026-10-22. **Type :** revue documentaire/contrat **test-only**, pas une évolution du moteur clinique.  
**FUE-H source de preuve :** [Actions #39836036083](https://github.com/hraaaaf/Digital_crown/actions/runs/39836036083), HEAD exact `8ebd8b013c54ee9417b4edce091c942fbdbaf22b`, artefact [#12450269332](https://github.com/hraaaaf/Digital_crown/actions/runs/39836036083/artifacts/12450269332).  
**PR parent :** [#1024](https://github.com/hraaaaf/Digital_crown/pull/1024), OPEN/DRAFT. **PR #1007 et #1019 :** DRAFT, non mergées.

## Pourquoi après FUE-H ?

FUE-H a confirmé sur **deux vraies radios publiques importées via l'UI** et sur vrai SRPose38 ONNX verrouillé SHA256 : deux études distinctes, **38 points automatiques par radio**, autorisations inter-cabinets négatives et réouverture après un nouveau login. **Ce n'est pas une vérification orthodontique des 38 points.** Les captures montrent des mesures géométriques brutes dans « Toutes analyses » alors que la réglette reste non vérifiée.

**Ne pas confondre** les trois concepts :
1. Géométrie brute : un **angle en degrés** ne requiert en principe pas de conversion mm/pixel. Un manque de calibration ne rend donc pas automatiquement l'angle indéfini.
2. Provenance et qualité de points : des angles calculés sur des **38 repères SRPose38 non corrigés par orthodontiste** ne sont pas des observations cliniques validées.
3. Norme / classification / diagnostic : interdits sans définition scientifique versionnée, source verrouillée et validation indépendante ; aucun passage de ce lot ne les autorise.

## Findings conservés, sans qualifier une mesure de « fausse »

| ID | Preuve dans code immuable | Risque à auditer |
|---|---|---|
| R23I-01 | `CephaloAnalysisWorkbenchPanel.tsx` compte toute `readValue !== null` ; compteur de mesures passe au vert dès `availableCount > 0`. | Confusion entre « géométriquement calculée » et « validée ». |
| R23I-02 | Détail de mesure : icône `CheckCircle2` si valeur numérique plutôt que `null`, sans gate visible de validation humaine. | Signal positif qui peut être pris pour une approbation clinique. |
| R23I-03 | Statut générique `Mesure brute` pour mesures sans statut ; panneau « Toutes analyses » sans étiquette SRPose38/repères automatiques non relus. | Provenance non explicite à côté de valeurs réellement visibles. |

**Contre-évidence favorable :** calibration `Échelle non vérifiée` et `Réglette à vérifier` sont explicitement prévues ; Step4Documents précise qu'une prévisualisation/archivage PDF ne vaut pas validation clinique ; le volet R23-G4 Ricketts utilise une voie `reference_display_only` et refuse la projection en l'absence de graphe source vérifié. **Ne pas supprimer les mesures brutes autorisées, ni inventer une norme.**

## Action décidée pour cette PR

Cette PR doit **uniquement** produire une preuve technique traçable qu'un nouveau gate scientifique d'UX est nécessaire : code source exact, fragment et ligne, SHA256 du fichier, contrôles anti-dérive de la détection, résultats JSON et rapport court. Elle n'affirme PAS avoir exécuté à nouveau FUE-H ni validé des données cliniques.

Le workflow compare la référence H figée avec son SHA exact et vérifie l'artefact Actions d'origine ; il échoue si un contrat de code évolue sans revue. Un workflow d'audit **SUCCESS** signifie seulement que le risque est toujours détecté/documenté, **pas que le produit est certifié**.

## Critères à faire approuver par le praticien responsable (hors cette PR)

- Une valeur géométrique calculée à partir de points automatiques doit être étiquetée **« automatique, non validée par un praticien »**, avec son identité image et méthode ; ne pas colorer en vert la seule disponibilité mathématique.
- Conserver **NC** lorsque la construction géométrique est absente/non finie ; conserver les angles bruts calculables même si mm/pixel non vérifié.
- Les distances en mm exigent une échelle adaptée et une preuve d'identité image ; aucune substitution de repères Ricketts.
- Le futur travail de correction par praticien doit produire des traces indépendantes (`validated_by`, `validated_at`, revision et source image), non une case cochée sans preuve.
- Avant affichage d'une classification patient ou d'une décision clinique : source de norme, tranche d'âge/population, géométrie source-exacte et adjudication orthodontique indépendante.

**Garde-fous :** CLINICAL NO-GO, pas de changement runtime, pas de merge, pas de déploiement, roadmap **41/99 inchangée**, approbation visuelle propriétaire pour la nouvelle PR distincte de #1007.

## Reproductibilité

Exécuter `python scripts/audit_ceph_r23i_provenance_gate.py` sur le HEAD de la branche audit ; lire `artifacts/ceph-r23i-provenance-gate/report.json` et `README.md`. Le rapport doit mentionner **3 ambiguïtés** et `clinical_release: false`.
