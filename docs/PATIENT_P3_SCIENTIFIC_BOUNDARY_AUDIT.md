# Patient P3 — Audit frontière scientifique des assistants cliniques

## Statut
Audit source effectué avant modification UI P3. Ce document ne certifie pas les questionnaires comme recommandations cliniques ; il vérifie uniquement leur frontière d'autorité dans le runtime actuel.

## Conclusion
Les assistants montés par `ClinicalHub` sont actuellement des questionnaires structurés de collecte/proposition. Les sorties inspectées ne créent pas d'étapes thérapeutiques autoritatives : elles retournent une synthèse textuelle et une liste de plan vide (`[]`), puis `ClinicalHub` conserve cette sortie en session comme `Proposition clinique à valider`.

Le diagnostic retenu et le Master Plan ne doivent donc jamais être mutés automatiquement à partir de ces assistants.

## Fichiers audités
- `AssistantExamenComplet.tsx`
- `AssistantGeneral.tsx`
- `AssistantParo.tsx`
- `AssistantEndo.tsx`
- `AssistantChirurgie.tsx`
- `AssistantProthese.tsx`
- `AssistantPedo.tsx`
- `AssistantOrtho.tsx`
- `AssistantATM.tsx`
- `AssistantPatho.tsx`

## Frontière vérifiée

### Examen complet
- branche urgence : observations + signaux de vigilance uniquement ;
- branche routine : observations + signaux de vigilance uniquement ;
- texte explicite : aucun diagnostic automatique et aucune conduite thérapeutique automatique ;
- résultat : `steps: []`, `next: null`.

### Assistants spécialisés
Endo, Paro, Chirurgie, Prothèse, Pédodontie, Orthodontie, ATM, Pathologie et Général :
- reprennent les réponses sélectionnées sous forme de synthèse ;
- indiquent explicitement que diagnostic/examens complémentaires/traitement relèvent du praticien ;
- `onComplete(summary, [])` ;
- aucune mutation directe du Master Plan dans ces composants.

## Écarts de vocabulaire à corriger en P3 UI
Les comportements sont neutralisés mais quelques textes décrivent encore une capacité que le code n'exécute plus :
- `AssistantParo` : `Génération du Diagnostic AAP/EFP 2017...` ;
- `AssistantProthese` : `Génération du Plan Prothétique...` ;
- `AssistantOrtho` : `Génération du Plan Orthodontique...`.

Cible P3 : remplacer ces formulations par `Synthèse ... structurée` sans modifier les questionnaires ni introduire de règle clinique supplémentaire.

## Points non certifiés par cet audit
- validité scientifique exhaustive de chaque libellé de question/options ;
- exhaustivité des examens proposés par rapport aux recommandations de spécialité ;
- pertinence thérapeutique, puisqu'aucune recommandation thérapeutique automatique ne doit être produite ;
- utilisation clinique sans validation du praticien.

## Règles P3 associées
1. proposition assistant ≠ conclusion clinique retenue ;
2. aucune sortie assistant ne peut créer/modifier le Master Plan automatiquement ;
3. toute conclusion persistée exige l'action explicite d'un praticien autorisé ;
4. les libellés UI doivent décrire la fonction réelle, pas une ancienne capacité diagnostique ;
5. aucune réintroduction de traitement, médicament, imagerie ou orientation automatiques sans certification scientifique dédiée.
