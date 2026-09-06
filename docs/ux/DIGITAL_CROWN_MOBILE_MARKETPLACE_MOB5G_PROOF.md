# Digital Crown Mobile — MOB-5G Marketplace — Proof

Status: CERTIFIED / MERGE PENDING
Repo: `hraaaaf/Digital_crown`
PR: `#362`
Certified product HEAD: `e13323772fb432f1b8bcb253361e08ba5e627995`
Deployment: none

## Goal
Refondre Marketplace / Approvisionnement pour un achat cabinet rapide desktop + mobile, sans dupliquer le moteur catalogue/commande existant.

## Success criteria
- desktop et mobile consomment le même controller Marketplace frontend ;
- le backend reste autorité pour prix, fournisseurs, split multi-fournisseurs et création DRAFT ;
- mobile accessible via `Plus → Marketplace` et `?tab=marketplace` ;
- DENTISTE / ADMIN uniquement, SECRETAIRE exclu, menu fail-closed ;
- recherche nom / SKU, quantité, panier et checkout DRAFT utilisables ;
- preview locale sans lecture/écriture API Marketplace ;
- BEFORE / AFTER aux viewports 390×844, 430×932, 768×1024 et 1280×800 ;
- zéro overflow horizontal et zéro erreur runtime ;
- build + tests frontend + régressions Marketplace backend verts.

## BEFORE verrouillé
- baseline : `062eadf1afc6ffc241be8420313e065a35f7d95b`
- run : `34045330209` ✅
- artifact : `9992935589`
- digest : `sha256:3e3701efc64a0eb3e3ed94be10b1a43bd5a0bd79cdf38e1c0917dda1220611db`
- viewports : 390×844 / 430×932 / 768×1024 / 1280×800

Constat BEFORE inspecté :
- surface fonctionnelle mais principalement desktop responsive ;
- pas d'accès Marketplace dans le cockpit mobile canonique ;
- hiérarchie davantage orientée catalogue que Quick Order ;
- checkout trop présent dans la page desktop.

## Implémentation certifiée
- controller partagé : `frontend/src/features/partnerMarketplace/usePartnerMarketplace.ts` ;
- desktop `PartnerMarketplacePage` refondu Quick Order / SKU-first ;
- view mobile dédiée `MarketplaceView` ;
- `Plus → Marketplace` ;
- deep-link `/mobile/dashboard?tab=marketplace` ;
- nav principale canonique inchangée : `Aujourd’hui / Patients / + / Assistant / Plus` ;
- DENTISTE / ADMIN autorisés ; SECRETAIRE exclu ; accès secondaires fail-closed tant que le rôle n'est pas résolu ;
- recherche nom / SKU, filtres, quantité, panier, checkout ;
- nom / cabinet / email préremplis depuis l'utilisateur courant ; téléphone / ville restent éditables ;
- preview locale déterministe, sans GET/POST Marketplace ;
- aucun backend métier Marketplace modifié ;
- ancien harness visuel P5 remplacé par la preuve MOB-5G canonique.

## Validation exacte du HEAD certifié
### MOB-5G Cert
Run `34049639818` ✅
- 5 fichiers Vitest ciblés ✅
- **18/18 tests** ✅
- build production ✅
- AFTER 390/430/768/1280 ✅
- artifact contract ✅

### Marketplace Final Certification
Run `34049639902` ✅
- frontend Marketplace regression + build ✅
- backend Marketplace P1-P10 : **105/105 passed** ✅
- visual 390/430/768/1280 ✅

### Régressions globales
- CI `34049639787` ✅
- T2 Runtime `34049639801` ✅
- Settings Security `34049639782` ✅
- Team `34049639833` ✅
- Frontdesk `34049639827` ✅
- Stock `34049639906` ✅
- Notifications `34049639766` ✅
- Bibliothèque `34049639810` ✅

Note connue, non résolue par MOB-5G : le job Marketplace installe `httpx==0.27.2`, ce qui provoque des avertissements de conflit avec `firebase-admin 7.5.0` et `ultralytics-platform`; les tests Marketplace restent verts. Ne pas présenter ce conflit comme corrigé.

## AFTER artifact
- run : `34049639818` ✅
- artifact : `9994164037`
- digest : `sha256:1f6b5426be0514ce398edc37e4671c44d86e168593cc5b2ab2d6899ec269481f`
- taille : 1,556,809 octets
- captures inspectées :
  - mobile liste 390×844 / 430×932 / 768×1024 ;
  - mobile checkout 390×844 / 430×932 / 768×1024 ;
  - desktop liste 1280×800 ;
  - desktop checkout 1280×800.

## Runtime / interaction proof
Pour 390 / 430 / 768 :
- HTTP 200 ;
- `scrollWidth == innerWidth` ;
- horizontal overflow = false ;
- page errors = 0 ;
- console errors = 0 ;
- 5 boutons de navigation ;
- nav height = 76 px ;
- recherche visible dans le premier viewport ;
- première référence visible dans le premier viewport.

Desktop 1280 :
- horizontal overflow = false ;
- page errors = 0 ;
- console errors = 0 ;
- checkout non permanent ;
- disclosure DRAFT visible ;
- préremplissage nom / cabinet / email vérifié ;
- exactement **1 POST** `/partner-orders` ;
- produit `101`, quantité `1`, total `390` ;
- URL inchangée après soumission.

## Comparaison visuelle BEFORE → AFTER
Inspection côte à côte effectuée sur les mêmes viewports.

Améliorations observées :
- mobile : passage d'une page desktop responsive à un cockpit cohérent avec la navigation mobile canonique ;
- recherche/SKU et quantité deviennent le chemin principal ;
- densité et hiérarchie mobile plus adaptées au téléphone ;
- desktop : recherche + achat rapide + panier deviennent dominants ;
- checkout sort du flux permanent et devient contextuel ;
- les checkouts restent lisibles et scrollables, y compris à 390 px.

Score visuel certifié après inspection : **9.4/10**.

## Conclusion
MOB-5G satisfait le Goal au HEAD `e13323772fb432f1b8bcb253361e08ba5e627995` avec preuves code, tests, runtime, interaction et visuelles.

État : **CERTIFIED / MERGE PENDING**.

Next exact : valider la vague docs-only finale, merger PR #362 avec verrouillage du HEAD, vérifier master/post-merge, marquer MOB-5G DONE / MERGED dans le canonique, puis ouvrir MOB-5H SuperAdmin mobile.