# V1.5-04.3 — Feuille de soins finalisée : audit de reprise (11/10/2026)

**PRE / statut : READ-ONLY RECONCILIATION — pas encore implémenté ni certifié.**

## Goal canonique

La station ne doit permettre **que le retrait** d'une feuille de soins déjà finalisée et explicitement autorisée pour le patient identifié. Aucune édition clinique, préparation, validation professionnelle ou nouvelle génération depuis le kiosk.

Source de vérité : Notion « Digital Crown — V1.5 | ROADMAP UNIQUE & HANDOVER CANONIQUE », chapitre `V1.5-04 Station Self-Service Documents` (13 SP), sous-lot `04.3 — Feuille de soins finalisée (2 SP, FUE-0)`. Ne pas assimiler ce lot au laboratoire expérimental de PDF Windows FUE-G04.

## Baseline exacte master

- **master** `fa377f1ee05534cafbc26971f70f2e8ba8b792fd`, audit read-only.
- **04.1 déjà produit et fusionné** : [PR #781](https://github.com/hraaaaf/Digital_crown/pull/781), merge `4b870926359e0dcb5e6bf9a74a1689e56263fe52`. `backend/services/station_document_eligibility.py` contient la whitelist de `presence_receipt` et `care_sheet`, le refus par défaut, session station bornée à 120 secondes, contrôle tenant/patient/version et les obligations `finalized` + `withdrawal_authorized` pour `care_sheet`. Tests unitaires sous `backend/tests/test_station_document_eligibility_v15.py`.
- **04.2 déjà produit et fusionné** : [PR #782](https://github.com/hraaaaf/Digital_crown/pull/782), merge `db7f0bba6cd9eafd020af7025f2fb591f7fdfc5d`. `backend/services/station_presence_receipt.py` vérifie la preuve de présence du staff/Queue Core et rend un justificatif PDF déterministe. Route authentifiée `/patient-session/{session_id}/documents/presence-receipt/{appointment_id}` dans `backend/routers/station_patient_session.py`.
- **04.3 non intégré au kiosk** : aucune route station de retrait de `care_sheet` découverte dans `station_patient_session.py`. L'énumération `models.DocumentType` ne possède pas `FEUILLE_SOIN` / `CARE_SHEET`; le stockage `DocumentArchive` possède statut, groupe, version, hash, chemins et métadonnées. Les documents d'assurance existants peuvent être archivés sous `AUTRE` avec `clinical_data.kind=INSURANCE_SUBMISSION`. Cette représentation **ne vaut pas preuve** de feuille de soins finalisée ou de droit au retrait en station.

## Frontière d'implémentation proposée

1. Définir et tester un identifiant canonique de feuille de soins finalisée sans réinterpréter silencieusement `AUTRE`, sans renommer d'enum historique et sans migration destructive ; si aucune autorité de finalisation n'existe, retourner refus.
2. Construire le candidat **uniquement depuis la base canonique**, jamais depuis `finalized`, `patient_id` ou `withdrawal_authorized` fournis par le client. Contrôler `employer_id` du praticien, patient/session/station identifiés et non révoqués, dernière version active et hash PDF.
3. N'offrir que lecture/retrait au patient validé via une route station protégée ; une demande ne doit ni modifier le document clinique, ni créer de nouvelle version, ni archiver d'autre document. `Cache-Control: no-store` et vérification anti-replay/expiration.
4. Prévoir un chemin de livraison court et révocable ; l'impression, Pocket et le QR éphémère appartiennent à **04.5**, la purge/audit au **04.6**, pas d'activation silencieuse ici.

## Tests exigés avant verdict 04.3

Cas positifs : bon tenant/patient/station, session courte, document finalisé autorisé, PDF exact/hash connu, uniquement lecture.
Cas négatifs fail-closed : documents `AUTRE` arbitraires ; assurance draft/non validée ; statut ARCHIVE/SUPPRIME ; version précédente ; hash invalide ; ID forgé/path traversal ; nouveau tenant ou patient ; station non enrôlée ou révoquée ; session purgée/expirée ; demande répétée concurrente ; disparition fichier ; perte réseau.
Preuve sans aucune donnée patient réelle. Aucun « VALIDÉ » avant tests backend réels, frontend mobile si écran créé, CI exact HEAD, deux revues adversariales et closeout Notion.

## Gate / next

L'objectif de cette branche est de **réconcilier l'existant avant de coder**. Ce n'est pas une PR de feature, de livraison ou de certification. Le code produit `master` et la PR Windows #831 restent intacts ; aucun merge, Vercel, Lenovo ou cabinet réel. Next : confirmer la source canonique du statut feuille de soins, implémenter le plus petit chemin autorisé, démontrer les cas négatifs puis clôturer 04.3 avant 04.4.
