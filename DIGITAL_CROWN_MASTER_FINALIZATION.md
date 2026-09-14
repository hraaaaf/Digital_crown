# DIGITAL CROWN — FINALISATION PRODUIT

**FICHIER CANONIQUE DE PILOTAGE GLOBAL — HORS CÉPHALOMÉTRIE**

Baseline de création : `master@dca24d01ca5591d4255f3ac85f79a32ab6d673c1`.

## Périmètre

Ce fichier fusionne le pilotage des chantiers Digital Crown restants en un seul programme maître.

**Exclusion explicite : la Céphalométrie reste un chantier séparé et n'entre ni dans le score global, ni dans le Next exact, ni dans les priorités de ce fichier.**

## Goal global

Obtenir un Digital Crown non-Céphalo cohérent, certifié et exploitable en cabinet réel.

## Méthode de score

Axes inclus : Document Studio 100 %, Dossier Patient UX 100 %, Clinique multi-praticiens 100 %, Portabilité 89,2 %, Mobile Terrain 70 %, Sécurité / Anti-piratage 60 %.

Calcul : `(100 + 100 + 100 + 89,2 + 70 + 60) / 6 = 86,53 %`.

**Indice global courant : 86,5 %.**

Le benchmark Competitive / Media reste un KPI séparé et n'entre pas dans ce calcul.

## État consolidé

### L1 — Document Studio — FERMÉ
P1→P6 actifs certifiés ; T1 transversal mergé via PR #465.

### L2 — Dossier Patient UX — FERMÉ
UX1-A/B PR #467 et UX1-C PR #468 mergées ; 390 / 768 / 1280 certifiés.

### L3 — Clinique multi-praticiens — FERMÉ
P3 final PR #463 mergée ; HEAD certifié `30e5c235cebdb9f4e460b03a0687856336149c08` ; merge `f16fc658dad0ee4ff67a919568359f1e90d4e2da` ; CI #3763, PostgreSQL #216 et T2 #2701 SUCCESS. Axe : 100 %.

### L4 — Portabilité — HUMAN GATE
`149/167 EP = 89,2 %`. P13 physique `0/13 EP`. Fermeture requiert Windows 11 cabinet réel + stockage hors machine + Apple Silicon + closure guard.

### L5 — Mobile Terrain — HUMAN GATE
Baseline 70 %. Gates physiques iPhone/Android/biométrie/Push restent non substituables.

### L6 — Sécurité / Anti-piratage — BLOQUÉ EXTERNE
Baseline 60 %. Accès control-plane production requis pour les mutations réelles et la chaîne OWNER/licences.

### L7 — Release / CI — ACTIF TRANSVERSE
Packaging #450/#451 mergés ; Document History #469 fermé ; P3 #463 fermé. Rechercher uniquement les dettes release/CI encore réellement ouvertes lors des closeouts suivants.

