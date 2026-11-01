# C05B-03H-03 — Windows current-user DPAPI Ed25519 vault

**LAB ISOLÉ UNIQUEMENT** — pas de route produit, migration clinique ni connexion matériel.

Un test Windows natif appelle les API Win32 CryptProtectData / CryptUnprotectData, avec DPAPI lié au compte utilisateur Windows courant et sans option LOCAL_MACHINE. La clé privée Ed25519 est chiffrée sur disque ; la clé publique et le scope non-PHI (tenant/device/station/generation/version) restent en clair. L'enveloppe et son entropy empêchent d'utiliser le blob avec un autre scope sans être détecté.

Le test déclenche un deuxième interpréteur Python **sous le même compte de la VM Windows éphémère** qui déchiffre la clé et signe ; un contrôle vérifie la signature. Refus des clés altérées, d'une tentative d'écrasement, d'un scope changé, d'une suppression locale, de l'environnement cabinet et de l'absence du flag LAB.

**Limites majeures** : DPAPI au repos seulement ; la clé privée est dans la mémoire Python lors de la signature. Ce n'est pas une clé non exportable CNG/TPM. Aucune preuve ACL, identité Windows distincte, extinction/reboot machine, stockage Windows professionnel ou véritable matériel dentaire. Le fichier hérite de l'ACL de son répertoire, non audité. Suppression locale ne révoque pas la clé dans le ledger SQLCipher serveur. Le driver Windows n'est pas connecté à H-02 ou à une vraie acquisition. Ne pas confondre reprise du processus avec reboot du système.

**Next H-04** : audit des ACL, compte de service/installateur, test deuxième compte Windows, reboot/profil/perte de clé, connecteur TWAIN/WIA/SDK/DICOM réel, révocation synchronisée, puis UX de confirmation et double revue. Aucune activation clinique.

PRODUCT_READY=false ; CLINICAL_GO=false ; ready_to_merge=false.
