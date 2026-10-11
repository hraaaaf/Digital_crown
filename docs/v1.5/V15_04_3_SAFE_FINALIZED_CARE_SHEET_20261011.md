# V1.5-04.3 — Feuille de soins déjà finalisée : candidat fail-closed

**Statut : DRAFT / tests GitHub requis / pas d'activation cabinet.** Branche indépendante du master canonique `fa377f1ee05534cafbc26971f70f2e8ba8b792fd`. La PR #836 reste l'audit documentaire et la PR #799 est trop divergente pour être fusionnée.

## Contrat d'autorité

- Seul `POST /api/insurance-submissions/finalize` (après revalidation DB + hash de template + rendu canonique) enregistre un événement de finalisation `STATION_CARE_SHEET_TRUSTED_FINALIZATION_V1`, lié à `document_id`, `patient_id`, SHA-256 et identité du praticien qui a produit ce PDF.
- La station ne croit pas une simple archive `AUTRE` même si des métadonnées déclarent `VALIDATED` ; elle exige l'événement serveur de finalisation lié au **SHA courant**, des métadonnées de rendu cohérentes, la version active et récente, le patient et le tenant courant.
- Avant la station, ce **même praticien** doit approuver explicitement le retrait via le poste staff autorisé (permission comptabilité + poste non-station) ; l'événement d'autorisation est également lié au SHA exact.
- Une session identifiée de station enrôlée, non révoquée, non expirée et appartenant au même tenant/patient est requise via le garde 03.3/04.1 existant ; aucune modification ni génération de contenu depuis la station.
- Retrait : chemin limité à l'archive privée autorisée, refus symlink/traversal, taille bornée, contrôle PDF et SHA-256 **des octets réellement retournés** au client. Réponse en mémoire, pas de `FileResponse` ouvrant plus tard un autre chemin. Audit de retrait, `Cache-Control: no-store`, `nosniff`.

## Limites / à prouver

- Ce mécanisme ajoute une preuve de finalisation aux **nouveaux** documents finalisés ; les anciennes feuilles historiques sans preuve restent non éligibles. Il n'y a pas de migration rétroactive automatique.
- SHA et audit en DB ne sont pas une signature cryptographique indépendante de la DB, et le contrôle ne prouve pas encore un environnement cabinet hostile ayant un accès local à la DB. La configuration physique et les ACL de fichiers restent des gates terrain.
- 04.3 ne fait ni QR éphémère, ni Pocket, ni impression (04.5), ni anti-replay spécifique à une remise unique (04.4/04.7). Aucun UI kiosk/mobile nouveau dans cette PR.
- CI cible : tests FastAPI de refus/provenance et tests 04.1, collecte + syntaxe + run exact HEAD. En cas de rouge, corriger avant revue ; aucune conclusion avant les logs.

## Revue contradictoire à appliquer sur SHA final

Perspective A Sécurité : une archive AUTRE forgée, des métadonnées artificiellement VALIDATED, un changement de file_hash ou une collision de tenant, un chemin ou lien symbolique peuvent-ils divulguer un PDF ? Refus et audit précèdent-ils le transfert ?

Perspective B Qualité métier : un praticien légitime peut-il explicitement autoriser puis un patient identifié retirer **seulement** le fichier finalisé, sans générer de nouvelle version ? Les tests couvrent-ils statut, annulation, version, expiration, téléphone/desktop et réponse binaire exacte ?

**NO-GO merge / NO-GO Vercel / NO-GO Lenovo** avant CI complet, revues adversariales sur le même commit et accord explicite de publication. Le chantier Windows native PDF #831 est indépendant.


## Revue A/B du 11 octobre — corrections en cours (non convergé)

- **Perspective A — sécurité / provenance** : le premier candidat avait une faiblesse de contrat entre le PDF renvoyé par le service de finalisation et le patient du draft. Le producteur de preuve vérifiera désormais explicitement `expected_patient_id == document.patient_id`, en plus du praticien et du SHA. Sans cette égalité, la finalisation HTTP refuse l'événement de confiance.
- **Perspective B — QA / faux vert** : les 51 tests verts sur `501e53f1` exerçaient le retrait station via une fonction de preuve invoquée directement par les fixtures, mais ne démontraient pas que la route `/api/documents/insurance-submissions/finalize` enregistrait cette preuve. Nouveaux tests HTTP : événement de provenance émis par la vraie route (service de rendu contrôlé/stub), refus d'un document de patient différent renvoyé par ce service, puis retrait autorisé. Ces tests sont une preuve d'intégration **du routage**, pas un E2E non simulé de rendu CNSS/CNOPS/FAR.
- **Périmètre résiduel** : la vérification symlink se fait sur chemins avant ouverture puis les octets réellement livrés sont SHA-vérifiés ; le risque résiduel de race sur le système de fichiers et les ACL poste/Windows doit être évalué au gate terrain. L'autorisation concurrente, les scénarios multi-utilisateurs staff et le chemin de rendu assurance non simulé ne sont pas certifiés par le sous-ensemble ciblé.
- **Gate** : redémarrer tests/CI exact nouveau HEAD après modifications ; deux perspectives propres + confirmation restent nécessaires. Pas de FUE complet pour 04.3 (FUE-0 selon plan), FUE-I prévu 04.4, FUE-G premier à 04.5 et final à 04.7. Aucun merge, Vercel ni activation cabinet autorisé.
