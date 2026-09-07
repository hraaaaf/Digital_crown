# DIGITAL CROWN — MOB-5I Salle d’attente — Proof

## Goal
Rendre la salle d’attente exploitable sur mobile depuis le modèle `Appointment` canonique, sans duplication métier ni métrique inventée.

## Baseline
- master de départ : `fd19dab006d46f274946fd932927b9ac4821d3ec` ;
- `EN_SALLE_ATTENTE` existait en DB mais était converti en `PLANIFIE` côté mobile ;
- `ticket_number` existait en DB mais n’était pas exposé dans le snapshot mobile.

## BEFORE — VERIFIED
- run : `34168710412` — SUCCESS ;
- artifact : `10035019049` ;
- digest : `sha256:add8126ca80cc347365732da80a766549840fe16cadafc572e424aff0c479873` ;
- viewports : 390×844 / 430×932 / 768×1024 ;
- HTTP 200 : 3/3 ;
- page errors : 0 ;
- console errors : 0 ;
- horizontal overflow : 0/3 ;
- waiting-room surface : absente 3/3 ;
- waiting-room navigation entry : absente 3/3.

## Implémentation
- état mobile `EN_ATTENTE` ↔ `AppointmentStatus.EN_SALLE_ATTENTE` ;
- `ticket_number` enrichi à partir des Appointment tenant-scoped ;
- GET `/snapshot` et GET `/appointments` remplacés par une façade qui délègue au moteur mobile existant, déchiffre/enrichit/rechiffre ;
- PATCH statut canonique conservé ;
- vue `WaitingRoomView` dérivée de `Snapshot.appointments` ;
- entrée secondaire dans `Plus`, bottom-nav principale inchangée ;
- Agenda permet `PLANIFIE → EN_ATTENTE` ;
- `Au fauteuil` utilise `EN_COURS` ;
- aucune durée d’attente ; aucune nouvelle table ; aucun déploiement Vercel.

## Tests versionnés
- backend : `backend/tests/test_mobile_waiting_room.py` ;
- frontend : `frontend/src/features/mobile/__tests__/waitingRoomMob5i.test.tsx` ;
- AFTER : `frontend/scripts/capture-mobile-waiting-room-mob5i-after.mjs`.

## Certification en cours
Premier run `34169261174` : job contrat non exploitable, échec d’environnement avant tests car le workflow avait utilisé `backend/requirements.txt` et pycairo ne trouvait pas Cairo. Le workflow a été réaligné sur le setup éprouvé de la CI générale.

Recertification exacte :
- run : `34169388445` ;
- HEAD de lancement : `11421e20913c90517cee5da7d7f2414ac2311e3d` ;
- statut au moment de cette écriture : pending/running ;
- aucune conclusion produit ne doit être tirée avant résultat des jobs contrat + AFTER.

## Gate de fermeture
MOB-5I ne peut être déclaré CLOSED qu’après :
1. contrat backend/frontend vert ;
2. AFTER 390/430/768 vert et artifact inspecté ;
3. comparaison visuelle + score ;
4. CI PR générale utile verte ;
5. merge produit exact ;
6. post-merge master vert ;
7. canonical/closeout cohérents.

Statut : `NOT CLOSED — CERTIFICATION RUNNING`.
