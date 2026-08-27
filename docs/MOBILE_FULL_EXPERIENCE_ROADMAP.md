# Digital Crown — Mobile Full Experience — Roadmap canonique

Date de réalignement : 2026-08-24
Dernière mise à jour vérifiée : 2026-08-27
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

**État : CLOSED côté produit/logiciel.** Tous les lots M6 prévus sont intégrés et les contrats logiciels agrégés sont certifiés. La certification globale Mobile reste ouverte uniquement sur les preuves terrain/appareils physiques décrites plus bas.

### Fondation visuelle M6

- **M6-G0 — Glass system mobile premium : CLOSED** — PR #249, HEAD certifié `d5c13f02233304c809984052ff518b1e78807a6a`, merge `1dd5de04602e3a0e4cdc97c690cabe1d06ea5d66`, closeout `docs/MOBILE_M6_G0_GLASS_SYSTEM_CLOSEOUT.md`, score visuel 9,4/10. Glass structurel sur onboarding/dashboard/contextes, CTA et inputs préservés, high-contrast opaque, reduced transparency et fallback sans backdrop-filter certifiés.
- **M6-G1 — Motif clinique + bottom navigation premium : CLOSED** — PR #251, HEAD certifié `feb8bfc33b6385ed14dae9d1d5e56cb5edd53ae4`, merge `7544da907781de063037661b31b06f102370d5db`, closeout `docs/MOBILE_M6_G1_CLINICAL_MOTIF_NAV_CLOSEOUT.md`, score visuel 9,7/10. Motif nodal + courbes d'arcades abstraites, capsule active fluide, targets 52 px, `aria-current`, high-contrast et reduced-motion certifiés.

### Lots métier M6

- **M6-A — Photo clinique contextuelle : CLOSED** — PR #252, HEAD certifié `24dcdc5543f68fd31b65a4facfa824f4a51cfbd8`, merge `5657ce7dfa529b39aaae2e562399938524bc43bd`, closeout `docs/MOBILE_M6_A_CLINICAL_PHOTO_CLOSEOUT.md`, score visuel 9,7/10. Capture/picker depuis le Patient exact, preview avant confirmation, upload lié au `context_key` sans `patient_id`, archivage `PHOTO_CLINIQUE`, validation réelle du média, limites 12 MiB / 50 MP, EXIF retiré et revalidation tenant/user/device/permission certifiés.
- **M6-B — Scan de documents contextuel : CLOSED** — PR #253, HEAD certifié `2eccb8710ae511f53282825f631d11ccddfbeb45`, merge `72d96ab2f796748fa5d1c7b4da008047ae7a6b17`, closeout `docs/MOBILE_M6_B_DOCUMENT_SCAN_CLOSEOUT.md`, score visuel 9,7/10. Scan 1–8 pages depuis le Patient exact, preview multipage, upload lié au `context_key` sans `patient_id`, PDF serveur archivé `DocumentArchive/AUTRE`, limites média certifiées et assemblage mémoire-safe page par page avec PyMuPDF.
- **M6-C — Validation / signature au fauteuil : CLOSED** — PR #254, HEAD certifié `a07ed396dae3af26b5a57170b8e0e42a67ccff41`, merge `7c8983d6da48c95de3798c72f7bce130ab3afb51`, closeout `docs/MOBILE_M6_C_CHAIRSIDE_SIGNATURE_CLOSEOUT.md`, score visuel 9,7/10. Targets ≥48 px, canvas responsive DPR, signature vide bloquée UI + serveur, PNG strictement validé et borné, re-signature interdite, devis signés exclus, ownership tenant et permission conservés.
- **M6-D1 — Centre de notifications mobile : CLOSED** — PR #256, HEAD certifié `cdac655b20b54e3a3cb7262fd1b5a634c9a30ede`, merge `101a6059919739bd508cd5e9fd26b5e33c9ca529`, closeout `docs/MOBILE_M6_D1_NOTIFICATION_CENTER_CLOSEOUT.md`, score visuel 9,6/10. Vérité `ProactiveAlert`, badge + bottom sheet, actions `Lu` / `+24 h`, stale-race fail-safe, filtrage RBAC des alertes financières et AFTER 390/430/768 certifiés.
- **M6-D2 — Push PWA/OS device-bound : CLOSED** — PR #258, HEAD certifié `23c402bbac770f6dd1deacaf88c48bdb3f1710ea`, merge `bad5a21f7729001e54f36ed69876ff0f91030c77`, closeout `docs/MOBILE_M6_D2_PUSH_PWA_OS_CLOSEOUT.md`, score visuel 9,7/10. Web Push standard device/user/tenant-bound, révocation fail-closed, RBAC conservé, payload OS sans PHI, VAPID privé persistant, HTTPS LAN et AFTER 390/430/768 certifiés. La réception OS réelle sur vrai iPhone/Android reste un gate de la certification finale globale.
- **M6-E — Communication patient mobile (appel + WhatsApp) : CLOSED** — PR #261, HEAD certifié `3c1ae523c7ced679f3b14a614d6b1ab1cfd58819`, merge `3dc875f1816244fc567b58197f9cee23afc2199b`, closeout `docs/MOBILE_M6_E_PATIENT_COMMUNICATION_CLOSEOUT.md`, score visuel 9,8/10. Appel `tel:` conservé sans inventer d'indicatif, WhatsApp uniquement avec numéro international explicite, aucune donnée patient/clinique préremplie, cibles 64 px et AFTER 390/430/768 certifiés.
- **M6-F — Partage mobile contextuel sûr : CLOSED** — PR #263, HEAD certifié `b5b349606fecb805fd5902189298bf30c238a2a0`, merge `731e1efc1b22c823cb6763d28dc551c974b1301d`, closeout `docs/MOBILE_M6_F_CONTEXTUAL_SHARE_CLOSEOUT.md`, score visuel 9,8/10. Partage natif limité au fichier Document déjà autorisé, `ShareData` file-only, nom générique, aucun URL/token/`context_key`/texte/titre ajouté par l’application, fallback Télécharger et AFTER 390/430/768 certifiés. Le document lui-même peut contenir des données patient ; sa destination reste choisie explicitement dans le share sheet OS.
- **M6-H — Imagerie panoramique mobile plein écran : CLOSED** — PR #265, HEAD certifié `da5c30c34f263e97cf65f6d741eb5869d8d6a717`, merge `9ed2694a327e65ca823f63e4a161a98168d27856`, closeout `docs/MOBILE_M6_H_PANORAMIC_VIEWER_CLOSEOUT.md`, score visuel 9,7/10. Viewer in-app 100dvh, zoom 1×–4×, pan, pinch, contrôles mono-pointeur ≥52 px, `inert`, Escape/focus restore et aucune requête réseau supplémentaire ; AFTER 390/430/768 certifié via M4-B exact-head.
- **M6-I — Biométrie / Passkey : CLOSED** — PR #272, HEAD produit/harness certifié `52357569dacd82604d77318fd933502368969b9f`, merge `41c1a4f894801a8ee5a1635b7ff1f457f9f852bd`, closeout `docs/MOBILE_M6_I_BIOMETRIC_PASSKEY_CLOSEOUT.md`, score visuel 9,7/10. WebAuthn/passkey user+tenant+device-bound, `userVerification: required`, challenge one-shot, session UV courte memory-only, coffre PRF + AES-GCM et révocation backend autoritaire ; AFTER 390/430/768 et frontière verrouillée certifiés. Face ID/Touch ID/biométrie Android réels restent des preuves terrain globales.

