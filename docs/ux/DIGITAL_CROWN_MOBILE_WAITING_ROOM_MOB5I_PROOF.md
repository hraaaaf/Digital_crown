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

## Certification dédiée — VERIFIED
Premier run `34169261174` : job contrat non exploitable, échec d’environnement avant tests car le workflow utilisait `backend/requirements.txt` et pycairo ne trouvait pas Cairo. Le workflow a été réaligné sur le setup éprouvé de la CI générale.

Recertification exacte :
- run : `34169388445` — SUCCESS ;
- product cert HEAD : `11421e20913c90517cee5da7d7f2414ac2311e3d` ;
- backend contract : SUCCESS ;
- frontend contract : SUCCESS ;
- frontend build : SUCCESS ;
- AFTER 390/430/768 : SUCCESS ;
- artifact : `10035225974` ;
- digest : `sha256:efa961010bb3c1d189f8447c99a70d5dfaf42c893f49fd8a4db558b5dbccbd50` ;
- report : `invalidCount = 0` ;
- HTTP 200 : 3/3 ;
- page errors : 0 ; console errors : 0 ; horizontal overflow : 0/3 ;
- waiting surface/count/patient : présents 3/3 ;
- ticket `#12` : présent 3/3 ;
- CTA `Au fauteuil` : présent 3/3 ;
- entrée `Salle d’attente` + badge dans `Plus` : présents 3/3.

## Comparaison visuelle BEFORE → AFTER
BEFORE : Agenda générique, aucun espace permettant d’isoler les patients réellement présents.

AFTER :
- hiérarchie immédiate `Salle d’attente → compteur → patient → ticket/heure → Au fauteuil` ;
- aucune sixième destination ajoutée à la bottom-nav ;
- lisibilité stable à 390×844, 430×932 et 768×1024 ;
- aucun chevauchement ou overflow observé ;
- densité volontairement faible sur tablette quand la file ne contient qu’un patient, sans information artificielle ajoutée pour remplir l’espace.

Score visuel : **9.3/10**.
Réserve : la vue est volontairement très épurée lorsqu’un seul patient attend ; une densité plus riche n’est justifiée qu’avec de vraies données métier supplémentaires, notamment un timestamp d’arrivée canonique.

## PR produit
- PR : `#367` ;
- base : `master` ;
- branche : `ux/mobile-waiting-room-mob5i` ;
- merge interdit tant que la CI générale utile de la PR n’est pas verte.

## Gate de fermeture
MOB-5I ne peut être déclaré CLOSED qu’après :
1. CI PR générale utile verte ;
2. merge produit exact ;
3. post-merge master vert ;
4. canonical/closeout cohérents.

Statut : `CERTIFIED PRE-MERGE — PR #367 OPEN — NOT CLOSED`.
