# Restauration guidée — AUDIT

Date : 2026-08-21
Repo : `hraaaaf/Digital_crown`
Statut : **AUDIT OUVERT — aucune modification produit**

## Goal

Cartographier la surface Sécurité & Backup et juger ce qui doit être gardé, simplifié, déplacé ou refondu pour obtenir une restauration guidée, sûre et compréhensible en cabinet.

## Succès

1. Inventaire des pages, composants, services, endpoints, modèles, permissions et formats de sauvegarde/restauration.
2. Identification des opérations réellement restaurables et des préconditions.
3. Analyse des risques : écrasement, tenant isolation, compatibilité de version, intégrité, pièces jointes, audit trail, rollback.
4. Cartographie UX du parcours actuel, sans modification.
5. Décision produit et roadmap du lot seulement après preuves.

## Preuve attendue

Code réel + tests + routes backend + comportement UI existant. BEFORE visuel requis uniquement si le lot passe ensuite à une modification UI/UX.

## Contraintes

- Aucun Vercel sans autorisation explicite.
- Aucun changement produit pendant cette phase d'audit.
- Aucun mécanisme de restauration ne sera déclaré sûr sans preuve d'intégrité et de rollback proportionnée au risque.
