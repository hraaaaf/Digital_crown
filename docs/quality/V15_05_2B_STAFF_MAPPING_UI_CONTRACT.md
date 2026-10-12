# LOT05.2-B1 — Écran staff Mapping Studio (préparation locale ; NO-GO import)

Branches parentes DRAFT : [PR #853](https://github.com/hraaaaf/Digital_crown/pull/853) Mapping Studio engine, [PR #850](https://github.com/hraaaaf/Digital_crown/pull/850) inspector. Autorité : décisions Notion V1.5-05 04–07, 10, 47–52, 58–60.

## Scope et guards
Nouvelle route /settings/migration sous ProtectedRoute + WorkstationModeGate protected + MainLayout. Contrôle UI supplémentaire : rôle ADMIN, superadmin, ou propriétaire dentiste dont employer_id est explicitement null. Un simple flag settings/admin d'employé ne suffit pas. Ce gate UI NE SUFFIT PAS à autoriser un import backend. Navigation staff seulement ; aucun accès ajouté dans /mobile, /companion, Station ou impression.

Interface responsive : trois étapes (source/cible JSON → décisions tables/colonnes → synthèse). Les inventaires JSON sont sélectionnés localement, strictement whitelistés, max 1 MiB, 512 tables et 512 colonnes par table, sans lignes patient, DEFAULT, SQL ni credential. Le rapport source doit correspondre à InspectionReport.to_dict() 05.1 et laisser toutes les autorisations fausses. Le manifest cible schema_revision+tables/columns est fourni par l'opérateur et NON CERTIFIÉ depuis les vrais modèles SQLAlchemy.

Propositions exact-name visibles sans décision implicite ; pour chaque table et colonne, choix explicite ou UNMAPPED. Changer une destination table efface ses décisions colonne. Collision, identifiants ambigus, credentials ou cible inconnue bloquent la synthèse. Tout nouvel upload, y compris invalide, efface décisions précédentes. Les fichiers restent en mémoire : aucun POST, persistance, localStorage/IndexedDB, approbation ou backup. Bouton Import HTML disabled.

## Preuves requises
Vitest/TypeScript pour parser, contrôle owner, collisions, secret mapping, interactions, remplacement du dump et bouton bloqué ; GitHub Actions exact-SHA ciblée frontend. BEFORE/AFTER desktop/mobile staff mêmes viewports sur harness synthétique ; captures de harness ne prouvent PAS authentification backend, test Windows cabinet, PWA mobile spécifique ni vrai schéma cible.

## Bloqueurs pour 05.2-B complet
Serveur qui vérifie rôle admin, cabinet via current_user.get_employer_id(), source hors-ligne, schéma target SQLAlchemy/Alembic, persistance de profils chiffrée et versionnée, exact dump SHA + empreinte target ; UI testée après vraie connexion, preuve visuelle humaine, 05.3 dry-run métier. Aucun merge, Vercel, import réel, mutation LOT04/06, Station/Companion.