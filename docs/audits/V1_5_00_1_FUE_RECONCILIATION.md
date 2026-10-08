# V1.5-00.1 — Réconciliation FUE-0 (Hub information architecture)

Date: 2026-10-08
Status: PARTIEL — revue documentaire effectuée, preuves exact-HEAD à compléter
Scope: V1.5-00.1 uniquement. Aucune simulation de parcours utilisateur.

## Référentiels
- Notion: V1.5 — Plan FUE canonique par lot / sous-lot
- FUE Lab: PR #783 / `docs/audits/FIRST_USER_EXPERIENCE_PROMPT.md`
- Audit source: `docs/architecture/V1_5_00_1_HUB_DISPATCHER_READONLY_AUDIT.md`

## Goal et critère de succès
Vérifier que le sous-lot d'architecture 00.1 déjà réalisé dispose de contrats explicites et de preuves adéquates. Comme il est classé **FUE-0**, le succès ne comporte ni navigation artificielle ni score FUE utilisateur.

## Vérifications documentaires observées
- Audit 00.1 présent sur master, document docs-only lié historiquement à PR #717 et au commit `db1cadd74eb60d3e11e6c31d5da6780fefaacbb4` (référence Notion, à revalider depuis les objets Git).
- Routes prévues: `/hub`, `/cabinet`, `/station`, `/control-center`.
- Hub = dispatcher neutre; expériences PC Cabinet / Station d'accueil / Centre de contrôle.
- Mobile équipe et Patient Companion restent distincts.
- Workstation mode distinct du `appMode` demo/prod et ne confère aucun privilège.
- Station escape / changement de mode permanent soumis à une autorisation backend et PIN propriétaire vérifié côté serveur.
- Absence serveur: diagnostic explicite au lieu d'un contournement de l'autorisation.

## Matrice de statut
| Critère | Observation | Statut |
| --- | --- | --- |
| Classement FUE | FUE-0 confirmé dans plan canonique | PROUVÉ (documentaire) |
| Contrat d'architecture | Audit canonique présent et consulté | PROUVÉ (documentaire) |
| Preuve d'intégration historique | Commit/PR mentionnés dans Notion; vérification Git/CI fine non réalisée ici | PARTIEL |
| Contradictions avec code actuel | Non audité sur exact HEAD pendant ce passage | À FAIRE |
| FUE navigateur utilisateur | Non applicable à 00.1; attendu à partir de 00.2 | N/A |

## Conclusion et Next
00.1 ne requiert **aucun FUE-I/G**. La réconciliation documentaire est amorcée, **pas certifiée terminée** : contrôler le commit/PR 00.1 et les contrats exact-HEAD avant de passer 00.1 à PROUVÉ global. Ensuite V1.5-00.2: adapter le FUE Lab #783 au parcours première ouverture Hub → choix espace → destination; artefacts captures/mesures et revues adversariales exigibles.

Aucune modification du runtime, aucun merge, aucun déploiement.

## Revue source courante — 2026-10-08
Lecture réelle de `master` : `App.tsx`, `accessControl.ts`, `Header.tsx`, `HubPage.tsx`, `WorkstationModeGate.tsx`, `WorkstationExperiencePage.tsx`. Contrats observés dans le code (pas une exécution navigateur) :
- `SmartRootRouter` conserve `/mobile/dashboard` pour mobile, `/hub` pour desktop authentifié; `/companion` est une route dédiée.
- `/hub`, `/station`, `/control-center` sont explicitement routés sous `WorkstationModeGate`; les routes métier utilisent `target="protected"`.
- `HubPage` présente exactement 3 cartes PC (Cabinet/Station/Control Center), lit `GET /api/clinics/me`, conserve les valeurs de fallback et affiche un message d'indisponibilité backend sans données patient.
- `WorkstationModeGate` redirige les routes protégées vers `/hub?mode-check=failed` quand l'autorité poste est indisponible, tandis que les surfaces de récupération demeurent accessibles.
- `WorkstationExperiencePage` conditionne la sortie Station à `authorizeStationEscape(ownerPin)` ; les protections backend et le PIN ne sont pas prouvés ici par un test négatif.
- `appMode` legacy demeure présent dans `App.tsx`; il n'est pas utilisé comme preuve d'autorisation Station dans les fichiers inspectés.

**Revue A — contrat / architecture** : pas de contradiction majeure entre contrat 00.1 et fichiers consultés. **Revue B — preuve et sécurité** : refus de qualifier l'absence de fail-open démontré sans tests négatifs backend ; cette lecture statique n'est pas une revue indépendante humaine ni une preuve de comportement runtime.

**État conservateur** : 00.1 = PARTIEL (preuve documentaire + source actuelle), FUE-0 correctement classé, pas de FUE navigateur à lancer. **Reste** : résultats exact-HEAD pertinents pour frontières auth/Station et validation du comportement runtime à réconcilier depuis les sous-lots 00.2/00.3/00.4, sans attribuer à 00.1 une certification ultérieure non justifiée. Prochain travail utile : 00.2 FUE-I basé sur le Lab #783, avec extraction des preuves visuelles Hub déjà disponibles, puis exécution ciblée si nécessaire.
