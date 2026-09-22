# PC-05 — Patient notifications — UI target

Date: 2026-09-20

## Goal

Ajouter une surface de notifications Patient Companion compacte, calme et immédiatement compréhensible sans transformer la Home en cockpit staff.

## Reference

Réutiliser la grammaire visuelle déjà certifiée de Patient Companion:
- carte blanche / fond doux;
- rayon 1.5rem;
- label uppercase discret;
- typographie forte pour le titre;
- contrôles tactiles >= 48 px;
- primary uniquement pour l'action principale;
- états d'attente en ambre;
- aucune information clinique sensible sur une éventuelle surface OS.

Ne pas copier le cockpit staff MOB-5C: le patient doit voir des actions simples et contextualisées, pas un centre d'exploitation.

## Target layout

1. Header compact
   - kicker: "À ne pas manquer"
   - titre: "Notifications"
   - compteur "N à traiter"
   - icône Bell passive + bouton Settings 44/48 px

2. Cards
   - badge de priorité: Action requise / Rappel / Information
   - titre court
   - message déterministe issu de la vérité métier
   - échéance si pertinente
   - deux actions seulement: Lu / 24 h
   - aucun bouton ne disparaît avant ACK cabinet

3. Préférences
   - disclosure à la demande
   - grille 2x2 des quatre catégories canoniques
   - bouton d'enregistrement séparé
   - microcopy explicite: réglage inchangé tant qu'ACK cabinet absent

4. Empty/loading/offline
   - empty: "Tout est à jour"
   - disabled: synchronisation requise
   - pending ACK: ambre, sans claim de succès

## Visual acceptance

Same-viewports:
- 360x800 Chromium
- 390x844 Chromium
- 360x800 WebKit
- 390x844 WebKit

Mandatory:
- no horizontal overflow;
- controls >= 48px where actionable;
- no text collision/truncation on title/message;
- settings panel remains readable at 360px;
- visual hierarchy does not overwhelm Agenda/Consent Vault;
- severe visual score target >= 9.0/10; residual cross-module density belongs to PC-FINAL.

## Truth boundary

- "Lu", snooze and preferences become authoritative only after durable ACCEPTED cabinet ACK.
- relay pending keeps prior UI state.
- no "livré", "confirmé", "enregistré" before ACK.
