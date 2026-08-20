# R4 + R6 — Recovery post-R7 — Closeout

Date : 2026-08-20
Repo : `hraaaaf/Digital_crown`
PR : `#193`
Branche : `settings-recovery-r4-r6-post-r7`
HEAD produit certifié : `5ac5104dae3e51cc72c22362bba5fd9b259df650`

## Goal

Restaurer les comportements certifiés de R4 Modèles documentaires et R6 Catalogue après les régressions hors scope introduites par R7, sans revert global de R7 et sans casser R5.

## Cause vérifiée

PR #178 / R7 avait modifié des surfaces appartenant à R4/R6 : renderer Settings documentaire, moteur premium, Catalogue CRUD, schéma `settings_preview`, tests et workflows associés.

Les surfaces régressées étaient byte-for-byte identiques aux baselines pré-certification :
- Catalogue : blob pré-R6 `3a93993e614445589c09b3cf2a4bcbd485960b1f` ;
- Preview documentaire : blob pré-R4 `50432b1f427008e87a3aade408cdadb2cd47bedf` ;
- Core documentaire : blob pré-R4 `ef695ba7abc0c8b6c98b3be255352996f806a1e9`.

Les BEFORE historiques R4/R6 sont donc réutilisables comme preuves exactes.

## Résultat R4

- PDF réel restauré comme source de vérité ;
- preview Settings explicite, sans régénération automatique ;
- preview isolé restauré dans `DocumentFactory` ;
- cinq modèles premium et mappings de fontes déterministes restaurés ;
- `settings_preview` restauré ;
- contrats Heritage centré et Playfair/serif restaurés ;
- implémentation R4 replacée dans `BaseTemplateCore` et `StudioControlsCore` ;
- façades R5 conservées.

## Résultat R6

- vrais formulaires CRUD restaurés ;
- absence de `prompt()` restaurée ;
- édition spécialité / acte / pathologie restaurée ;
- désactivation contrôlée restaurée ;
- store, tests et certification visuelle R6 restaurés.

## Compatibilité R5 / R7

- aucun fichier Agenda/R7 dans le diff final ;
- `backend/services/base_template.py` R5 inchangé ;
- R5 continue à surcharger uniquement `_draw_qr_code` ;
- le moteur R4 reste hérité du Core ;
- gate QR R5 exact-head vert.

## Preuves exact-head

HEAD produit certifié : `5ac5104dae3e51cc72c22362bba5fd9b259df650`.

- CI #1481 `32380900040` — **SUCCESS** ;
- R4 Document Models #21 `32380899919` — **SUCCESS** — artifact `9410944349` — digest `sha256:7328713254e85d01e30fafe5815c0b252ac2d6897b7f3e46d7a57f69fa9b385c` ;
- R4 Branding #68 `32380899866` — **SUCCESS** — artifact `9411001718` — digest `sha256:f8fa9a5e1a0c012b7626e619a337d774c0e5ea6d02a7251ecc4fe4dff4300616` ;
- R5 QR AFTER #6 `32380899991` — **SUCCESS** — artifact `9411019214` — digest `sha256:8c5725f4ac6eaf0b7162816ad13d503be8853dd04a46b90bf82ae018a2451309` ;
- R6 Visual #11 `32380900007` — **SUCCESS** — artifact `9410994197` — digest `sha256:97141b254b39088c3ee549df55f9ac4560d1288ee5fce88a86faa8c1f5437fd5` ;
- RBAC #135 `32380899868` — **SUCCESS** ;
- Read Truth #39 `32380899917` — **SUCCESS** ;
- T2 #715 `32380899946` — **SUCCESS** ;
- R11 reachability #7 `32380899937` — **SUCCESS** ;
- Patient P7 Final #14 `32380899916` — **SUCCESS**.

Backend CI initial de récupération : 2077 tests passaient avant détection du contrat Heritage R4 régressé par R7. Après restauration du contrat historique, CI #1481 est verte.

## Validation visuelle

Même grille de viewports : `1440 / 1024 / 768 / 430 / 390`.

- R4 : 5 viewports + 5 PDF premium réels inspectés ; arabe Unicode lisible ; Heritage centré ; score maintenu **9,2/10** ;
- R5 : 5 viewports sans overflow ; QR factuel intact ; score maintenu **9,4/10** ;
- R6 : 5 viewports + 5 modales inspectés ; erreurs runtime 0/5 ; score maintenu **9,6/10**.

## Statut

**CERTIFIÉ — READY TO MERGE**.

Cette récupération ne crée pas de nouveau lot produit et ne change pas l’avancement nominal de la roadmap : après merge, les lots R4 et R6 redeviennent créditables et l’état vérifié revient à **10/15 = 66,7 %**.

## Vercel

Aucun déploiement Vercel.
