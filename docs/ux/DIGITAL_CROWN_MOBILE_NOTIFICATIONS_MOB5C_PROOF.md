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

Runs sur ce candidat :
- CI `33986784125` ✅
- T2 Runtime Browser Certification `33986784120` ✅
- Settings Security Visual Certification `33986784086` ✅
- Mobile Notifications MOB-5C Cert `33986784147` ✅

Artifact visuel :
- id `9975417271`
- nom `mobile-notifications-mob5c-after`
- digest `sha256:4e40891c94abc35a49548220b76e075c3d8884157dd8160255f4956a6325fe3c`
- head SHA artifact `fc40af1a28cb1a8cdc65bce2a5b0357075d3a0a1`.

## AFTER visuel
Viewports inspectés :
- `390×844`
- `430×932`
- `768×1024`

Assertions runtime issues de la certification :
- 5 boutons de navigation permanents sur chaque viewport ;
- hauteur nav `76 px` ;
- `horizontalOverflow = false` ;
- `runtimeErrors = []` ;
- scrollWidth identique à innerWidth sur chaque viewport.

Inspection visuelle finale :
- hiérarchie claire `À traiter → Notifications → filtres → cartes` ;
- badges de priorité distincts sans surcharge ;
- actions primaires compactes et tactiles ;
- densité correcte sur 390/430 ;
- tablette 768 exploite correctement l’espace sans devenir une page desktop compressée ;
- la nav fixe peut recouvrir le bas d’une carte avant scroll sur petit viewport, sans perte de contenu ni blocage de scroll.

Score visuel : **9.4 / 10**.

## Sécurité / données
- source serveur partagée avec desktop ;
- filtrage tenant conservé ;
- RBAC conservé ;
- actions contextuelles limitées par allowlist ;
- push OS générique sans donnée patient ;
- aucune alerte Labo exposée tant que son isolation tenant n’est pas démontrée.

## Verdict
MOB-5C satisfait le Goal technique et visuel au niveau navigateur certifié sur le candidat `fc40af1a28cb1a8cdc65bce2a5b0357075d3a0a1`.

Déploiement Vercel : **aucun**.
