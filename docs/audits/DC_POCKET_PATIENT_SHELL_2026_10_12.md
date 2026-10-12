# Pocket patient — coque commune

Goal : organiser le companion local-first existant en cinq destinations patient : Aujourd’hui, Agenda, Documents, Messages, Plus. Référence : rythme visuel Pocket personnel approuvé, tokens existants, navigation fixe avec safe area ; aucune destination cabinet.

BEFORE : trois captures WebKit du vrai /companion aux formats 390×844, 768×1024, 1280×900, coffre IndexedDB chiffré réel avec données fictives, toutes API interceptées (503). Sources de base a739dbdb102d9ccab8eaac4eeb0323461a05a560. Preuves locales : pocket-after-reference/patient-shell-before.

Target : accueil court avec identité du dossier, fraîcheur de synchronisation et prochain rendez-vous. Agenda conserve ses demandes/confirmations existantes ; Documents expose les seuls partages du coffre ; Messages conserve son transport ; Plus regroupe les autres modules existants et les réglages de l’appareil. Le choix de dossier reste explicite et réinitialise la navigation. Aucune permission du personnel, nouvelle API, DB ou migration.

Success : navigation accessible et cinq boutons sur les trois formats, aucun overflow, aucun module d’un ancien dossier après sélection, retour Aujourd’hui, absence de confirmation réseau inventée. Préserver les commandes existantes.

Exclusions : accès distant réel, installation iPhone, évolution de la session et révocation des copies offline ; aucune autorisation de merge. Validation patient distincte de celle du personnel.

Correction de cible demandée par le propriétaire : la première coque fonctionnelle ne reprenait pas suffisamment le standard visuel personnel. Ces AFTER sont rejetés/supersédés, non validés. Cible obligatoire : même fichier logo `frontend/src/assets/logo.png` que MobileHeader, même badge Pocket, mêmes dimensions de marque, boutons d’en-tête, typographie, système mobileGlassSystem via data-dc-mobile-shell, cartes 24px et navigation flottante 76px/rayon 30px avec indicateur animé. Fonctions et intitulés restent adaptés au patient ; aucun service staff n’est importé. PatientPocketHeader utilise seulement le helper de salutation sans données. Référence visuelle exacte : AFTER dentiste/assistante WebKit 390×844 approuvés. Aucun style du personnel modifié.

Revues prévues, séparées sur le même HEAD : A — réfuter isolation contexte, montage des modules, coffre et confusion patient/personnel ; B — réfuter navigation, accessibilité, preuve synthétique, états hors ligne et régression des modules. Confirmation supplémentaire après convergence. Score provisoire 7.9/7.9/min 7.9 : AFTER, CI et validation humaine patient à obtenir.
