# V1.5-04.8-D — UX Station impression : piste parallèle, sans API d'impression

Base exacte figée : PR #849 HEAD `673e908713b6995afd68d42e8aa8abfa28b76c36` (empilée sur PR #840 encore DRAFT). Aucun merge/master/Vercel et aucun usage de données réelles.

## Surfaces existantes réellement constatées
- UI Station documentaire **existante** dans `frontend/src/features/hub/StationPatientIdentity.tsx` : but `documents`, liste `availableDocuments`, messages FR/EN/AR, statuts `pending/identified/expired` et purge de session. Cette surface a été créée responsive, **il n'existe pas de dossier séparé `frontend/src/features/station` ni de preuve qu'une nouvelle fonction d'impression existe dans la vue mobile** ; ne pas inventer un bouton fonctionnel.
- Contrat API `frontend/src/services/stationPatientSession.ts` : `availableDocuments` renvoie seulement `documentId/kind`, et aucune méthode print/queue n'est disponible. Il faut une API Cabinet sécurisée issue de C et un signal de politique B avant de brancher l'action.
- Impression Desktop du personnel : `StudioFooter.tsx` et `useDocumentGenerator.ts` ; ces composants nécessitent une adaptation à l'**archive déjà finalisée**, ne pas utiliser le hook PDF navigateur côté Station.

## Travail indépendant possible avant C
Concevoir un composant de confirmation **purement présentatif**, testable sur données statiques `printAvailable=false` par défaut, sans réseau, sans PDF, sans token ni `window.print`. Choix explicite accueil/près Station lorsque les deux sont réellement certifiés, **aucune destination précochée**. Accessible clavier/lecteur d'écran, FR/EN/AR RTL, taille 200 %, captures comparables BEFORE/AFTER à 360/390/430/768/1280 ; vérifier présence de la fonctionnalité dans la vraie vue mobile avant toute correction dédiée.

## Machine d'états commune à C
`disabled/not_ready` (bouton absent), `confirming` (ne pas afficher de contenu médical), `requested` (demande reçue), `held` (attendre personnel), `accepted` (en file, pas « imprimé »), `uncertain` (intervention humaine, pas retry), `failed/cancelled`, `completed` (**seulement preuve réelle du job**). Ne jamais afficher un secret de libération sur écran partagé, ni PDF sous forme Blob, ObjectURL, iframe, téléchargement ou lien direct.

## Gate de raccordement
Le composant de présentation peut être développé/testé sur sa branche isolée, mais aucun branchement dans `StationPatientIdentity`, `stationPatientSessionService` ou Settings ne sera fait avant contrat/stats C et décision B stables. Mise en service interdite tant que l'impression est `disabled` et le registre physique absent. Les vraies observations papier/Station et les appareils iOS/NFC relèvent **exclusivement du LOT10** ; les captures WebKit/simulation restent dans 04.8-E.

## Statut
**Audit de surfaces et contrat figés, UI présentative/CI à faire** ; aucune impression en production ni modification mobile supposée.
