# LOT06-N — checkpoint C conditional freshness LAB (synthetic only)

**2026-10-16 | EXPERIMENTAL | DRAFT stacked on PR #899 | NOT PHYSICAL | clinical NO-GO.**
This lab implements a deliberately **volatile** in-process C checkpoint fixture, a signed C anchor and a conditional B/C-head classifier. Its objective is to demonstrate one narrow statement: a full rollback of B's SQLite DB *with the old still-valid B signing key* is detectable **if and only if** an authentic **current** C checkpoint remains intact and independent. The test harness owns BOTH private keys and ALL state. Hence it does not establish actual independent custody, durability, a monotonic hardware counter, WORM, secure transport to C or operational B9 protection.

## Scope and source
- Changes only under `tools/imaging_gateway/checkpoint_c_lab.py`, synthetic tests and CI. No clinical API, application DB, workstation or backend code.
- Bases: [LOT06-M authority ADR](V15_06_M_DURABLE_AUTHORITY_ADR.md), [LOT06-N loopback LAB](V15_06_N_INDEPENDENT_WITNESS_SYNTHETIC.md), and [LOT06-M HUMAN GATE](V15_06_M_HUMAN_GATE_DECISION_PACKET_V1.md).
- Separate PR head, branched from `81d0a6c1fb7cd7761396495d17e5cd4276f7d2b5` (#899). Never infer that #899's old green runs prove this newer head.

## Synthetic protocol assumptions (not design completion)
1. B's `durable_cas_lab.apply` creates an accepted CAS+receipt (signed receipt under TEST B key) on a disposable SQLite file. `SyntheticCheckpointC.anchor(receipt)` verifies authority, epoch, scope, pinned B signer, contiguous `before_seq/before_mac` and exact successor, then signs C checkpoint `(seq,mac,op_id,hash(receipt),hash(previous C checkpoint),witness_pin)`. The full receipt bytes and per-op proof exist only in-memory. An identical replay returns the same signed proof; gap/fork/other key fails closed. The signed historical proof is **NOT a fresh assertion of C state**.
2. `classify_verified_head` requires a **freshly challenged, signed B HEAD envelope** verified under the pinned B public key and a C-signed checkpoint under a different pinned key. It outputs `UNKNOWN_NO_INDEPENDENT_CURRENT_C_LAB` on absent proof; `B_ROLLBACK_DETECTED_LAB` when B sequence is lower; `PENDING_C_ANCHOR_LAB` when B is ahead; `SAME_SEQ_FORK_REFUSED_LAB` when heads differ; otherwise `MATCH_LAB_NOT_GLOBAL_FRESHNESS`, **never DECIDED/COMMITTED, patient ACK or PHYSICAL PASS**.
3. The comparison **assumes** `C_packet` truly represents C's CURRENT trusted high-watermark. The model deliberately does not implement/enforce that assumption. A valid replayed older C checkpoint can match restored older B, demonstrating that **signing C proofs is not sufficient**. A compromised/rolled-back C or common admin domain defeats the claimed independence. Before any use outside LAB, this remains a design BLOCKER.
4. The C fixture is *not* transactionally coordinated with B. A B commit followed by C timeout must remain `PENDING_ANCHOR`; rollback/restore and partial loss require an independently designed production protocol and a separate human decision. No clinical availability claim.

## Test contracts
`test_checkpoint_c_lab.py` tests:
- synthetic signed genesis; sequential proof chain; exact receipt idempotence; replay/gap refuse; wrong C pin, tampered signed checkpoint, wrong B receipt or scope refused;
- missing C or B proof => unknown; B head signed but ahead of C => pending; signed B fork => conflict; old nonce => refuse;
- **B9 negative**: copy B SQLite at sequence 1, commit B seq2, anchor C seq2, restore B from seq1 and retain valid B signer; fresh valid signed B head seq1 is correctly labeled `B_ROLLBACK_DETECTED_LAB` against C seq2;
- **counterexample**: replay old genuine C seq1 proof as well => B seq1 and C seq1 produce `MATCH_LAB_NOT_GLOBAL_FRESHNESS`. This is a negative result, not a safety success. No external WORM / freshness is proven.
- all patients/media/scope are random synthetic data in disposable temporary paths; no service is created or connected to a clinical environment.

## CI classification, physical boundary and exit
- [synthetic C workflow](../../.github/workflows/v15-06n-checkpoint-c-synthetic.yml): Windows + Ubuntu Python 3.11, checkpoint C tests plus original independent B witness tests and LOT06-M SQLite CAS regression on the **same new head**. The run result is authoritative only once retrieved with exact SHA and per-job/test counts.
- REQUIRED for this branch LAB: those three test collections and tests not skipped; green CI is not a physical or architectural approval. Legacy imaging CI may run on PR's temporary merge ref and must not be mislabelled exact-head.
- **LOT10 EXCLUSIVE**: A/B/C real machines, HSM, OS/NTFS/SSD durability, independent-admin reality, C WORM lock & restore, TPM counter, real LAN/power-cut, B0–B9 physical injections, operators, PHYSICAL PASS/NO-GO. Map to LOT10 10.1/10.4/10.7/10.8 and 10.3 where restores overlap. Retain the existing LOT10 13-SP baseline; any additional complexity requires independent LOT10 planning decision. NO pilot hardware in LOT06-N.
- D-STRICT real independence and `current-C` authentic freshness **UNPROVEN**. Security/reliability independent reviewers NOT present. LOT06 global NOT CONVERGED; HUMAN GATE physical PENDING; clinical NO-GO; no release, purchase, patient, merge, Vercel or cabinet installation.

## Known adversarial edges
- A captured C signature is replayable if the verifier relies only on a caller-provided C packet. `MATCH_LAB_NOT_GLOBAL_FRESHNESS` must not be reinterpreted as an authorization.
- B/C signer and witness DB share one CI runner: their separate logical identities do not constitute separate administrative or rollback domains.
- The checkpoint fixture's updates are volatile, in-process and non-atomic with the B CAS transaction. Its integrity does not survive hostile restore or power loss as a promised property.
- True HSM Ed25519 private key protection and reliable per-decision immutable C checkpoint acknowledgement remain implementation feasibility questions. Real validation exclusively LOT10.

## ADR §3 / §8 and LOT06-N contract reconciliation — C challenged HEAD, v0.2

**Two distinct challenges are necessary but insufficient.** B's already-existing `DC06N_SYNTHETIC_V1` HEAD carries a signed challenge. New `DC06N_C_HEAD_SYNTHETIC_V1` C HEAD now signs its *own* caller-supplied 32-hex challenge plus the current in-memory C anchor in a separately domain-separated envelope `DC06N|checkpoint-C-HEAD|synthetic-v1`. `verify_challenged_c_head` checks shape, exact challenge, C public pin, signature, nested signed anchor and B key pin/scope. `classify_challenged_heads` requires both, then delegates the state relationship to the historical-only B/C comparator. **This proves challenge binding of C's claim, not global freshness of C's state.**

| ADR demand / adverse case | LAB observation | Invariant status |
| --- | --- | --- |
| Fresh B signed query bound to authority/epoch/scope/challenge | `verify_response` on B `HEAD_ONLY` | Synthetic cryptographic binding only |
| Fresh C signed query plus independently pinned C identity | C challenge signature verified against supplied pin; pin provenance is not independently demonstrated | **Missing physical enrollment and anti-rollback store** |
| B lower than C checkpoint after B DB+same-key rollback | `B_ROLLBACK_DETECTED_LAB` with intact C | Conditional LAB negative proof only |
| B ahead of C, including B commit before C anchor | `PENDING_C_ANCHOR_LAB`, never clinical ACK | Synthetic classifier only |
| Equal B and C heads | `MATCH_LAB_NOT_GLOBAL_FRESHNESS`; NOT `COMMITTED` | No current-C or receipt-reconciliation proof |
| Malicious replay of previous C HEAD *packet* against NEW nonce | `C_HEAD_CHALLENGE_BINDING_REFUSE` | Synthetic replay binding only |
| **B and C both restored**, C still has valid old key and signs *new* challenge | `MATCH_LAB_NOT_GLOBAL_FRESHNESS` — **undetected rollback** | **B9 BLOCKER persists** |
| Receipt, manifest, op_id and previous C checkpoint linkage | C signed anchor carries `receipt_sha256`, `op_id`, `prev_checkpoint_sha256`; fixture checks *on anchor advance* | B/C equality classifier checks only `seq/mac`, not full current receipt history; **NOT a COMMITTED proof** |
| C signer failure between B commit and C state update | sign first, mutate synthetic C state only afterward; regression | In-process behavior only, not C/WORM durable ack |
| True Windows/NTFS SSD power-off, independent operators, HSM/WORM lock | Not used and not exercised | **LOT10 EXCLUSIVELY** |

**No approval by a green classification.** The "B current" evidence and "C current" evidence are both signed responses in a harness that controls keys, DB, the source of challenges and recovery snapshots. A returned old signed C anchor **or** a freshly signed C HEAD over a restored old C state remains a counterexample. Even if both report the same seq/mac, the local journal/media/manifest and exact B/C full receipts must be reconciled independently before any future COMMITTED or clinical ACK; not implemented here.

**Gate placement:** all real-device, true-WORM/TPM, cross-admin recovery, unplug/power-cut, physical B0–B9 and installation work stays in existing LOT10 10.1/10.3/10.4/10.7/10.8. LOT06-N remains design + CI LAB only; no new LOT10 sub-lot and no automatic 13-SP increase.

## v0.3 — Réconciliation des reçus B/C, preuve synthétique non autorisante (2026-10-16)

**Écart identifié :** les HEAD B et C peuvent partager la même paire `(sequence, mac)` malgré des décisions différentes ; l'ancre C transporte `op_id` et `SHA-256(bytes du reçu B)` mais le comparateur v0.2 ne les rapprochait pas. Un verdict `MATCH_LAB_NOT_GLOBAL_FRESHNESS` ne constitue donc même pas une concordance de reçus.

**Contrat expérimental `reconcile_challenged_receipt` :**
1. Vérifier les HEAD B et C chacun sous leur défi frais, signature et pin fourni (modèle LAB) via `classify_challenged_heads`. Retourner immédiatement toute divergence : `B_ROLLBACK_DETECTED_LAB`, `PENDING_C_ANCHOR_LAB`, `SAME_SEQ_FORK_REFUSED_LAB`, `UNKNOWN`.
2. Genesis `seq=0` n'a **aucun** reçu B : `MATCH_GENESIS_LAB_NOT_AUTHORITY`, jamais une autorisation. Pour tout `seq>0`, absence de preuve courante de `LOOKUP` B signée => `UNKNOWN_B_CURRENT_RECEIPT_LAB`.
3. Exiger `LOOKUP` sous un **troisième défi**, lié au même `scope` et à l'`op_id` du checkpoint C déjà signé. Vérifier la signature, l'identité et la réponse `DECIDED_LAB_ONLY`; refuser `HISTORICAL_ONLY`, tout `UNKNOWN_OP` et une paire `(seq,mac)` du LOOKUP différente du HEAD B de référence.
4. Vérifier la signature Ed25519 et les octets canoniques du reçu B transmis par LOOKUP, puis comparer son `authority, epoch, scope, op_id, before_seq, after_seq, after_mac` au HEAD B, à l'epoch du laboratoire et à l'ancre C. Comparer enfin **l'empreinte SHA-256 des octets complets du reçu** au `receipt_sha256` signé par C.
5. Si et seulement si ces contrôles LAB réussissent, classifier **`MATCH_B_C_RECEIPT_LAB_NOT_AUTHORITY`**. Ce nom n'exprime **ni fraîcheur C anti-rollback**, ni cohérence transactionnelle entre B et C, ni authenticité d'administration/custody, ni intégrité de la chaîne clinique/média A, ni autorisation médicale. Il reste interdit de convertir ce statut en `COMMITTED` ou ACK patient.

**Contre-exemples et jeux synthétiques :** l'ancien modèle retourne `MATCH_LAB_NOT_GLOBAL_FRESHNESS` sur B/C à `seq/mac` identiques. Après restauration volontaire du SQLite B dans le répertoire LAB, le test re-signe une demande différente avec le **même `op_id`, même `seq` et même `after_mac`** mais un manifeste différent ; la preuve C conserve l'empreinte du reçu initial. Le nouveau contrat détecte `B_C_RECEIPT_HASH_CONFLICT_LAB`. Un second cas signe un nouvel `op_id` avec le même HEAD : le LOOKUP de l'ancien `op_id` reste `UNKNOWN_B_CURRENT_RECEIPT_LAB`. Le rejeu d'une ancienne réponse LOOKUP une fois B avancé devient `B_RECEIPT_HEAD_CONFLICT_LAB`. Le manque de LOOKUP et sa signature modifiée ne deviennent jamais succès.

**Revue SEC, identité :** l'enrôlement C et la vérification de son ancre refusent maintenant explicitement l'usage d'une **même clé Ed25519 pour B et C** (`C_B_SAME_SIGNER_REFUSE`), y compris en LAB. Deux clés différentes ne prouvent pas à elles seules deux domaines d'administration indépendants ; cette preuve reste entièrement absente jusqu'aux essais physiques du LOT10.

**Frontière prouvée :** le B LOOKUP et les HEAD sont synthétiques, signés par clés de test détenues par un seul harnais ; aucune session/réseau réel ni propriété de snapshot distribué. Trois réponses valides produites à des instants différents ne constituent pas une lecture atomique ; seules des séquences/empreintes strictement liées sont acceptables comme constat LAB. Le checkpoint C reste en mémoire, révocable et restaurable ; une compromission simultanée B+C, le repli d'une époque, l'altération du stockage physique et l'administration commune demeurent des risques non résolus. Le reçu et la chaîne complète DC6A/DC6B ainsi que les médias/manifestes cliniques A **ne sont pas reconstruits ici**.

**LOT10 exclusivement :** matériel B/C réellement séparé, WORM/TPM/HSM, power-cut/NTFS/SSD, latences, restauration, capteurs, unités de sauvegarde et preuve humaine B0–B9 ; sous-lots existants 10.1/10.3/10.4/10.7/10.8, **13 SP baseline inchangée**. Aucun pilote physique dans LOT06-N.
