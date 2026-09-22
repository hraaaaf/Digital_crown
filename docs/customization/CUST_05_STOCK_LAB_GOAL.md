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


## Tranche 2 — décision verrouillée

### Source unique
- laboratoires : table `labs`, maintenant scoppée par `employer_id`;
- matériaux : `StockItem` catégorie `MATERIAU` sert uniquement de source de suggestions ;
- type de travail : reste en saisie libre pour ne pas créer une taxonomie concurrente.

### Compatibilité legacy
- `labs.employer_id` est ajouté nullable.
- les laboratoires historiques non attribués restent invisibles dans les listes tenant-safe ;
- aucune attribution automatique n'est inventée.

### Mockup target

```text
Travaux prothétiques
Laboratoires du cabinet et matériaux issus de votre stock.

[ Gérer les laboratoires ]  [ + Nouvelle demande ]

Nouvelle demande labo
┌──────────────────────────────────────────────┐
│ N° patient *      N° acte *                 │
│ Laboratoire       [ Labo Atlas        v ]   │
│ Type de travail   [ Couronne            ]   │
│ Dent              [ 46                  ]   │
│ Matériau          [ Zircone             ]   │
│ suggestions depuis Stock / saisie libre     │
│ [ ] Réfection ou réparation                 │
│                         Annuler   Créer      │
└──────────────────────────────────────────────┘

Laboratoires du cabinet
┌──────────────────────────────────────────────┐
│ Labo Atlas            06...       Supprimer │
│ Labo Central          05...       Supprimer │
│                                              │
│ Ajouter un laboratoire                      │
│ [ Nom ] [ Téléphone ]                       │
│ [ Ajouter le laboratoire ]                  │
└──────────────────────────────────────────────┘
```

## Succès observable — tranche 2
1. un cabinet ne voit que ses laboratoires ;
2. un `lab_id` d'un autre cabinet est rejeté ;
3. un laboratoire utilisé ne peut pas être supprimé ;
4. les matériaux proposés viennent du Stock du cabinet ;
5. la saisie matériau reste libre ;
6. aucun laboratoire legacy non attribué n'est exposé ;
7. BEFORE/AFTER 390×844, 768×1024, 1280×900 ;
8. modals “Nouvelle demande” et “Laboratoires du cabinet” certifiés visuellement.
