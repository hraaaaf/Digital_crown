# DIGITAL CROWN — MOB-5I Salle d’attente — Audit

## Baseline auditée
Master de départ : `fd19dab006d46f274946fd932927b9ac4821d3ec`.

## Faits vérifiés

### Modèle métier existant
`AppointmentStatus` contient déjà :
- `PREVU` ;
- `EN_SALLE_ATTENTE` ;
- `EN_FAUTEUIL` ;
- `TERMINE` ;
- `ANNULE`.

`Appointment.ticket_number` existe déjà. Aucune nouvelle table n’est nécessaire pour matérialiser l’état Salle d’attente.

### Contrat mobile BEFORE
Dans `backend/routers/mobile_legacy.py` sur la baseline :
- `_MOBILE_TO_BACKEND_STATUS` ne connaissait que `PLANIFIE`, `EN_COURS`, `TERMINE`, `ANNULE` ;
- `_BACKEND_TO_MOBILE_STATUS` transformait `EN_SALLE_ATTENTE` en `PLANIFIE` ;
- `/snapshot` exposait les rendez-vous sans `ticket_number` ;
- le PATCH `/appointments/{appointment_id}/status` refusait tout statut hors vocabulaire mobile initial.

Conséquence vérifiée : un patient déjà en salle d’attente côté métier était indistinguable d’un patient seulement planifié dans l’expérience mobile.

### Frontend mobile BEFORE
`frontend/src/features/mobile/Dashboard/types.tsx` :
- `ApptStatus = 'PLANIFIE' | 'EN_COURS' | 'TERMINE' | 'ANNULE'` ;
- aucun meta-status Salle d’attente.

`MobileDashboard.tsx` :
- aucune tab/vue `waiting-room` ;
- Agenda restait la seule surface opérationnelle des rendez-vous.

## BEFORE certifié
- workflow : `.github/workflows/mobile-waiting-room-mob5i-before.yml` ;
- run principal : `34168710412` — SUCCESS ;
- artifact : `10035019049` ;
- digest : `sha256:add8126ca80cc347365732da80a766549840fe16cadafc572e424aff0c479873` ;
- viewports : 390×844, 430×932, 768×1024 ;
- HTTP 200 sur 3/3 ;
- pageErrors = 0 ; consoleErrors = 0 ; horizontalOverflow = false sur 3/3 ;
- aucune surface Salle d’attente et aucune entrée dédiée sur 3/3.

## Implémentation certifiée
Backend :
- `EN_ATTENTE` mappe vers `AppointmentStatus.EN_SALLE_ATTENTE` ;
- le reverse mapping conserve exactement `EN_ATTENTE` ;
- façade `mobile_waiting_room.py` réutilise les GET mobiles canoniques, enrichit uniquement `ticket_number` sous tenant scope, puis rechiffre le payload ;
- POST/DELETE/PATCH existants ne sont pas remplacés.

Frontend :
- `ApptStatus` et `STATUS_META` connaissent `EN_ATTENTE` ;
- Agenda permet `PLANIFIE → EN_ATTENTE` ;
- vue `WaitingRoomView` dérivée du snapshot ;
- entrée `Salle d’attente` dans `Plus`, avec badge si compteur > 0 ;
- `ticket_number` affiché seulement s’il existe ;
- action `Au fauteuil` envoie `EN_COURS` ;
- aucune durée d’attente inventée ;
- bottom-nav principale conservée à 5 destinations.

## Tests ajoutés
- `backend/tests/test_mobile_waiting_room.py` : mapping exact, unicité des routes GET/PATCH et ticket nullable ;
- `frontend/src/features/mobile/__tests__/waitingRoomMob5i.test.tsx` : filtrage, ticket et transition `Au fauteuil`.

## Incident de certification diagnostiqué
Le premier job contrat du run `34169261174` a échoué avant pytest pendant `pip install -r backend/requirements.txt` : `pycairo` ne trouvait pas Cairo. Cet incident était un défaut de workflow, pas une preuve produit.

Le workflow a été réaligné sur le setup Python éprouvé de `.github/workflows/ci.yml`.

## Certification finale pré-merge
- run exact : `34169388445` — SUCCESS ;
- product cert HEAD : `11421e20913c90517cee5da7d7f2414ac2311e3d` ;
- backend contract : SUCCESS ;
- frontend contract : SUCCESS ;
- frontend build : SUCCESS ;
- AFTER 390×844 / 430×932 / 768×1024 : SUCCESS ;
- artifact : `10035225974` ;
- digest : `sha256:efa961010bb3c1d189f8447c99a70d5dfaf42c893f49fd8a4db558b5dbccbd50` ;
- score visuel : **9.3/10**.

## Merge produit
- PR : `#367` ;
- HEAD final PR : `d6a234a24fbc3a64a69763688322de31fa38f7ba` ;
- CI générale PR : `34169598948` — SUCCESS sur tous les jobs utiles ;
- merge exact : `e2522a6d8b4794e64253eb4af36500e18cd87b40`.

## Post-merge
- run master : `34170398551` ;
- état au moment de ce closeout : `pending`.

Statut : `MERGED — PRE-MERGE CERTIFIED — POST-MERGE PENDING — NOT YET CLOSED`.
