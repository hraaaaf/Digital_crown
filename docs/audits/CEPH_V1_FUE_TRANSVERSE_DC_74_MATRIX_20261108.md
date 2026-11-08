# DIGITAL CROWN — Céphalo V1 — Matrice FUE métier §74-D (08/11/2026)

**Décision / scope :** FUE transversal *Dossier Clinique + Bilan Orthodontique A4*, sur Desktop local, données de test exclusivement. **GOAL :** prouver les dix scénarios DC-DOS-01…04, DC-PDF-01…05, DC-E2E-01 de la roadmap canonique, et non compter les dix assertions exploratoires comme dix FUE validés.

**Source de vérité :** `docs/audits/CEPH_V1_LOT1_SCIENCE_APPROVAL_FUE_PREFLIGHT.md` §74-B/C/D, [PR #1227](https://github.com/hraaaaf/Digital_crown/pull/1227) *Draft* ; matrice datée **08/11/2026**. Les statuts ci-dessous sont des **constats de couverture probatoire**, pas des autorisations cliniques. Aucun patient réel, aucune signature de bilan simulée comme réelle et aucune archive officielle nouvelle.

## Règles de décision

- **PASS :** chaque sous-assertion du scénario §74-D a été exécutée sur le *même HEAD* avec preuve (logs, identités synthétiques, capture/document, empreinte ou résultat DB) et ses cas adversariaux sont couverts.
- **PARTIEL :** preuve technique ciblée disponible, **mais une ou plusieurs sous-assertions obligatoires** restent sans preuve. Ne jamais convertir en PASS par inférence.
- **BLOQUÉ :** un FUE complet ne peut pas être réalisé de façon sûre, p. ex. signature clinique absente, import de périphérique non certifié.
- **NON EXÉCUTÉ :** aucune tentative du scénario intégré telle que définie dans §74-D.

## État de la couverture au lancement de la tranche 1

| Scénario §74-D | Statut probatoire | Vérifié sur des sous-contrats | Preuve indispensable encore manquante |
|---|---|---|---|
| **DC-DOS-01** A/B + cabinet B, assets, URL/cache/split, purge | **PARTIEL** | E2E Cabinet réel synthétique A/B : absence de fuite des notes entre *études* (`frontend/scripts/fue-ceph-v1-fourstep-desktop.mjs`) ; `test_media_core_timeline_api.py::test_timeline_rejects_another_tenants_patient` et `test_asset_content_cannot_be_rebound_to_a_different_patient_path` existent | Véritable bascule entre **deux patients** puis cabinet B dans *toutes* les surfaces : cache/blob URL, document, split/MultiView. E2E humain + permissions réelles |
| **DC-DOS-02** import manuel / timeline / split et source unique | **PARTIEL** | `test_media_core_ingestion_api.py::test_authenticated_image_import_persists_encrypted_asset_and_thumbnail` et `test_media_core_timeline_api.py::test_timeline_lists_primary_asset_only_and_keeps_storage_secrets_private` testent l'import chiffré et un seul asset primaire | Import **radio + photo + document**, sélection du même ClinicalAsset ID dans timeline et split réel, absence de deuxième stockage |
| **DC-DOS-03** acquisition LOT06 ambiguë = quarantine/no-write | **NON EXÉCUTÉ / LOT06 HOLD** | Contrat §74-B impose la quarantaine et le refus des appareils non certifiés ; ce n'est pas une preuve d'exécution | Pipeline d'acquisition LOT06 **certifié** et tests réels rejet/no-write/idempotence. L'acquisition automatique reste désactivée |
| **DC-DOS-04** T0/T1 et deux viewers, refus source étrangère | **PARTIEL** | `test_cephalo_four_part_report.py` vérifie des provenances photo, `test_media_core_timeline_api.py` vérifie la lecture patient-scoped | Deux viewers réels T0/T1, source radio + étude corrélées, modifications simultanées isolées et source d'un autre tenant refusée en UI |
| **DC-PDF-01** quatre parties sourcées et autorité clinique | **PARTIEL** | Cabinet JWT `fourstep-unsigned-draft.pdf` + section I/II/III/IV ; `test_cephalo_four_part_report.py` vérifie études, révisions, photos et avertissements | Trace anatomique complète, provenance moulages et interprétation **confirmée par praticien** ; pas de document final autorisé |
| **DC-PDF-02** cinq modèles / paramètres cabinet / QR | **PARTIEL** | `test_four_part_a4_inherits_cabinet_theme_tokens` et `test_four_part_a4_shared_header_footer_logo_and_two_themes` vérifient héritage et **deux** modèles | Matrice visuelle **Swiss, Clinical, Royal, Modern, Heritage** sur mêmes données/viewports, en-tête/pied/QR/A4/sauts de page et signature réelle |
| **DC-PDF-03** QR sans faux identifiant + QR valide contrôlé | **PARTIEL / SIGNATURE HOLD** | `test_cephalo_four_part_report.py` vérifie la suppression d'une validation QR fictive `DOC-TEMP` ; Archive Guard refuse les nouvelles archives non signées | Archive finale **signée** autorisée et QR de validation avec permissions / révocation ; ne pas l'imiter en test sans contrat clinique |
| **DC-PDF-04** rejet données essentielles non fiables | **PARTIEL** | `test_presentation_measures_only_verifiable_typed_values`, refus des valeurs mm non calibrées côté projection, et PDF sous statut *brouillon non signé* | Chaîne complète refusant l'export **final** pour âge/normes/échelle manquants ; omission facultative non décisive prouvée |
| **DC-PDF-05** bilan diagnostic seul ou plan validé, archive immuable | **PARTIEL / SIGNATURE HOLD** | Tests Archive Guard de refus HTTP 409 et relecture historique ; notes libres maintenues non validées dans le PDF brouillon | Confirmation diagnostic et plan **distinctes**, signature liée au SHA du PDF, nouvelle version si révision, archive officielle historique conservée |
| **DC-E2E-01** Dossier→Media→Étude→I/II/III/IV→final→Dossier | **PARTIEL / CLINIQUE HOLD** | [CI Cabinet #42481152017](https://github.com/hraaaaf/Digital_crown/actions/runs/42481152017) : 10/10 **checks exploratoires** Step1→4, DDM/notes sauvées, séparation A/B et réouverture, brouillon A4 ; [Archive Guard #42481152045](https://github.com/hraaaaf/Digital_crown/actions/runs/42481152045) : refus officiel et BEFORE/AFTER | Route depuis **Dossier Clinique**, import Media Core, deux viewers/MultiView, signature persistée, archive référencée dans Dossier, revue clinique **humaine** et impression comparée |

**Verdict :** **0/10 FUE métier intégralement prouvés**, **9 PARTIEL**, **1 NON EXÉCUTÉ** dans cette première classification de couverture. Cela **n'annule pas** les 10/10 vérifications exploratoires au SHA `9c1b403243ac839a170b0f915ef3e2f026f508c5` : les périmètres sont différents. Cette matrice est une base d'audit à faire évoluer uniquement avec preuves exact HEAD.

## Exécution autorisée — tranche 1

**GOAL :** faire tourner sur la PR expérimentale les suites déjà présentes pour Media Core A/B et l'import manuel, timeline et rendu A4 :

```bash
python -m pytest \
  backend/tests/test_media_core_ingestion_api.py \
  backend/tests/test_media_core_timeline_api.py \
  backend/tests/test_media_core_c7_certification.py \
  backend/tests/test_cephalo_four_part_report.py -q
```

Le workflow `.github/workflows/ceph-p2ter-master-bridge-real-cabinet.yml` exécute ces tests sur un runtime GitHub isolé. **Un PASS de ces suites ne clôt PAS** DC-DOS-01, DC-DOS-02 ou DC-PDF-01 : seuls leurs sous-contrats testés deviennent prouvés. Le succès doit être établi sur le **HEAD après création de cette matrice**, à partir du log et de l'artefact GitHub.

**SUCCESS observable tranche 1 :** suite Media Core + A4 de test réellement terminée SUCCESS, aucun effet sur la base patient réelle, baseline du parcours Cabinet et Archive Guard toujours SUCCESS sur le même HEAD. Si rouge, diagnostic et correction en branche Draft uniquement.

**PROOF :** liens exacts des jobs, commit, log pytest, artefacts SHA-bound, liste des assertions couvertes et non couvertes. Pas de Vercel, merge, migration, activation clinique.

## Priorités suivantes (ne pas faire passer pour exécutées)

1. **DC-DOS-01** : E2E cross-patient + cross-tenant, vérification des blob URLs et de la purge MultiView/React.
2. **DC-DOS-02 puis DC-DOS-04** : un asset Media Core unique T0/T1 avec radio/étude et deux viewers Desktop isolés.
3. **DC-PDF-02** : cinq templates en A4 ; **DC-PDF-04** : intégrité des données essentielles ; puis signature/clinicien/archivage seulement après gates humains.
4. **DC-DOS-03** reste HOLD tant que LOT06 acquisition n'est pas certifié.

**Gates absolus :** clinique HOLD, sécurité indépendante HOLD, signatures officielles HOLD, patient réel NON, merge/déploiement NON. **Fichier de reprise :** ce document, associé au canonique §74–84 et à Notion.
