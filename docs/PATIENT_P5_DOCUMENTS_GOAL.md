# Patient P5 — Documents

## Goal
Conserver le Document Studio déjà durci comme moteur unique de génération, mais rendre l’entrée Patient plus simple, honnête et cohérente : permissions visibles avant action, historique fail-closed, vocabulaire exact, et aucun moteur de diagnostic caché dans Documents.

## Succès observable
1. `Créer` et `Historique` restent dans le même espace Documents, sans recréer une seconde archive.
2. Ordonnance, certificat, devis, note d’honoraires, échéancier et document libre conservent leurs contrats de génération/preview/archivage existants.
3. Les types de documents non autorisés par RBAC backend ne sont pas proposés comme actions disponibles dans StudioTabs.
4. Une erreur de chargement Historique affiche un état d’erreur + Réessayer, jamais un faux « Aucune archive médicale ».
5. La détection de doublon heuristique frontend n’est jamais présentée comme une vérité canonique ; elle est soit supprimée, soit explicitement reclassée comme signal à vérifier.
6. `Compagnon Diagnostique` n’est plus un type de document. Il sort de Document Studio. Sa conservation éventuelle relève de P3 Clinique et exige une certification scientifique dédiée.
7. Ouverture/téléchargement restent authentifiés par blob ; les object URLs sont révoquées après usage.
8. Corbeille reste la suppression normale depuis l’historique ; aucune suppression permanente ajoutée à la surface Patient.
9. A5/A4, preview, impression, archivage et édition depuis Historique restent testés sur leurs contrats existants.
10. Zéro overflow horizontal, erreur runtime ou HTTP 5xx sur 390x844, 430x932, 768x1024, 1280x900.

## Audit initial

### Architecture déjà correcte
P1 a déjà fusionné Documents et Archives. `PatientDetailsInner` expose un seul espace Documents avec deux vues : `Créer` (`DocumentHub`) et `Historique` (`PatientDocuments`). P5 ne reconstruit pas cette architecture.

### DocumentHub / Document Studio
`DocumentHub.tsx` orchestre les composants modulaires existants : header, tabs, content, footer, preview et dialogs. Le moteur `useDocumentGenerator` contient des validations strictes, un preview séparé, la gestion de brouillons et les flux d’archivage existants. P5 doit préserver ces contrats.

### Permissions
`StudioTabs.tsx` affiche actuellement tous les onglets sans matrice RBAC frontend. Le backend, lui, impose des permissions par type de document : notamment `prescriptions`, `accounting`, `clinical`, `patients` selon le type. L’UI doit refléter la permission réelle avant l’action, sans affaiblir le contrôle backend.

### Historique
`PatientDocuments.tsx` :
- charge `/patients/{id}/documents` ;
- sur erreur, log uniquement puis `loading=false`, ce qui produit ensuite un faux état vide ;
- ouvre/télécharge via blob authentifié ;
- met à la corbeille via `/documents/{id}/trash` ;
- permet de réinjecter `clinical_data` dans DocumentHub pour régénération.

### Signal « doublon »
L’historique calcule localement une signature `type + actes/dents` et affiche `Doublon de contenu détecté`. Cette heuristique n’est pas une source backend et ne prouve pas qu’un document est un doublon métier. P5 doit supprimer ce verdict ou le reclasser explicitement comme « contenu similaire à vérifier ».

### Compagnon Diagnostique
`DocumentStudioVocabulary.ts` déclare encore `plan: 'Compagnon Diagnostique'` et `DocumentHubContent` monte `TreatmentPlanStudio` comme un type de document.

L’audit de `TreatmentPlanStudio.tsx` confirme qu’il contient des embranchements déterministes codés en dur qui produisent des hypothèses nommées et des actes proposés (endodontie, antibiothérapie, anti-inflammatoires, CBCT, etc.) à partir de réponses. Même s’il affiche une notion de confirmation praticien et ne constitue pas une archive documentaire en soi, il ne doit pas rester dans Documents. Sa conservation en Clinique est conditionnée à la certification scientifique P3 ; aucun simple déplacement n’est autorisé.

### A5/A4
Le Document Libre expose explicitement `A5` / `A4`. Les autres types ont leurs propres générateurs/contracts existants. P5 vérifie les formats réellement supportés au lieu de généraliser artificiellement A5/A4 à tous les documents.

## Découpage P5

### P5-A — Vérité Historique
- état erreur + Réessayer ;
- état vide uniquement après réponse backend réussie ;
- reclasser/supprimer le verdict de doublon frontend ;
- révocation des object URLs après ouverture/téléchargement.

### P5-B — RBAC visible
- matrice frontend des tabs selon les mêmes permissions métier que backend ;
- backend reste autoritaire ;
- test sous-compte sans prescriptions/accounting/clinical.

### P5-C — Nettoyage du Studio
- retirer `Compagnon Diagnostique` de la liste des types de documents ;
- ne pas supprimer son code tant que P3 n’a pas tranché sa conservation scientifique ;
- conserver ordonnance, certificat, devis, honoraires, échéancier, libre.

### P5-D — Certification Document Studio Patient
- preview/generate/archive ;
- édition depuis Historique ;
- A5/A4 pour les surfaces qui le supportent réellement ;
- impression ;
- permissions ;
- isolation Patient A→B ;
- AFTER 4 viewports pour Créer + Historique ;
- CI/T2 exact-HEAD.

## Wireframe cible

```text
DOCUMENTS
[ CRÉER ] [ HISTORIQUE ]

CRÉER
[Ordonnance]* [Certificat]* [Devis]* [Honoraires]* [Échéancier]* [Document libre]*
* uniquement si permission réellement disponible

┌─────────────────────────────────────────────────────────────┐
│ FORMULAIRE / STUDIO EXISTANT                                │
│ validations + preview + génération                         │
└─────────────────────────────────────────────────────────────┘

HISTORIQUE
┌─────────────────────────────────────────────────────────────┐
│ Recherche                                     12 documents  │
├─────────────────────────────────────────────────────────────┤
│ Document · date · type      [Modifier] [Voir] [Télécharger] │
│                               [Mettre à la corbeille]       │
└─────────────────────────────────────────────────────────────┘

Erreur backend :
┌─────────────────────────────────────────────────────────────┐
│ Impossible de charger l’historique              [Réessayer] │
└─────────────────────────────────────────────────────────────┘
```

## Preuve requise
- BEFORE Créer + Historique sur 390/430/768/1280 ;
- tests frontend ciblés sur erreur/empty, RBAC, tabs, object URLs ;
- tests backend existants de génération/permissions/isolation réutilisés et complétés uniquement si manque démontré ;
- preview/archivage/édition testés ;
- AFTER mêmes viewports ;
- comparaison BEFORE / wireframe / AFTER ;
- CI + T2 exact-HEAD ;
- certificat P5 puis roadmap.

## Règles
- pas de rebuild gratuit du Document Studio ;
- pas de diagnostic dans Documents ;
- pas de faux état vide après erreur réseau ;
- pas de permission purement cosmétique : le backend reste l’autorité ;
- pas d’élargissement artificiel des formats papier ;
- aucun déploiement Vercel.
