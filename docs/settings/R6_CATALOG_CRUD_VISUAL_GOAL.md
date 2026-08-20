# R6 — Catalogue Actes : Goal visuel et métier

Date : 2026-08-19
Scope : **Réglages → Catalogue Actes uniquement**

## Goal

Conserver l'architecture métier **Spécialité → Actes → Pathologies**, mais remplacer le CRUD par `window.prompt()` par une administration explicite, validée et sûre, utilisable sur desktop, tablette et mobile.

## BEFORE certifiée

Workflow : `Settings Catalog R6 Visual Certification` #1
Run : `32206072956`
HEAD : `797d1d7e5d307dd5de87882cb833992074ab36ab`
Artifact : `9349191243`
Digest : `sha256:76256ba5237a492b7cac2f01ba89792ab9e0dc98dc22cf1396930ceef39b00cb`
Viewports : 1440 / 1024 / 768 / 430 / 390 × 1200.

Constats BEFORE :
- structure Spécialités / Actes / Pathologies claire et à conserver ;
- création via prompts navigateur ;
- édition d'un acte limitée au prix ;
- pathologies non éditables depuis l'UI ;
- état actif/inactif non visible alors qu'il existe pour actes/pathologies ;
- sur mobile, le CTA `Nouvelle Spécialité` concurrence le titre et comprime l'en-tête ;
- aucun DELETE backend : ne pas inventer une suppression physique ;
- spécialités sans `is_active` : aucune action destructrice ou faux archivage dans R6.

## Décisions métier verrouillées

1. **Pas de suppression physique** dans R6.
2. Actes et pathologies : utiliser `is_active` pour désactiver/réactiver.
3. Spécialités : création + édition nom/couleur seulement.
4. Toutes les mutations restent atomiques, donc pas de bouton de sauvegarde global.
5. Une modale ne se ferme qu'après mutation backend réussie.
6. Les champs invalides sont expliqués dans le formulaire, jamais ignorés silencieusement.

## Wireframe cible

### Page

```text
Catalogue des actes                         [+ Nouvelle spécialité]
Gérez les spécialités, tarifs et pathologies utilisés dans le cabinet.

┌ Spécialités ─────────────┐   ┌ Omnipratique                  [Modifier] ┐
│ ● Omnipratique           │   │ Actes cliniques                [+ Acte] │
│   2 actifs · 1 inactif   │   │ ┌ Consultation  CONS  300 DH  [Actif]✎ │
│ ○ Orthodontie            │   │ ├ Détartrage   DET   450 DH  [Actif]✎ │
│   1 actif                │   │ └ Composite... COMP1 500 DH [Inactif]✎ │
└──────────────────────────┘   │                                    │
                               │ Pathologies                  [+ Ajouter] │
                               │ [Caries · Actif ✎] [Gingivite · Actif ✎]│
                               └──────────────────────────────────────────┘
```

### Modale Acte

```text
Nouvel acte / Modifier l'acte
Nom *                 [________________]
Code                   [________________]
Tarif de base (DHS) * [________________]
Couleur                [● preset / input]
Statut (édition)       [ Actif  ● ]

                         [Annuler] [Créer / Enregistrer]
```

### Modale Pathologie

```text
Nouvelle pathologie / Modifier la pathologie
Nom *          [________________]
Description    [________________]
Statut (édition) [ Actif ● ]

                         [Annuler] [Créer / Enregistrer]
```

### Modale Spécialité

```text
Nouvelle spécialité / Modifier la spécialité
Nom *      [________________]
Couleur    [● preset / input]

                         [Annuler] [Créer / Enregistrer]
```

## Responsive

- >= 1280 : rail spécialités + contenu côte à côte.
- 768–1024 : spécialités au-dessus du contenu, cartes actes en 2 colonnes si espace réel.
- 390–430 : en-tête en pile ; CTA pleine largeur ou aligné sous le texte, jamais superposé au titre ; cartes actes en une colonne ; modale largeur écran avec marges 16 px et scroll vertical.
- Aucun overflow horizontal sur les 5 viewports certifiés.

## Critères de succès

1. `prompt(` absent de `CatalogTab.tsx`.
2. Création/édition spécialité par vrai formulaire.
3. Création/édition complète acte : nom, code, tarif, couleur, actif/inactif.
4. Création/édition pathologie : nom, description, actif/inactif.
5. Actes/pathologies inactifs explicitement identifiés dans la liste.
6. Aucun DELETE ajouté.
7. Aucune suppression/archivage fictif de spécialité.
8. Mutation échouée → formulaire reste ouvert + feedback erreur.
9. AFTER 1440/1024/768/430/390 sans overflow ni collision.
10. Tests frontend + CI/T2 proportionnés verts avant clôture.

## Preuve attendue

- tests de contrat frontend ;
- visual certification R6 sur les mêmes 5 viewports ;
- captures supplémentaires modale desktop + mobile ;
- inspection BEFORE / wireframe / AFTER ;
- score visuel final.

## Hors scope

- tarification automatique ;
- modifications des workflows cliniques consommateurs ;
- suppression physique ;
- migration DB pour `is_active` spécialité ;
- P2.2 Catalogue avancé (recherche, import/export, duplication, familles tarifaires) ;
- déploiement Vercel.
