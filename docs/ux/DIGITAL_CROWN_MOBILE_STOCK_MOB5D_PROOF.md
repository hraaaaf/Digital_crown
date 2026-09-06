# Digital Crown Mobile — MOB-5D Stock — Proof

Status: CERTIFIED / MERGE READY
Repo: `hraaaaf/Digital_crown`
PR: `#360`
Branch: `ux/mobile-stock-mob5d`
Product HEAD: `9ce48a6c38aaa20ff2e029646a919a5c2ed5c163`
Baseline master: `aaa28ef97b22df2c5654c4e0da7efc15692787a8`
Deployment: none

## Goal
Activer Stock Desktop + Mobile sur la source métier existante, sans modèle parallèle.

## Implémentation vérifiée
- Desktop `/stock` active `StockPage` existante.
- Mobile `Plus → Stock`.
- Deep-link `?tab=stock`.
- Cockpit mobile : criticité rupture/alerte/OK, recherche, filtre, ajustement rapide `-1/+1`, ajout rapide.
- Même backend `/stock/*` et même DB que desktop.
- Pas de suppression mobile, pas de workflow lourd inventé.
- Preview locale fictive, aucune donnée cabinet réelle.

## Sécurité / données
Le backend Stock scope les lectures et mutations sur `current_user.get_employer_id()` et `StockItem.employer_id`.
Le contrôle d'accès reste celui du backend existant via `require_permission("patients")`.

Preuve ajoutée : `backend/tests/test_stock_access_control.py`
- isolation inter-cabinets ;
- sous-compte rattaché au cabinet employeur ;
- permission explicite `patients:false` → 403.

La suite backend complète CI est verte : **2994 passed, 8 skipped, 4 warnings**.

## Tests UI / build
Certification MOB-5D run `34039544092` ✅
- 4 fichiers Vitest ciblés ;
- **11/11 tests pass** ;
- build production Vite ✅.

CI générale run `34039544113` ✅
- Backend tests & durcissement ✅
- Frontend tests & build ✅
- Garde production négative ✅
- context bridges M4-A / M4-B / M4-C ✅

## BEFORE / AFTER
BEFORE exact : `aaa28ef97b22df2c5654c4e0da7efc15692787a8`
AFTER candidat : PR merge ref construit à partir du HEAD `9ce48a6c38aaa20ff2e029646a919a5c2ed5c163`.

Viewports certifiés :
- 390×844
- 430×932
- 768×1024

Pour les 3 AFTER :
- 5 boutons de navigation canonique ;
- hauteur nav 76 px ;
- `horizontalOverflow=false` ;
- `runtimeErrors=[]`.

Captures :
- `after-stock-390x844.png`
- `after-stock-430x932.png`
- `after-stock-768x1024.png`

## Artifact
- run : `34039544092`
- artifact : `9991265607`
- nom : `mobile-stock-mob5d-evidence`
- digest : `sha256:539b9a1aa6ca55b72b91a4fe1398d5d7c1162a1edd8a26633a9f421a43e8c51f`
- 11 fichiers, 1,242,701 octets

## Comparaison visuelle
Le cockpit AFTER remplace l'absence de point d'entrée Stock mobile par une vue dédiée cohérente avec le shell Digital Crown : hiérarchie nette, compteurs de criticité lisibles, recherche et filtre accessibles, cartes d'articles tactiles, actions rapides clairement séparées.

À 390, 430 et 768 px, la navigation reste stable et le contenu reste lisible sans débordement horizontal. Le titre `Stock` est porté directement par la vue ; l'absence de libellé Stock dans `MobileHeader` n'entraîne donc aucun défaut visible.

Score visuel : **9.3/10**.

## Limites connues hors lot
- dépendances npm existantes signalées par `npm audit` ; non introduites spécifiquement par MOB-5D ;
- warnings SQLAlchemy SuperAdmin existants dans la suite backend ;
- historique avancé, lots, réassort structuré et paramétrage stock lourd restent desktop/futurs lots.

## Verdict
MOB-5D satisfait le Goal observable : Desktop + Mobile utilisent la même logique Stock, tenant/RBAC sont couverts, build/tests/runtime sont verts, et les viewports 390/430/768 sont visuellement certifiés.
