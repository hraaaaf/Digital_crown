# V1.5-07 / 07-C — Contrat technique Command → Cabinet Desktop

**Statut : CONTRAT PROPOSÉ / READ-ONLY AUDIT — NON IMPLÉMENTÉ — 07-C OPEN.**
**Baseline auditée :** master@15cde06c377b6122478ef300ec68a09dd2bf7a93, 2026-10-20.
**Sources de décision :** Notion « Digital Crown — V1.5 | ROADMAP UNIQUE & HANDOVER CANONIQUE », section V1.5-07 ; PR #961 fusionnée c58f33df et #971 fusionnée 15cde06c.
**Hors périmètre :** 07-D sélection/persistance d'expérience, 07.1 MultiView, 07-E certification finale, refonte Signature/Pocket/tablette/Hub/Station/Patient Companion, deployment et données patients réelles.

## 1. Goal et invariants non négociables

Connecter graduellement le **deuxième rendu de travail Desktop Command** au **même Cabinet** que Signature : identité, rendez-vous, dossier patient, imagerie, autorisations, erreurs, transactions et règles cliniques. Ne jamais fabriquer un second backend, second store médical, second jeu de règles ou état métier concurrent. Signature Core continue d'être l'expérience par défaut et de référence BEFORE ; Signature Iconic reste facultative. Les palettes, tokens CSS, selected_theme, préférences du cabinet et données existantes ne sont jamais mutés par ce raccordement.

**Contrat 07-C :** changer la présentation, pas l'autorité. Une action Command autorisée doit produire le même résultat serveur et la même visibilité qu'une action équivalente Signature pour une identité et une donnée identiques. Une action interdite ou une erreur serveur doit rester interdite/explicite dans les deux expériences.

**Restriction d'activation :** le prototype de frontend/command-target.html et les modules frontend/src/features/command/command-* restent des cibles **synthétiques**, hors routes de Cabinet. Ne pas activer une route Command pour des utilisateurs du cabinet tant que les gates ci-dessous ne sont pas prouvés sur le même HEAD ; aucun 07-D anticipé.

## 2. État confirmé dans le code, pas inféré

| Couche | État source constaté | Règle de raccordement 07-C |
| --- | --- | --- |
| Entrée Command | frontend/command-target.html ; command-react-target-entry.tsx importe command-react-target ; target importe command-synthetic-fixtures et useSyntheticSession ; pas de route Cabinet | Supprimer l'autorité synthétique dans tout futur chemin produit ; réserver les fixtures au laboratoire |
| Shell Signature | frontend/src/App.tsx (ProtectedRoute, PermissionRoute, workstation bootstrap et routes) ; components/Layout/MainLayout.tsx | Conserver ces protections et le shell autorisé. Aucun doublon de mécanisme auth/enrôlement |
| Cockpit Cabinet | pages/Dashboard.tsx ; features/dashboard/hooks/useTodayAppointments.ts | Réutiliser une source de rendez-vous réelle et les états idle/loading/ready/error, filtrée par droits, sans interpréter error comme zéro rendez-vous |
| Agenda Cabinet | pages/AgendaPage.tsx encadre AgendaStudio ; features/agenda/AgendaStudio.tsx ; features/clinic/practitionerContext.ts | Ne pas monter AgendaStudio seul : AgendaPage installe des interceptors contextualisant praticien et résolution des conflits, puis les ejecte |
| Dossier patient | routes /patients/:id avec PermissionRoute patients ; features/patients/PatientDetails.tsx et PatientDetailsInner.tsx | Garder la frontière de route : resetPatientDocumentBoundary, blocage transitoire, tree key=id, précautions brouillons avant changement A→B |
| Imagerie | features/patients/components/PatientMediaTimeline.tsx ; GET /patients/:id/assets et /assets/:assetId/content ; PatientDetailsInner tabs radiology | Réutiliser composants, séparation d'accès, preview blob authentifié/revoke. Ne pas mettre d'URL média publique ni réutiliser blob de A sous B |
| Permissions | utils/accessControl.ts hasAccess ; App PermissionRoute ; PatientDetailsInner canClinical/canFinance/canPanoramic/canCephalo ; serveur autoritaire | Contrôles d'affichage et d'appel conformes à Signature, sans se substituer aux refus du backend |
| Préférences visuelles | index.css et réglages cabinet selected_theme déjà persistés | Command consomme les mêmes tokens sans réécriture de selected_theme ; expérience utilisateur+poste relève seulement de 07-D |

**Limite essentielle :** les chemins relevés démontrent les points d'entrée ; ils ne prouvent ni la correction complète des contrôles backend ni une parité fonctionnelle Cabinet/Command exécutée.

## 3. Contrats par frontière

