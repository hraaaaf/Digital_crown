# V1.5-04.3 — Feuille de soins déjà finalisée : retrait station fail-closed

**Statut produit : MERGED vers master le 11 octobre 2026 — FUE-0 technique prouvée sur HEAD de la PR ; FUE-I / FUE-G / terrain non certifiés.**
- [PR produit #837](https://github.com/hraaaaf/Digital_crown/pull/837) : fusionnée ; candidat exact `db2756a5de97967260c8f1e1b248beff564cdb6e`, merge commit master `db403bb4d4aee38470d537f71d39893142e1b983`.
- [CI ciblée #38128827178](https://github.com/hraaaaf/Digital_crown/actions/runs/38128827178) : **102/102 tests collectés et PASS** (suites Station care sheet, Eligibility, Patient Session, Insurance Finalization et Insurance Submission API).
- Revues contradictoires **internes** sur le même HEAD : A sécurité/provenance **8.8/10**, B QA/métier **8.6/10**, zéro BLOCKER/MAJOR dans le scope FUE-0 ; pas de reviewer humain indépendant.
- [Campagne intégrée FUE LAB #38132438594](https://github.com/hraaaaf/Digital_crown/actions/runs/38132438594), [PR #839](https://github.com/hraaaaf/Digital_crown/pull/839) encore Draft : 48 captures BEFORE/AFTER mockées, 8 autorisations simultanées sur PostgreSQL 18 isolé (1 créée, 7 dédupliquées), 30 tests assurance incluant finalisation HTTP PDF réel **sur document/template synthétique** jusqu'au retrait HTTP. Ne pas confondre ces tests avec un essai sur imprimante, NFC, Pocket ou vrai patient.
- [Post-merge PostgreSQL #38141345526](https://github.com/hraaaaf/Digital_crown/actions/runs/38141345526) exécuté sur master exact **TERMINAL SUCCESS**, avec les deux jobs verts : **Windows PowerShell 5.1 release guards** et **PostgreSQL 18 + immutable release invariants**. Closeout technique GitHub post-merge validé. Le workflow CI ciblé 04.3 n'est pas déclenché par push master : la preuve des 102 tests porte sur HEAD parent intégré sans changement de contenu dans le commit de merge.
- **Aucun déploiement Vercel, activation cabinet ni validation UX terrain autorisé par cette fusion.** Le bouton Station « Retirer un document » affiche encore « en cours de construction » ; cette PR ajoute des routes/contrats backend et pas une interface de retrait utilisable.

## Contrat d'autorité (implémenté)

- Seule la route `POST /api/documents/insurance-submissions/finalize`, après revalidation DB du patient et praticien, provenance du template, empreinte et production PDF, peut attester une finalisation serveur `STATION_CARE_SHEET_TRUSTED_FINALIZATION_V1`.
- La station ne croit pas une simple archive `AUTRE` ni des métadonnées `VALIDATED` : elle exige événement de confiance lié au SHA-256 **actuel**, métadonnées de rendu, version la plus récente, patient et tenant.
- Le **même praticien** qui a finalisé doit autoriser explicitement le retrait depuis un poste staff non-Station avec permission comptabilité ; autorisation liée à la même empreinte documentaire.
- Le retrait exige une session patient identifiée d'une station enrôlée, non révoquée, non expirée et dans le bon cabinet. Station = **lecture/retrait uniquement**, jamais édition clinique.
- Les octets PDF réellement renvoyés sont contrôlés (extension/chemin privé, taille, validation PDF, empreinte SHA-256) avant envoi, avec audit, `Cache-Control: no-store` et `X-Content-Type-Options: nosniff`.

## Limites connues et sous-lots suivants

- Historiques sans événement de finalisation : **non éligibles** ; pas de migration automatique.
- SHA et audit stockés ensemble en DB ne constituent pas une signature indépendante contre un administrateur DB malveillant. Résidus : ACL physiques / Windows, attaques de course symlink/TOCTOU, scénarios multiprocess et rendu sur les vrais documents administratifs assureurs.
- 04.3 est un **FUE-0** backend ; la station Documents reste « en cours de construction » sur mobile, tablette et bureau.
- [PR #840 — 04.4 QR/NFC](https://github.com/hraaaaf/Digital_crown/pull/840) reste Draft avec preuves backend (103 tests) et captures lab, mais FUE-I complète ouverte : origine HTTPS de handoff doit être configurée sur site, QR/NFC physiques non testés. 04.5 = impression/Pocket/QR remise ; 04.6 = audit/purge ; 04.7 = gate FUE-G adversarial final.
- Le workflow « UI Human Visual Approval » vert est un statut CI et **ne remplace pas** une observation auprès d'un patient humain.

## Chaîne de preuves et closeout

Le produit 04.3 est intégré dans master au commit `db403bb4d4aee38470d537f71d39893142e1b983`. Ne pas inférer « installable / deployed / ready for patient » depuis cette fusion. Le post-merge technique GitHub est **validé sur le merge SHA exact** (les deux jobs de certification PostgreSQL/Windows sont verts) ; les validations utilisateur FUE-I/G restent à mener. Les sous-lots en aval nécessitent leurs propres checks, leurs propres revues et accord de merge distinct.

---
