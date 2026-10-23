# LOT07 R2 — Cabinet Desktop MultiView | Contrat de sécurité 07-A / 07.1.A

**Statut : branche de preuve DRAFT, non fusionnée, non déployée.** Référence de gouvernance et avancement : Notion « LOT07 | ROADMAP UNIQUE · Avancement vérifié · Reprise propre » ; ce fichier n'est **pas** une nouvelle roadmap.

## Constat et correctif limité

Le pilote clinique G1 #1039 utilise `PatientMediaTimeline`, qui proposait la mutation `POST /patients/:id/assets/import` en plus de la consultation. Un slot théoriquement « R » ne peut pas laisser un bouton Importer actif. Dans cette branche :
- `PatientMediaTimeline.readOnly` masque l'interface d'import, supprime l'input file et refuse les événements de fichier reçus malgré tout. `readOnly` vaut **false par défaut**, afin de ne pas modifier le Cabinet normal hors MultiView.
- L'**adapter MultiView en colonne Imagerie** monte la vraie `PatientMediaTimeline readOnly`. Les autres panneaux G1 restent consultatifs (dossier résumé ; suivi orthodontique comparatif existant sans écriture). Le **repli monovue du laboratoire Desktop** reste lui aussi `readOnly`. En revanche, hors MultiView (dont mobile/tablette), le Cabinet normal conserve son comportement antérieur.
- `studioLayouts.ts` formalise `R` (read), `W` (focused edit) et `X` (exclusive sensitive action). **R seul est accepté par le pilote** ; `W` et `X` sont refusés avant rendu et exclus des préférences sérialisées. Les rejets ne constituent **pas** une implémentation d'édition ni d'action exclusive.

La restriction readOnly est une défense d'interface, **pas une autorisation de données**. Le serveur reste source de vérité pour chaque requête (session, tenant, patient, RBAC, protocole et opération).

## Matrice R/W/X — politique de montage (scope figé LOT07, aucun nouveau produit)

| Module prévu | Lecture R | Édition W | Action exclusive X | État implémentation |
| --- | --- | --- | --- | --- |
| Dossier | Résumé du patient courant | Modifier patient/notes seulement dans une vue focalisée et autorisée | Suppression/archive/signature hors split | **R réel G1**, W/X non certifiés |
| Agenda | RDV/activité selon droits effectifs | Créer/déplacer/confirmer sous règles serveur Agenda | Mutation concurrente/massive si sensible | R déclaré, adapter non branché |
| Imagerie | Médias GET authentifiés, viewer, comparaison | Importer/annoter dans vue dédiée autorisée | Acquisition/suppression destructive dédiée | **R réel G1** avec `readOnly`, W/X non certifiés |
| Galerie | Collections médias | Ajouter/ordonner explicitement autorisé | Suppression majeure dédiée | R déclaré, adapter non branché |
| Céphalo | Examen/provenance/mesures vérifiées | Tracé manuel dans instance isolée | Validation clinique/signature dédiée | R déclaré ; **deux instances simultanées INTERDITES** tant que stores non isolés |
| Photos | Consultation photos patient | Import/caption dans vue focalisée | Suppression définitive dédiée | R déclaré, adapter non branché |
| Traitement | Plan/actes affichés | Modifier plan dans workspace focalisé | Acte ou facturation sensitive séparés | R déclaré, adapter non branché |
| Suivi | Longitudinal T0/T1/T2 | Changer explicitement des données sources dans écran dédié | Publication/validation exclusive | **R réel G1** (comparateur existant), W/X non certifiés |
| Documents | Documents/état de brouillons | Éditeur focalisé avec anti-perte de brouillons | Impression/signature/émission contrôlées | R déclaré, adapter non branché |
| Présentation | Lecture patient volontaire et filtrée | Aucun W dans la vue publique | Présenter/masquer/popout avec révocation | R déclaré, écran patient physique R2 non livré (prévu 07.1.D) |

**Important** : les exemples de W/X sont des classes d'opérations à protéger, **pas une affirmation que les permissions backend et modules existent déjà sous ces noms**. Les adaptateurs non branchés restent refusés, et ne doivent pas être créés avec des composants de simulation. L'intégration module par module et les autorisations serveur véritables font partie des gates figés.

