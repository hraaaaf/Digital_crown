# Digital Crown — Mobile Full Experience — Roadmap canonique

Date de réalignement : 2026-08-24
Dernière mise à jour vérifiée : 2026-08-25
Source : roadmap originale retrouvée par le produit/utilisateur. Ce document remplace les reconstructions ultérieures qui avaient artificiellement introduit un « M7 ».

## Goal

Faire de la version mobile une vraie surface produit, pas simplement le desktop comprimé à 390 px.

Résultat recherché :

- toutes les pages utiles fonctionnent réellement sur mobile ;
- aucune fonction critique ne disparaît silencieusement ;
- les workflows sont adaptés au tactile ;
- le QR depuis le poste cabinet ouvre le bon contexte directement sur mobile ;
- desktop et mobile restent cohérents sans forcer une parité inutile lorsque l'usage mobile mérite une UX différente.

## Succès global

- 100 % des routes / sous-pages / overlays inventoriés ;
- chaque fonctionnalité classée Garder / Améliorer / Repenser / Supprimer du mobile ;
- aucun P0/P1 mobile ;
- parcours critiques certifiés sur 390 / 430 / 768 px + vrai iPhone + Android ;
- QR → mobile : contexte, auth, retour arrière, expiration et erreurs validés ;
- BEFORE → cible → AFTER pour chaque lot visuel.

## M0 — Cartographie totale

Inventorier routes, pages, composants interactifs, overlays, formulaires, tableaux, uploads/caméra, PDF/documents, imagerie, interactions clavier/souris, endpoints, permissions, comportements desktop-only et QR codes.

Livrable : matrice Desktop ↔ Mobile ↔ Backend.

**État : substantiellement réalisé.** Inventaire mobile initial établi ; l'exhaustivité 100 % reste à recroiser lors de la certification finale.

## M1 — Audit fonctionnel mobile page par page

Tester non seulement l'affichage mais les workflows complets : chargement, navigation/retour, CRUD, formulaires/clavier, dropdowns, dates, uploads, caméra, partage, tableaux, scroll, sticky, overlays, erreurs backend, loading/empty, offline, refresh, orientation, safe areas, permissions et session/auth.

**État : baseline réalisée.** 8 surfaces × 3 viewports = 24 captures ; score baseline 6,6/10 ; aucun overflow/runtime error dans le harness. Les parcours finaux complets restent à recertifier après corrections.

## M2 — Comparaison Desktop ↔ Mobile

Classification canonique :

- KEEP
- ADAPT
- REDESIGN
- MOBILE-FIRST
- DESKTOP ONLY
- REMOVE

**État : réalisé.**

## M3 — Audit UX/UI mobile

Score /10 :

- Fonctionnel 25 %
- UX tactile 20 %
- Hiérarchie / lisibilité 15 %
- Ingénierie / robustesse 20 %
- Performance 10 %
- Accessibilité + sécurité 10 %

Seuils : 9–10 garder ; 8–8,9 polish ; 7–7,9 améliorer ; 5–6,9 redesign ciblé ; <5 refaire.

**État : réalisé pour la baseline et les lots corrigés.** Le score global final n'est pas encore certifiable.

## M4 — Mobile Bridge contextuel

Desktop → QR → token opaque temporaire → mobile → auth/pairing → résolution du contexte → ouverture exacte de la fonctionnalité.

Exemples obligatoires :

- Patient précis → ce patient ;
- radio/panoramique précise → cette radio ;
- document précis → ce document ;
- rendez-vous précis → ce rendez-vous.

Le QR ne contient ni nom patient, ni donnée médicale, ni identifiant sensible exploitable. Token court TTL, révocable, usage unique, lié user/session/appareil, contrôlé backend et journalisé. Cas erreurs : expiré, réseau, non-autorisé, non-pairé, ressource supprimée, backend local inaccessible.

**État : CLOSED.** Les quatre ressources obligatoires et la matrice finale erreurs / retour / expiration sont certifiées.

Fondation certifiée via PR #234 / merge `ea0f6e41f055b90d8bceabb5e100dbe008230f16` : utilisateur cible + destination serveur autorisée, QR sans PHI, pairing device-bound, destination revalidée, E2E Finance 390/430/768.

Sous-lots ressource certifiés :

