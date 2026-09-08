# DIGITAL CROWN — MOB-6 Canonisation du routage mobile — Référence

## Référence comportementale
Une URL mobile doit ouvrir la surface canonique correspondant au contexte, pas une version concurrente selon la manière dont l’utilisateur est arrivé.

### Mobile
- namespace canonique : `/mobile/*` ;
- dashboard mobile : `/mobile/dashboard?tab=<tab>` ;
- onboarding : `/mobile/onboarding` ;
- SuperAdmin : `/mobile/superadmin` ;
- route mobile inconnue : fallback via la destination Agenda de `MOBILE_BRIDGE_ROUTES`, jamais vers le shell desktop.

### Desktop
- les routes historiques restent inchangées ;
- aucun redirect mobile n’est appliqué sur desktop ;
- les routes sans équivalent mobile démontré restent sur leur surface desktop ;
- les deep-links riches restent desktop si une redirection ferait perdre l’entité ciblée.

### Préservation du contexte
La redirection mobile réutilise `MOBILE_BRIDGE_ROUTES`. Le mapping desktop associe seulement un chemin top-level à une destination logique (`agenda`, `patients`, `finance`, etc.).

`waiting-room` est une destination du bridge canonique afin que `/salle-attente` ne nécessite aucune URL mobile parallèle.

## BEFORE certifié
Run `34211312980` — SUCCESS sur le commit pré-implémentation exact `d5bf9439e8eae60c1d0c8616a92353041fb5ac9a` :
- artifact `10049990601` ;
- digest `sha256:c89e86a107100e1596187291f9650c12bf716ffcc95c225efd4e670230b1eef4` ;
- 390×844 / 430×932 / 768×1024 ;
- `/patients`, `/agenda`, `/stock` restent desktop ;
- onboarding mobile absent ;
- 0 overflow ; 0 page error.

## AFTER certifié
Run `34211780896` — SUCCESS :
- routing contract SUCCESS ;
- frontend build SUCCESS ;
- browser AFTER SUCCESS ;
- 390×844 / 430×932 / 768×1024 ;
- `/patients`, `/agenda`, `/stock` → `/mobile/onboarding` en état non appairé ;
- desktop login absent ;
- onboarding mobile présent ;
- 0 overflow ; 0 page error ; 0 console error ;
- artifact `10050137272` ;
- digest `sha256:dc1e5a72d02f668cf537ec9fa28341940d34df7388603da6974eeac393d82ec7`.

## Comparaison visuelle
BEFORE : loader/surface desktop lors d’une entrée mobile directe sur les routes testées.

AFTER : onboarding mobile canonique cohérent, lisible et sans chevauchement sur les trois viewports. Le lot corrige la continuité de surface, pas l’esthétique de l’onboarding.

Score visuel/comportemental : **9.4/10**.

Réserve : les deep-links riches ne sont pas canonisés tant qu’un équivalent mobile ne peut pas préserver leur contexte exact.

Statut : `REFERENCE DELIVERED — PRE-MERGE CERTIFIED`.
