# P5 — Compagnon diagnostique + interactions inter-pages : pré-audit statique

## Statut de preuve

Pré-cartographie **lecture seule** réalisée pendant les gates CI P2.

- **CODE VÉRIFIÉ** : oui, pour les constats ci-dessous.
- **TESTS EXÉCUTÉS P5** : non.
- **INTERACTION RUNTIME** : non exécutée.
- **CERTIFICATION CLINIQUE / UX / PRODUCTION** : non revendiquée.

## P5-A — Labels d’origine ≠ validation clinique

### Fait vérifié
`EliteAssistant` expose `source_type: DETERMINISTIC | HEURISTIC`.

Dans l’UI :
- `DETERMINISTIC` est affiché comme `🛡️ VÉRIFIÉ` ;
- `HEURISTIC` est affiché comme `🤖 IA`.

### Risque
`VÉRIFIÉ` peut être interprété comme une validation clinique/scientifique alors que le champ décrit seulement une catégorie technique de génération du signal.

### Décision recommandée
Utiliser une terminologie descriptive non autoritative : par exemple `Règle déterministe` / `Heuristique`, et réserver tout vocabulaire de validation à une preuve réellement qualifiée.

---

## P5-B — Actions de fallback déduites de l’identifiant ou du texte

### Fait vérifié
Quand un insight n’a pas de callback `onAction`, `EliteAssistant` déduit une navigation à partir :
- du préfixe de `insight.id` (`pano_detect`, `financial_alert`, `rag_history`, `trigger_`, etc.) ;
- parfois du texte de `actionLabel` (`dossier`, `agenda`, `planifier`, etc.).

### Risque
Une action produit peut changer si un libellé ou un identifiant évolue, sans contrat typé explicite entre backend et frontend.

### Décision recommandée
Transporter une action structurée et whitelistée (`action_type`, paramètres), puis router explicitement. Aucun comportement métier ne doit dépendre d’une recherche lexicale dans un label visible.

---

## P5-C — Insights WebSocket

### Fait vérifié
Les insights reçus par WebSocket sont convertis en `source_type: HEURISTIC` et ajoutés au store si leur ID n’est pas déjà présent.

Le composant construit l’URL WebSocket avec le token d’authentification en query string lorsqu’un token local/session existe.

### Limite de ce pré-audit
La sécurité/authentification WebSocket relève aussi du chantier credentials/auth global. Elle n’est pas requalifiée ici sans audit backend correspondant.

---

## P5-D — Points restant à cartographier

- source backend exacte de chaque famille d’insights ;
- HouseWizard et arbre complet des questions ;
- conservation/perte d’état entre onglets ;
- passage Compagnon → Devis/Ordonnance ;
- validation praticien avant mutation ;
- feedback accept/reject et effets persistants ;
- reconnect WebSocket et déduplication ;
- tests runtime/accessibilité avant certification.
