# T1 — surface certifiable actuelle

Date : 2026-09-11

## Verdict

Le Document Studio certifiable actuel couvre **P1→P6 uniquement** : Ordonnance, Certificat, Devis, Note Honoraires, Suivi Paiement et Document Libre.

Le Compagnon Diagnostique historique P7 a été retiré volontairement du contrat produit actif. Son code et certains tests subsistent dans le dépôt, mais ils ne font pas partie de la surface runtime à certifier par T1.

## Preuves vérifiées

- `StudioTabs.tsx` expose uniquement P1→P6.
- `DocumentStudioVocabulary.ts` ne contient plus `plan` et `CertifiableDocumentStudioTab` couvre six pages.
- `DocumentTabNavigationPolicy.ts` et son test couvrent uniquement les états dirty des six pages actives.
- le navigateur T2 certifie les six pages actives et possède `assertCompanionAbsent(...)` pour empêcher la réapparition silencieuse de P7.
- commits historiques `a294dacc428d7bee43f910bcb3e71bd8bc6f3496` et `8e8bb2c245e5b742a37ac29d9b0b6a9aec9e4481` retirent explicitement le tab et réduisent le vocabulaire aux pages produisant des documents.

## Conséquence pour T1

Le harness T1 historique mélangeait encore la surface active avec `P7DirtyState.p7f.test.tsx` et annonçait une matrice P1→P7.

Ce lot réaligne le gate exécutable sur la réalité actuelle :

- régression ciblée T1 = patient boundary + navigation + clinical boundary + UI truth + shell a11y + dirty-state P1/P6, sans P7 dormant ;
- full frontend suite et build restent inchangés ;
- les gates runtime portent sur P1→P6 ;
- P7 reste un chantier produit/clinique séparé si une réactivation est décidée un jour.

## Probe runtime préparé — non exécuté

Le T2 existant couvre déjà la matrice navigateur P1→P6, 390/430/768/1280, dark desktop, preview/Escape, overflow, page errors, stress de navigation manuel, P6 dédié et fraîcheur print/PDF. T1 ne duplique donc pas cette couverture.

Le nouveau `frontend/scripts/certify-t1-transversal.mjs`, exécuté dans le même job T2, cible seulement les trous de preuve distincts :

1. création d'un second patient synthétique isolé `T2-0002` via `scripts/t1_runtime_seed_patient_b.py` ;
2. navigation SPA B→A avec réponse HTTP A volontairement retardée, puis A→B avant libération de A ;
3. preuve que B reste autoritaire avant et après libération de la réponse A ;
4. brouillon Document Libre → transition URL vers Certificat : `Annuler` restaure `libre` et conserve le brouillon ; `Continuer` atteint `certificat` ;
5. absence du Compagnon Diagnostique et de toute requête `ai-diagnostic` pendant le probe ;
6. artefact structuré `t1-transversal.json` + captures ciblées.

Le workflow T2 a été préparé pour exécuter ce probe après sa matrice navigateur existante et conserver les preuves dans l'artefact `t2-browser-evidence`.

**Aucun PASS runtime n'est revendiqué tant que ce HEAD n'a pas réellement tourné.**

## Gates T1 encore ouverts

1. exécuter le harness T1 réaligné sur le HEAD final avec Node 20 ;
2. exécuter le probe runtime ciblé A→B + URL dirty ;
3. repasser le T2 complet sur le même HEAD pour réutiliser sa couverture P1→P6 responsive/preview/PDF/print ;
4. repasser la CI principale ;
5. inspecter les preuves puis fermer audit/roadmap ;
6. exact-head final après closeout documentaire avant merge.

## Limite

Cette correction ne modifie aucun comportement produit. Elle corrige uniquement le périmètre de certification T1 et ajoute de la preuve runtime sur l'infrastructure CI isolée.
