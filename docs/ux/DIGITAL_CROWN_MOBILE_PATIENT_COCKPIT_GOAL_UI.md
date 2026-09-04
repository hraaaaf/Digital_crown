# Digital Crown — Mobile Patient Cockpit — Goal UI v1

Status: DRAFT — visual realignment in progress
Canonical parent: `docs/ux/DIGITAL_CROWN_MOBILE_PRODUCT_CANONICAL.md`
Repo: `hraaaaf/Digital_crown`
Branch: `ux/mobile-product-canonical`
Lot: MOB-1
Deployment: none

## Goal

Concevoir l'écran mobile patient canonique de Digital Crown comme un cockpit clinique opérationnel, utilisable à une main et permettant au praticien d'identifier un patient, voir l'information critique et lancer l'action utile en moins de 30 secondes.

Le résultat ne doit pas être une réduction du dossier patient desktop.

## Correction visuelle — 2026-09-04

Le premier mockup conceptuel généré pour MOB-1 est **REJETÉ comme Goal UI**.

Raisons vérifiées :

- il reprenait la logique produit, mais pas assez fidèlement la signature visuelle de la PWA existante ;
- il introduisait une esthétique iOS générique plus plate que les surfaces Digital Crown actuelles ;
- il n'utilisait pas assez le header réel avec logo, notifications et pill de synchronisation ;
- il ne reproduisait pas la bottom navigation flottante vitrée et son active pill ;
- il introduisait des éléments hors scope tels que création de devis, annotation et génération de rapport panoramique.

Ce mockup ne doit servir ni de référence d'implémentation ni de preuve visuelle.

## Baseline visuelle obligatoire

Le prochain mockup doit dériver explicitement de la PWA réelle et des références mobiles déjà certifiées dans le repo.

### Shell / header existant

Référence : `frontend/src/features/mobile/Dashboard/components/MobileHeader.tsx`.

Invariants à reprendre :

- vrai logo Digital Crown en haut à gauche ;
- actions notifications + sync à droite ;
- pill sync vitrée, bordée, arrondie, avec état Live / Offline ;
- titre principal très fort en `font-outfit`, `font-black`, taille proche du `text-4xl` actuel ;
- spacing mobile généreux (`px-6`, top safe-area important) ;
- bleu primaire Digital Crown comme ancre visuelle.

### Navigation mobile existante

Référence : `frontend/src/features/mobile/Dashboard/components/MobileBottomNav.tsx`.

Invariants à reprendre :

- barre flottante détachée des bords ;
- hauteur environ 76 px ;
- rayon très fort, environ 34 px ;
- fond `glass-bg`, bord `glass-border`, backdrop blur fort ;
- active pill interne arrondie et discrète ;
- icônes Lucide ;
- labels petits, uppercase, fortement graissés ;
- safe-area conservée.

La future navigation `Aujourd'hui / Patients / + / Assistant / Plus` reste une hypothèse produit à tester, mais elle doit conserver **ce langage visuel**, pas inventer une nouvelle barre.

### Surfaces / cartes existantes

Références :

- `frontend/src/features/mobile/Dashboard/views/SecuriteView.tsx` ;
- `frontend/src/features/mobile/Dashboard/views/FinanceView.tsx` ;
- `.audit/mobile-m6-i-mockup.svg` ;
- `.audit/mobile-m6-e-mockup.svg` ;
- `.audit/mobile-m6-f-mockup.svg` ;
- `.audit/mobile-m6-h-mockup.svg`.

Invariants :

- fond médical perle / bleu très clair ;
- surfaces premium vitrées avec `glass-bg` / `glass-border` ;
- rayons 20 à 32 px selon importance ;
- ombres multicouches douces ;
- reflets blancs internes très discrets ;
- héros ou CTA primaire pouvant utiliser le gradient `primary → secondary` ;
- texte principal bleu nuit / presque noir, secondaire slate ;
- emerald réservé aux états positifs ;
- rose/rouge réservé aux alertes et risques ;
- aucune esthétique néon/sombre ni redesign générique.

## Scénario primaire

1. Le praticien ouvre `Patients` depuis la navigation mobile.
2. La recherche est immédiatement disponible.
3. Il saisit quelques lettres du nom, prénom ou numéro de dossier.
4. Il sélectionne le patient.
5. Le cockpit affiche immédiatement : identité, alerte médicale, prochain RDV, contexte financier autorisé et actions natives.
6. Il peut appeler, ouvrir WhatsApp, prendre une photo clinique, scanner un document ou encaisser selon permission sans traverser le dossier desktop.

## Invariants fonctionnels du mockup

Le Goal UI doit montrer au minimum :

- header Digital Crown fidèle au shell mobile existant ;
- recherche patient très visible ;
- identité patient : nom/prénom, numéro dossier, âge, assurance si disponible ;
- alerte médicale critique clairement prioritaire ;
- actions Appeler / WhatsApp ;
- prochain rendez-vous / prochaine séance ;
- finance synthétique seulement si permission ;
- actions Photo clinique / Scanner document / Encaisser si permission ;
- accès au contexte mobile existant sans exposer les studios lourds desktop ;
- état de synchronisation discret ;
- navigation exploratoire : `Aujourd'hui / Patients / + / Assistant / Plus`.

## Hiérarchie cible

1. header réel Digital Crown + sync ;
2. recherche / identité patient ;
3. alerte médicale ;
4. actions Appeler / WhatsApp ;
5. prochain RDV ;
6. finance synthétique ;
7. Photo / Scan / Encaisser ;
8. bottom navigation.

## Hors scope strict

Ne pas intégrer :

- odontogramme complet ;
- ClinicalHub complet ;
- Master Plan ;
- RVG Studio ;
- Panoramic Studio complet ;
- comparaison T0/T1 ;
- annotations panoramiques ;
- génération / édition de rapport panoramique ;
- Céphalométrie ;
- création de devis / Document Studio complet ;
- Analytics ;
- Treasury Hub ;
- paramètres cabinet ;
- administration Marketplace.

## Ergonomie

- usage principal à une main ;
- touch targets >= 48 px sur les actions majeures ;
- recherche et alerte visibles sans scroll sur 390 px si possible ;
- bottom navigation compatible safe-area ;
- aucun overflow horizontal ;
- états loading / empty / error / offline prévus après validation du screen principal.

## Viewports de référence

- 390 px : primaire ;
- 430 px : large phone ;
- 768 px : tablette compacte / boundary actuelle.

## Critères de validation

Le nouveau mockup n'est accepté que si :

- il est immédiatement reconnaissable comme **Digital Crown mobile actuel** ;
- le shell, le verre, les rayons, la hiérarchie typographique et la navigation sont cohérents avec l'existant ;
- la priorité patient est évidente en moins de 3 secondes ;
- l'alerte médicale domine correctement l'information secondaire ;
- les actions rapides sont compréhensibles sans surcharge ;
- aucune fonction desktop lourde n'est artificiellement miniaturisée ;
- aucune implémentation MOB-2 ne commence avant validation visuelle explicite.

## BEFORE

La baseline fonctionnelle et les références visuelles existantes sont maintenant documentées. Une capture runtime BEFORE 390 px devra encore être archivée avant implémentation MOB-2 ; les mockups M6 existants servent entre-temps de références visuelles certifiées du langage Digital Crown mobile.

## Next exact

Produire un nouveau mockup haute fidélité **390 px, un seul écran Patient Cockpit**, directement dérivé du shell mobile réel et des références M6 existantes, puis le soumettre à validation visuelle avant tout code produit.
