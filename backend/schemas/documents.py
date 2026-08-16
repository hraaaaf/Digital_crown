from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_core import PydanticCustomError
import datetime
import math
from typing import Optional, Dict, List, Literal, Any, Union

from .base import DocumentType, DocumentStatus, ConflictResolution
from backend.utils.installment_reconciliation import validate_installments


# --- DOCUMENT FACTORY ---

class MedicationItem(BaseModel):
    nom: str
    dosage: Optional[str] = ""
    forme: Optional[str] = "Sachets"
    posologie: Optional[str] = ""
    type: Optional[str] = "MEDICAMENT"


class OrdonnanceData(BaseModel):
    medications: List[MedicationItem] = []
    doc_date: Optional[datetime.date] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    show_legal_annotations: bool = True


class CertificatData(BaseModel):
    reason: Optional[str] = "Arrêt de travail"
    days: Optional[int] = 1
    doc_date: Optional[datetime.date] = None
    start_date: Optional[datetime.date] = None
    content: Optional[str] = None
    is_work_stop: bool = False
    age: Optional[int] = None
    gender: Optional[str] = None


class ToothTreatmentInfo(BaseModel):
    code: str
    name: str
    price: float


class ToothData(BaseModel):
    tooth_number: int
    treatments: List[ToothTreatmentInfo]
    surfaces: List[str] = []
    notes: Optional[str] = None


class InstallmentBase(BaseModel):
    label: str
    amount: float
    due_date: datetime.date
    paid_date: Optional[datetime.date] = None
    status: str = "EN_ATTENTE"
    notes: Optional[str] = None


class InstallmentCreate(InstallmentBase):
    pass


class InstallmentOut(InstallmentBase):
    id: int
    plan_id: int
    model_config = ConfigDict(from_attributes=True)


class InstallmentPlanBase(BaseModel):
    title: str
    total_amount: float


class InstallmentPlanCreate(InstallmentPlanBase):
    patient_id: int
    installments: List[InstallmentCreate]


class InstallmentPlanOut(InstallmentPlanBase):
    id: int
    patient_id: int
    created_at: datetime.datetime
    installments: List[InstallmentOut]
    model_config = ConfigDict(from_attributes=True)


class DevisItem(BaseModel):
    acte: str = ""
    dent: str = ""
    dents: List[Union[int, str]] = []
    prix_unitaire: float = 0.0


class InstallmentItem(BaseModel):
    date: Optional[datetime.date] = None
    amount: float = 0.0
    label: str = "Versement"


class DevisData(BaseModel):
    items: List[DevisItem] = []
    doc_date: Optional[datetime.date] = None
    teeth_data: List[ToothData] = []
    age: Optional[int] = None
    gender: Optional[str] = None
    installments: List[InstallmentItem] = []


class PaymentItem(BaseModel):
    date: Optional[datetime.date] = None
    acte: str = ""
    dent: str = "-"
    dents: List[Union[int, str]] = []
    montant: float = 0.0
    mode_reglement: str = "Espèces"


class HonorairesData(BaseModel):
    payments: List[PaymentItem] = []
    doc_date: Optional[datetime.date] = None
    teeth_data: List[ToothData] = []
    age: Optional[int] = None
    gender: Optional[str] = None
    installments: List[InstallmentItem] = []


class LibreData(BaseModel):
    titre: str = Field(default='DOCUMENT MÉDICAL', alias='title')
    contenu: str = Field(default='', alias='content')
    doc_date: Optional[datetime.date] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    custom_patient: Optional[str] = None
    custom_date: Optional[str] = None
    hide_patient_header: bool = False
    page_size: str = "A5"
    alignment: str = "justify"
    model_config = ConfigDict(populate_by_name=True)


class DocumentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["ordonnance", "certificat", "devis", "note", "honoraires", "libre", "lettre", "echeancier"]
    patient_id: int
    data: Dict
    is_accounted: bool = True
    payment_status: Optional[Literal["EN_ATTENTE", "PAYE", "PARTIEL"]] = "EN_ATTENTE"

    @model_validator(mode="after")
    def reject_implicit_partial_payment(self):
        """This document flow has no explicit amount-paid field for PARTIEL."""
        if self.payment_status == "PARTIEL":
            raise PydanticCustomError(
                "partial_payment_requires_explicit_amount",
                "Paiement partiel refusé : aucun montant encaissé explicite n'est fourni. Enregistrez le montant réel via le flux d'encaissement dédié."
            )
        return self

    @model_validator(mode="after")
    def validate_honoraires_financial_contract(self):
        if self.type not in {"note", "honoraires"}:
            return self
        payments = (self.data or {}).get("payments") or []
        if not payments:
            raise PydanticCustomError(
                "honoraires_empty",
                "Une note d'honoraires doit contenir au moins un acte.",
            )
        for index, payment in enumerate(payments, start=1):
            if not isinstance(payment, dict):
                raise PydanticCustomError("honoraires_invalid_item", f"Acte #{index} invalide.")
            if not str(payment.get("acte") or "").strip():
                raise PydanticCustomError("honoraires_empty_label", f"Acte #{index} : la description est requise.")
            try:
                amount = float(payment.get("montant"))
            except (TypeError, ValueError) as exc:
                raise PydanticCustomError("honoraires_invalid_amount", f"Acte #{index} : montant non numérique.") from exc
            if not math.isfinite(amount) or amount <= 0 or amount > 1_000_000:
                raise PydanticCustomError(
                    "honoraires_invalid_amount",
                    f"Acte #{index} : le montant doit être fini, strictement positif et ≤ 1 000 000 MAD.",
                )
            if "mode_reglement" not in payment or not str(payment.get("mode_reglement") or "").strip():
                raise PydanticCustomError(
                    "honoraires_payment_method_required",
                    f"Acte #{index} : le mode de règlement doit être choisi explicitement.",
                )
        return self

    @model_validator(mode="after")
    def reconcile_global_honoraires_installments(self):
        if self.type not in {"note", "honoraires"}:
            return self
        data = self.data or {}
        if not data.get("is_global_note"):
            return self
        installments = data.get("installments") or []
        if not installments:
            return self
        payments = data.get("payments") or []
        billed_amounts = [payment.get("montant", 0) for payment in payments if isinstance(payment, dict)]
        installment_amounts = [item.get("amount", 0) for item in installments if isinstance(item, dict)]
        try:
            validate_installments(sum(billed_amounts), installment_amounts)
        except (TypeError, ValueError) as exc:
            raise PydanticCustomError("installment_total_mismatch", str(exc)) from exc
        return self

    @model_validator(mode="after")
    def validate_direct_echeancier_contract(self):
        if self.type != "echeancier":
            return self
        data = self.data or {}
        if data.get("plan_id"):
            return self

        title = str(data.get("title") or "").strip()
        if not title:
            raise PydanticCustomError("installment_title_required", "Le titre du plan de paiement est requis.")
        try:
            total = float(data.get("totalAmount"))
        except (TypeError, ValueError) as exc:
            raise PydanticCustomError("installment_total_invalid", "Le total du plan est invalide.") from exc
        if not math.isfinite(total) or total <= 0 or total > 10_000_000:
            raise PydanticCustomError("installment_total_invalid", "Le total du plan doit être fini et strictement positif.")

        items = data.get("items") or []
        if not items:
            raise PydanticCustomError("installment_items_required", "Le plan doit contenir au moins une échéance.")
        amounts = []
        for index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                raise PydanticCustomError("installment_item_invalid", f"Échéance #{index} invalide.")
            if not str(item.get("label") or "").strip():
                raise PydanticCustomError("installment_label_required", f"Échéance #{index} : libellé requis.")
            if not item.get("dueDate"):
                raise PydanticCustomError("installment_date_required", f"Échéance #{index} : date explicite requise.")
            try:
                datetime.date.fromisoformat(str(item.get("dueDate")).split("T")[0])
                amount = float(item.get("amount"))
            except (TypeError, ValueError) as exc:
                raise PydanticCustomError("installment_item_invalid", f"Échéance #{index} invalide.") from exc
            if not math.isfinite(amount) or amount <= 0 or amount > 1_000_000:
                raise PydanticCustomError("installment_amount_invalid", f"Échéance #{index} : montant invalide.")
            amounts.append(amount)
        try:
            validate_installments(total, amounts)
        except (TypeError, ValueError) as exc:
            raise PydanticCustomError("installment_total_mismatch", str(exc)) from exc
        return self


# --- SMART ORDONNANCE ---

class MedicationOut(BaseModel):
    id: int
    nom: str
    dosage: Optional[str] = None
    forme: Optional[str] = None
    usage_count: int
    model_config = ConfigDict(from_attributes=True)


class ClinicalCategoryOut(BaseModel):
    id: int
    label: str
    model_config = ConfigDict(from_attributes=True)


