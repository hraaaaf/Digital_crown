# R7 — Horaires & Agenda — Closeout

Date : 2026-08-19
Repo : `hraaaaf/Digital_crown`
PR : `#178` — **MERGED**
Merge : `4f20832ee70fecf5878242cc1a98ef633d8be129`
HEAD produit certifié : `e45f677a44d7ad7c950efcd88d9afed17585df95`

## Goal

Faire de **Réglages → Horaires & Agenda** une configuration réellement appliquée par l’Agenda : semaine 7 jours, jours fermés, plages horaires, journée continue, exceptions/congés et refus explicites hors disponibilité.

## Résultat produit vérifié

- semaine 7 jours persistée avec fallback legacy ;
- jours fermés et exceptions CRUD ;
- `agenda_mode` retiré de l’UI active ;
- `use_tickets` retiré de l’UI active et bouton Ticket mort supprimé ;
- DailyView / WeeklyView bornés par les horaires configurés ;
- vue hebdomadaire mobile empilée ;
- clic exact-time neutralisé pendant la pause et hors plage via `isTimeWithinSchedule` ;
- backend autoritaire sur POST / PUT / bulk via `agenda_availability.py` ;
- durée complète vérifiée, y compris chevauchement de pause/fermeture ;
- schéma R7 non initialisé : comportement legacy préservé, sans DDL dans une écriture de rendez-vous ;
- bulk prévalidé avant insertion ;
- AgendaModal restitue le `detail` backend lorsqu’un rendez-vous est refusé.

## Preuves exactes du produit mergé

Toutes les gates ont terminé **SUCCESS** sur le HEAD produit `e45f677a44d7ad7c950efcd88d9afed17585df95` :

- Agenda downstream #20 — run `32247944292` ;
- Settings RBAC #120 — run `32247944286` ;
- Settings Agenda R7 Visual #28 — run `32247944586` ;
- Settings Read Truth #36 — run `32247944343` ;
- CI #1353 — run `32247944342` ;
- T2 Runtime Browser #601 — run `32247944318`.

Le delta de closeout jusqu’au HEAD PR final était documentaire uniquement ; la synchronisation avec `master` avait **zéro fichier modifié**. Le squash merge `4f20832...` a donc intégré le même produit certifié.

### Tests

- backend : **2748 passed, 7 skipped, 4 warnings** ;
- frontend : **92 fichiers de tests, 367 tests passed** ;
- `agendaR7Schedule.test.ts` : 3/3 ;
- `agendaR7Truth.test.ts` : 4/4 ;
- `agendaR7AvailabilityError.test.ts` : 1/1 ;
- build frontend production-safe : SUCCESS ;
- T2 authenticated browser matrix : SUCCESS.

### Preuves visuelles

Settings Agenda AFTER :
- artifact `9368814126` ;
- digest `sha256:8e842ae392125dff4b68e6d6ab37398d4463aa8b0fa0091c6d3bfbd857520587` ;
- 10 captures : écran principal + modale exception × 1440/1024/768/430/390 ;
- aucun défaut visuel bloquant observé ;
- modale utilisable à 390 px.

Downstream Agenda :
- artifact `9367836333` ;
- digest `sha256:b84a8b4fc3d790460e989e228885cb67f20c483c50c05634042fc863c85acb6e` ;
- 10 captures Jour/Semaine × 1440/1024/768/430/390 ;
- `scrollWidth == clientWidth` partout ;
- aucune erreur console/page.

Read Truth : artifact `9368899089`, digest `sha256:aa88423df608baa007eb9dfc95af432522a58c75b8832ef61ec4e5f3b9470960`.

RBAC : artifact `9368027180`, digest `sha256:f7739ec8d68a2b2152103b104b18969d25ff650593dddb439193fafff4e686e5`.

## Score visuel

**9,3/10**.

Forces : hiérarchie claire, cohérence desktop/tablette/mobile, états fermés/exceptions compréhensibles, modale mobile saine, aucune troncature horizontale.

Réserve : le formulaire 7 jours reste naturellement long et dense sur mobile ; il est fonctionnel mais pas minimaliste.

## Anomalies non bloquantes hors scope R7

La CI verte expose encore des avertissements existants : dépendances npm signalées par `npm audit`, warnings React `act(...)`, gros chunk PatientDetails et warnings SQLAlchemy superadmin. R7 ne prétend pas les corriger.

## Statut

**CLOSED — CERTIFIÉ — MERGED**.

Avancement chantier après merge : **5/15 = 33,3 %**.

Aucun déploiement Vercel.