### Audit des capacités M6 restantes

- **Consultation rapide dossier patient : couverte par les lots certifiés existants.** Le contexte Patient exact M4-A, les actions M6-A/M6-B et la communication M6-E fournissent déjà la surface rapide prévue ; aucun nouveau lot produit n’est justifié.
- **Actions rapides au fauteuil : couvertes par les lots certifiés existants.** Agenda, appel/WhatsApp, photo, scan et signature sont déjà présents et certifiés ; aucun lot supplémentaire n’est créé artificiellement.
- **Mode portrait / plein écran imagerie : CLOSED via M6-H.**
- **Biométrie : CLOSED via M6-I.** Les contrats WebAuthn/passkey et la frontière logicielle sont certifiés ; la présentation biométrique réelle reste un gate terrain de la certification complète.

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

**État : certification logicielle obtenue, certification terrain ouverte.** Le candidat `5c1a505c94cb6e168c4c272914530616aa60cabe` a passé le run `33056672222` : backend mobile ✅, frontend fondations + M6 ✅, build ✅, gate agrégé ✅. La CI générale post-merge M6-I #1917 est également verte. Le checkpoint détaillé est `docs/MOBILE_FULL_EXPERIENCE_SOFTWARE_CERTIFICATION.md`.

Cette preuve ne simule pas Face ID, Touch ID, biométrie Android ni réception Push réelle sur appareil ; elle ne ferme donc pas la certification globale.

## Ordre canonique restant

1. Certification terrain sur vrai iPhone + Android, incluant biométrie réelle, réception Push réelle et parcours critiques finaux.
2. Closeout global Mobile Full Experience seulement après validation de ces gates.

## Avancement

Aucun pourcentage global n'est publié ici : la roadmap originale ne définit pas de dénominateur pondéré permettant un % honnête. L'état est suivi par gates explicites.

Aucun Vercel sans autorisation explicite.
