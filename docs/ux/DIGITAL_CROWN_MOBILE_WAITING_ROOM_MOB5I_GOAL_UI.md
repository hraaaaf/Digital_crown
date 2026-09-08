# DIGITAL CROWN — MOB-5I Salle d’attente — Goal UI

## Goal
Rendre la salle d’attente réellement exploitable sur mobile à partir du modèle `Appointment` canonique existant, sans dupliquer le métier ni inventer de données.

## Succès observé
- distinction `EN_SALLE_ATTENTE` / `PLANIFIE` livrée ;
- flux `PLANIFIE → EN_ATTENTE → EN_COURS → TERMINE` disponible dans le contrat mobile autorisé ;
- vue Salle d’attente avec heure de RDV et `ticket_number` quand présent ;
- aucune durée d’attente inventée ;
- tenant scope / permission `agenda` préservés ;
- aucune nouvelle table ;
- 390×844 / 430×932 / 768×1024 : 0 overflow, 0 erreur page, 0 erreur console ;
- score visuel **9.3/10**.

## Preuves
- BEFORE `34168710412` — SUCCESS ;
- AFTER `34169388445` — SUCCESS ; artifact `10035225974` ;
- PR `#367` mergée au SHA `e2522a6d8b4794e64253eb4af36500e18cd87b40` ;
- post-merge master `34170398551` — SUCCESS ;
- closeout PR `#369` : CI `34170522549` SUCCESS, T2 `34170522692` SUCCESS.

Aucun déploiement Vercel.

Statut : `GOAL ACHIEVED — DONE / MERGED / CLOSED`.
