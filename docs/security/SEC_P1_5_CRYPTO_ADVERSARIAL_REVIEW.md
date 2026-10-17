# SEC-P1.5 — Revue adversariale interne du vérificateur Ed25519

**État : EXPERIMENTAL / DRAFT. Pas de validation crypto indépendante externe.**

Base : [SEC-P1.4 PR #948](https://github.com/hraaaaf/Digital_crown/pull/948),
qui n'est elle-même PAS une licence commerciale. Ce sous-lot garde le
vérificateur dans `scripts/security`, sans raccordement à
`backend.services.license_service`, sans émetteur, sans clé privée
permanente, sans modification du backend ni autorisation produit.

## Perspective A — cryptographe adversarial (revue indépendante interne)

### Défauts découverts dans le code de référence P1.4

1. **MAJOR — Unicode malformé hors domaine de rejet contractuel** :
   `len(envelope_json.encode("utf-8"))` s'exécutait avant tout
   `try` ; un texte Python contenant un surrogate isolé entraînait
   `UnicodeEncodeError` non converti en `LicenseRejected`.
   Correction : validation de longueur UTF-8 isolée, rejet fail-closed.
2. **MAJOR pour la politique temporelle — future last_online_at** :
   le payload signé pouvait déclarer une vérification en ligne
   postérieure à `trusted_now` sans refus si `not_before` était antérieur.
   L'émetteur est supposé honnête, mais un lease mal émis ne doit pas
   contourner la logique de fraîcheur. Correction : refuser cet état,
   en exigeant toujours `trusted_now` issu d'une autorité fiable.
3. **MINOR — bornes temporelles inclusives** : `trusted_now > expires_at`
   et `> offline_until` acceptaient une licence à la seconde exacte de
   son expiration. Correction : dates de fin exclusives `>=`.
4. **MINOR — contexte de vérification type-confus** :
   manifeste de clés ou ensemble de clés révoquées non conformes
   pouvaient lever des exceptions techniques avant rejet contractuel.
   Correction : validation explicite des types avant accès.
5. **LIMITATION REQUIRED — pas de trusted time/epoch physique** :
   une horloge ou un snapshot local contrôlé peut rejouer un
   lease Ed25519 pourtant légitime. Ce test ne résout pas le problème :
   architecture KMS/TPM/service en ligne à arbitrer.
6. **LIMITATION REQUIRED — binaire client patchable** :
   un attaquant contrôlant le PC peut modifier le code de vérification
   lui-même. La signature empêche la falsification de claims dans un
   vérificateur honnête, pas l'intégrité d'un EXE non attesté.

### Tests ajoutés

20 tests de scénario utilisant une clé privée Ed25519 créée puis perdue
**uniquement en RAM** : enveloppe valide, surrogates non appariés,
`last_online_at` futur et exactement au présent, seuils exacts
subscription/offline, contexte manifeste et clés révoquées mal typés,
revocation epoch, tenant/device replay, modification des droits et fenêtre
offline, feature invalide, enveloppe legacy sans signature et absence
d'identifiants de cabinet dans les erreurs.

Les 37 tests hérités de P1.4 doivent aussi rester verts sous Windows et
Linux au **même SHA**, ainsi que le garde statique de non-raccordement.

## Perspective B — architecture produit / sécurité clinique (revue interne)

**Décision proposée** : ne pas intégrer ce moteur à la production avant
preuve E2E et accord explicite. Le runtime actuel combine Firebase et un
coffre local chiffré sous secret cabinet, avec 72h de grâce offline.
Ce coffre n'est pas une signature éditeur. L'application traite
principalement les licences expirées en bloquant les mutations tout en
laissant passer des lectures, MAIS le droit de consultation, d'export,
de sauvegarde et de restauration de **toutes** les données patient
n'est pas certifié dans chaque parcours ni sur mobile.

**Séparation impérative** : le chiffrement SQLCipher et les clés de
récupération doivent rester indépendants de la licence commerciale,
y compris après expiration, déconnexion ou révocation du cabinet.
Les opérateurs restent soumis à authentification, RBAC, Station,
traçabilité et confidentialité patient ; aucun accès public en secours.

## Blocage SEC-P0 documenté

Le constructeur legacy `scripts/build_exe.py` sur master peut encore
embarquer `firebase_creds.json` dans une distribution. [SEC-P0
#898](https://github.com/hraaaaf/Digital_crown/pull/898) avait déjà un
correctif mais reste sur base obsolète. [La PR séparée SEC-P1.5
#949](https://github.com/hraaaaf/Digital_crown/pull/949) propose un
fail-close de ce script basé sur le master actuel. Elles sont des
**alternatives**, pas deux patches à fusionner ensemble.

Ne pas confondre ce correctif avec l'activation Ed25519 du produit.

## Gates

- **EXPERIMENTAL** : original 37/37 + nouveaux 20/20 + guard static PASS
  sous Python 3.12 Windows/Linux sur SHA exact ; logs GitHub requis.
- **REQUIRED pour diffusion commerciale** : revue crypto par personne
  réellement indépendante, implémentation émetteur HSM/KMS, trusted time,
  révocation/rotation, mécanisme d'identité appareil robuste,
  vrai backend/main et Station, continuité patients et export/restore
  testé y compris en mode licence invalide, security release provenance,
  nettoyage builder legacy, signature Windows et GO propriétaire.
- **HORS SCOPE** : toute ouverture Firebase, signature réelle, licence
  vendue, matériel/installation clinique, publication d'EXE, merge,
  déploiement ou modification de visibilité GitHub.

Le statut `CONVERGED` commercial n'est pas revendiqué. Les scores de
revue interne doivent rester séparés des certifications indépendantes.
