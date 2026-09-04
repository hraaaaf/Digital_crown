# Digital Crown — Mobile Patient Cockpit — Goal UI v1

Status: CLOSED / CONSUMED BY MOB-2
Canonical parent: `docs/ux/DIGITAL_CROWN_MOBILE_PRODUCT_CANONICAL.md`
Proof: `docs/ux/DIGITAL_CROWN_MOBILE_PATIENT_COCKPIT_MOB2_PROOF.md`
Repo: `hraaaaf/Digital_crown`
Lot design: MOB-1
Lot implementation: MOB-2
Deployment: none

## Goal

Concevoir l'écran mobile patient canonique comme un **cockpit clinique opérationnel**, utilisable à une main et permettant au praticien de trouver un patient, comprendre sa situation critique et lancer l'action utile rapidement.

Le résultat ne doit jamais être une réduction du dossier patient desktop.

## Référence visuelle

Mockup versionné :

`docs/ux/assets/MOBILE_PATIENT_COCKPIT_GOAL_V1.svg`

Commit de création : `b6924f0f57931e0361dc0db45653b63c4de9fb0c`.

Le rendu Ghost Elite du SVG est une référence visuelle, pas une palette ou une police à coder en dur.

## Invariant thème / typographie

Réglages cabinet reste la source de vérité unique :

- `selected_theme`
- `primary_color`
- `secondary_color`
- `accent_color`
- `font_fr`

Règles verrouillées :

1. aucune couleur de marque propre au Patient Cockpit ;
2. aucune police locale forcée ;
3. surfaces/textes/bordures/états actifs via tokens CSS partagés ;
4. `font_fr` propagée au runtime mobile ;
5. aucun moteur de thème mobile parallèle ;
6. couleurs danger/warning/succès restent sémantiques et contrastées.

## Baseline visuelle à préserver

- logo Digital Crown ;
- notification + état de synchronisation ;
- surfaces premium vitrées ;
- grands rayons et ombres douces ;
- hiérarchie forte ;
- barre mobile flottante ;
- touch targets adaptés ;
- safe-area ;
- aucun redesign iOS générique ou néon déconnecté du produit.

## Scénario primaire

1. ouvrir Patients ;
2. rechercher par nom / dossier / téléphone autorisé ;
3. sélectionner le patient ;
4. voir identité + alerte médicale + prochain RDV + finance autorisée ;
5. appeler / WhatsApp ;
6. accéder aux actions cliniques mobiles utiles.

## Hiérarchie cible initiale 390 px

1. header Digital Crown ;
2. Patients + recherche ;
3. identité ;
4. alerte médicale ;
5. contact rapide ;
6. prochain RDV ;
7. finance synthétique ;
8. photo / scan ;
9. navigation flottante.

## Hors scope

- odontogramme complet ;
- ClinicalHub complet ;
- Master Plan ;
- RVG Studio ;
- Panoramic Studio complet ;
- T0/T1 ;
- annotations et rapports panoramiques ;
- Céphalométrie ;
- Document Studio complet ;
- Analytics ;
- Treasury Hub ;
- paramètres cabinet ;
- administration Marketplace.

## Validation MOB-1

MOB-1 est DONE :

- Goal UI versionné ✅
- mockup 390 versionné ✅
- invariant thème + `font_fr` documenté ✅
- validation visuelle humaine explicite reçue le 2026-09-04 ✅
- aucune implémentation MOB-2 commencée avant ce gate ✅

## Consommation par MOB-2

MOB-2 a été certifié sur :

- run `33889545163` ✅
- candidat `2a01e58d4bf3e3deff833723a52e3449bb26e4ac`
- AFTER 390×844 / 430×932 / 768×1024
- artifact `9943369750`
- digest `sha256:b4d274590a3349cbcab8a71faeb25e880acc3aee4ab818420fab8918813777fd`

Comparaison finale :

- identité forte ✅
- alerte médicale prioritaire ✅
- appel / WhatsApp proéminents ✅
- actions cliniques mobiles cohérentes ✅
- aucun overflow/runtime error accepté par le gate ✅

Écarts assumés :

- actions cliniques placées avant le prochain RDV ;
- recherche remplacée par `Tous les patients` après sélection ;
- navigation cible reportée à MOB-4 ;
- `Encaisser` reporté à MOB-3.

**Score visuel MOB-2 : 9.2 / 10.**

## Conclusion

Cette référence a rempli son rôle et ne constitue plus un gate ouvert.

Next exact : PR/merge MOB-2, puis MOB-3 avec son propre BEFORE → Goal UI → mockup avant code.
