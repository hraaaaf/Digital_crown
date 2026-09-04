# Digital Crown — Mobile Patient Cockpit — Goal UI v1

Status: READY FOR VISUAL VALIDATION
Canonical parent: `docs/ux/DIGITAL_CROWN_MOBILE_PRODUCT_CANONICAL.md`
Repo: `hraaaaf/Digital_crown`
Branch: `ux/mobile-product-canonical`
Lot: MOB-1
Deployment: none

## Goal

Concevoir l'écran mobile patient canonique de Digital Crown comme un **cockpit clinique opérationnel**, utilisable à une main et permettant au praticien de trouver un patient, comprendre immédiatement sa situation critique et lancer l'action utile en moins de 30 secondes.

Le résultat ne doit jamais être une réduction du dossier patient desktop.

## Direction produit retenue

La direction visuelle réalignée sur la PWA existante est retenue, avec un invariant supplémentaire demandé avant implémentation : **le Patient Cockpit ne possède ni palette ni police propres**.

Le mockup versionné est :

`docs/ux/assets/MOBILE_PATIENT_COCKPIT_GOAL_V1.svg`

Commit de création : `b6924f0f57931e0361dc0db45653b63c4de9fb0c`.

Le rendu du SVG représente le thème Ghost Elite uniquement pour rendre la cible lisible. Les couleurs et la police de ce fichier ne constituent pas un contrat d'implémentation.

## Invariant thème / typographie — VERROUILLÉ

L'application mobile doit consommer la même source de vérité que les réglages du cabinet.

Paramètres concernés :

- `selected_theme` ;
- `primary_color` ;
- `secondary_color` ;
- `accent_color` ;
- `font_fr`.

Règles :

1. aucune couleur de marque ne doit être codée en dur dans le Patient Cockpit ;
2. aucune police de marque ne doit être forcée localement dans le Patient Cockpit ;
3. les surfaces, textes, bordures, gradients et états actifs doivent consommer les tokens CSS partagés du thème ;
4. la police active doit être dérivée de `font_fr` via une source de vérité partagée ;
5. un changement dans Réglages doit se refléter sur le mobile sans configuration mobile parallèle ;
6. les couleurs sémantiques danger / warning / succès peuvent rester sémantiques, mais leur contraste doit être testé sur les thèmes supportés ;
7. aucun mockup ne doit être interprété comme une autorisation à figer une palette ou une police.

## Dette runtime vérifiée avant MOB-2

L'audit du code actuel montre que cette exigence n'est **pas encore satisfaite globalement** :

- `useSettingsStore.applyTheme()` applique `selected_theme`, `primary_color`, `secondary_color` et `accent_color` via les variables CSS, mais n'applique pas `font_fr` au runtime de l'application ;
- le shell mobile appelle actuellement au montage :
  - `document.documentElement.dataset.theme = ''` ;
  - `document.body.dataset.theme = ''` ;
  ce qui réinitialise explicitement le thème mobile au thème par défaut ;
- `MobileDashboard.tsx` force actuellement `font-outfit` sur le shell ;
- `MobileHeader.tsx` force également `font-outfit` sur les titres ;
- le type frontend `Snapshot` mobile ne contient actuellement aucun bloc branding/thème ;
- le backend `/api/mobile/snapshot` retourne actuellement `generated_at`, rôle, superadmin, rendez-vous, finance et débiteurs, mais pas la présentation du cabinet.

Conclusion : MOB-2 devra commencer par **réconcilier la présentation mobile avec le thème cabinet**, avant d'implémenter le nouveau Patient Cockpit. On ne dupliquera pas le moteur de thème.

## Baseline visuelle obligatoire

Le Goal UI dérive de la PWA réelle et des références mobiles déjà présentes dans le repo.

### Shell / header

Référence : `frontend/src/features/mobile/Dashboard/components/MobileHeader.tsx`.

À préserver :

- logo Digital Crown ;
- notifications et synchronisation en haut à droite ;
- pill de synchronisation vitrée avec état Live / Offline ;
- spacing mobile généreux et safe-area ;
- hiérarchie forte ;
- tokens de thème, jamais une palette locale.

La taille et la graisse du titre peuvent rester proches de l'existant, mais **la famille typographique doit suivre `font_fr`**, pas `font-outfit` imposé.

### Navigation mobile

Référence : `frontend/src/features/mobile/Dashboard/components/MobileBottomNav.tsx`.

À préserver :

- barre flottante détachée des bords ;
- hauteur proche de l'existant ;
- rayon très fort ;
- fond et bord dérivés des tokens glass ;
- active pill interne ;
- icônes Lucide ;
- labels compacts ;
- safe-area.

