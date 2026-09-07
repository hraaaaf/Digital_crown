# DIGITAL CROWN — MOB-5F — QUICK DOCUMENT STUDIO — GOAL UI

Status: CLOSED — AFTER CERTIFIED — MERGED

## Goal UI

Depuis le patient déjà sélectionné, lancer un document courant sans quitter le cockpit, avec une interaction mobile courte, sûre et cohérente avec le reste de Digital Crown.

Cible produit: document courant en idéalement <30 s lorsque les données nécessaires sont déjà connues. Aucun test chronométré n'a été réalisé, donc le seuil <30 s reste un objectif produit et non une mesure certifiée.

## Références retenues

### Référence interne
- `MobilePatientsView`: cartes compactes, actions cliniques rapides, patient déjà contextualisé.
- pattern MOB-5H: détail / action complexe dans une sheet plutôt qu'une forêt de boutons inline.
- moteur desktop Document Studio: source de vérité fonctionnelle, pas référence de layout mobile.

### Référence externe
- CareStack: actions documentaires en quick links depuis le contexte patient.
- Open Dental / ODTouch: création clinique/prescription depuis le patient sélectionné.

## Structure implémentée

### État 1 — Cockpit patient
CTA primaire unique `Créer un document` dans `Actions cliniques rapides`, sans supprimer les actions existantes.

### État 2 — Choix du type
Sheet mobile filtrée par capacités serveur:
- Ordonnance;
- Certificat;
- Devis;
- Honoraires;
- Document libre.

Échéancier reste hors du Quick Document Studio car il constitue un flux financier dédié.

### État 3 — Éditeur rapide
- patient verrouillé par le contexte du cockpit;
- rappel de l'alerte médicale dans Ordonnance lorsqu'elle existe;
- champs strictement nécessaires;
- contrôles financiers bornés comme le backend;
- CTA primaire `Prévisualiser`;
- aucune création de moteur/template parallèle.

### État 4 — Preview / confirmation
1. `preview=true&archive=false`;
2. écran `Aperçu prêt`;
3. payload verrouillé;
4. `Modifier` ou `Archiver le document`;
5. archivage avec le même payload validé.

En démo isolée, preview et archivage sont simulés localement sans requête API.

### État 5 — Succès
- document archivé;
- ouverture du PDF créé si URL disponible;
- retour patient conservé.

## Sécurité / vérité UI

Contrats recoupés avec `DOCUMENT_TYPE_PERMISSIONS`:
- Ordonnance → `prescriptions`;
- Certificat → `patients`;
- Devis → `accounting`;
- Honoraires → `accounting`;
- Document libre → `clinical`.

Le backend revérifie patient + permission lors de la génération. L'UI n'est jamais une autorité RBAC.

## BEFORE vérifié

- baseline `e30b858f58686f5f7bef19ca93f1c5dae42929c9`
- run `34143420251` — SUCCESS
- artifact `10026785108`
- digest `sha256:b827b8b31f7bb604667d1a8df624eda98b1aa794ac25145f8c7acec72af5bdff`
- 390x844 / 430x932 / 768x1024
- 4 actions cliniques existantes
- `Créer un document` absent
- 0 overflow / page error / console error

## AFTER certifié

- product HEAD `91688ffc2d5bf97e584844f972a12df717fc74da`
- run `34149391346` — SUCCESS
- artifact `10028850934`
- digest `sha256:8b27d1c8658d0472f663a152d14bf463cfd519a7ac6ca5d65e4af7811c94080e`
- mêmes viewports 390x844 / 430x932 / 768x1024
- `Créer un document` visible
- 5 familles lisibles
- Certificat prouvé jusqu'à `Aperçu prêt` + `Archiver le document`
- 0 requête API réelle en preview
- 0 overflow / page error / console error
- score visuel **9.1/10**

Réserve: à 390 px, la navigation fixe mord légèrement la zone d'actions initiale avant scroll; le sheet et la confirmation restent propres.

## Fermeture

- PR `#365` merged
- HEAD final `d39c9a207f1bc8b54333a332d7b6ea44a5ef9c58`
- merge exact `d9d1c255be6c9878ce6b7127c7f723cfb61e38a0`
- CI post-merge `34163696668` — SUCCESS
- aucun Vercel

Goal UI atteint au niveau prouvé. MOB-5F est CLOSED.
