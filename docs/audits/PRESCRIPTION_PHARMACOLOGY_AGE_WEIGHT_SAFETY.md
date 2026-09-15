# Prescription Pharmacology — Age & Weight Safety

Status: VALIDATED — PRE-MERGE

## Goal

Utiliser l’âge et le poids réels du patient lorsqu’une règle pharmacologique dentaire sourcée les rend pertinents, sans inventer de poids, sans créer un second moteur de posologie et sans ajuster automatiquement une dose au-delà de ce que les sources permettent.

## Success

- les règles âge existantes restent inchangées lorsqu’elles sont compatibles avec le contexte patient ;
- aucun poids pédiatrique n’est inféré ;
- pour l’ibuprofène pédiatrique, un poids réel connu contrôle le plafond SDCEP de 30 mg/kg/j ;
- si le schéma déjà arbitré dépasse ce plafond, aucun schéma de remplacement n’est fabriqué : statut `requires_review`, regimen nul, validation praticien ;
- si le poids n’est pas renseigné, le moteur conserve la règle SDCEP par tranche d’âge au lieu d’inventer un poids ;
- les valeurs explicitement saisies par le praticien ne sont jamais écrasées silencieusement ;
- le gate Maroc reste inchangé ;
- tests ciblés + régression générale applicables verts avant merge.

## Sources vérifiées

### Source dentaire primaire

SDCEP, Drug Prescribing for Dentistry — Ibuprofen:
https://sdcepdentalprescribing.nhs.scot/guidance/odontogenic-pain/analgesics/ibuprofen/

La page publie les tranches d’âge déjà utilisées par Digital Crown et précise un maximum pédiatrique de 30 mg/kg/j ; à partir de 7 ans, ce plafond ne doit en outre pas dépasser 2,4 g/j.

### Cross-check médicament

eMC, Nurofen for Children Orange Singles — SmPC:
https://www.medicines.org.uk/emc/product/5641/smpc

Ce SmPC indique pour ce produit une dose quotidienne recommandée de 20–30 mg/kg/j en prises réparties et inclut la douleur dentaire parmi les indications. Ce cross-check confirme la pertinence du contrôle pondéral, mais n’est pas utilisé comme calculateur universel de dose pour toutes les présentations d’ibuprofène.

## Architecture retenue

Le garde-fou `PrescriptionPharmacologyWeightSafety` s’exécute après l’arbitrage pharmacologique source-backed et avant l’application au médicament patient.

Il ne possède aucune table de dose par âge. Il lit la borne quotidienne maximale du schéma déjà arbitré, la compare au plafond pondéral documenté lorsqu’un poids réel est disponible, puis :

- laisse passer le schéma s’il respecte le plafond ;
- échoue fermé vers `requires_review` si le plafond est dépassé ;
- échoue fermé si le schéma ne peut pas être vérifié de façon déterministe ;
- ne fabrique jamais de dose ajustée.

## Hors périmètre de ce sous-lot

Le modificateur pondéral d’amoxicilline en infection sévère n’est pas activé ici. La sévérité appartient à `DentalAbscessContext` et doit rester un contexte clinique structuré explicite ; elle ne sera pas inférée depuis du texte libre ni mélangée au simple contexte patient.

## Proof

HEAD fonctionnel certifié : `46f695b62abc40172b376c2f5ada41c7156736ed`.

PR #511, exact-head checks :
- CI #4327 : SUCCESS ;
- Ordonnance Fidelity V3 Visual Certification #176 : SUCCESS ;
- T2 Runtime Browser Certification #3214 : SUCCESS ;
- Patient P7 Final Certification #1646 : SUCCESS ;
- Cabinet Upgrade PostgreSQL Certification #729 : SUCCESS ;
- Settings R11 TemplateBuilder Dependency Audit #745 : SUCCESS ;
- M6-I Biometric Passkey Certification #2014 : skipped, hors périmètre du diff.

Frontend `tests & build` : SUCCESS dans CI #4327.

Cas de sécurité couverts par les tests du sous-lot :
- 10 ans / 25 kg : schéma âge ibuprofène 300 mg x3 = 900 mg/j, plafond pondéral 750 mg/j => `requires_review`, aucun regimen automatique ;
- 10 ans / 30 kg : plafond 900 mg/j => schéma source-backed conservé ;
- poids absent : aucun poids inventé, règle âge existante conservée ;
- dose/posologie explicitement saisies par le praticien : jamais écrasées silencieusement, même lorsque la revue est exigée.

Diff fonctionnel revu : 1 commit fonctionnel initial, 4 fichiers touchés, aucune modification UI/UX et aucune modification DB. Le garde-fou ne crée aucune posologie de remplacement et ne contourne pas le gate Maroc.

Aucune capture BEFORE/AFTER requise pour ce sous-lot : comportement de sécurité interne sans modification visuelle.

Merge autorisable uniquement après certification du commit documentaire de closeout et vérification finale de la PR. Aucun déploiement Vercel.