La navigation cible exploratoire reste :

`Aujourd'hui / Patients / + / Assistant / Plus`.

Elle doit utiliser le même langage visuel et le même thème que la barre actuelle.

### Surfaces

Références :

- `frontend/src/features/mobile/Dashboard/views/SecuriteView.tsx` ;
- `frontend/src/features/mobile/Dashboard/views/FinanceView.tsx` ;
- `.audit/mobile-m6-e-mockup.svg` ;
- `.audit/mobile-m6-f-mockup.svg` ;
- `.audit/mobile-m6-h-mockup.svg` ;
- `.audit/mobile-m6-i-mockup.svg`.

À préserver :

- surfaces premium légèrement vitrées ;
- rayons 20 à 32 px selon importance ;
- ombres douces ;
- reflets internes discrets ;
- CTA primaire dérivé de `primary → secondary` ;
- couleurs danger/succès utilisées sémantiquement ;
- aucune esthétique générique iOS, néon ou redesign déconnecté de Digital Crown.

## Premier mockup conceptuel — REJETÉ

Le premier mockup généré avant le réalignement ne doit servir ni de référence d'implémentation ni de preuve visuelle.

Raisons :

- identité trop générique ;
- shell/header insuffisamment fidèle ;
- navigation non conforme au langage glass existant ;
- fonctions hors scope telles que création de devis, annotation et génération de rapport panoramique.

## Scénario primaire

1. le praticien ouvre `Patients` ;
2. la recherche est immédiatement disponible ;
3. il recherche par nom, prénom, dossier ou information autorisée ;
4. il sélectionne le patient ;
5. il voit immédiatement identité, alerte médicale, prochain RDV et contexte financier autorisé ;
6. il peut appeler, ouvrir WhatsApp, accéder à l'agenda, prendre une photo clinique, scanner un document ou encaisser selon permission.

## Hiérarchie cible du screen 390 px

1. header Digital Crown + sync ;
2. titre `Patients` + recherche ;
3. identité patient ;
4. alerte médicale ;
5. Appeler / WhatsApp / Agenda ;
6. prochain RDV ;
7. finance synthétique + Encaisser si permission ;
8. Photo clinique / Scanner document ;
9. bottom navigation flottante.

## Hors scope strict

Ne pas intégrer dans ce cockpit :

- odontogramme complet ;
- ClinicalHub complet ;
- Master Plan ;
- RVG Studio ;
- Panoramic Studio complet ;
- comparaison T0/T1 ;
- annotations panoramiques ;
- génération ou édition de rapport panoramique ;
- Céphalométrie ;
- création de devis / Document Studio complet ;
- Analytics ;
- Treasury Hub ;
- paramètres cabinet ;
- administration Marketplace.

## Ergonomie

- usage à une main ;
- touch targets majeurs >= 48 px ;
- priorité patient compréhensible en moins de 3 secondes ;
- alerte médicale prioritaire ;
- aucun overflow horizontal ;
- bottom nav compatible safe-area ;
- états loading / empty / error / offline à produire avec les mêmes tokens après validation du screen principal.

## Viewports de référence

- 390 px : primaire ;
- 430 px : large phone ;
- 768 px : tablette compacte / boundary actuelle.

## Critères de succès MOB-1

MOB-1 peut passer DONE seulement si :

- Goal UI versionné ;
- mockup 390 px versionné ;
- mockup fidèle au langage mobile existant ;
- invariant thème + `font_fr` documenté ;
- aucun workflow desktop lourd réintroduit ;
- validation visuelle explicite du mockup cible obtenue ;
- aucune implémentation produit commencée avant cette validation.

## Preuves disponibles

- Goal UI versionné dans le présent fichier ;
- mockup cible : `docs/ux/assets/MOBILE_PATIENT_COCKPIT_GOAL_V1.svg` ;
- commit mockup : `b6924f0f57931e0361dc0db45653b63c4de9fb0c` ;
- audit source du moteur de thème et du shell mobile réalisé sur la branche du chantier.

## Gate restant

**Validation visuelle humaine du mockup `MOBILE_PATIENT_COCKPIT_GOAL_V1.svg`.**

Aucun code produit MOB-2 n'est autorisé avant ce gate.

## Next exact

Présenter le mockup MOB-1 versionné. Si la validation visuelle est positive, passer MOB-1 à DONE, mettre à jour le canonique, puis ouvrir MOB-2 par la correction du contrat thème/typographie mobile avant le Patient Cockpit.