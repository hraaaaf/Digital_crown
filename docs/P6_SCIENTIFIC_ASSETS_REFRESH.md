# P6 Scientific Assets Refresh

Status: **CEPH TECHNIQUE FERMÉ — PANO READY FOR CLINICIAN ANNOTATION — PRIVATE BINARY RETENTION OPEN — WINDOWS PACKAGING UNBLOCKED FAIL-CLOSED**.

Ce sous-lot ne remplace pas Portability P6 et ne crédite aucun EP.

## Goal
Fournir à P6 une vérité scientifique exploitable : assets autorisés et reproductibles quand ils existent, et capacités explicitement indisponibles/fail-closed quand ils ne sont pas encore qualifiés. Aucun benchmark ne devient un claim clinique par simple enthousiasme administratif.

## Céphalométrie — gagnant technique
Candidat : `DC-Ceph-UNet29Q4 / Aariz v1`.

- training `32876308676` — SUCCESS ;
- evidence commit `1da113b8776aa2b57e42ac194f12b7a48b01558c` ;
- dataset Aariz v1, DOI `10.6084/m9.figshare.27986417.v1`, CC BY 4.0 ;
- dataset SHA256 `d9fa872b36065dac9615cfcad0c7512c450fe2d86a1839cdec4cbe001def33ea` ;
- ONNX SHA256 `809f1d3d2347d2a34f57d4a3415bb319c29f8a25c325d41160e5f28d4e5dadad` ;
- taille `7,624,307 bytes` ;
- contrat `[1,1,512,512] -> [1,29,128,128]`, opset 17 ;
- direct-20 held-out : MRE `1.232893 mm`, SDR2 `83.1333%`, SDR4 `97.2667%` ;
- `clinical_claim=false` ;
- `Occ_Ant` / `Occ_Post` non synthétisés ; Wits fail-closed.

Protocole clinique : `docs/P6_CEPHALOMETRY_CLINICAL_VALIDATION_PROTOCOL.md`.

### Boundary produit
Le moteur produit actuel `backend/services/sota_vision_service.py` attend un autre contrat : image couleur 1024×1024, 38 heatmaps / 38 landmarks. Le gagnant 29 points / 512 grayscale **ne doit donc pas être copié sous `model.onnx` ni embarqué silencieusement dans P6**. Un adapter produit et les gates cliniques restent nécessaires avant wiring.

## Binaire céphalo — récupération exacte
La récupération du binaire exact est prouvée sans réentraînement :

- bridge `32911633368` — SUCCESS ;
- artifact `9586717545` ;
- digest artifact `sha256:3ed73e3d39325d5b880e72264ac2a8a25996aa5eaef7bedd1a14b76d9b03ec55` ;
- SHA modèle revalidé `809f1d3d2347d2a34f57d4a3415bb319c29f8a25c325d41160e5f28d4e5dadad` ;
- taille revalidée `7,624,307 bytes`.

Cette preuve ferme la récupération, **pas la rétention privée**.

## Rétention privée — OPEN / EXTERNAL GITHUB GATE
Cible : `hraaaaf/DigitalCrown-assets`, branche `training/p6-ceph-unet29`.

Preuves :
- `32911260037` a échoué sur le workflow public historique car `P6_ASSET_TOKEN` était absent ; aucune copie privée n’a eu lieu ;
- le workflow privé a ensuite été isolé avec un smoke minimal ne contenant qu’un `echo` ;
- commit privé `7022d34608be268c3b364963bd2de833b53ecbad` ;
- run privé `32911736812` — FAILURE avant toute step, `steps=null`.

Conclusion : le runner Actions du repo privé est actuellement inutilisable avant exécution de nos steps. Ne pas relancer aveuglément le même workflow. La rétention privée reste non prouvée.

Un bundle exact de rétention peut être déposé manuellement dans le repo privé puis vérifié par SHA. Cette rétention est une conservation scientifique ; elle **n’est plus un prérequis au build Windows**, puisque le build P6 n’embarque aucun poids non qualifié.

## Panoramique — contrat Phase A
Le produit cible **tooth localization + FDI enumeration**. La pathologie automatique reste hors scope Phase A ; la sémiologie clinique reste praticien/déterministe.