## Contrat identité et changement de patient

- **Un seul patient actif par workspace.** Ni layout ni préférence utilisateur+poste ne stocke un patient, un asset, un token, un brouillon ou une note. A/B simultanés interdits.
- La route G1 `/patients/:id` impose la même identité patient entre URL, GET autorisé et panneaux ; montage refusé avant réponse valide, poste enrôlé et permissions effectives. Dès identité/session/poste invalide : retirer les panneaux. Les médias sont chargés via endpoints patient authentifiés et doivent révoquer les object URLs sur unmount / requête tardive.
- **Blocage restant, P0 :** sur `master`, `PatientDetails.tsx` appelle `resetPatientDocumentBoundary()` à chaque `id` de route. `hasUnsavedPatientDocumentDraft()` ne protège que `beforeunload`, pas la navigation SPA A→B. La preuve « brouillon enregistré / Annuler navigation / Quitter sans sauvegarder » n'existe pas. **NE PAS qualifier 07.1.A de certifié** jusqu'à une navigation confirmée sans perte implicite et tests A→B→A/auth/logout.
- Le serveur, non le client, doit refuser les médias cross-tenant et cross-patient, les droits retirés, les requêtes tardives et les actions W/X non autorisées. **NE PAS** considérer la suppression du bouton comme preuve du refus HTTP POST direct.

## Essai isolé de navigation A→B→A (non activé)

- `patientDraftNavigationGate.ts` fournit la politique de sortie de dossier patient et un **hook dormant de Data Router** (`usePatientDraftExitBlocker`).
- Le test `patientDraftNavigationGate.test.tsx` utilise exclusivement `createMemoryRouter` et des brouillons **synthétiques**. Il couvre : navigation A→B bloquée si brouillon, bouton **Rester** qui conserve l'entrée d'A, bouton **Quitter sans sauvegarder** qui détruit les états documentaires avant de poursuivre, retour B→A sans contamination et changement d'onglet du même dossier sans perte.
- Le hook n'est **PAS MONTÉ** dans `App.tsx` ni `PatientDetails.tsx`. Le Cabinet utilise encore `BrowserRouter` : `useBlocker` exige un routeur Data et ne doit pas y être monté sous peine d'échec au runtime. `MainLayout.tsx` monte aussi un `motion.div` avec `key=location.pathname`; une interception après changement de route arriverait trop tard et aurait déjà démonté l'éditeur.
- **Étape bloquante** : migration contrôlée ou mécanisme de blocage équivalent **avant** navigation effective au niveau du routeur commun, maintient du composant A pendant demande de décision, prise en compte `POP` et liens/programmatique, exception de révocation/logout (purge immédiate indépendante), puis **tests sur route Cabinet complète**. Ne pas confondre tests de la stratégie isolée avec correctif fonctionnel de `master`.

## Critères de gate (R2 toujours OPEN)

- Tests R UI : menu `Importer` absent, input file absent, aucun `api.post` depuis le slot, Cabinet standard inchangé.
- Tests W/X : aucun `renderSlot` d'une composition demandant W/X, préférences sérialisées refusées, droits/tenant/poste/patient vérifiés, contenu R seulement.
- TypeScript complet + build prod statique + suites Vitest exact HEAD ; tests FastAPI+Chromium A→B et cross-tenant à reprendre si HEAD change.
- **BLOQUANTS non levés par cette PR** : route SPA avec brouillons, focus W + éditeurs et exclusivité X autorisés côté serveur, variations de poste/revocation, tests terrain physiques, 9 presets et 07.1.C/D. Aucun statut « livré » avant gates.

## Périmètre et gouvernance

Branche en pile sur #1039, elle-même sur #1038, toutes non fusionnées ; **aucun rebase forcé**. Ne pas altérer #1038/#1039 ni master à ce stade. Toute fusion, intégration clinique ou déploiement exige un GO distinct. Actualiser **la page Notion unique** avec HEAD, CI et statut ; ne pas créer de roadmap parallèle.
