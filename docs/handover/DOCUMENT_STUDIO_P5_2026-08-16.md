# Document Studio — P5 Suivi Paiement Handover — 2026-08-16

## P5 — état vérifié

Engineering financier local convergé sur la branche `agent/p5-suivi-paiement-audit`.

### Corrigé
- création de plan fail-closed : total/échéances positifs, finis, bornés, libellés réels, statut initial EN_ATTENTE, somme exacte ;
- modification : statuts/montants bornés, pas de paid_date client, réconciliation exacte ;
- échéance payée non réouvrable/rechiffrable sans contrepassation ;
- suppression d’un plan bloquée dès qu’un règlement réel ou Payment lié existe ;
- TPE normalisé vers le mode carte backend ;
- suivi des plans persistés séparé du brouillon de création ;
- aucun faux toggle local `Réglé` ;
- règlement réel uniquement via `PUT /installments/{id}` + mode explicite + rechargement backend ;
- résumé payé/restant/prochaine échéance/en retard déterministe en centimes ;
- nouveau plan sauvegardé explicitement via `POST /installments/` ;
- payload de création centralisé/testé ;
- action globale Studio `Enregistrer` masquée pour P5, car le footer ne persiste pas un plan ;
- preview reste read-only ;
- rappel WhatsApp = action manuelle, pas scheduler serveur.

### Preuves locales
- backend création/update/delete : **15/15 PASS** ;
- tracking summary : **4/4 PASS** ;
- create-payload policy : **tsc --strict PASS + 8/8 assertions PASS**.

### Non exécuté / différé
- full React/Vite build ;
- smoke authentifié create → reload → payment par chaque méthode → inspection Payment DB ;
- browser 390 / 768 / desktop ;
- clavier/touch/focus dialog ;
- WhatsApp réel sur appareil ;
- ready/merge/post-merge.

Audit canonique : `docs/audits/DOCUMENT_STUDIO_P5_SUIVI_PAIEMENT_AUDIT.md`.

## Décision produit/architecture

La restructuration des montants d’un plan existant n’est pas simulée avec plusieurs updates successifs. Si requise plus tard, elle doit passer par un endpoint atomique de réallocation multi-lignes avec réconciliation globale.

## Prochaine page

### P6 — Document Libre

Objectif : recroiser l’engineering historique avec le head actuel, rechercher les régressions depuis les anciens lots P3-C→P3-H, exécuter les tests/PDF isolables sous Linux, corriger les P0/P1 puis mettre à jour la roadmap avant P7.

Points à vérifier :
- champs title/content/date/patient/header/page size/alignment ;
- toolbar non-submit ;
- preview auto et erreurs silencieuses ;
- archive/reopen ;
- dirty-state/navigation ;
- impression fraîche ;
- texte long/multipage et PDF A4/A5 ;
- permission d’émission ;
- responsive/accessibilité.

## Règles critiques
- backend autoritaire ;
- aucune écriture financière inférée ;
- preview read-only ;
- tests ciblés != certification production ;
- aucun pourcentage sans pondération roadmap validée.
