# P6 — Audit transversal premium : pré-audit statique

## Statut de preuve

Pré-cartographie **lecture seule** réalisée pendant les gates CI P2.

- **CODE VÉRIFIÉ** : oui, pour les constats ci-dessous.
- **TESTS EXÉCUTÉS P6** : non.
- **INTERACTION RUNTIME** : non exécutée.
- **CERTIFICATION UX / ACCESSIBILITÉ / PRODUCTION** : non revendiquée.

## P6-A — Typographie globale trop petite

### Faits vérifiés
- `StudioTabs` utilise `text-[10px]` pour les libellés principaux.
- `StudioHeader` utilise notamment `text-[9px]` pour patient/actions/date.
- Plusieurs sous-écrans P2/P3 inspectés descendent également à 7–10 px.

### Décision recommandée
Rehausser les tailles minimales fonctionnelles et la hiérarchie typographique. Le positionnement premium ne doit pas dépendre d’une micro-typographie difficile à lire.

---

## P6-B — Sémantique/accessibilité des onglets

### Faits vérifiés
`StudioTabs` est une rangée de boutons visuels, sans rôle `tablist/tab`, sans `aria-selected`/`aria-current` dans le code inspecté.

### Décision recommandée
- sémantique d’onglets explicite ;
- état actif accessible ;
- navigation clavier cohérente ;
- focus visible certifié.

---

## P6-C — Action Quitter et protection du brouillon

### Fait vérifié
`StudioHeader` exécute directement `window.history.back()` sur `Quitter`.

`DocumentHub` possède une garde explicite pour les changements d’onglet internes et un `beforeunload` pour certains brouillons, mais le code inspecté ne démontre pas qu’une navigation SPA via history back traverse la même garde métier.

### Risque
Perte potentielle d’un brouillon si la navigation route ne déclenche pas la protection attendue.

### Décision recommandée
Centraliser toute sortie du Studio dans une seule garde de dirty-state, y compris back/navigation route/fermeture.

---

## P6-D — Actualiser

### Fait vérifié
Le bouton global `Actualiser` appelle `window.location.reload()`.

### Décision recommandée
Préférer une actualisation ciblée des données et conserver la garde dirty-state. Un reload complet est un marteau disproportionné pour un Studio local-first riche en état.

---

## P6-E — Terminologie transversale

### Faits déjà vérifiés dans les audits P1/P2/P5
Plusieurs labels `IA`, `Ghost`, `Intelligence`, `VÉRIFIÉ` ne correspondent pas toujours à la nature déterministe/heuristique réelle des moteurs.

### Décision recommandée
Terminologie fonctionnelle et descriptive. Aucun label autoritatif ou « IA » décoratif lorsque le comportement est une règle locale déterministe/heuristique.

---

## P6-F — Points restant à cartographier

- dark mode complet ;
- contrastes WCAG des états secondaires ;
- focus/ARIA de tous les contrôles custom ;
- responsive 390 / 768 / 1280 ;
- split preview et stacking/z-index ;
- raccourcis clavier ;
- états loading/empty/error/success ;
- cohérence dirty-state entre tous les types documentaires ;
- recertification runtime/accessibilité ciblée.
