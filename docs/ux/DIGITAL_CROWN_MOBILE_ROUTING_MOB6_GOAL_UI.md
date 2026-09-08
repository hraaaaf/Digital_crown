# DIGITAL CROWN — MOB-6 Canonisation du routage mobile — Goal UI

## Goal
Unifier la politique d’entrée mobile afin qu’un utilisateur mobile arrive dans le cockpit mobile canonique pour les parcours déjà couverts, tout en conservant les routes desktop sur desktop et sans détourner les routes publiques/auth.

## Succès observable
- `/` sur mobile → `/mobile/dashboard` ;
- les routes desktop couvertes ont une destination mobile explicite conservant le contexte ;
- `/mobile/*` inconnu reste dans le domaine mobile et ne tombe jamais dans `MainLayout` ;
- `/mobile/onboarding` reste hors `MobileProtectedRoute` ;
- les routes mobiles protégées conservent appairage/cache/biométrie ;
- aucune route desktop non couverte n’est redirigée artificiellement vers une surface mobile non équivalente ;
- desktop inchangé ;
- tests de politique + BEFORE/AFTER 390×844, 430×932, 768×1024 sans overflow/page/console errors.

## Table de destination cible
Pour les routes desktop dont une surface mobile canonique existe déjà :
- `/dashboard` → `/mobile/dashboard?tab=agenda`
- `/agenda` → `/mobile/dashboard?tab=agenda`
- `/patients` et sous-routes patient → `/mobile/dashboard?tab=patients`
- `/accounting` → `/mobile/dashboard?tab=finance`
- `/stock` → `/mobile/dashboard?tab=stock`
- `/approvisionnement` et sous-routes → `/mobile/dashboard?tab=marketplace`
- `/bibliotheque` et sous-routes → `/mobile/dashboard?tab=library`
- `/super-admin` → `/mobile/superadmin`
- `/salle-attente` → `/mobile/dashboard?tab=waiting-room`

Les routes sans équivalent mobile prouvé restent desktop, même depuis un petit viewport, plutôt que d’inventer une correspondance.

## Garde-fous
- pas de redirect basé uniquement sur largeur pour les pages publiques/auth ;
- ne jamais casser les deep links desktop sur desktop ;
- ne jamais court-circuiter `MobileProtectedRoute` ;
- pas de nouvelle architecture de navigation parallèle ;
- pas de Vercel.

Statut : `GOAL LOCKED — BEFORE REQUIRED`.
