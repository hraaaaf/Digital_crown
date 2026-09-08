# DIGITAL CROWN — MOB-6 Canonisation du routage mobile — Référence

## Référence comportementale
Une URL mobile doit ouvrir la surface canonique correspondant au contexte, pas une version concurrente selon la manière dont l’utilisateur est arrivé.

### Mobile
- namespace canonique : `/mobile/*` ;
- dashboard mobile : `/mobile/dashboard?tab=<tab>` ;
- onboarding : `/mobile/onboarding` ;
- SuperAdmin : `/mobile/superadmin` ;
- route mobile inconnue : fallback mobile explicite vers la destination Agenda canonique, jamais vers le shell desktop.

### Desktop
- les routes historiques restent inchangées ;
- aucun redirect mobile n’est appliqué sur desktop ;
- les routes sans équivalent mobile démontré restent sur leur surface desktop ;
- les deep-links riches restent desktop si une redirection ferait perdre l’entité ciblée.

### Préservation du contexte
La redirection mobile réutilise `MOBILE_BRIDGE_ROUTES`. Le mapping desktop associe seulement un chemin top-level à une destination logique (`agenda`, `patients`, `finance`, etc.) ; l’URL mobile reste définie une seule fois dans le bridge canonique.

`waiting-room` est désormais également une destination du bridge canonique afin que `/salle-attente` ne nécessite aucune URL mobile parallèle.

## BEFORE observé
Sur 390×844, 430×932 et 768×1024, les entrées directes `/patients`, `/agenda`, `/stock` restent sur leur chemin desktop et n’atteignent pas l’onboarding mobile. Le report brut du premier run `34210241473` a confirmé ce comportement sur 9/9 probes ; le run a échoué uniquement parce que le harness attendait à tort `/login`. Une recertification corrigée est lancée sur le commit pré-implémentation exact.

## AFTER observé
Run `34210579881` :
- contrat routage SUCCESS ;
- frontend build SUCCESS ;
- browser AFTER SUCCESS ;
- 390×844 / 430×932 / 768×1024 ;
- `/patients`, `/agenda`, `/stock` → `/mobile/onboarding` en état non appairé ;
- desktop login absent ;
- onboarding mobile présent ;
- zéro overflow ;
- zéro page error ;
- zéro console error.

Artifact AFTER `10049662623`, digest `sha256:aa08739d1f5430588d0c9587f69d7ed36bcef28e00041edabc1e90d5c2298edd`.

## Comparaison visuelle
BEFORE : loader desktop générique sur les deep-links testés, sans bascule vers le cockpit mobile.

AFTER : onboarding mobile cohérent, lisible et sans chevauchement sur les trois viewports. La modification n’introduit pas une nouvelle esthétique ; elle garantit que l’utilisateur tombe sur la bonne surface existante.

Score visuel/comportemental : **9.4/10**.

Réserve : ce lot ne prétend pas canoniser les deep-links riches tant qu’un équivalent mobile ne peut pas préserver leur contexte exact.

Statut : `REFERENCE IMPLEMENTED — AFTER CERTIFIED ON INITIAL PRODUCT HEAD — FINAL RECERTIFICATION PENDING`.
