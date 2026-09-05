# Digital Crown — MOB-5C Notifications — Proof

## Goal
Fournir sur mobile un cockpit de notifications actionnables, priorisées, tenant-scoped, sans exposer de donnée patient dans les notifications OS et sans modifier la navigation canonique à cinq entrées.

## Scope livré
- `Plus → Notifications` dans le shell mobile canonique ;
- deep-link `?tab=notifications` ;
- vue `NotificationsView` dédiée ;
- source in-app unique `/api/mobile/notifications` ;
- filtres `Toutes / Prioritaires` ;
- actions contextuelles allowlistées ;
- marquer comme lu ;
- snooze 24 h ;
- états empty/error explicites ;
- alertes Labo exclues tant que l’isolation tenant Labo n’est pas prouvée ;
- push OS conservé sans PHI.

## Validation technique
Candidat certifié : `fc40af1a28cb1a8cdc65bce2a5b0357075d3a0a1`.

Runs :
- CI `33986784125` ✅
- T2 Runtime Browser Certification `33986784120` ✅
- Settings Security Visual Certification `33986784086` ✅
- Mobile Notifications MOB-5C Cert `33986784147` ✅

Artifact :
- id `9975417271`
- nom `mobile-notifications-mob5c-after`
- digest `sha256:4e40891c94abc35a49548220b76e075c3d8884157dd8160255f4956a6325fe3c`

## AFTER visuel
Viewports certifiés :
- `390×844`
- `430×932`
- `768×1024`

Assertions runtime observées dans `runtime-evidence.json` :
- 5 boutons de navigation permanents sur chaque viewport ;
- hauteur nav `76 px` ;
- `horizontalOverflow = false` ;
- `runtimeErrors = []` ;
- scrollWidth identique à innerWidth sur chaque viewport.

Inspection visuelle :
- hiérarchie claire `À traiter → Notifications → filtres → cartes` ;
- badges de priorité distincts sans surcharger l’écran ;
- actions primaires compréhensibles et tactiles ;
- densité correcte sur 390/430 ;
- tablette 768 exploite correctement l’espace sans étirer abusivement la lecture ;
- la nav fixe peut recouvrir visuellement le bas d’une carte sur petits viewports avant scroll, mais aucun contenu n’est perdu ni non-scrollable.

Score visuel : **9.4 / 10**.

## Sécurité / données
- source serveur partagée avec desktop ;
- filtrage tenant conservé ;
- RBAC conservé ;
- actions contextuelles limitées par allowlist ;
- push OS générique sans donnée patient ;
- aucune alerte Labo exposée tant que son isolation tenant n’est pas démontrée.

## Verdict
MOB-5C satisfait le Goal technique et visuel au niveau navigateur certifié.

Déploiement Vercel : **aucun**.
