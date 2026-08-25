# M4-D — Rendez-vous contextuel — Closeout

Date : 2026-08-25
État : CLOSED

## Goal

Depuis les vues Agenda Jour / Semaine / Mois, ouvrir le rendez-vous existant exact puis permettre son passage vers le mobile appairé via un bridge opaque, sans exposer `appointment_id`, `patient_id` ni donnée clinique dans le QR ou l’URL mobile.

## Produit livré

- PR : #245
- HEAD produit certifié : `77e253487af1dc387c79a47a537736db663cc418`
- merge master : `d42a618f3cffe6b81786a5169eefe5663a37423d`
- 1 commit produit / 10 fichiers / 0 behind avant merge
- vue Mois : clic sur un RDV existant ouvre désormais ce RDV exact ; le clic sur une case vide conserve `Nouveau Rendez-vous`
- bridge `appointment` opaque avec permission `agenda`
- existence de la ressource, tenant, utilisateur, appareil et permission revalidés côté serveur
- contexte mobile idless : `/mobile/context`
- onboarding : libellé serveur exact `Rendez-vous`
- nouveaux contrôles M4-D et cible RDV Mois >= 44 px

## Preuves

### BEFORE

Run `32839944720` — SUCCESS.

- 7/7 captures
- Jour exact : OK
- Semaine exacte : OK
- Mois : sélection perdue, ouverture `Nouveau Rendez-vous`
- contexte mobile `appointment` absent
- 0 overflow / 0 erreur runtime dans le harness

### Pré-PR

Run `32843366721` — SUCCESS.

- scope exact : PASS
- régression backend M4-A/B/C/D : PASS
- frontend build : PASS

### AFTER exact-head

Run `32843731985` — SUCCESS.

Artifact `9561522093`
Digest `sha256:73a0b544617d2ed0b5d7c3c012d3fb21d4af2b1689220ae6e19d6dea7a8fb4d1`

- exact HEAD : `77e253487af1dc387c79a47a537736db663cc418`
- 8/8 captures
- Jour / Semaine / Mois : RDV exact
- modal QR RDV
- contexte mobile exact sur 390 / 430 / 768 px
- 0 overflow
- 0 contrôle M4-D < 44 px
- comparaison BEFORE → mockup → AFTER inspectée
- score visuel : **9,6/10**

## CI exact-head

- Settings Security Visual Certification #37 : SUCCESS
- T2 Runtime Browser Certification #997 : SUCCESS
- Catalog Connected Truth Certification #270 : SUCCESS
- Patient P7 Final Certification #296 : SUCCESS
- CI globale #1837 / run `32843657028` : SUCCESS

## Limites / dette hors M4-D

M4-D ne ferme pas M4 complet. La matrice finale erreurs / retour / expiration au niveau ressource reste à certifier. Un BEFORE séparé a déjà mis en évidence un défaut réel : lorsque le backend local est inaccessible, le mobile peut afficher le message technique brut `Failed to fetch`.

Aucun Vercel.
