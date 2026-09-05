# Digital Crown — MOB-5B Frontdesk Mobile — BEFORE

Status: IMMUTABLE BASELINE RECORDED
Date: 2026-09-05
Repo: `hraaaaf/Digital_crown`
Baseline commit: `89098066ef0c943c0e084af4b9cd388d3ab0aa5b`

## BEFORE observé

Sur le baseline post-MOB-5A, le shell mobile canonique existe avec cinq entrées permanentes `Aujourd’hui / Patients / + / Assistant / Plus`.

Dans `Plus`, les accès secondaires disponibles sont Équipe, Finance, Envois Labo et Sécurité selon rôle. **Frontdesk n’existe pas encore dans la navigation mobile** et aucune vue mobile dédiée Frontdesk n’est rendue dans `MobileDashboard`.

Le métier Frontdesk existe uniquement via les composants desktop et le backend partagé.

## Référence BEFORE

Le baseline visuel canonique réutilisé est la preuve MOB-5A certifiée aux mêmes viewports :
- run `33963384867`
- artifact `9968666702`
- digest `sha256:6a463707a1c7dbe2bb9623db1e3b19b631d267294ad08dc6bb32dcb729929385`
- 390×844 / 430×932 / 768×1024

Cette preuve montre le shell et `Plus` avant l’ajout Frontdesk. Le baseline Git exact est `89098066ef0c943c0e084af4b9cd388d3ab0aa5b`.

## Gap mesuré

Goal MOB-5B : ajouter un parcours Frontdesk mobile sans modifier les cinq entrées permanentes, sans dupliquer la logique backend et sans porter les composants desktop tels quels.

Deployment: none. No Vercel deployment authorized.
