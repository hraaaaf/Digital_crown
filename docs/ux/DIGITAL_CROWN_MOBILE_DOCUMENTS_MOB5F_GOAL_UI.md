# DIGITAL CROWN — MOB-5F — QUICK DOCUMENT STUDIO — GOAL UI

Status: IMPLEMENTED — FINAL AFTER PENDING — NOT CLOSED

## Goal UI

Depuis le patient déjà sélectionné, lancer un document courant sans quitter le cockpit, avec une interaction mobile courte, sûre et cohérente avec le reste de Digital Crown.

Cible produit: document courant en idéalement <30 s lorsque les données nécessaires sont déjà connues.

## Références retenues

### Référence interne

- `MobilePatientsView`: cartes compactes, actions cliniques rapides, patient déjà contextualisé.
- pattern MOB-5H: détail / action complexe dans une sheet plutôt qu'une forêt de boutons inline.
- moteur desktop Document Studio: source de vérité fonctionnelle, pas référence de layout mobile.

### Référence externe

- CareStack: actions documentaires en quick links depuis le contexte patient.
- Open Dental / ODTouch: création clinique/prescription depuis le patient sélectionné.

## Structure cible implémentée

### État 1 — Cockpit patient

Dans `Actions cliniques rapides`, un CTA primaire unique:

`Créer un document`

Il ne remplace aucune action existante.

### État 2 — Choix du type

Sheet mobile filtrée par capacités serveur:
- Ordonnance;
- Certificat;
- Devis;
- Honoraires;
- Document libre.

Échéancier reste hors du Quick Document Studio car il constitue un flux financier dédié.

### État 3 — Éditeur rapide

Principes appliqués:
- patient verrouillé par le contexte du cockpit;
- rappel de l'alerte médicale dans Ordonnance lorsqu'elle existe;
- champs strictement nécessaires;
- contrôles financiers bornés comme le backend;
- CTA primaire unique `Prévisualiser`;
- aucune création de moteur/template parallèle.

En vraie session, le sheet relit le cockpit patient de façon tenant-scoped pour récupérer `medical_alert_summary`; cette lecture est non bloquante et n'accorde aucune permission.

### État 4 — Preview / confirmation

Le flow est explicitement séparé:
1. `preview=true&archive=false`;
2. écran `Aperçu prêt`;
3. payload verrouillé;
4. `Modifier` ou `Archiver le document`;
5. archivage avec le même payload validé.

En démo isolée, la preview et l'archivage sont simulés localement sans requête API.

### État 5 — Succès

Retour compact:
- document archivé;
- ouverture du PDF créé si URL disponible;
- retour patient conservé.

## Comportement responsive

Viewports de certification:
- 390x844;
- 430x932;
- 768x1024.

Règles:
- aucun overflow horizontal;
- zones tactiles adaptées au mobile;
- CTA final sans ambiguïté;
- sheet scrollable;
- pas de tableau desktop compressé.

## Sécurité / vérité UI

L'UI filtre les types à partir des capacités exactes renvoyées par le serveur et échoue fermé si elles ne sont pas disponibles.

Contrats recoupés avec `DOCUMENT_TYPE_PERMISSIONS`:
- Ordonnance → `prescriptions`;
- Certificat → `patients`;
- Devis → `accounting`;
- Honoraires → `accounting`;
- Document libre → `clinical`.

Le backend revérifie patient + permission lors de la génération. L'UI n'est jamais une autorité RBAC.

## BEFORE vérifié

Baseline produit exacte: `e30b858f58686f5f7bef19ca93f1c5dae42929c9`.
Run `34143420251` — SUCCESS.
Artifact `10026785108`.
Digest `sha256:b827b8b31f7bb604667d1a8df624eda98b1aa794ac25145f8c7acec72af5bdff`.

Constat:
- patient cockpit fonctionnel;
- quatre actions cliniques existantes;
- aucune entrée `Créer un document`;
- 0 overflow / runtime error sur 390/430/768.

## AFTER attendu pour fermeture

Même patient, mêmes viewports:
- `Créer un document` visible et priorisé;
- cinq familles lisibles dans la preview SuperUser;
- Certificat prouvé jusqu'à l'écran `Aperçu prêt` + bouton `Archiver le document`;
- aucune régression des actions existantes;
- 0 requête API en preview;
- 0 overflow / page error / console error;
- inspection manuelle BEFORE/AFTER;
- score visuel >= 9/10 visé, sans le déclarer avant inspection.

Aucun Vercel.
