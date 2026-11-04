# Digital Crown — Entrée Claude Code

> **Source unique des instructions générales : [AGENTS.md](AGENTS.md).**
>
> Ce fichier est uniquement un point d'entrée compatible avec Claude Code. Il ne définit **aucune seconde doctrine générale** d'exécution, de FUE, de revue, de scoring, de CI, de communication ou de closeout. Toute modification de ces consignes générales se fait **exclusivement dans AGENTS.md**.

## Auditeurs spécialisés V1.5

Pour la revue indépendante, consulter **[docs/quality/V15_INDEPENDENT_REVIEWER_MATRIX.md](docs/quality/V15_INDEPENDENT_REVIEWER_MATRIX.md)** puis charger le ou les `.claude/agents/reviewer-*.md` seulement si le lot et le risque le justifient. Ces agents sont en lecture seule, leurs noms ne constituent pas des reviews humaines indépendantes et leurs avis ne remplacent pas les tests/FUE ou le gate physique V1.5-10. Les agents scientifiques existants restent sous leurs contrats. Les instructions communes et l'autorisation de merge restent exclusivement dans [AGENTS.md](AGENTS.md).

## Lecture opérationnelle

1. Lire `AGENTS.md` pour identifier le lot, sous-lot, chantier, mission, GO et contrat de communication.
2. Lire les références factuelles exigées par `AGENTS.md` (roadmap canonique, `STATE.md`, HEAD, PR, CI) ; ne pas en déduire de GO implicite.
3. Appliquer les règles de domaine concernées sous `.claude/rules/` et le `SKILL.md` pertinent sous `.claude/skills/` ou `skills/`, puis consulter l'agent spécialisé si le travail le nécessite.
   **Contrat de scoring applicable :** lire `.claude/rules/execution-scoring-verification.md` pour les définitions de `EXECUTION_SCORE`, `FUE_EVIDENCE_SCORE`, le gate `VERIFIED` et la `Perfection Pass`. Les seuils et tests restent dans cette règle spécialisée, sans duplication ici.
4. Respecter les restrictions scientifiques, sécurité, confidentialité, read-only, approbations humaines et politiques de release des contrats spécialisés. Ce renvoi ne les remplace pas.
5. Pour le déroulé, les preuves, le résultat, les runs GitHub, les réserves `techdoubt.md`, le Next/effort et le pied **Lot · Sous-lot · Chantier · Roadmap**, suivre **AGENTS.md**.

**En cas de duplication ou contradiction d'instructions générales : AGENTS.md prévaut.** Les sources spécialisées restent applicables dans leur domaine et aucune instruction de ce document n'autorise une fusion, un déploiement, une installation cabinet ou une activation clinique.

