# LOT05 — piste parallèle A : laboratoire isolé, AUCUN import de patient réel

Base fixée à [PR #863](https://github.com/hraaaaf/Digital_crown/pull/863), HEAD `5ef07d2ed693f5cb85ac980af567c4c1133192f1`. Cette piste est indépendante des deux autres et demeure DRAFT. **A — Tenant link** : `SyntheticPrincipal` n'est qu'un stub de principal; le code n'implémente **pas** l'auth de production. Le guard test-only refuse un patient d'un autre cabinet même si le moteur SQL admettrait un lien inter-cabinets, dérive le cabinet du principal fictif, refuse la valeur tenant et les champs contrôlés par le client, exige les rôles de labo ADMIN/DENTISTE. Un test vérifie l'égalité du refus pour patient absent/inter-tenant (non-divulgation). TODO bloquant : authentification réelle côté backend, WorkstationModeGate, tenant depuis l'identité serveurs, vraie migration SQL relationnelle, preuve E2E.

## Preuve ciblée
Suite de 7 tests **distincts** exécutés avec Python3.12 et SQLAlchemy==2.0.28, puis 10 tests du modèle ORM réel et 109 régressions d'import fictif ; CI exact HEAD de cette piste obligatoire. Ne compter aucun succès de la branche parente ni d'une autre piste comme preuve. Deux perspectives de revue interne + confirmation après tests. Périmètre de la PR = test-only + CI + ce document.

## Frontière de sécurité
Aucun changement backend runtime, route auth, ALembic, SQLCipher, migrations, frontend/mobile, LOT04/06, fichier client, source SQL exécutée, merge ou Vercel. Pas de GO 9/10 avant contrôle physique/auth/tenant complet, vraie reprise et intégration finale des trois contrats. Les snapshots et compteurs de lab ne démontrent pas l'intégrité clinique d'un vrai cabinet.
