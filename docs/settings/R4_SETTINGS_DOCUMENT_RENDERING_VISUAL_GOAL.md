# R4 — Réglages / Modèles & rendu des documents — Goal visuel et produit

Date : 2026-08-19
Repo : `hraaaaf/Digital_crown`
Base : `master@c290095415d9f139b8b6c08078c958415d424e0a`

## Périmètre

R4 appartient **uniquement au chantier Réglages**.

Dans le scope :
- choix du modèle documentaire depuis `Design & Ambiance` ;
- typographie, couleurs, marges et réglages de rendu exposés dans Réglages ;
- aperçu documentaire depuis Réglages ;
- vérification downstream minimale du moteur PDF uniquement pour prouver que le réglage produit bien l'effet attendu.

Hors scope :
- Document Studio clinique ;
- création métier d'ordonnances, devis, certificats ;
- archivage clinique/comptable ;
- contenu métier des documents.

## BEFORE

Référence visuelle : AFTER R3 `Document` certifiée sur 1440 / 1024 / 768 / 430 / 390.

État visible actuel :
- colonne gauche : Palette, Typographie, Modèles d'ordonnance, Mise en page, Fond de page, QR ;
- colonne droite : carte `Aperçu en direct — Document A4` ;
- bouton secondaire `Voir le rendu PDF réel` sous un renderer React simulé.

## Cartographie vérifiée avant implémentation

### Frontend Réglages

`StudioControls` expose les cinq modèles officiels :
- `swiss`
- `royal`
- `clinical`
- `modern`
- `heritage`

`StudioPreview.renderDocPreview()` contient encore des branches legacy :
- `classic`
- `asymetric`
- `future`
- `frame`
- `double-column`

Conséquence : le renderer React simulé ne constitue pas une preuve fidèle du PDF final.

### Vérification downstream minimale

`BaseTemplate._draw_auto_header()` implémente explicitement :
- `_draw_header_swiss`
- `_draw_header_royal`
- `_draw_header_clinical`
- `_draw_header_modern`
- `_draw_header_heritage`

Le endpoint `/documents/sample-preview` appelle le vrai `DocumentFactory.create_ordonnance()` avec le profil courant.

Conclusion : **la taxonomie officielle est cohérente entre les réglages et le moteur PDF ; la divergence est dans le renderer React historique de Réglages.**

### Dette du preview réel

Quand le preview réel est ouvert, le frontend régénère actuellement après chaque changement avec un debounce de 600 ms. Le générateur produit un fichier PDF physique.

Décision R4 : supprimer la régénération automatique. Une modification marque simplement le rendu comme `À actualiser`; l'utilisateur déclenche explicitement la génération.

## Goal

Faire du **PDF réel** la source de vérité de l'aperçu documentaire dans Réglages.

Le produit doit :
- supprimer le faux renderer documentaire comme représentation prétendument fidèle ;
- afficher le PDF réel comme aperçu principal ;
- ne jamais régénérer en boucle à chaque micro-changement ;
- rendre visible l'état `Rendu à actualiser / Rendu à jour`.

## Wireframe retenu

```text
[ Contrôles de Réglages ]               [ RENDU DOCUMENT ]

Palette                                 Modèle : Swiss Clinic
Typographie                             État : À actualiser
Modèle                                  [ Actualiser le rendu ]
  ◉ Swiss Clinic
  ○ Royal Elite                         ┌─────────────────────────────┐
  ○ Clinical Grid                       │                             │
  ○ Modern Flush                        │       PDF RÉEL              │
  ○ L'Héritage                          │                             │
                                        └─────────────────────────────┘
Mise en page
...
```

Mobile : contrôles puis bloc PDF réel pleine largeur. Aucun panneau sticky ne doit masquer le formulaire.

## Critères de succès

1. Plus aucun renderer documentaire simulé n'utilise les anciennes taxonomies comme s'il était fidèle.
2. Le PDF réel est l'aperçu principal de la vue Document dans Réglages.
3. Changement de réglage → état `À actualiser`, sans génération réseau automatique.
4. `Actualiser le rendu` → génération réelle → état `À jour`.
5. Le preview ne déclenche aucun archivage clinique/comptable.
6. La fréquence de génération est contrôlée par action explicite et ne crée plus une rafale de fichiers à chaque micro-changement.
7. Les cinq modèles officiels restent testables via le moteur PDF réel.
8. 1440 / 1024 / 768 / 430 / 390 : aucune collision/overflow.
9. Tests frontend ciblés + régression + CI globale avant merge.

## Hors scope

- Document Studio clinique ;
- contenu métier des documents ;
- QR détaillé : R5 ;
- catalogue actes ;
- redesign global de Settings ;
- TemplateBuilder legacy : P3.

Statut : **GOAL + WIREFRAME VERROUILLÉS — PÉRIMÈTRE CORRIGÉ — IMPLÉMENTATION FRONTEND EN COURS**.
