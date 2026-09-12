# P1 — UI multi-praticiens

## Goal

Rendre le praticien actif explicite et cohérent dans les trois surfaces cœur du cabinet — Dashboard, Agenda et Réglages / Mon Équipe — puis faire porter ce contexte par les écritures Agenda sans modifier les invariants tenant du P0.

## Succès observable

1. Un rail « Contexte clinique » est visible sur Dashboard, Agenda et Settings.
2. Les praticiens actifs sont présentés sous forme de chips lisibles et sélectionnables, sans débordement horizontal à 390 / 768 / 1280.
3. Le praticien choisi reste cohérent lors de la navigation dans la session.
4. Sur Agenda, create / check-conflicts / bulk reçoivent le `praticien_id` actif lorsque l'appel n'en fournit pas déjà un explicitement ; l'update conserve le praticien existant sauf réaffectation explicite.
5. Le comportement P0 reste autoritaire : le backend continue de valider tenant, rôle, statut actif/approuvé et conflits.
6. Un secrétaire dispose d'un fallback sûr vers le praticien principal quand la liste multi-praticiens n'est pas disponible.
7. Aucun déploiement Vercel n'est nécessaire pour la certification P1.

## BEFORE vérifié

Head baseline : `eedb1e6a57f57c016f6837f45dd06e6a671866b9`.

Run visuel : `34681249518` — success.

Viewports : 390x844, 768x1024, 1280x900.

Constats :

- Dashboard 390 : `scrollWidth=402`, soit 12 px de débordement dans le harnais direct.
- Agenda : aucun débordement, mais aucun contexte praticien explicite malgré la vue Multi disponible.
- Team Manager : aucun débordement, mais la relation entre équipe et praticien actif n'est pas visible.
- `AgendaModal` n'envoie pas lui-même `praticien_id`; le backend P0 exige pourtant ce contexte pour une assistante.

## Référence / mockup

Direction retenue : **clinical context rail** cohérent avec le langage Digital Crown existant.

- carte glass claire, bord blanc translucide, ombre douce ;
- pictogramme clinique compact ;
- titre de contexte + statut du nombre de praticiens actifs ;
- chips horizontales avec initiales, nom, activité du jour et check sur la sélection ;
- mobile : rail horizontal interne scrollable, jamais de scroll document ;
- desktop : identité à gauche, sélection praticiens à droite ;
- aucune couche décorative gratuite : la sélection pilote réellement les écritures Agenda.

## Implémentation

- `frontend/src/features/clinic/practitionerContext.ts` : état session du praticien actif.
- `frontend/src/features/clinic/ClinicPractitionerBar.tsx` : rail global + résolution de la liste via la vue multi-praticiens, avec fallback mono-praticien.
- `frontend/src/components/Layout/MainLayout.tsx` : insertion du rail sur Dashboard / Agenda / Settings et resserrement responsive des paddings.
- `frontend/src/pages/AgendaPage.tsx` : injection non destructive du contexte praticien dans create / conflict-check / bulk, conservation explicite du praticien existant lors d'un update, et mapping rendez-vous → praticien pour les conflict-check d'édition.
- `frontend/src/ClinicPractitionerUX.test.ts` : contrat frontend du contexte praticien.

## AFTER vérifié

Code HEAD certifié : `3c29f2e29b730d447aff72f81416249bdf5073f5`.

Preuves :

- Visual run `34681876692` : completed / success.
- T2 Runtime Browser `34681876693` : completed / success.
- CI principale `34681876685` : completed / success.
- Voluntary Tutorial Visual `34681876771` : completed / success.
- 9 captures AFTER produites : Dashboard / Agenda / Team × 390x844 / 768x1024 / 1280x900.
- 0 overflow horizontal sur les 9 captures.
- 0 pageerror / console error selon le gate visuel exact-head.
- aucun déploiement Vercel.

## Comparaison BEFORE → AFTER

- Dashboard 390 : 12 px d'overflow BEFORE → 0 AFTER.
- Dashboard / Agenda / Team disposent désormais d'un contexte praticien homogène et visible.
- Mobile : la sélection praticien reste confinée dans son rail scrollable, sans élargir le document.
- Desktop : hiérarchie claire entre identité clinique, praticien actif et contenu de l'écran.
- Agenda : la sélection n'est pas cosmétique ; elle pilote les nouvelles écritures et les conflict-checks tout en évitant la réaffectation silencieuse d'un rendez-vous existant.

## Score visuel P1

**9,2 / 10** sur la matrice certifiée.

Évaluation :

- hiérarchie / lisibilité : 9,3 ;
- cohérence avec le design system existant : 9,4 ;
- responsive 390 / 768 / 1280 : 9,4 ;
- densité / efficacité clinique : 9,0 ;
- robustesse UX liée au contexte praticien : 9,1.

Le score n'est pas 10/10 : le rail ajoute volontairement une couche de contexte et donc une petite hauteur fixe supplémentaire ; une éventuelle phase ultérieure pourra étudier une version compacte conditionnelle quand un seul praticien est disponible, sans remettre en cause le P1 certifié.

## Verdict

P1 UI est **certifié sur le code HEAD `3c29f2e29b730d447aff72f81416249bdf5073f5`**. La clôture Git reste à finaliser par merge de la PR #430 puis vérification de `master`.