### 3.1 Identité et navigation
- Démarrer à l'authentification Cabinet existante, vérifier enrôlement et contexte poste dans App/ProtectedRoute, garder l'identité serveur et les restrictions de rôles comme source de vérité.
- Une navigation Command « Agenda », « Patients », « Dossier », « Imagerie » ne doit déclencher une lecture de données protégées qu'après PermissionRoute/hasAccess pertinent ET contrôle serveur. Une simple entrée de menu ne constitue jamais une permission.
- Ne jamais recopier JWT, données patient, drafts ou media dans préférence d'expérience ou layout local. Session/logout/changement d'utilisateur efface tout état patient visible et toute URL blob active.
- Le contexte praticien choisi à l'écran ne remplace pas la résolution d'autorité backend, ni l'appartenance de l'acteur au cabinet.

### 3.2 Cockpit et Agenda
- Remplacer les 21 RDV synthétiques par des DTOs réels (ID de rendez-vous et patient numériques) fournis par l'API existante, avec gestion stricte des réponses et de l'absence de données.
- Les statuts et transitions dans command-synthetic-session.ts sont des exemples de démonstration : ne pas les utiliser comme oracle de la clinique. Écritures uniquement par services métier existants avec réponse serveur, refresh et erreur visible. Pas d'optimisme qui prétend une sauvegarde réussie.
- Ne pas importer AgendaStudio directement sans préserver le wrapper AgendaPage : les interceptors y ajoutent praticien pour lectures/créations/bulk, préservent le praticien historique d'une modification, et évitent un fallback global de check-conflicts lors d'une édition.
- Réutiliser la vraie gestion des conflits/plannings et les horaires de Cabinet. **Dépendance 07-A ouverte** : PR #929 Agenda Integrity (horaire wall-clock et conflit fail-closed) est toujours DRAFT/non fusionnée à la date d'audit. 07-C ne prétend pas que ses corrections sont sur master et ne les absorbe pas.
- Le multi-praticien et les rendez-vous legacy non assignés doivent conserver leur sémantique serveur ; pas d'attribution automatique fictive à un praticien.

### 3.3 Dossier et changement patient A → B
- Rejoindre le dossier par /patients/:id et sa frontière existante PatientDetails. Le composant PatientDetailsInner seul ne garantit pas resetPatientDocumentBoundary, suppression de l'ancien arbre ni sûreté des brouillons.
- Sur demande A→B : interroger l'état de brouillon document/activité critique ; confirmer, annuler ou empêcher le switch selon politique Cabinet. Tant que la transition n'est pas validée, ne pas afficher B avec les notes/images/actes de A.
- À la confirmation : neutraliser les panneaux patients de A avant toute présentation de B, invalider état/transient/brouillon selon contrats existants et monter l'arbre par identité B. Refus 403/404/timeout → erreur explicite, aucun fallback vers patient précédent.
- Tester A→B→A, rapid switches, requête tardive de A et confirmation annulée ; une promesse de « patient unique » dans le seul reducer synthétique ne prouve pas l'isolement clinique réel.

### 3.4 Imagerie et états cliniques
- Réutiliser PatientMediaTimeline(patientId), PatientRvgPanel, PanoramicStudio et CephaloWorkspace à travers les contrôles déjà requis dans PatientDetailsInner. Le mot « Imagerie » dans le menu Command n'accorde pas panoramic/cephalo/clinical.
- Préserver GET de contenus authentifiés, URL.createObjectURL + revoke, request-id guards, récupération explicite des erreurs, type MIME et provenance des médias. Un assetId de A ne doit jamais être servi/présenté comme celui de B.
- Aucun nouveau diagnostic, acte clinique, stockage de données, export, téléchargement, publication ni automatisation de décision en 07-C.

### 3.5 Signature, palette, poste, autres surfaces
- Aucun changement de comportement sur routes Signature existantes ; test de parité des données, statuts, permissions, navigation et erreurs. Rendu CSS de Command isolé pour ne pas modifier Signature.
- selected_theme et palettes personnalisées ne sont pas des commutateurs d'expérience. La future préférence Signature Core / Iconic / Command est **par utilisateur ET poste**, sans sync et sans réglage cabinet : conception/persistance exclusivement en 07-D.
- Command Desktop seulement ; vérifier 390/430/768 comme **smoke de non-régression/repli sûr**, sans promettre un Command mobile. 07.1 MultiView reste un chantier transverse séparé.

## 4. Matrice de preuve requise avant activation Cabinet

