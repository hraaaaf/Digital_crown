# CUST-05 — Stock & laboratoire — Goal

Date: 2026-09-22

## Goal
Rendre Stock & Laboratoire personnalisables par cabinet sans créer de seconde source de vérité ni exposer des données inter-cabinets.

## Vérité actuelle vérifiée
- `StockItem` possède déjà `employer_id`.
- `backend/routers/stock.py` scope déjà list/create/update/delete par `current_user.get_employer_id()`.
- `LabJob` ne porte pas `employer_id`, mais référence un `Patient` qui en porte un.
- `GET /api/lab-jobs/` lit actuellement tous les `LabJob` sans filtre tenant.
- `PATCH /api/lab-jobs/{id}` ne vérifie pas l'accès au patient.
- `POST /api/lab-jobs/` ne vérifie pas que le patient appartient au cabinet ni que l'acte appartient au patient.
- `Lab` ne porte actuellement aucun `employer_id`; il ne peut donc pas encore servir de catalogue labo personnalisable multi-tenant sans évolution de schéma.

## Décision d'architecture
1. **Sécurité avant personnalisation** : corriger d'abord les frontières tenant de `LabJob`.
2. **Stock** : conserver `StockItem` comme source unique, déjà tenant-safe.
3. **Laboratoires** : ne pas exposer de CRUD de catalogue `Lab` tant que l'isolation tenant n'est pas structurée.
4. Les champs libres actuels `material` et `type` restent éditables ; aucune liste système fermée ne doit devenir une seconde vérité.

## Succès observable — tranche 1
1. GET lab jobs ne retourne que les travaux dont le patient appartient au cabinet courant.
2. PATCH d'un travail d'un autre cabinet échoue.
3. POST sur un patient d'un autre cabinet échoue.
4. POST refuse un `act_id` qui n'appartient pas au patient demandé.
5. Aucun changement DB pour cette tranche.
6. Tests d'isolation multi-tenant verts.

## Tranche 2 — à auditer après sécurité
- catalogue de laboratoires par cabinet ;
- matériaux personnalisables ;
- types de travaux personnalisables ;
- cohérence avec StockItem / fournisseur sans duplication.

## Hors scope tranche 1
- migration de `Lab`;
- refonte visuelle du board labo ;
- intégration fournisseur externe ;
- déploiement Vercel.
