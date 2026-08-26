# M6-D2 — Push PWA / OS device-bound

## BEFORE

La baseline visuelle est l'AFTER certifié M6-D1, immédiatement antérieur à D2.

- Run : `32901108250` — SUCCESS
- Artifact : `9583139456` (`mobile-m6-d1-after`)
- Digest : `sha256:e3b30c86210e99c7f9adc49a8ff23be1efeb80924b4af7a56a9561ccc7d689a9`
- Viewports : 390×844, 430×932, 768×1024
- État : sheet Notifications sans contrôle Push OS.

## Goal

Ajouter des notifications OS PWA réelles sans affaiblir M6-D1 : chaque souscription est liée au `MobilePairedDevice`, à l'utilisateur et au cabinet réellement authentifiés ; un appareil révoqué ne reçoit plus rien ; le payload verrouillé écran reste générique et sans donnée patient.

## Succès observable

1. Web Push standard, pas dépendance FCM navigateur propriétaire.
2. HTTPS/secure-context obligatoire ; iOS exige l'app ajoutée à l'écran d'accueil.
3. Permission demandée uniquement depuis le bouton utilisateur.
4. Subscription backend liée à `device_id + user_id + employer_id` et jamais choisie depuis une valeur client.
5. Envoi exclut appareils révoqués, utilisateurs inactifs et alertes non autorisées RBAC.
6. Notification OS : aucun nom patient, montant, motif ou contenu d'alerte ; clic vers le contexte mobile authentifié.
7. Cibles UI ≥48 px, zéro overflow 390/430/768, zéro erreur runtime.
8. Désactivation locale invalide immédiatement la capacité navigateur ; le serveur purge aussi les endpoints 404/410.

## Cible visuelle

Référence : `.audit/mobile-m6-d2-mockup.svg`.

- Le sheet D1 est conservé.
- Une seule carte `Push OS` apparaît sous l'en-tête.
- État normal : `Alertes hors écran` + CTA `Activer les notifications OS`.
- État actif : `Push OS activé` + CTA secondaire `Désactiver sur cet appareil`.
- États bloqués : HTTPS requis / installation écran d'accueil / permission refusée, sans faux CTA.
- Microcopy permanente : `Aucune donnée patient dans la notification OS.`