| ID | Scénario et oracle | Couche | Niveau |
| --- | --- | --- | --- |
| P01 | Signature et Command, même acteur/date : mêmes RDV/identifiants/statuts réels, même droit d'accès et même erreur | API + navigateur connecté | REQUIRED FUE-G |
| P02 | Secrétaire, praticien propriétaire, praticien employé : agenda/patient/facturation/clinique/imagerie respectent la même matrice permission explicite | UI négatif + API 403 | REQUIRED |
| P03 | Patient du cabinet A demandé par compte du cabinet B ; media/asset croisés : interdiction serveur, aucun flash UI | T2 tenants synthétiques + API | REQUIRED BLOCKER si fail-open |
| P04 | A→B→A et switch interrompu/rapid switching avec requêtes différées + brouillon non enregistré : aucune donnée/draft/media de A visible sous B | navigateur réel + state/log contrôlés | REQUIRED |
| P05 | Conflit horaire, modification de RDV praticien P sans réassignation à Q, legacy unassigned, timezone cabinet ; échec/pending check empêche faux succès | API/DB + navigateur | REQUIRED, dépend de 07-A #929 |
| P06 | Backend hors-ligne, timeout, 401/403/423, 404 dossier, échec media : refus/état d'erreur et retour sûr Signature, jamais UI clinique fictive | tests négatifs/fault injection | REQUIRED |
| P07 | Capture BEFORE Signature → AFTER Command sur vraies fixtures T2 même viewport 1280/1440/1920/2560, clavier, contraste, zoom réel 200% + reflow | FUE-G + AFTER | REQUIRED pour changement UX |
| P08 | Petit écran 390/430/768 : pas de fuite ou déclenchement de Command non autorisé, repli sûr, aucune modification de Pocket/mobile | smoke/permission | REQUIRED non-régression seulement |
| P09 | Tokens CSS/palettes, selected_theme, stockage, documents/drafts et données existants identiques avant/après route Command | instrumentation + assertions | REQUIRED |
| P10 | MultiView 07.1, choix/persistance 07-D, déploiement Windows réel 07-E | autre sous-lot | OUT OF SCOPE |

**Traçabilité :** pour chaque preuve donner SHA exact, run GitHub, tests réellement collectés/exécutés/skips, fixtures synthétiques, comptes/autorisations, BEFORE/ACTION/AFTER, erreurs et artefacts inspectables. Tests synthétiques du prototype #971 (FUE-I/labo) **ne remplissent aucun P01–P09** à eux seuls. Ne pas lancer de FUE-G avec patients réels.

## 5. Livraison incrémentale autorisable en 07-C, sans sélecteur

1. Établir composant d'intégration interne sous auth Cabinet et feature désactivée par défaut, sans route client active, et créer tests de non-régression Signature. Conserver prototype synthétique séparé.
2. Raccorder cockpit en **lecture seule** via données du jour/états API réels ; preuves P01, P02, P06, P09 avant nouvelles actions.
3. Raccorder Agenda en réutilisant intégralement la frontière praticien ; ne pas embarquer les modifications de #929 sans résolution séparée ; preuves P05 + parité.
4. Raccorder dossier et imagerie du **même patient** après preuve P03/P04 et refus serveur, puis seulement considérer l'activation des actions existantes.
5. Revue risque spécialisée, FUE-G Desktop BEFORE/AFTER, non-régression Signature/small screens. Handover 07-C vers 07-D seulement quand preuves et décision humaine compatibles.

Chaque incrément est une PR distincte ou série de commits traçables, avec tests qui suivent le HEAD. Si aucune route Cabinet n'est exécutée, statuts P01–P09 = NON TESTÉ et aucun « converged » n'est possible.

## 6. Revue contradictoire interne, réserves et STOP

**Perspective sécurité/data :** le chemin Command cible ne possède aucune autorisation serveur propre. Monter directement le patient workspace démo, reprendre l'état du reducer ou réutiliser Inner/AgendaStudio seuls crée une voie plausible de contournement des garde-fous. **Risque MAJOR/BLOCKER POTENTIEL, non vulnérabilité démontrée dans Cabinet**, car le prototype n'est pas activé.

**Perspective UX/clinique :** une interface dense peut afficher un mauvais praticien, un ancien patient ou une fausse transition « finie » si l'UI s'appuie sur un état local et masque refus/chargements. **Risque MAJOR potentiel**, à prouver/réfuter par tests négatifs et FUE sur Cabinet réel en T2.

**Autre dépendance ouverte :** Agenda #929 n'est pas mergée ; ne pas la contourner ni élargir le chantier 07-C à son correctif. Les Google Fonts héritées du CSS partagé limitent les revendications offline/privacy du laboratoire #971 ; changement CSS partagé hors scope sans décision.

**Gate d'arrêt :** tout affichage d'un patient d'un autre contexte, 403 qui devient succès, identités praticiens réattribuées, brouillon de A dans B, média de A dans B, code qui altère selected_theme, prototype synthétique branché en production, ou parcours FUE non exécuté présenté comme certifié. Noter réserves dans techdoubt.md.

## 7. État de sortie de ce contrat

- Livré : cartographie source-à-source et plan de vérification **documentaires** sur exact master.
- Non livré : code d'intégration, tests runtime, PR d'activation, Cabinet AFTER, nouvelle CI pertinente, déploiement ; aucun résultat P01–P09 revendiqué.
- Décision : **07-C OPEN / integration NOT READY**. GO suivant limité au premier incrément lecture seule après vérification des dépendances et validation des critères ci-dessus. 07-D, 07.1 et 07-E inchangés.
