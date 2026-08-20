# Catalogue connecté — Goal & preuve attendue

Statut : implémentation en cours, non certifiée.

## Goal

Faire du catalogue R6 tenant-scoped la source de sélection des actes cliniques et du Master Plan sans rendre l'historique dépendant d'un tarif mutable.

## Succès

- Soin : `/api/actes/catalog/search` lit uniquement le catalogue R6 du cabinet courant.
- Soin enregistré : `libelle` + `montant` restent des valeurs copiées, jamais une relation tarifaire dynamique.
- Master Plan : un acte du catalogue préremplit nom/code/tarif ; nom et tarif restent modifiables avant ajout.
- Master Plan : la valeur finale est persistée dans un snapshot dédié et recopiée dans chaque révision immutable.
- Une modification future du catalogue ne modifie ni l'acte historique ni le snapshot du plan.
- Les étapes legacy sans snapshot restent lisibles.
- Devis : aucune réécriture produit ; le flux existant est déjà connecté au catalogue R6 et archive son payload par valeur.

## Goal visuel

Baseline exacte : Patient P7 Final Certification #20, run `32392304926`, artifact `9415451482`, digest `sha256:32a4fff11c83f9c128da0eebbb45a2d4d1fa3dfdcbbc232135365343c483440d`.

Référence visuelle préparée avant implémentation : couche compacte `Catalogue → Master Plan` au-dessus du ClinicalHub certifié, avec recherche, préremplissage, override et CTA explicite. Le ClinicalHub historique est conservé byte-for-byte dans `ClinicalHubCore.tsx`.

Critères AFTER : mêmes viewports P7 (desktop/tablette/mobile), zéro overflow horizontal, zéro erreur runtime, catalogue fail-closed, copie claire du caractère capturé du tarif.
