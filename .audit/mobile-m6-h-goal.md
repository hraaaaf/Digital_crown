# M6-H — Imagerie mobile plein écran — Goal

## Goal
Transformer la consultation Panoramique mobile exacte en viewer clinique mobile-first sans modifier l’analyse : aperçu contextualisé + ouverture d’un viewer plein écran dans l’app, zoom et déplacement tactiles, fermeture immédiate et contrôles accessibles.

## Succès observable
- Le contexte `panoramic` et son média déjà autorisé restent la seule source ; aucun nouvel endpoint ni nouvelle donnée clinique.
- CTA `Agrandir` disponible uniquement si le média est chargé, cible >=52 px.
- Viewer in-app `position: fixed; inset: 0; 100dvh` : aucun besoin du Fullscreen API, aucun verrouillage d’orientation OS.
- Fond noir, image `object-contain`, safe areas respectées.
- Zoom borné 1× à 4× ; boutons − / + / Réinitialiser >=52 px.
- Pinch tactile à deux doigts et pan à un doigt lorsque zoom >1 ; aucun scroll de page parasite dans le viewer.
- Double-tap ou équivalent non requis : les boutons restent toujours un fallback explicite.
- Fermer restaure le viewer à 1× et ne modifie pas le contexte, le média ni l’URL.
- Escape ferme au clavier ; dialog accessible avec nom explicite ; le reste de l’app est `inert` pendant l’ouverture.
- M4-B historique, statut, retour et chargement média préservés.
- 390×844, 430×932, 768×1024 : zéro overflow/runtime error, contrôles >=48 px ; viewer certifié en portrait et état zoomé.

## Preuve attendue
- BEFORE exact : run 32949490898 / artifact 9599589719, 390/430/768 inspectés.
- Mockup main + viewer inspecté avant implémentation.
- Tests unitaires du moteur zoom/pan : bornes, clamp, zoom ancré, pan, reset.
- Harness M4-B étendu : ouverture/fermeture, zoom boutons, pinch/pan, Escape, aucune requête supplémentaire et captures AFTER mêmes viewports.
