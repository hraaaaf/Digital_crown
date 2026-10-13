# V1.5-04.8-C — Ledger durable des demandes d'impression : piste parallèle

Base exacte figée : PR #849 HEAD `673e908713b6995afd68d42e8aa8abfa28b76c36` (empilée sur PR #840 encore DRAFT). Aucun merge/master/Vercel et aucun usage de données réelles.

## Objectif observable
Implémenter/tester **indépendamment** un ledger de livraison Cabinet atomique sur données synthétiques, sans dispatcher le PDF ni activer d'imprimante. La simulation CUPS-PDF existante ([run #38372453419](https://github.com/hraaaaf/Digital_crown/actions/runs/38372453419)) certifie uniquement `lp` et son output ; la chaîne Cabinet→archive→auth→ledger→spool reste à écrire et à tester.

## Entrée de confiance future
- `tenant_id`, `session_id`, `document_kind` (`care_sheet|presence_receipt`), `document_id`, `document_sha256` (64 hex), `printer_id` destination choisie, TTL et acteur/session vérifiés.
- Le ledger reçoit ces faits **depuis le backend Cabinet** après revalidation tenant/patient, éligibilité, consentement, session, SHA et `can_offer_print`. Il ne fait JAMAIS confiance au corps JSON de la borne comme preuve de clinique, d'identité ou de certificats.
- La `delivery_identity(tenant_id,session_id,kind,id,sha)` existante est **indépendante de la destination** ; la base doit lui imposer une unicité par tenant, même avec des clés d'idempotence client différentes.

## États et transitions minimales
`requested → accepted/held → (released/completed | failed | cancelled | uncertain)`. Le passage `accepted` signifie **acceptation dans la file seulement**. `completed` exige une preuve indépendante de sortie + remise à la bonne personne. En cas de crash après spool, résultat ambigu ou deadline dépassée : `uncertain/held_for_manual_review` **bloque la relance et les deux destinations**. Pas de retry automatique d'une seconde impression, même après retour `5xx` ou timeout. Réémission exceptionnelle : décision humaine/audit dédiés, pas un override caché du ledger.

## Limites contractuelles de ce chantier
Aucun `window.print()`, aucun PDF en Station, pas de `/documents/generate` au clic, pas de traitement direct du driver Windows ni de fenêtre d'impression ; l'archive vérifiée reste une intégration Cabinet future et la destination simulée ne vaut pas matériel certifié. Écrire tests concurrence PostgreSQL, snapshot/changement de statut et crash/reprise, conflits inter-destinations. Ne pas modifier registre B ni UI D ; ne brancher un endpoint que lorsque B a figé les autorisations.

## Sorties futures attendues par 04.8-D
Réponse sans clinique : `requestId`, `status` (`requested|held|accepted|uncertain|cancelled|failed|completed`), éventuellement `destination` reconnue. **Jamais** un PDF, un nom de patient, un jeton d'impression ou un secret de retrait.

## Statut
**Contrat figé, implémentation ledger et CI À FAIRE**. 04.8-E QA intégré après B/C/D, LOT10 tests physiques uniquement.
