# DIGITAL CROWN — MOB-6 Canonisation du routage mobile — Goal UI

## Goal
Unifier la politique d’entrée mobile afin qu’un utilisateur mobile arrive dans le cockpit mobile canonique pour les parcours déjà couverts, tout en conservant les routes desktop sur desktop et sans détourner les routes publiques/auth.

## Succès observable
- `/` sur mobile → `/mobile/dashboard` ;
- les routes desktop top-level couvertes ont une destination mobile explicite ;
- `/mobile/*` inconnu reste dans le domaine mobile et ne tombe jamais dans `MainLayout` ;
- `/mobile/onboarding` reste hors `MobileProtectedRoute` ;
- les routes mobiles protégées conservent appairage/cache/biométrie ;
- aucune route desktop non couverte n’est redirigée artificiellement vers une surface mobile non équivalente ;
- les deep-links riches restent desktop tant qu’un équivalent mobile ne peut pas conserver leur contexte exact ;
- desktop inchangé ;
- tests de politique + BEFORE/AFTER 390×844, 430×932, 768×1024 sans overflow/page error.

## Table de destination verrouillée
Routes top-level avec équivalent mobile prouvé :
- `/dashboard` → `agenda`
- `/agenda` → `agenda`
- `/patients` → `patients`
- `/accounting` → `finance`
- `/stock` → `stock`
- `/approvisionnement` → `marketplace`
- `/bibliotheque` → `library`
- `/salle-attente` → `waiting-room`
- `/super-admin` → `superadmin`

Les destinations sont résolues via `MOBILE_BRIDGE_ROUTES`, pas via une seconde table d’URLs mobiles.

## Deep-links volontairement non redirigés
Exemples : `/patients/:id`, `/patients/:id/edit`, `/patients/:id/archives`, `/bibliotheque/:code`, `/approvisionnement/partenaire/:partnerId`, `/approvisionnement/produits/:productId`.

Ils restent desktop tant que le mobile ne peut pas préserver le patient, protocole, partenaire ou produit ciblé sans perte de contexte.

## Garde-fous
- pas de redirect des pages publiques/auth ;
- deep links desktop conservés sur desktop ;
- `MobileProtectedRoute` non court-circuité ;
- appairage/cache/biométrie inchangés ;
- pas de nouvelle architecture de navigation parallèle ;
- pas de Vercel.

## Preuves Goal → résultat
- BEFORE final `34211312980` ✅ ; artifact `10049990601` ; digest `sha256:c89e86a107100e1596187291f9650c12bf716ffcc95c225efd4e670230b1eef4` ;
- AFTER final `34211780896` ✅ ; artifact `10050137272` ; digest `sha256:dc1e5a72d02f668cf537ec9fa28341940d34df7388603da6974eeac393d82ec7` ;
- routing contract ✅ ;
- frontend build ✅ ;
- 390×844 / 430×932 / 768×1024 : browser AFTER ✅ ;
- 0 overflow / page error / console error ;
- score visuel/comportemental **9.4/10**.

Statut : `GOAL DELIVERED — PRE-MERGE CERTIFIED`.
