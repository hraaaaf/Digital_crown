# LOT07 R2 — candidat master-native R-only (preuve, pas release)

- Base exclusive : `master@46362e2986e3b6b08598f518eff95fa01f161571`.
- Source certifiée historique : [#1082](https://github.com/hraaaaf/Digital_crown/pull/1082) `45138aa4433e18704c57dc3582ec0be8b16c251d`.
- Nouveau candidat : arbre `master` + **51 fichiers de portage à contenu conservé**, dont un `backend/main.py` assemblé de manière additive (garde BILAN R-only de R2 + route CrownBot guidée ajoutée côté master). Le commit sera **un parent unique sur master**, aucun merge/rebase de branche, aucun changement de master.
- Périmètre : clinique R-only MultiView, sécurité BILAN historique / QR public générique 404, refus W/X, route de brouillons, médias C5, thèmes et 1280 px, fixtures et contrôles T2 exclusivement.
- Le code protecteur `--color-*` CSS demeure issu des tokens du thème; aucune valeur de couleur de marque codée dans les ajouts de polish.
- Hors périmètre explicitement **non porté** : ancien rehearsal CI `lot07-r2-decisions-master-integration.yml`; visual CI ordonnance; scripts de capture ACIG et scripts/certification Ordonnance Fidelity/Composer; modification métier `DrugRowV1.tsx`, test de provenance Ordonnance; contrat PWA mobile Pocket; E2E général « trois éditeurs » et son ancien workflow expérimental. Ces fonctionnalités demeurent en master ou branches dédiées; leur release n'est ni attestée ni approuvée ici.
- Les CI R2 historiquement branchées sur `feat/*` sont reciblées vers des PR **base master**. Le test d'intégration ne fait plus de `git merge`: il exige un `master` SHA épinglé, son ascendance stricte et aucun `MERGE_HEAD`; aucun push/merge/Prod. Matrice backend/RBAC et Vitest inclut les deux suites de garde des brouillons.
- Les anciennes 8 certifications #1082 ne **se transfèrent pas** à ce nouveau HEAD : exiger de nouveaux résultats exact-SHA et des captures authentiques avant une quelconque approbation technique.
- Requiert une autorisation humaine distincte avant merge, puis une autre avant Preview, puis avant Production; laisser `W/X` refusés, `R3` non commencé, lot R2 gouvernance OPEN.
- Ne contient aucune donnée patient réelle, ne doit générer de captures que sur comptes synthétiques T2; ne jamais remplacer les refus API serveur par des masquages d'UI seuls.
