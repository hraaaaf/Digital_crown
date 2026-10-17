# Digital Crown — CEPH-UXCLIN-01 / R23-G11 — Deux vraies téléradios publiques, test non clinique

**2026-10-17. TEST DES FICHIERS PUBLICS / CONTRAT D'ADMISSION G10. PAS DE GOLDSET NI DE MESURE CLINIQUE.**

## Pourquoi ce sous-lot

L'utilisateur a demandé d'utiliser deux téléradiographies publiques pour tester la suite G9/G10 et de comprendre « le poste Aariz ». **Aariz** est le dataset scientifique de 1000 téléradiographies/29 repères qualifié au **LOT02**, pas le nom d'une machine. `DESKTOP-3MAJEEH` est le poste Windows de développement à distance mentionné dans `docs/handovers/V1_5_00_2_HANDOVER.md` ; `docs/audits/CEPHALO_VNEXT_LOT04_DETECTOR_SELECTION_EXECUTION.md` dit que les 2,1 Go d'Aariz y avaient été matérialisés. Cela n'implique ni que cette machine soit actuellement disponible ni que tout système doive l'utiliser.

Le test G11 se passe **sans le PC Aariz** : les fichiers JPEG publics originaux sont téléchargés dans un dossier éphémère sur le runner CI GitHub. Aucun fichier du dataset Aariz, aucune image patient privée, aucun landmark authentique ou faux et aucune extraction de données sensibles n'est publié.

## Sources originales déjà utilisées dans le produit G4

| ID | Wikimedia Commons / attribution | Taille px | SHA-1 (fichier original) | Licence |
|---|---|---|---|---|
| `anug` | [Cephalometric radiograph.JPG — ANUG, 2014](https://commons.wikimedia.org/wiki/File:Cephalometric_radiograph.JPG) | 2272×1818 | `2a284993c666790a72d0c004044b35a92534ce9d` | CC BY-SA 4.0 |
| `challiyan` | [A lateral cephalogram without true vertical.jpg — Challiyan, 2023](https://commons.wikimedia.org/wiki/File:A_lateral_cephalogram_without_true_vertical.jpg) | 1000×1255 | `66c74c588af3c54dfc581f8a870c5276c3427498` | CC BY-SA 4.0 |

Vérification croisée avec `frontend/scripts/capture-cephalo-r23g4-public-source-profiles.mjs` et les sources Wikimedia. Ces deux images et les droits des auteurs doivent être attribués ; redistributions dérivées suivent CC BY-SA. Les repères sur les anciennes captures R23-G4 sont **SYNTHÉTIQUES NON RECALÉS** sur l'anatomie, et le profil `NOT_COMPUTABLE` ne vaut pas diagnostic.

## Épreuve exécutée par G11

Le [contrat versionné](schemas/cephalo_r23g11_public_radiographs_v1.json) exige **exactement deux** images sources (URL originale, licence, attribution, taille, hash) sans prétendre à une calibration, orientation ou annotation validée. Le [script Python](../../scripts/cephalo_r23g11_public_radiograph_smoke.py) :

1. lit les octets JPEG d'origines Wikimedia téléchargés temporairement et vérifie leurs SHA-1 exacts (puis calcule des SHA-256 additionnels), leurs headers SOF et dimensions d'origine ;
2. refuse des métadonnées source contrefaites, une image remplacée, une troisième image, une licence altérée ou une étiquette `orientation_verified/calibration_verified` fictivement vraie ;
3. fait un **vrai appel au vérificateur G10**, à partir du SHA-256 de chacune des deux images réelles, dans un dossier d'essai marqué `public_demo` : **l'admission comme cas LOT02/Aariz doit échouer** (seuls les splits gelés train/valid sont autorisés ; le test original est réservé) ;
4. constate que le manifest de travail G10 a **0 cas externes réellement attachés** et `clinical_release=false`, `expert_goldset_ready=false`, `atlas33_clinical_measurements_validated=0` ;
5. sort uniquement un **JSON de preuve source NON clinique**, sans JPEG, coordonnées de repères ou identité patient, accessible en artefact Actions. Les JPEG eux-mêmes ne sont ni commités ni transmis dans les artefacts.

Commande équivalente sur machine locale **si** les deux JPEG originaux ont déjà été récupérés et identifiés :

```bash
python -m scripts.cephalo_r23g11_public_radiograph_smoke \
  --input-dir /CHEMIN/PRIVE_DOSSIER_PUBLIC_JPEG \
  --report /CHEMIN/PRIVE_SOURCE_ONLY_REPORT.json
```

## Ce que G11 ne prouve pas

- Le contraste, le rendu dans l'interface et la conformité UX desktop ont un test antérieur G4 distinct. Un test de bytes JPEG+gates G10 ne prétend pas tester une détection de 21 repères.
- Aucune image n'a une graduation mm/pixel, un étalon radiologique, une orientation anatomique reconnue par expert, des points Ricketts source-spécifiques observés, deux vrais annotateurs indépendants, ou des calculs Atlas33 validés par G11.
- Un cliché public ≠ cas enregistré dans le jeu Aariz. Les images appartiennent à des provenances distinctes et les rendus UX G4 ne doivent pas être réinterprétés comme des « annotations cliniques ».
- Tout système clinique doit rester `NOT_COMPUTABLE` sur les mesures exigeant ces preuves ; aucune mise à jour runtime, base patients, modèles, rapport, migration, Vercel ou déploiement n'est permise par cette PR.

**Acceptation G11 :** images publiques réelles SHA1/dimensions vérifiées sur le HEAD exact ; refus d'admission G10 observé pour chacune ; aucun test négatif en échec ; preuve CI tracée. **Clinique NO-GO.** Vérifier la CI au HEAD après chaque commit avant closeout.

**Roadmap :** R23-G9 ✓ registre de compatibilité → R23-G10 ✓ préparation secure intake → R23-G11 ✓/attente de CI images publiques → présence de vrais experts + vrai goldset protégé OPEN → validation Atlas33 → décision humaine indépendante.
