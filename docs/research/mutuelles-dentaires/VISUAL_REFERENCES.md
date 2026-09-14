# Références visuelles — Mutuelles dentaires

Date : 2026-09-14.
Statut : RESEARCH ONLY. Ce fichier sert à retrouver immédiatement les trois modèles visuels lors d’une reprise de chantier.

## 1. CNSS — VALIDÉ CABINET
- Organisme : CNSS / DAMO.
- Formulaire : `Feuille de soins dentaires`.
- Référence : `610-1-04` ; Réf. ANAM `1.2.03.01`.
- PDF de référence cabinet : `https://dentiste-rabat.com/wp-content/uploads/2023/03/610-1-04_2.pdf`
- Statut : `VERIFIED_CABINET_REFERENCE / PRIMARY_LOCK_PENDING`.
- Validation : praticien utilisateur, 2026-09-14.
- Repères visuels : formulaire bilingue FR/AR, CNSS en tête, bloc assuré, bénéficiaire, INP chirurgien-dentiste, type de soins, entente préalable, signatures.

## 2. Mutuelle des FAR / DMFAR — VALIDÉ CABINET
- Formulaire de référence : `Feuille de Mutuelle FAR 2021-1`.
- Copie publique utilisée pour validation : `https://fr.scribd.com/document/1025435428/Feuille-de-Mutuelle-FAR-2021-1`
- Portail institutionnel : `https://mutuelle.far.ma`
- Statut : `VERIFIED_CABINET_REFERENCE / PRIMARY_LOCK_PENDING`.
- Validation : praticien utilisateur, confirmée le 2026-09-14.
- Repères visuels : `Feuille de maladie`, page `ORDONNANCE`, page `SOINS ET PROTHESE DENTAIRE (INPE)`, tableau Date / Position dent / Nature des travaux / Coefficient / Honoraires, schéma dentaire, INPE/cachet/signature.

## 3. CNOPS — RÉFÉRENCE INSTITUTIONNELLE IDENTIFIÉE
- Page institutionnelle : `https://www.cnops.org.ma/fr/infopratiques`
- Copie PDF visuelle secondaire facilement récupérable : `https://docteurtarikrhafli.wordpress.com/wp-content/uploads/2020/10/cnops-feuille-de-soins-dentaire.pdf`
- Statut : `VERIFIED_INSTITUTIONAL_PAGE / BINARY_HASH_PENDING`.
- À la reprise : récupérer le binaire exact depuis CNOPS si possible, comparer visuellement à la copie secondaire, calculer SHA-256 et conserver le nombre de pages/version.

## Règle de reprise
Ne pas relancer une recherche générique de modèles avant d’avoir ouvert ces références. CNSS et FAR ont déjà reçu une validation métier cabinet. CNOPS possède déjà une page institutionnelle identifiée ; le travail restant est le verrouillage du binaire, pas la redécouverte du formulaire.

## Règle de sécurité
`VERIFIED_CABINET_REFERENCE` signifie : bon modèle pour le workflow réel du cabinet selon validation du praticien. Cela ne signifie pas automatiquement `VERIFIED_PRIMARY`. Conserver les deux notions séparées.
