"""Schemas for RVG (intra-oral X-ray) upload and display."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

ALLOWED_RVG_TYPES = {"rvg", "periapical", "bitewing", "occlusal", "other"}
ALLOWED_MIMES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_RVG_SIZE = 10 * 1024 * 1024  # 10 MB


class RVGUploadForm(BaseModel):
    """Form data for RVG upload."""
    radio_type: str = Field(default="rvg")
    tooth_number: Optional[str] = Field(None, max_length=20)
    sector: Optional[str] = Field(None, max_length=100)
    acquisition_date: Optional[date] = None
    note: Optional[str] = Field(None, max_length=1000)


class RVGResponse(BaseModel):
    """RVG document response (from DocumentArchive)."""
    id: int
    patient_id: int
    document_type: str
    original_filename: Optional[str]
    download_url: str
    tags: Optional[list]
    clinical_data: Optional[dict]
    created_at: datetime
    uploaded_by_id: Optional[int]

    class Config:
        from_attributes = True
