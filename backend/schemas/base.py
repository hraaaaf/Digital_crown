from enum import Enum


class QRCodeType(str, Enum):
    NONE = "NONE"
    VALIDATION = "VALIDATION"
    VCARD = "VCARD"
    WEBSITE = "WEBSITE"
    INSTAGRAM = "INSTAGRAM"
    PAYMENT = "PAYMENT"
    WHATSAPP = "WHATSAPP"
    LOCATION = "LOCATION"


class StyleKey(str, Enum):
    CLASSIQUE = "classique"
    MODERNE = "moderne"
    MINIMALISTE = "minimaliste"
    MEDICAL = "medical"
    PREMIUM = "premium"
    SANINOVA = "saninova"


class AppointmentStatus(str, Enum):
    # Legacy statuts
    PREVU = "PRÉVU"
    EN_SALLE_ATTENTE = "EN_S_ATTENTE"
    EN_FAUTEUIL = "EN_FAUTEUIL"
    TERMINE = "TERMINÉ"
    ANNULE = "ANNULÉ"
    # Frontdesk statuts
    EN_ATTENTE_DEMANDE = "EN_ATTENTE_DEMANDE"
    EN_ATTENTE_CONFIRM = "EN_ATTENTE_CONFIRM"
    CONFIRME = "CONFIRMÉ"
    REFUSE = "REFUSÉ"
    EXPIRE = "EXPIRÉ"
    ABSENT = "ABSENT"


class SchedulingType(str, Enum):
    EXACT_TIME = "EXACT_TIME"
    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"
    FULL_DAY = "FULL_DAY"


class DocumentType(str, Enum):
    RAPPORT_CEPHALO = "RAPPORT_CEPHALO"
    ORDONNANCE = "ORDONNANCE"
    CERTIFICAT = "CERTIFICAT"
    DEVIS = "DEVIS"
    NOTE_HONORAIRES = "NOTE_HONORAIRES"
    LETTRE_MEDICALE = "LETTRE_MEDICALE"
    DOCUMENT_LIBRE = "DOCUMENT_LIBRE"
    PHOTO_CLINIQUE = "PHOTO_CLINIQUE"
    RADIOGRAPHIE = "RADIOGRAPHIE"
    MOULAGE = "MOULAGE"
    AUTRE = "AUTRE"


class DocumentStatus(str, Enum):
    ACTIF = "ACTIF"
    SUPPRIME = "SUPPRIME"
    ARCHIVE = "ARCHIVE"


class ConflictResolution(str, Enum):
    KEEP_BOTH = "KEEP_BOTH"
    OVERWRITE = "OVERWRITE"
    CANCEL = "CANCEL"
    CREATE_VERSION = "CREATE_VERSION"
