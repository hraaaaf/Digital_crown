# P1 — UI multi-praticiens

## Goal

Rendre le praticien actif explicite et cohérent dans les trois surfaces cœur du cabinet — Dashboard, Agenda et Réglages / Mon Équipe — puis faire porter ce contexte par les écritures Agenda sans modifier les invariants tenant du P0.

## Succès observable

1. Un rail « Contexte clinique » est visible sur Dashboard, Agenda et Settings.
2. Les praticiens actifs sont présentés sous forme de chips lisibles et sélectionnables, sans débordement horizontal à 390 / 768 / 1280.
3. Le praticien choisi reste cohérent lors de la navigation dans la session.
4. Sur Agenda, create / update / check-conflicts / bulk reçoivent le `praticien_id` actif lorsque l'appel n'en fournit pas déjà un explicitement.
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
- `frontend/src/pages/AgendaPage.tsx` : injection non destructive du contexte praticien dans create / update / conflict-check / bulk.

## AFTER attendu

Même matrice 390x844 / 768x1024 / 1280x900, mêmes trois écrans, avec :

- 9 captures produites ;
- 0 overflow horizontal ;
- 0 pageerror / console error ;
- contexte praticien lisible aux trois tailles ;
- comparaison BEFORE / AFTER et score visuel avant certification.