## Mendeley V3 — first-party truth
Dataset `73n3kz2k4k.3`, DOI `10.17632/73n3kz2k4k.3`, record CC BY 4.0.

- inventaire `32910249394` — SUCCESS ;
- sémantique `32910743873` — SUCCESS ;
- 111 fichiers / `84,254,649` octets ;
- 107 images metadata ; 25 avec géométrie source ; 772 régions ;
- `annotations.json` SHA256 `b6de2c396cb76758227562798141a00fb5d769f9d8f9eb3919470f4ff23578bd` ;
- 540 régions ont une clé `Teeth`; les 540 valeurs sont `""` ;
- 0 token dentaire ; 0 code FDI ; 0 région FDI ;
- `direct_fdi_ground_truth_ready=false`.

Le miroir ancien limité à trois images était incomplet. La source first-party confirme néanmoins plus fortement la conclusion utile : **aucune vérité FDI source**.

## Pack FDI clinicien — READY
Un pack d’annotation reproductible a été construit sans inventer de FDI ni d’orientation :

- builder `scripts/p6_mendeley_fdi_annotation_pack.py` ;
- workflow `.github/workflows/p6-mendeley-fdi-annotation-pack.yml` ;
- HEAD `6f7614f23b793dd6804d6c7d770f62928a3a09f0` ;
- run `32912109975` — SUCCESS ;
- artifact `9586914372` ;
- digest `sha256:a72599acf4b96b3d8519f174614feca3cec011dddce0dcc594f01ac4c656ea09` ;
- 107 images ; 25 avec propositions géométriques ; 772 propositions ;
- FDI clinicien attribué `0` ; orientation confirmée `0` ; split attribué `0` ;
- ledger SHA256 `42950b89eb2856b8b4c9302837ea95a170aec5b11257d15a06ed3ae619122cad` ;
- source manifest SHA256 `f59fb925d9e33123300fcd984edb6091e6353205e6b9ef5b0a549a4b5ce8cebd`.

Le protocole canonique est `docs/P6_PANORAMIC_FDI_ANNOTATION_PROTOCOL.md`. Le prochain gate pano est **humain clinique** : orientation → validation/édition géométrie → FDI → déduplication/splits → double review test → adjudication. Aucun entraînement lourd avant ces gates.

## Packaging P6 — UNBLOCKED FAIL-CLOSED
La décision packaging est désormais de ne distribuer **aucun poids scientifique non qualifié**.

Candidat Windows :
- PR de certification `#259` ;
- branche `portability/p6-windows-packaging-final-20260826` ;
- base `portability/p10-update-engine` ;
- préparation produit `247179c04064031bfedce9a673e2318290add46d` ;
- commit final de certification `6634f9296d077309487ce6e23801ae65158a5c78` ;
- `protobuf==5.29.6` + `pip check` ;
- `DigitalCrown.spec` ne collecte plus `panoramic_model.onnx`, `ceph_weights.pth` ni un SOTA weight ;
- le self-test frozen rejette ces poids s’ils réapparaissent et impose `cephalo_sota=deferred`, `cephalo_legacy=external`, `panoramic=external` ;
- marqueurs attendus : `P6_SCIENTIFIC_PACKAGE_POLICY=FAIL_CLOSED_NO_WEIGHTS` et `P6_SCIENTIFIC_CAPABILITIES=FAIL_CLOSED`.

Aucun Vercel.

## Next exact
1. Laisser le **run Windows exact-head** de `6634f929...` être la seule certification heavy du candidat ; aucun micro-push pendant ce benchmark.
2. Si vert : inspecter artifact installateur + logs des gates → closeout P6 → merge selon les preuves.
3. En parallèle hors packaging : clinicien annote le pack pano ; la rétention privée céphalo peut être faite manuellement puis SHA-vérifiée quand le repo privé le permet.
4. Le wiring clinique des modèles reste séparé et ne doit pas être présenté comme acquis par le packaging.

Portability : **65/162 = 40,1 %**, P6 = **0/8 EP** tant que le run Windows/closeout n’est pas certifié.
