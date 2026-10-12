# Digital Crown V1.5 — LOT04.8 / contrat de frontière Pocket #852 ↔ Station #840 ↔ Cabinet

**Statut : DESIGN D'INTÉGRATION, NON IMPLÉMENTÉ, NO-GO IMPRESSION.** La présente note ne certifie ni un périphérique, ni une API, ni un parcours réel. Décision produit déjà acquise : `disabled` par défaut ; `reception`, `near_station` ou `both` seulement après configuration/certification explicites.

## Sources exactes observées (12 octobre 2026)

- [Pocket Patient #852](https://github.com/hraaaaf/Digital_crown/pull/852), `80a482fdb87dac8d20395958a783d4ef9bcf4dee`, OPEN/DRAFT, empilée sur [#847](https://github.com/hraaaaf/Digital_crown/pull/847) OPEN/DRAFT : `PatientCompanionApp.tsx`, `PatientCompanionStorage.ts` et captures synthétiques. Validation propriétaire **visuelle** sur les cinq vues, pas autorisation de merge ni preuve de session réelle.
- [Station 04.7 #840](https://github.com/hraaaaf/Digital_crown/pull/840), `445d63b9b1a677a4b0059744cc6c9d08a15a3131`, OPEN/DRAFT : `station_patient_session.py` et `station_document_eligibility.py`. Gate visuel réussi ; field gate non terminé.
- [Policy 04.8-A #849](https://github.com/hraaaaf/Digital_crown/pull/849), base au HEAD de #840, candidat avant cette note `ded90cf8b8621334f686d32d42ce392bb9e0cbe5` : `can_offer_print` = simple droit de **proposer** une destination, jamais un ordre d'imprimer ; `delivery_identity` = empreinte logique, jamais verrou durable.
- [SPEC 04.8 #848](https://github.com/hraaaaf/Digital_crown/pull/848) : principe de réutilisation Desktop, double destination C, refus PDF Station HTTP 423, atomicité, contrôle physique et sécurité des spools.

## Frontières de confiance — ne pas fusionner les trois identités

| Surface | Référence réelle | Autorité sur document / impression | Interdit |
| --- | --- | --- | --- |
| Pocket Patient personnel | `PatientPairing.context.access_id`, coffre IndexedDB chiffré, `PatientWalletSnapshot.shares[].share_id` avec `resource_type=document|media` et métadonnées | Lecture de partages autorisés dans son propre contexte, après vérification serveur des droits ; **pas** de décision d'impression publique | Ne pas convertir `share_id`, `title`, `document_type`, cache, `accessToken` ou contenu offline en `DocumentArchive.id`, SHA clinique ou autorisation de Station |
| Station partagée | Session identifiée `tenant_id/patient_id/station_id/session_id` validée sur Cabinet ; liste serveur `{documentId, kind}` | `evaluate_document_eligibility` reconstruit depuis DB : dossier, état actif/version, finalisation + accord retrait (feuille) ou preuve fiable de présence (attestation) | Aucun PDF/Blob/ObjectURL/download/print navigateur Station ; GET PDF existants doivent rester **423** |
| Cabinet / personnel de confiance | Session Station relue dans DB + archive/présence vérifiée + politique d'imprimante | Seul un futur endpoint authentifié/worker de confiance peut accepter/tenir/libérer une **intention** après validation atomique | Ne jamais considérer un `can_offer_print: allowed` ou un code QR seul comme permis d'imprimer |
| Desktop personnel authentifié | `StudioFooter` / `useDocumentGenerator` actuels | UX/confirmation et impression navigateur pour **archive vérifiée**, après adaptateur et acte personnel distinct | Ne pas réutiliser le hook tel quel sur Station : il génère potentiellement un nouveau document et utilise Blob/iframe/window.open |

### Faits de schéma qui empêchent un branchement direct

1. Pocket expose des `share_id` et des labels, pas l'identité canonique `DocumentArchive.id`, la version active, une empreinte SHA-256 validée, ni l'autorisation de retrait. Un document visible dans Pocket **n'est pas** par déduction imprimable en Station.
2. Station `GET /patient-session/{session_id}/documents` fournit des références `{documentId, kind}` déjà évaluées, **mais chaque nouvelle demande exige une relecture DB**. Une liste ancienne ou un état Pocket hors ligne ne saurait activer l'impression.
3. Le PDF Station reste bloqué (`GET .../care-sheet/{id}` et `.../presence-receipt/{id}` => 423). Les octets approuvés passent uniquement par le Cabinet vers un consommateur **de confiance** ; jamais via Pocket/Station pour alimenter l'impression de la borne.
4. Le choix `both` implique **sélection explicite et destination immuable** dès la demande ; l'indisponibilité d'un périphérique n'autorise aucun basculement silencieux. `near_station` requiert une libération confidentielle prouvée, sinon mode désactivé.

## Proposition de contrat minimal 04.8-C (NON déployé)

Station envoie une intention ne comportant que `sessionId`, `kind`, `documentId`, `printerId`, `requestNonce`; pas de nom, titre, PHI, PDF, PIN de retrait, SHA d'origine navigateur ni `share_id`. Cabinet authentifie Station + tenant ; réobtient patient/session/document/version et autorisations en DB ; revalide l'empreinte de l'archive avant tout job ; résout la destination dans allowlist. L'empreinte calculée par serveur et l'identité de délivrance (indépendante de l'imprimante) sont conservées dans une **transaction atomique** contre double clic/cross-destination. Le client ne choisit pas un état `completed`.

Contrat d'états serveur conservateur : `requested -> accepted -> held -> released -> completed` ou `failed/cancelled/uncertain`. La perte de preuve matérielle produit `uncertain`, bloque retry et exige réconciliation humaine. `completed` ne peut pas être déduit de HTTP 202, du spool ou de la seule ouverture d'un dialogue d'impression. Réémission exceptionnelle = nouveau geste habilité et audité.

Réponse publique Station limitée à `requestId` opaque et code d'état neutre, avec expiration courte et `Cache-Control: no-store`. Les secrets de libération doivent être communiqués par canal **personnel** distinct de la borne ou sous garde du personnel. Aucune nouvelle API n'est autorisée par cette note ; il faut d'abord définir modèle, routes, permissions, transaction et recouvrement de panne.

## Matrice de tests REQUIRED avant 04.8-C/D

| Risque | Scénario négatif obligatoire | Résultat exigé |
| --- | --- | --- |
| Confusion Pocket ↔ Station | `share_id` arbitraire, document visible offline, mauvais `access_id`, patient multi-dossiers, document non finalisé | Refus ou absence d'offre ; le backend ne fait jamais confiance au portefeuille Pocket pour imprimer |
| Autorisation et contexte | tenant étranger, patient/station différents, révocation, expiration, purge, QR replay, droits praticien retirés entre liste et POST | Refus **avant** émission PDF ou mutation d'un job |
| Idempotence | deux demandes même archive/version vers `near_station` et `reception`, nonces distincts en concurrence | Au plus une intention atomiquement acceptée ; aucune destination changée silencieusement |
| Inconnu matériel | crash après spool, printer offline, état `uncertain`, panne de libération, spool non purgé | Pas de retry/release automatique ; personnel réconcilie |
| Vie privée | GET PDF Station, devtools/network/cache/downloads/logs, secret de libération sur écran partagé | HTTP 423, **zéro octet PDF** côté Station et aucune divulgation de secret ou PHI |
| Réemploi Desktop | ouverture manuelle, archive déjà finalisée, jamais génération/re-archivage sur clic Station | Contrat d'impression personnel séparé et preuve explicite de destination |
| UX | FR/EN/AR RTL, 390/430/768/1280, reflow 200 %, clavier, erreur/offline/retour accueil | AFTER réels, cible comparée, aucun état `imprimé` sur simple queue ; vérifier d'abord les surfaces mobiles existantes |

## Séquence de reprise et décisions GO/NO-GO

1. **04.8-A** : contrat présent, revue des frontières Pocket/Station/Desktop ; garder la policy pure. Le bon progrès n'est pas d'importer le shell #852 dans #849.
2. **04.8-B** : uniquement après validation des contrats, configuration tenant + allowlist + preuve du matériel. Valeur par défaut `disabled`; `both` exige deux périphériques réellement contrôlés.
3. **04.8-C** : job Cabinet authentifié, transactions/idempotence/reconciliation, adaptateur archive du Desktop, tests backend négatifs et preuves de non-fuite.
4. **04.8-D/E** : UI Station avec confirmation et destination explicites ; BEFORE/AFTER, tests accessibilité ; ensuite laboratoire Windows/Station distinctes, spool, sortie papier synthétique et approbation de l'utilisateur.

**Gate de décision** : #852 validée visuellement ne signifie ni Pocket intégré sur master, ni Station 04.7 certifiée terrain. Ne pas merger #849 vers #840/master, ni activer printing, ni déployer Vercel sans décisions distinctes et preuves exact-HEAD. Cette note a pour seul objectif de prévenir une intégration dangereuse.