# M6-G0 — Glass system mobile — Goal

Date : 2026-08-25
État : GOAL VERROUILLÉ AVANT IMPLÉMENTATION

## Goal

Appliquer le standing glassmorphism premium déjà prévu par les tokens Digital Crown au produit mobile réel, de manière cohérente et sobre, sans modifier les flows, les données, les permissions ni la lisibilité clinique.

## Surface

- Onboarding / appairage mobile ;
- Dashboard mobile et vues Agenda / Finance / Labo / Assistant / Sécurité via leurs surfaces partagées ;
- header, cartes, bottom navigation et modales du dashboard ;
- contextes QR Patient / Panoramique / Document / Rendez-vous et états d’erreur.

## Cible visuelle

Référence verrouillée : direction glassmorphism générée dans la conversation du 25 août 2026 à partir des écrans réels M4-D / M4 final. Elle sert uniquement de référence de traitement : surfaces translucides/frosted, profondeur légère, contours lumineux, arrière-plan froid subtil, hiérarchie et CTA inchangés.

## Critères

1. Glass réel : `backdrop-filter` / `-webkit-backdrop-filter`, translucidité, saturation et ombre douce sur les surfaces structurantes.
2. Pas d’effet aquarium : texte, champs de saisie, badges métier et CTA primaires restent opaques/lisibles.
3. Les tokens existants `--glass-bg` et `--glass-border` restent source de vérité pour les thèmes.
4. Mode `high-contrast` : surfaces opaques, blur neutralisé, bordures fortes.
5. Fallback navigateur sans `backdrop-filter` : surface opaque lisible.
6. Aucun changement fonctionnel, route, API, permission ou stockage.
7. 0 overflow horizontal aux viewports 390x844 et 768x1024.
8. Aucun nouveau contrôle tactile < 44 px.
9. BEFORE → référence → AFTER inspectés sur Onboarding, Dashboard et Contexte mobile.
10. Build frontend et CI exact-head verts avant merge.

## Preuve requise

- BEFORE exact master `13b79f572b6a62f6c743f75f4d93b841454d3417` ;
- AFTER exact-head sur les mêmes vues/viewports ;
- métriques `backdrop-filter` visibles en hausse sur surfaces structurantes ;
- inspection visuelle réelle et score ;
- aucun Vercel.
