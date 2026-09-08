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
Exemples :
- `/patients/:id`
- `/patients/:id/edit`
- `/patients/:id/archives`
- `/bibliotheque/:code`
- `/approvisionnement/partenaire/:partnerId`
- `/approvisionnement/produits/:productId`

Ils restent desktop tant que le mobile ne peut pas préserver le patient, protocole, partenaire ou produit ciblé sans perte de contexte.

## Garde-fous
- pas de redirect basé uniquement sur largeur pour les pages publiques/auth ;
- ne jamais casser les deep links desktop sur desktop ;
- ne jamais court-circuiter `MobileProtectedRoute` ;
- appairage/cache/biométrie inchangés ;
- pas de nouvelle architecture de navigation parallèle ;
- pas de Vercel.

## Preuves disponibles
- AFTER cert `34210579881` : contrat, build et browser 390/430/768 SUCCESS sur le premier product head certifié `fcbdb8afb590f29c7d923743ca75b7eec017885f` ;
- artifact AFTER `10049662623`, digest `sha256:aa08739d1f5430588d0c9587f69d7ed36bcef28e00041edabc1e90d5c2298edd` ;
- recertification requise après refactor vers `MOBILE_BRIDGE_ROUTES` ;
- BEFORE exact pré-implémentation en recertification.

Statut : `GOAL LOCKED — IMPLEMENTED — FINAL RECERTIFICATION PENDING`.