### L8 — Competitive / Media — C6 FERMÉ
- C5 reste fermé via PR #478 ; baseline visuelle certifiée C5 : **9,6/10**.
- PR #482 `feat(media): add C6 controlled smartphone capture` : **MERGED**.
- HEAD candidat C6 certifié : `b9565ed1374b9fb9e43880e09e2c303e24496408`.
- Merge squash C6 : `78be81a718980fe81a3a597456c7bf8d73c16528`.
- Base exacte avant merge : `master@4023d978f82b954ebbba9bec1c05a7bdd5e73896` ; master n'avait pas dérivé avant merge.
- Scope final C6 : exactement 3 fichiers backend ; aucun frontend, migration, workflow, configuration d'authentification ou fichier scientifique Céphalo.
- Fonctionnalité fermée : la capture photo existante du smartphone appairé et du contexte patient est persistée via le Media Core canonique en `ClinicalAsset` `PHOTO / DEVICE_CAPTURE`, sans dual-write `DocumentArchive` ; le contrat JSON mobile historique utile est conservé.
- Contrôles hérités et revalidés : JWT mobile `surface=mobile` / `kind=device_session`, utilisateur actif, tenant/employer exact, `jti` non blacklisté, appareil appairé actif et non révoqué, contexte ressource serveur lié au tenant/utilisateur/appareil, patient du tenant exact.
- Validation C6 : MIME non-image rejeté ; faux JPEG rejeté par vérification réelle de l'image ; taille > 12 MiB rejetée ; aucune écriture Media Core sur ces rejets.
- Ingestion canonique C3 conservée : détection réelle du type, hash serveur, thumbnail, stockage chiffré AES-GCM et déduplication limitée au tenant.
- Provenance : `MOBILE_RESOURCE_BRIDGE`, `SMARTPHONE_CAMERA`, contexte patient et device id ; audit `CLINICAL_PHOTO_CAPTURED` rattaché au `CLINICAL_ASSET` après commit réussi.
- Local-first : upload vers `api_base_url` du cabinet appairé ; en perte réseau la photo reste en aperçu pour retry ; aucun fallback cloud/public et aucun canal média anonyme ajouté.
- Test historique M6-A réaligné sur le Media Core : vérifie `ClinicalAsset`, `DEVICE_CAPTURE`, stockage `AESGCM_V1`, lecture contrôlée et suppression EXIF ; le legacy `DocumentArchive` n'est pas réintroduit.
- Exact-head candidat : CI #3921 **SUCCESS** ; PostgreSQL #357 **SUCCESS** ; T2 #2842 **SUCCESS** ; P7 #1466 **SUCCESS** ; M6-I #1642 **SKIPPED attendu**.
- Post-merge master `78be81a7…` : CI #3922 / run `34841456003` **SUCCESS** ; backend Tests & durcissement SUCCESS ; frontend tests & build SUCCESS ; garde production négative SUCCESS ; bridges M4-A/B/C SKIPPED car hors scope du push.
- Audit PR avant merge : reviews 0 ; threads 0 ; comments 0 ; mergeable true.
- UI/UX C6 : aucun fichier frontend modifié. Sur master mergé, `PatientMediaTimeline.tsx` conserve le blob `5a55e735c6f70f2c34df373939cfa0c5689f0bac` et `MobileContext.tsx` le blob `b35b69b3c5cda9f9dc75ad0bd72a293682a520fa`, identiques à la baseline C5 certifiée. Donc aucun nouveau score visuel C6 n'est inventé ; référence visuelle inchangée : **9,6/10**.
- Aucun déploiement Vercel.
- Le KPI Competitive global n'est pas recalculé à C6 : le gain Media `6,0 → 8,5` reste conditionné à la fermeture complète du Lot C.

## Chemin critique unique

1. **Fermer Competitive/Media C7, sans reprendre C4/C5/C6 et sans toucher au chantier scientifique Céphalo.**
2. **Exécuter les gates physiques** : Portabilité P13 puis Mobile Terrain, selon disponibilité du matériel réel.
3. **Fermer Sécurité** dès que l'accès control-plane production permet l'exécution réelle des mutations autorisées.
4. **Certification globale non-Céphalo** : master propre, CI transverse verte, docs canoniques cohérents, inventaire explicite des human/external gates résiduels.

## Next exact

**Ouvrir un nouveau lot dédié Competitive / Media C7 — certification volumétrique + cross-tenant + responsive (5 EP) ; ne pas reprendre C4/C5/C6, ne pas toucher à la Céphalométrie et ne pas déployer Vercel sans autorisation explicite.**

## Règles de continuité

- Une fenêtre = un lot principal jusqu'à son closeout, puis HANDOVER + STOP.
- Une CI en cours n'arrête pas le programme ; faire le travail indépendant restant.
- Aucun lot déclaré fermé sans preuve exacte.
- Aucun déploiement Vercel sans autorisation explicite.
- Les chantiers Céphalo ne sont ni modifiés, ni scorés, ni priorisés depuis ce fichier.

## Repères courant

- master avant merge C6 : `4023d978f82b954ebbba9bec1c05a7bdd5e73896`
- C6 PR #482 : **MERGED**
- C6 HEAD certifié : `b9565ed1374b9fb9e43880e09e2c303e24496408`
- C6 merge squash : `78be81a718980fe81a3a597456c7bf8d73c16528`
- CI candidat #3921 : **SUCCESS**
- CI post-merge #3922 : **SUCCESS**
- T2 #2842 : **SUCCESS**
- P7 #1466 : **SUCCESS**
- PostgreSQL #357 : **SUCCESS**
- UI C6 : **zéro delta frontend**, référence C5 9,6/10 conservée
- audit PR : **0 review / 0 thread / 0 comment**
- indice global : **86,5 %**
- Céphalométrie : **hors périmètre**
- prochain gate logiciel : **Competitive / Media C7 — certification volumétrique + cross-tenant + responsive (5 EP)**
- human gates : **Portabilité P13 + Mobile Terrain**
- external gate : **Security control-plane production**
