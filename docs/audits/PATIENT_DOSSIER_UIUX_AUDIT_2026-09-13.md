# Audit UI/UX — Dossier patient Digital Crown

Date : 2026-09-13

## État vérifié

T1 est fermé : PR #465 squash-mergée, master post-merge `b9fc9ca6f0e978d51fa2180c30143b2c2c047200` vérifié.

Le lot UX transversal est porté par la PR #467, branche `ux/patient-dossier-transversal`. La preuve visuelle de référence ci-dessous est le HEAD produit `5846b7bd46b0d9cc2ec18319f86c8867755f8472` ; le closeout documentaire qui contient ce texte doit encore être recertifié exact-head avant merge.

Gates observés sur `5846b7bd46b0d9cc2ec18319f86c8867755f8472` :
- Patient P7 Final Certification #1325 : SUCCESS, 40/40 captures attendues ;
- Clinic P2 Patient Billing Visual Certification #51 : SUCCESS ; artifact `clinic-p2-patient-visual-evidence` ID `10317211290`, digest `sha256:2487167d7d247d810e97bfc28ab9029b84b1e1bf33b5460b5d1d64bcc2078150` ;
- T2 Runtime Browser Certification #2662 : SUCCESS ;
- Cabinet Upgrade PostgreSQL #177 : SUCCESS ;
- Settings R11 #518 : SUCCESS ;
- M6-I #1462 : SKIPPED attendu ;
- CI #3719 et Clinic P1 #21 étaient encore non terminaux lors de ce closeout intermédiaire.

## BEFORE inspecté

Captures réelles 390x844, 430x932, 768x1024 et 1280x900 sur : Vue d’ensemble, Clinique, Imagerie RVG, Panoramique, Céphalométrie, Documents création, Documents historique, Finances, Nouveau patient, Modifier patient.

Le desktop était stable, mais le mobile restait trop dérivé du desktop : chrome patient trop haut, destinations hors champ, sous-navigation Imagerie tronquée, types de documents cachés et couches flottantes couvrant du contenu.

## Goal UX1

À 390/430/768, garder les fonctions actuelles mais rendre le dossier patient immédiatement lisible et navigable. À 1280, préserver la densité et la stabilité existantes.

Succès observable :
- aucune destination patient essentielle hors champ ;
- RVG / Panoramique / Céphalométrie tous lisibles ;
- les 6 types du Document Studio immédiatement découvrables ;
- zéro overflow horizontal sur les surfaces certifiées ;
- couches globales non bloquantes ;
- captures AFTER 390/768/1280 + tests + comparaison avant merge.

## Référence / mockup fonctionnel

Mobile :

```text
[←] NOM Patient              [actions]
N° dossier · âge · téléphone
[ RDV ][ Examen ][ Document ][ Encaisser ]
[ Vue ][ Clinique ][ Imagerie ][ Documents ][ Finances ]
             contenu métier
```

En Imagerie, les 3 modalités doivent être visibles simultanément. Dans Document Studio, les 6 types passent en grille mobile plutôt qu’en bandeau horizontal caché. Un overlay lourd prend le viewport ; une action secondaire flottante ne doit pas couvrir une zone clinique critique.

## Résultat page par page / transversal

### PASS — shell patient mobile

- Header compacté sans suppression fonctionnelle.
- `Ouvrir sur mobile` reste disponible avec cible tactile >= 44 px.
- À 390 px, les cinq destinations `Vue d’ensemble / Clinique / Imagerie / Documents / Finances` sont simultanément visibles.
- L’onglet actif `Finances` reste visible et souligné dans la capture dédiée.

### PASS — Imagerie

- RVG / Panoramique / Céphalométrie sont visibles en grille 3 colonnes à 390/430/768.
- Les captures Patient P7 #1325 couvrent les trois modalités sur 4 viewports.

### PASS — Document Studio

- Les six types P1→P6 sont visibles à 390 en grille 2 colonnes : Ordonnance, Certificat, Devis, Note Honoraires, Suivi Paiement, Document Libre.
- Le Live Preview P6 reste une vraie modale responsive : 390 plein écran, 768 overlay 736x992, 1280 modale centrée 1024x836 ; clipping = 0 sur la certification T2 antérieure puis T2 exact-head #2662 SUCCESS.

### PASS — overflow / stabilité

Clinic P2 #51 a produit 12 fichiers de métriques pour `details`, `finances`, `edit`, `add` aux viewports 390/768/1280 : `overflowPx = 0` et `errors = []` sur les 12.

Patient P7 #1325 : `status = PASS`, 40 captures / 40 attendues, 10 surfaces × 4 viewports.

### PARTIAL — CrownBot

- La fenêtre ouverte est désormais contrainte au viewport mobile et respecte la safe-area.
- Le launcher flottant peut encore recouvrir une petite zone de contenu, notamment en bas du Document Studio à 390.
- Ce point n’est donc pas certifié « zéro collision ».

### OPEN — toast NBA

- Le toast `Dossier à compléter` est encore rendu via le Toaster global `bottom-right` et peut masquer une partie de l’Imagerie à 390 pendant sa durée d’affichage.
- Ne pas le déclarer corrigé. Sa transformation en callout persistant / centre de notifications reste une décision produit séparée ; un simple repositionnement non bloquant reste réversible.

## P2 / human gates séparés

- Ne pas supprimer automatiquement `Ouvrir sur mobile` sans décision produit.
- Ne pas remplacer le wording interne `Étape P7 certifiée` sans mapping métier validé.
- Ne pas transformer le NBA en nouveau flux métier sans arbitrage produit.

## Scores visuels

- P6 Live Preview : **9,2/10**. Réserve : header preview encore un peu haut à 390.
- Shell/navigation patient après UX1-A/B : **8,8/10**. Les destinations sont enfin visibles sans scroll horizontal caché ; réserve principale : labels compacts à 390.
- UX1 global : **non clôturé** tant que CrownBot launcher + toast NBA restent potentiellement superposés au contenu.

## Lots

### UX1-A — Shell patient mobile
État : PASS visuel sur HEAD `5846b7bd...`.

### UX1-B — Navigations secondaires
État : PASS visuel sur HEAD `5846b7bd...`.

### UX1-C — Couches globales
État : PARTIAL / OPEN. CrownBot ouvert est responsive, mais launcher et toast NBA nécessitent encore un traitement non bloquant.

## Next exact

1. Recertifier le HEAD documentaire final issu de ce closeout.
2. Si vert, merger PR #467 après contrôle mergeability/reviews/threads.
3. Ouvrir UX1-C depuis master : CrownBot launcher + toast NBA, avec BEFORE/AFTER 390/768/1280 et sans changement de logique clinique.
