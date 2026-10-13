# LOT05 — piste parallèle B : laboratoire isolé, AUCUN import de patient réel

Base fixée à [PR #863](https://github.com/hraaaaf/Digital_crown/pull/863), HEAD `5ef07d2ed693f5cb85ac980af567c4c1133192f1`. Cette piste est indépendante des deux autres et demeure DRAFT. **B — Physical schema** : vérification read-only d'un `Connection` **injecté exclusivement par des tests**; comparaison tables, colonnes, nullabilité, FK, uniques, et révision Alembic factice. Cette chaîne teste la capacité de détecter une dérive dans une DB construite par `create_all`; **elle ne réalise pas un upgrade Alembic ni une attestation authentifiée d'une base existante**. Le marqueur `neo000000027` est écrit par le banc, donc ne prouve pas qu'une migration y a été appliquée. DB PostgreSQL/SQLCipher et source `neo000000028` hors scope.

## Preuve ciblée
Suite de 6 tests **distincts** exécutés avec Python3.12 et SQLAlchemy==2.0.28, puis 10 tests du modèle ORM réel et 109 régressions d'import fictif ; CI exact HEAD de cette piste obligatoire. Ne compter aucun succès de la branche parente ni d'une autre piste comme preuve. Deux perspectives de revue interne + confirmation après tests. Périmètre de la PR = test-only + CI + ce document.

## Frontière de sécurité
Aucun changement backend runtime, route auth, ALembic, SQLCipher, migrations, frontend/mobile, LOT04/06, fichier client, source SQL exécutée, merge ou Vercel. Pas de GO 9/10 avant contrôle physique/auth/tenant complet, vraie reprise et intégration finale des trois contrats. Les snapshots et compteurs de lab ne démontrent pas l'intégrité clinique d'un vrai cabinet.
