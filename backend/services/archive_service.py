# ==============================================================================
# ARCHIVE SERVICE - Gestion intelligente des documents
# ==============================================================================
import hashlib
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple, BinaryIO

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import shutil

from backend import models
from backend.models import DocumentType, DocumentStatus
from backend.schemas import ConflictResolution

# Configuration
BASE_DIR = Path(__file__).parent.parent
ARCHIVE_BASE_DIR = BASE_DIR / "static" / "archives"
LEGACY_DOCS_DIR = BASE_DIR / "static" / "documents"
TRASH_RETENTION_DAYS = 365  # 1 an
THUMBNAIL_SIZE = (300, 400)


class ArchiveService:
    """
    Service de gestion documentaire avec :
    - Hashing SHA-256 pour détection des doublons
    - Versioning automatique
    - Corbeille avec récupération
    - Génération de miniatures
    """
    
    def __init__(self, db: Session):
        self.db = db
        ARCHIVE_BASE_DIR.mkdir(parents=True, exist_ok=True)
    
    def _calculate_file_hash(self, file_content: bytes) -> str:
        """Calcule le hash SHA-256 du fichier."""
        return hashlib.sha256(file_content).hexdigest()
    
    def _generate_document_group_id(self) -> str:
        """Génère un UUID pour regrouper les versions d'un même document."""
        return str(uuid.uuid4())
    
    def _get_storage_path(self, patient_id: int, doc_type: DocumentType, 
                          filename: str, version: int = 1) -> Path:
        """Génère le chemin de stockage hiérarchique."""
        today = datetime.now()
        path = ARCHIVE_BASE_DIR / str(patient_id) / doc_type.value / str(today.year) / str(today.month)
        path.mkdir(parents=True, exist_ok=True)
        
        # Ajouter la version dans le nom si > 1
        if version > 1:
            stem = Path(filename).stem
            suffix = Path(filename).suffix
            filename = f"{stem}_v{version}{suffix}"
        
        return path / filename
    
    def check_conflicts(self, patient_id: int, file_hash: str, 
                       filename: str, doc_type: DocumentType, 
                       clinical_data: Optional[dict] = None) -> dict:
        """
        Vérifie les conflits potentiels avant archivage.
        Retourne : has_conflict, existing_doc, conflict_reason, suggested_action
        """
        # 1. Vérifier doublon exact (même hash)
        existing_by_hash = self.db.query(models.DocumentArchive).filter(
            and_(
                models.DocumentArchive.patient_id == patient_id,
                models.DocumentArchive.file_hash == file_hash,
                models.DocumentArchive.status == DocumentStatus.ACTIF
            )
        ).first()
        
        if existing_by_hash:
            return {
                "has_conflict": True,
                "existing_document": existing_by_hash,
                "conflict_reason": "same_hash",
                "suggested_action": ConflictResolution.CANCEL,
                "message": "Ce fichier existe déjà (doublon exact)"
            }
        
        # 2. Vérifier même nom même jour
        today = datetime.now().date()
        existing_by_name = self.db.query(models.DocumentArchive).filter(
            and_(
                models.DocumentArchive.patient_id == patient_id,
                models.DocumentArchive.document_type == doc_type,
                models.DocumentArchive.original_filename == filename,
                func.date(models.DocumentArchive.created_at) == today,
                models.DocumentArchive.status == DocumentStatus.ACTIF
            )
        ).first()
        
        if existing_by_name:
            return {
                "has_conflict": True,
                "existing_document": existing_by_name,
                "conflict_reason": "same_name_same_day",
                "suggested_action": ConflictResolution.CREATE_VERSION,
                "message": f"Un document '{filename}' existe déjà pour aujourd'hui"
            }
        
        # 4. Vérifier Doublon de CONTENU (Mêmes actes, même montant)
        if clinical_data:
            existing_by_content = self.db.query(models.DocumentArchive).filter(
                and_(
                    models.DocumentArchive.patient_id == patient_id,
                    models.DocumentArchive.document_type == doc_type,
                    models.DocumentArchive.status == DocumentStatus.ACTIF
                )
            ).all()
            
            for doc in existing_by_content:
                if doc.clinical_data == clinical_data:
                    return {
                        "has_conflict": True,
                        "existing_document": doc,
                        "conflict_reason": "duplicate_content",
                        "suggested_action": ConflictResolution.CANCEL,
                        "message": "Une note identique existe déjà pour ce patient (mêmes actes)."
                    }
        
        return {"has_conflict": False}
    
    def archive_document(self, patient_id: int, file_content: bytes, 
                        filename: str, doc_type: DocumentType,
                        uploaded_by_id: Optional[int] = None,
                        title: Optional[str] = None,
                        description: Optional[str] = None,
                        tags: List[str] = None,
                        clinical_data: Optional[dict] = None,
                        analysis_id: Optional[int] = None,
                        on_conflict: ConflictResolution = ConflictResolution.CREATE_VERSION,
                        force_group_id: Optional[str] = None) -> Tuple[models.DocumentArchive, bool]:
        """
        Archive un document avec gestion intelligente des conflits.
        Retourne: (document, is_new_version)
        """
        tags = tags or []
        
        # Calculer le hash
        file_hash = self._calculate_file_hash(file_content)
        file_size = len(file_content)
        
        # Vérifier les conflits (Hash, Nom, ou Contenu clinique)
        conflict = self.check_conflicts(patient_id, file_hash, filename, doc_type, clinical_data=clinical_data)
        
        if conflict["has_conflict"]:
            # Si c'est un doublon de contenu et que l'utilisateur n'a pas forcé
            if conflict["conflict_reason"] == "duplicate_content" and on_conflict == ConflictResolution.CANCEL:
                raise ValueError("DOUBLE_DETECTED: " + conflict["message"])
            
            # Autres types de conflits (nom, hash) gérés via le comportement par défaut
            if on_conflict == ConflictResolution.CANCEL:
                raise ValueError(conflict["message"])
            
            elif on_conflict == ConflictResolution.OVERWRITE:
                # Supprimer l'ancien (soft delete)
                old_doc = conflict["existing_document"]
                old_doc.status = DocumentStatus.SUPPRIME
                old_doc.deleted_at = datetime.now()
                old_doc.permanent_delete_at = datetime.now() + timedelta(days=TRASH_RETENTION_DAYS)
                
            elif on_conflict == ConflictResolution.CREATE_VERSION:
                # Créer une nouvelle version du groupe existant
                if conflict["existing_document"]:
                    force_group_id = conflict["existing_document"].document_group_id
        
        # Déterminer le groupe de versions
        if force_group_id:
            # Nouvelle version d'un document existant
            existing_versions = self.db.query(models.DocumentArchive).filter(
                models.DocumentArchive.document_group_id == force_group_id
            ).all()
            
            # Marquer l'ancienne version comme obsolète
            for doc in existing_versions:
                doc.is_latest_version = False
            
            version_number = len(existing_versions) + 1
            document_group_id = force_group_id
        else:
            # Nouveau document
            version_number = 1
            document_group_id = self._generate_document_group_id()
        
        # Générer le chemin de stockage
        storage_path = self._get_storage_path(patient_id, doc_type, filename, version_number)
        
        # Sauvegarder le fichier
        with open(storage_path, 'wb') as f:
            f.write(file_content)
        
        # --- DOUBLE EXPORT : RESTAURATION DOSSIERS HISTORIQUES (static/documents/YYYY/MM) ---
        if doc_type in [DocumentType.NOTE_HONORAIRES, DocumentType.DEVIS, DocumentType.ORDONNANCE, DocumentType.CERTIFICAT]:
            today = datetime.now()
            legacy_dir = LEGACY_DOCS_DIR / str(today.year) / f"{today.month:02d}"
            legacy_dir.mkdir(parents=True, exist_ok=True)
            
            # Consiste à utiliser le même nommage que l'ancien générateur
            legacy_path = legacy_dir / storage_path.name
            shutil.copy2(storage_path, legacy_path)

        # Créer l'entrée en base
        doc = models.DocumentArchive(
            patient_id=patient_id,
            uploaded_by_id=uploaded_by_id,
            document_type=doc_type,
            filename=storage_path.name,
            original_filename=filename,
            document_group_id=document_group_id,
            version_number=version_number,
            is_latest_version=True,
            file_hash=file_hash,
            file_size=file_size,
            file_path=str(storage_path),
            title=title or filename,
            description=description,
            tags=tags,
            clinical_data=clinical_data,
            analysis_id=analysis_id,
            status=DocumentStatus.ACTIF
        )
        
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        
        return doc, version_number > 1
    
    def get_document_versions(self, document_group_id: str) -> List[models.DocumentArchive]:
        """Récupère toutes les versions d'un document."""
        return self.db.query(models.DocumentArchive).filter(
            models.DocumentArchive.document_group_id == document_group_id
        ).order_by(desc(models.DocumentArchive.version_number)).all()
    
    def move_to_trash(self, document_id: int) -> models.DocumentArchive:
        """Déplace un document dans la corbeille."""
        doc = self.db.query(models.DocumentArchive).filter(
            models.DocumentArchive.id == document_id
        ).first()
        
        if not doc:
            raise ValueError("Document non trouvé")
        
        doc.status = DocumentStatus.SUPPRIME
        doc.deleted_at = datetime.now()
        doc.permanent_delete_at = datetime.now() + timedelta(days=TRASH_RETENTION_DAYS)
        
        self.db.commit()
        return doc
    
    def restore_from_trash(self, document_id: int) -> models.DocumentArchive:
        """Restaure un document depuis la corbeille."""
        doc = self.db.query(models.DocumentArchive).filter(
            and_(
                models.DocumentArchive.id == document_id,
                models.DocumentArchive.status == DocumentStatus.SUPPRIME
            )
        ).first()
        
        if not doc:
            raise ValueError("Document non trouvé dans la corbeille")
        
        doc.status = DocumentStatus.ACTIF
        doc.deleted_at = None
        doc.permanent_delete_at = None
        
        self.db.commit()
        return doc
    
    def permanent_delete(self, document_id: int) -> bool:
        """Supprime définitivement un document."""
        doc = self.db.query(models.DocumentArchive).filter(
            models.DocumentArchive.id == document_id
        ).first()
        
        if not doc:
            return False
        
        # Supprimer le fichier physique
        try:
            file_path = Path(doc.file_path)
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            print(f"Erreur suppression fichier: {e}")
        
        # Supprimer la miniature si existe
        if doc.thumbnail_path:
            try:
                thumb_path = Path(doc.thumbnail_path)
                if thumb_path.exists():
                    thumb_path.unlink()
            except:
                pass
        
        # Supprimer de la base
        self.db.delete(doc)
        self.db.commit()
        
        return True
    
    def cleanup_expired_trash(self) -> int:
        """
        Nettoie les documents de la corbeille dont la date de suppression permanente est dépassée.
        À exécuter via cron job quotidien.
        Retourne le nombre de documents supprimés.
        """
        expired_docs = self.db.query(models.DocumentArchive).filter(
            and_(
                models.DocumentArchive.status == DocumentStatus.SUPPRIME,
                models.DocumentArchive.permanent_delete_at <= datetime.now()
            )
        ).all()
        
        count = 0
        for doc in expired_docs:
            if self.permanent_delete(doc.id):
                count += 1
        
        return count
    
    def search_documents(self, patient_id: Optional[int] = None,
                        doc_type: Optional[DocumentType] = None,
                        status: DocumentStatus = DocumentStatus.ACTIF,
                        tags: List[str] = None,
                        search_query: Optional[str] = None,
                        date_from: Optional[datetime] = None,
                        date_to: Optional[datetime] = None,
                        page: int = 1, page_size: int = 20) -> Tuple[List[models.DocumentArchive], int]:
        """Recherche avancée de documents."""
        query = self.db.query(models.DocumentArchive)
        
        # Filtres
        if patient_id:
            query = query.filter(models.DocumentArchive.patient_id == patient_id)
        if doc_type:
            query = query.filter(models.DocumentArchive.document_type == doc_type)
        if status:
            query = query.filter(models.DocumentArchive.status == status)
        if tags:
            # Recherche dans le JSON des tags
            for tag in tags:
                query = query.filter(models.DocumentArchive.tags.contains([tag]))
        
        # Recherche texte
        if search_query:
            search_filter = or_(
                models.DocumentArchive.title.ilike(f"%{search_query}%"),
                models.DocumentArchive.description.ilike(f"%{search_query}%"),
                models.DocumentArchive.original_filename.ilike(f"%{search_query}%")
            )
            query = query.filter(search_filter)
        
        # Dates
        if date_from:
            query = query.filter(models.DocumentArchive.created_at >= date_from)
        if date_to:
            query = query.filter(models.DocumentArchive.created_at <= date_to)
        
        # Compter total
        total = query.count()
        
        # Pagination
        docs = query.order_by(desc(models.DocumentArchive.created_at))\
                   .offset((page - 1) * page_size)\
                   .limit(page_size)\
                   .all()
        
        return docs, total


# Singleton
def get_archive_service(db: Session) -> ArchiveService:
    return ArchiveService(db)