class ClinicalProtocolOut(BaseModel):
    id: int
    category_id: int
    variant_name: str
    medications_json: Any
    model_config = ConfigDict(from_attributes=True)


class PrescriptionLearnRequest(BaseModel):
    medications: List[MedicationItem]


# --- CATALOGUE DES ACTES ---

class ClinicalActCatalogBase(BaseModel):
    name: str
    base_price: float


class ClinicalActCatalogOut(ClinicalActCatalogBase):
    id: int
    usage_count: int
    model_config = ConfigDict(from_attributes=True)


class ActLearnRequestItem(BaseModel):
    name: str
    price_applied: float


class ActLearnRequest(BaseModel):
    acts: List[ActLearnRequestItem]


# --- ERP & IA PHARMACOLOGIQUE ---

class AIPrescriptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    acte: str
    age: Optional[int] = None


class BIStatsOut(BaseModel):
    ca_mensuel: float
    ca_annuel: float
    repartition_actes: Dict[str, float]
    evolution_mensuelle: List[Dict[str, Any]]


# --- ARCHIVAGE DOCUMENTAIRE ---

class DocumentArchiveBase(BaseModel):
    document_type: DocumentType
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []


class DocumentArchiveCreate(DocumentArchiveBase):
    patient_id: int
    analysis_id: Optional[int] = None
    clinical_data: Optional[Dict] = None


class DocumentVersionInfo(BaseModel):
    version_number: int
    created_at: datetime.datetime
    file_size: int
    is_latest: bool


class DocumentArchiveOut(DocumentArchiveBase):
    id: Union[int, str]
    patient_id: int
    filename: str
    original_filename: str
    file_size: int
    file_hash: str
    document_group_id: str
    version_number: int
    is_latest_version: bool
    status: DocumentStatus
    created_at: datetime.datetime
    updated_at: datetime.datetime
    deleted_at: Optional[datetime.datetime] = None
    thumbnail_url: Optional[str] = None
    download_url: str
    file_exists: bool = False
    all_versions: List[DocumentVersionInfo] = []

    class Config:
        from_attributes = True


class DocumentConflictCheck(BaseModel):
    has_conflict: bool
    existing_document: Optional[DocumentArchiveOut] = None
    conflict_reason: Optional[str] = None
    suggested_action: Optional[ConflictResolution] = None


class DocumentArchiveRequest(BaseModel):
    document_type: DocumentType
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    check_conflicts: bool = True
    on_conflict: ConflictResolution = ConflictResolution.CREATE_VERSION


class DocumentArchiveResponse(BaseModel):
    success: bool
    message: str
    document: Optional[DocumentArchiveOut] = None
    conflict_info: Optional[DocumentConflictCheck] = None
    requires_action: bool = False


class DocumentListParams(BaseModel):
    patient_id: Optional[int] = None
    document_type: Optional[DocumentType] = None
    status: Optional[DocumentStatus] = DocumentStatus.ACTIF
    tags: List[str] = []
    search_query: Optional[str] = None
    date_from: Optional[datetime.datetime] = None
    date_to: Optional[datetime.datetime] = None
    page: int = 1
    page_size: int = 20


class DocumentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    documents: List[DocumentArchiveOut]


class DocumentTrashResponse(BaseModel):
    message: str
    document_id: Union[int, str]
    deleted_at: datetime.datetime
    permanent_delete_at: datetime.datetime


class DocumentRestoreResponse(BaseModel):
    message: str
    document_id: Union[int, str]
    restored_at: datetime.datetime


class DocumentBatchDeleteRequest(BaseModel):
    document_ids: List[Union[int, str]]
    permanent: bool = False


class DocumentBatchResponse(BaseModel):
    success: List[int]
    failed: List[Dict[int, str]]


class DocumentShareLink(BaseModel):
    token: str
    expires_at: datetime.datetime
    download_url: str
    max_downloads: int = 5


class DocumentPreviewResponse(BaseModel):
    document_id: Union[int, str]
    preview_url: str
    thumbnail_url: Optional[str] = None
    file_type: str
    can_preview: bool


class HonoraireItem(BaseModel):
    id: Union[int, str]
    patient_id: int
    patient_name: str
    assurance: Optional[str] = "AUCUNE"
    date: datetime.datetime
    title: str
    amount: float
    file_url: str
    payment_status: Optional[str] = "EN_ATTENTE"
    validated_by: Optional[str] = None


class HonoraireListResponse(BaseModel):
    total: int
    total_amount: float
    total_collected: float = 0.0
    items: List[HonoraireItem]
    summary_by_title: dict = {}
