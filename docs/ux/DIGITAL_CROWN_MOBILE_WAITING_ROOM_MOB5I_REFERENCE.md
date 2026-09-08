# DIGITAL CROWN — MOB-5I Salle d’attente — Référence UI

## Référence livrée et certifiée

Navigation : accès secondaire `Salle d’attente` dans `Plus`, avec badge uniquement si au moins un patient attend. La bottom-nav principale reste `Aujourd’hui / Patients / + / Assistant / Plus`.

Vue livrée :
- compteur Salle d’attente ;
- liste dérivée de `Snapshot.appointments` ;
- ordre par heure de rendez-vous ;
- ticket seulement s’il existe ;
- état vide explicite ;
- CTA `Au fauteuil` → `EN_COURS` / backend `EN_FAUTEUIL` ;
- touch targets >= 44 px ;
- aucune durée d’attente inventée.

Agenda : `Planifié → En salle d’attente` via le statut existant.

Anti-patterns évités : aucune collection métier locale, aucun calcul d’attente artificiel, aucune sixième destination principale, aucune action contournant le serveur.

## Preuves
- AFTER `34169388445` — SUCCESS ;
- artifact `10035225974` ;
- 390×844 / 430×932 / 768×1024 sans overflow ni erreur page/console ;
- score visuel **9.3/10** ;
- PR produit `#367` mergée au SHA `e2522a6d8b4794e64253eb4af36500e18cd87b40` ;
- post-merge master `34170398551` — SUCCESS ;
- closeout PR `#369` : CI `34170522549` SUCCESS et T2 `34170522692` SUCCESS.

Statut : `REFERENCE DELIVERED / CERTIFIED / CLOSED`.
