# V1.5-00.2 — FUE-I Hub première ouverture (PR #783 Lab)

Date: 2026-10-08
Status: OPEN / INVENTAIRE

## Contexte et classification
- Campagne: réconciliation rétrospective V1.5 des sous-lots CLOSED, avant V1.5-04.
- Sous-lot: 00.2 — Shell Hub + routing; exigence du plan V1.5: **FUE-I**.
- Laboratoire de référence: PR #783, `docs/audits/FIRST_USER_EXPERIENCE_PROMPT.md`; personnaliser le protocole pour ce sous-lot sans réutiliser son score FUE-A.
- Persona: utilisateur autorisé devant un PC cabinet à première ouverture; contextes poste non configuré et poste mémorisé si pertinents, sans substitution du scénario 00.3.
- First Value: choix explicite Cabinet / Station / Centre de contrôle puis arrivée dans la surface sélectionnée, avec une possibilité de récupération appropriée.

## Parcours et preuves attendues
1. Environnement synthétique isolé, session/poste vierge, état auth explicite.
2. Ouverture racine/Hub; observer l'identité de l'établissement et les 3 espaces.
3. Cliquer chaque carte, vérifier destination et garde d'accès : `/cabinet`, `/station`, `/control-center`.
4. Vérifier retour contrôlé Hub et résistance à la navigation URL directe Station; ne jamais contourner owner PIN.
5. Panne backend simulée sur fixture isolée : Hub et diagnostic restent visibles, espace clinique non ouvert sans autorité.
6. Captures BEFORE/AFTER comparables desktop 1280×900 et tablette 768×1024 ; mobile 390×844 seulement si le scénario Hub est applicable à ce viewport, sinon expliciter N/A (le routeur mobile est distinct).
7. Consigner latences, interactions, exceptions HTTP, console, erreurs navigateur, overflow, P0/P1/P2 et score sévère; deux revues adversariales et confirmation sur même HEAD.

## Inventaire initial
- PR historique #720 : preuve visuelle Hub 390/768/1280 et validation humaine documentées dans roadmap Notion.
- PR #724 : Hub 00.4 closeout/visuel, et #727 closeout documentaire; preuves à réconcilier sans les substituer au FUE-I de 00.2.
- `App.tsx` et `HubPage.tsx` actuels : routes et 3 cartes présents (revue source seulement).
- Les artefacts existants ne sont pas encore téléchargés ni inspectés pour les étapes « première ouverture → choix → destination »; **aucun score FUE-I attribuable aujourd'hui**.

## Verdict initial
**PARTIEL** — contrat scénario défini, preuves historiques identifiées; observabilité du parcours réel et preuves exact-HEAD du FUE-I encore à réunir. Pas de produit modifié. Pas de merge ni déploiement.