- **Patient contextuel : CLOSED** — PR #238, merge `4ad243013c2d999f014302252e5e2bb9f2184c29`, closeout `docs/MOBILE_M4_A_PATIENT_CONTEXT_CLOSEOUT.md`, score visuel 9,5/10.
- **Radio panoramique contextuelle : CLOSED** — PR #243, merge `f0c120868c71948bf835758f472c741179e7b128`, closeout `docs/MOBILE_M4_B_PANORAMIC_CONTEXT_CLOSEOUT.md`, score visuel 9,5/10.
- **Document contextuel : CLOSED** — PR #244, merge `8a11a452cc7a3b14964a1908a32589700a4cb6f7`, closeout `docs/MOBILE_M4_C_DOCUMENT_CONTEXT_CLOSEOUT.md`, score visuel 9,6/10.
- **Rendez-vous contextuel exact : CLOSED** — PR #245, HEAD certifié `77e253487af1dc387c79a47a537736db663cc418`, merge `d42a618f3cffe6b81786a5169eefe5663a37423d`, closeout `docs/MOBILE_M4_D_APPOINTMENT_CONTEXT_CLOSEOUT.md`, score visuel 9,6/10.
- **Matrice finale erreurs / retour / expiration : CLOSED** — PR #247, HEAD certifié `03d1150a8071088890bdfd431e845d55e7930f98`, merge `d8561c441987047db4cf67ddb6b764c33a9d72f3`, closeout `docs/MOBILE_M4_FINAL_RESOURCE_MATRIX_CLOSEOUT.md`, score visuel 9,7/10. Expiration sans consommation, usage unique, révocation, suppression, non-pairé, backend local inaccessible et retour Agenda certifiés ; aucune erreur réseau technique brute n'est exposée.

## M5 — Architecture mobile

Comparer :

A. responsive web complet ;
B. PWA installable ;
C. natif uniquement si caméra, notifications, biométrie, background ou API OS le justifient réellement.

Direction initiale : responsive certifié → PWA → natif seulement si besoin démontré.

**État : conception/architecture réalisée ; décisions à confirmer par les preuves finales de terrain.**

## Corrections prioritaires après M5

Ces lots ont été historiquement nommés M6.1–M6.4, mais ils correspondent aux corrections prioritaires de la roadmap originale, pas au M6 mobile-first complet :

- sécurité pairing/session mobile : CLOSED ;
- offline truth / queue unique : CLOSED ;
- Patient/RDV canonique + Agenda UX : CLOSED, score 9,6/10 ;
- bridge destination / onboarding tactile : CLOSED, score 9,5/10 ; fondation M4 certifiée.

## M6 — Mobile-first réel

Exploiter ce que le téléphone peut faire mieux :

- scan QR ;
- caméra patient/document ;
- photos cliniques ;
- scan de documents ;
- consultation rapide agenda ;
- validation/signature ;
- notifications ;
- appels/WhatsApp si pertinent ;
- partage ;
- consultation rapide dossier patient ;
- actions rapides au fauteuil ;
- biométrie ;
- mode portrait/plein écran imagerie.

**État : ACTIVE.** M4 est CLOSED ; M6 peut maintenant être audité et exécuté en réutilisant les fondations sécurité/offline/contextuelles certifiées.

Premier lot à auditer : **M6-A — Photo clinique contextuelle**, depuis le contexte Patient exact. Aucun changement produit n'est crédité tant que BEFORE → Goal → mockup → AFTER n'est pas certifié.

## Certification complète finale — pas un « M7 »

Après M6 :

- 390 / 430 / 768 ;
- vrai iPhone ;
- Android réel ;
- session/navigation/patient/agenda/imagerie/documents/paiements/réglages ;
- QR Desktop → Mobile contexte exact ;
- online → offline → reconnect ;
- auth/expiration/révocation/permissions ;
- aucun P0/P1 ;
- BEFORE → cible → AFTER pour chaque lot visuel ;
- score global Mobile Digital Crown seulement quand la couverture est suffisante.

## Ordre canonique restant

1. Exécuter M6 Mobile-first réel, en commençant par M6-A Photo clinique contextuelle.
2. Certification complète finale sur émulation + appareils physiques.
3. Closeout global Mobile Full Experience.

## Avancement

Aucun pourcentage global n'est publié ici : la roadmap originale ne définit pas de dénominateur pondéré permettant un % honnête. L'état est suivi lot par lot jusqu'à définition d'un système de gates explicite.

Aucun Vercel sans autorisation explicite.
