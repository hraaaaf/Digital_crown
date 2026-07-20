# Gouvernance de l'infrastructure scientifique — Digital Crown

## Objet

Ce document régit l'infrastructure d'agents et de skills Claude Code
dédiée au développement des fonctionnalités scientifiques de Digital
Crown : pharmacologie/ordonnance, examen clinique, diagnostic dentaire,
céphalométrie/orthodontie, panoramique/radiologie.

Ces agents ne sont **pas** des assistants visibles dans l'application. Ils
codent, auditent, testent et révisent le code de Digital Crown sous
supervision humaine.

## Garanties obligatoires

Tout changement scientifique produit via cette infrastructure doit :

1. commencer par l'analyse du dépôt réel (jamais une supposition) ;
2. s'appuyer sur des sources officielles ou scientifiques identifiables
   (voir `SOURCE_POLICY.md`) ;
3. distinguer clairement une règle clinique, un calcul, une valeur
   normative et un texte généré ;
4. conserver la provenance et la version de chaque source utilisée ;
5. ajouter des tests adaptés (voir `AGENT_HANDOFF_PROTOCOL.md`) ;
6. refuser d'inventer une règle manquante ;
7. signaler toute contradiction scientifique rencontrée ;
8. n'utiliser aucune donnée patient réelle dans les recherches ou les
   tests ;
9. n'écrire jamais rien dans la base de production ;
10. rester soumis à une validation humaine avant toute activation d'une
    règle clinique.

## Ce que cette infrastructure ne fait pas

- Elle ne corrige pas directement les fonctionnalités ordonnance,
  diagnostic, céphalométrie ou panoramique en dehors d'une tâche
  explicitement demandée par la gouvernance produit existante.
- Elle n'ajoute aucune nouvelle logique médicale active sans validation
  clinique documentée.
- Elle ne modifie jamais les modèles de production sans migration revue.
- Elle ne lance jamais de migration en production.
- Elle n'utilise jamais de données patients réelles.
- Elle n'envoie jamais de radiographie, dossier ou donnée clinique vers un
  service externe.
- Elle ne télécharge jamais automatiquement de dataset radiologique.
- Elle ne modifie jamais les permissions Claude Code
  (`.claude/settings.json`) sans nécessité démontrée et validée par
  ailleurs.
- Elle ne déclare jamais Digital Crown conforme à une norme médicale ou
  réglementaire (voir `research/architecture-and-interoperability.md`).

Les recherches scientifiques effectuées par cette infrastructure
alimentent un **registre de sources candidates**
(`SOURCE_REGISTRY.yaml`), pas des règles cliniques actives.

## Composants

| Composant | Rôle |
|---|---|
| `.claude/agents/scientific-architect.md` | Architecture transversale, distribution du travail |
| `.claude/agents/pharmacology-engineer.md` | Ordonnance et pharmacologie |
| `.claude/agents/clinical-diagnosis-engineer.md` | Examen clinique et diagnostic |
| `.claude/agents/cephalometry-engineer.md` | Céphalométrie et orthodontie |
| `.claude/agents/radiology-engineer.md` | Panoramique et radiologie |
| `.claude/agents/scientific-test-engineer.md` | Tests scientifiques |
| `.claude/agents/scientific-reviewer.md` | Revue indépendante, lecture seule |
| `.claude/skills/*/SKILL.md` (11) | Workflows spécialisés invoqués par les agents |
| `.claude/rules/scientific-engineering.md` | Règle path-scoped sur les chemins scientifiques réels |
| `docs/scientific-ai/SOURCE_REGISTRY.yaml` | Registre des sources, avec statut de validation |
| `docs/scientific-ai/templates/*.schema.yaml` | Schémas de définition des règles/mesures |
| `scripts/validate_scientific_ai_assets.py` | Validateur structurel de cette infrastructure |

## Chaîne de responsabilité

Voir `AGENT_HANDOFF_PROTOCOL.md` pour le format exact de transmission
entre agents. En résumé :

```
scientific-architect → agent de domaine → scientific-test-engineer → scientific-reviewer → validation humaine
```

Aucune règle clinique ne devient active sans passage par
`scientific-reviewer` et sans `status: approved-by-clinician` sur chaque
source qui la fonde.

## Mise à jour de cette gouvernance

Toute modification de ce document ou de la structure ci-dessus doit rester
compatible avec `CLAUDE.md` / `AGENTS.md` à la racine du dépôt (guide
général du projet) et ne doit jamais les dupliquer intégralement — un
pointeur court suffit dans ces fichiers.
