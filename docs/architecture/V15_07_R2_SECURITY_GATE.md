# LOT07 R2 — Cabinet Desktop MultiView | Contrat de sécurité 07-A / 07.1.A

**Statut : branche de preuve DRAFT, non fusionnée, non déployée.** Référence de gouvernance et avancement : Notion « LOT07 | ROADMAP UNIQUE · Avancement vérifié · Reprise propre » ; ce fichier n'est **pas** une nouvelle roadmap.

## Constat et correctif limité

Le pilote clinique G1 #1039 utilise `PatientMediaTimeline`, qui proposait la mutation `POST /patients/:id/assets/import` en plus de la consultation. Un slot théoriquement « R » ne peut pas laisser un bouton Importer actif. Dans cette branche :
- `PatientMediaTimeline.readOnly` masque l'interface d'import, supprime l'input file et refuse les événements de fichier reçus malgré tout. `readOnly` vaut **false par défaut**, afin de ne pas modifier le Cabinet normal hors MultiView.
- L'**adapter MultiView en colonne Imagerie** monte la vraie `PatientMediaTimeline readOnly`. Les autres panneaux G1 restent consultatifs (dossier résumé ; suivi orthodontique comparatif existant sans écriture). Sur tablette/mobile et en repli monovue hors MultiView, le Cabinet normal conserve son comportement antérieur.
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

## Critères de gate (R2 toujours OPEN)

- Tests R UI : menu `Importer` absent, input file absent, aucun `api.post` depuis le slot, Cabinet standard inchangé.
- Tests W/X : aucun `renderSlot` d'une composition demandant W/X, préférences sérialisées refusées, droits/tenant/poste/patient vérifiés, contenu R seulement.
- TypeScript complet + build prod statique + suites Vitest exact HEAD ; tests FastAPI+Chromium A→B et cross-tenant à reprendre si HEAD change.
- **BLOQUANTS non levés par cette PR** : route SPA avec brouillons, focus W + éditeurs et exclusivité X autorisés côté serveur, variations de poste/revocation, tests terrain physiques, 9 presets et 07.1.C/D. Aucun statut « livré » avant gates.

## Périmètre et gouvernance

Branche en pile sur #1039, elle-même sur #1038, toutes non fusionnées ; **aucun rebase forcé**. Ne pas altérer #1038/#1039 ni master à ce stade. Toute fusion, intégration clinique ou déploiement exige un GO distinct. Actualiser **la page Notion unique** avec HEAD, CI et statut ; ne pas créer de roadmap parallèle.
