# R4 — Modèles documentaires / Document Studio — Goal visuel et produit

Date : 2026-08-19
Repo : `hraaaaf/Digital_crown`
Base : `master@c290095415d9f139b8b6c08078c958415d424e0a`

## BEFORE

Référence visuelle : AFTER R3 `Document` certifiée sur 1440 / 1024 / 768 / 430 / 390.

État visible actuel :
- colonne gauche : Palette, Typographie, Modèles d'ordonnance, Mise en page, Fond de page, QR ;
- colonne droite : carte `Aperçu en direct — Document A4` ;
- bouton secondaire `Voir le rendu PDF réel` sous un renderer React simulé.

## Cartographie vérifiée avant implémentation

### Frontend

`StudioControls` expose les cinq modèles :
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

Conséquence : le renderer React simulé peut afficher presque la même maquette pour plusieurs modèles officiels et ne constitue pas une preuve fidèle du PDF final.

### Backend réel

`BaseTemplate._draw_auto_header()` implémente explicitement :
- `_draw_header_swiss`
- `_draw_header_royal`
- `_draw_header_clinical`
- `_draw_header_modern`
- `_draw_header_heritage`

Le endpoint `/documents/sample-preview` appelle le vrai `DocumentFactory.create_ordonnance()` avec le profil en cours.

Conclusion : **la taxonomie officielle est cohérente entre contrôles et moteur PDF ; la divergence est dans le renderer React historique.**

### Dette technique du preview réel

Quand le preview réel est ouvert, le frontend regénère après chaque changement (debounce). Le générateur d'ordonnance crée un fichier PDF physique horodaté. Le endpoint sample-preview ne supprime pas explicitement ces fichiers après lecture.

Décision : R4 doit éviter qu'une simple séance de personnalisation transforme le dossier documents en décharge de previews.

## Goal

Faire du **PDF réel** la source de vérité du Document Studio tout en gardant une interaction fluide et compréhensible.

Le produit doit distinguer clairement :
- **Aperçu rapide** : facultatif, indicatif uniquement ;
- **Rendu PDF réel** : fidèle, autoritatif, généré par le moteur de production.

Aucune maquette simulée ne doit laisser croire qu'elle représente fidèlement un modèle si elle n'utilise pas sa vraie logique.

## Wireframe retenu

```text
[ Contrôles Document ]                  [ RENDU DOCUMENT ]

Palette                                 ┌─────────────────────────────┐
Typographie                             │  PDF RÉEL                    │
Modèle                                  │  Swiss Clinic               │
  ◉ Swiss Clinic                        │                             │
  ○ Royal Elite                         │  [ vraie page PDF ]          │
  ○ Clinical Grid                       │                             │
  ○ Modern Flush                        └─────────────────────────────┘
  ○ L'Héritage
                                        [ Actualiser le rendu ]
Mise en page                            Dernière génération : à jour
...

Option secondaire discrète :
[ Voir un aperçu rapide ]  → clairement marqué `Indicatif`
```

Mobile : contrôles puis bloc PDF réel pleine largeur. Aucun panneau sticky masquant le formulaire.

## Principes d'interaction

1. Le PDF réel est la preuve visuelle principale.
2. La génération n'est pas déclenchée en boucle à chaque micro-changement sans contrôle.
3. Un état `Rendu à actualiser` apparaît après une modification.
4. `Actualiser le rendu` génère le PDF à la demande.
5. Après génération : état `Rendu à jour`.
6. Les fichiers de preview ne doivent pas polluer les vrais documents persistants.
7. Les cinq modèles officiels doivent produire des différences vérifiables dans le PDF réel.

## Critères de succès

1. Plus aucun rendu simulé n'utilise les anciennes taxonomies comme s'il était fidèle.
2. Les cinq modèles officiels sont testés contre le moteur PDF réel.
3. Le preview réel n'archive aucune donnée clinique/comptable.
4. Les fichiers temporaires de preview ont un cycle de vie maîtrisé.
5. 1440 / 1024 / 768 / 430 / 390 : aucune collision/overflow.
6. Changement de modèle → état visuel `à actualiser` → actualisation → PDF correspondant.
7. Tests frontend + backend ciblés + CI globale avant merge.

## Hors scope

- contenu métier des ordonnances ;
- QR détaillé : R5 ;
- catalogue actes ;
- redesign global de Settings ;
- TemplateBuilder legacy : P3.

Statut : **GOAL + WIREFRAME VERROUILLÉS — IMPLÉMENTATION NON DÉMARRÉE**.
