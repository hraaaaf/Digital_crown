# DIGITAL CROWN MOBILE — MOB-5H SUPERADMIN GOAL UI

Status: GOAL UI VERIFIED — AFTER CERTIFIED, PR PENDING
Baseline exact: `6eb93c75f91402031ecc2c8fc1f8858372a97b9b`
Branch: `ux/mobile-superadmin-mob5h`
Audit: `docs/ux/DIGITAL_CROWN_MOBILE_SUPERADMIN_MOB5H_AUDIT.md`
Proof: `docs/ux/DIGITAL_CROWN_MOBILE_SUPERADMIN_MOB5H_PROOF.md`

## Goal

Transformer la surface mobile SuperAdmin en cockpit complet, sans perte de prérogative par rapport aux capacités SuperAdmin actives du backend/desktop.

## Structure UI verrouillée et implémentée

- Vue globale
- Clients
- Essais
- Marketplace
- Opérations

La navigation reste interne à la console SuperAdmin et ne remplace pas la navigation mobile canonique.

## Principes appliqués

- pas de SuperAdmin lite;
- pas d'empilement de mutations destructives sur les cartes de liste;
- détails denses en sheet plein écran mobile;
- confirmations explicites pour revoke licence, suspend, archive, revoke trial, force sync, gouvernance globale, dispatch et autres actions sensibles;
- busy states + feedback succès/erreur;
- endpoints canoniques réutilisés, aucune logique métier dupliquée;
- step-up WebAuthn uniquement lorsque le contrat sécurité backend l'exige;
- preview fictive sans données réelles ni appels API réels.

## BEFORE vérifié

Artifact `9997848118`, baseline `6eb93c75...`.

Aux viewports 390×844, 430×932 et 768×1024, le baseline expose essentiellement clients/recherche, pack, prolongation licence et suspend/reactivate. Les autres domaines de parité sont absents.

## AFTER vérifié

Run `34139199751` — SUCCESS.
Artifact `10025281786`.
Digest `sha256:595a430c22dd8f82a3887b30b01192d6061dfc6a8857eb0cd3961694e253793a`.

Aux trois viewports:
- 0 overflow horizontal;
- 0 page error;
- 0 console error;
- 0 requête API inattendue;
- cinq sections présentes;
- contrôles critiques clients, Marketplace et opérations observés.

Inspection manuelle réalisée sur la vue globale, le détail client et le détail opération en 390×844.

Score visuel pré-merge: **9,3/10**.

## Critère de fermeture

La cible UI est atteinte sur la branche et certifiée avant merge. MOB-5H ne passe en CLOSED qu'après PR verte, merge, post-merge CI et closeout du canonique.

Aucun Vercel.
