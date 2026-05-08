from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.services.clinical_intelligence import clinical_intel
from backend.routers.auth import get_current_user
from backend import models

router = APIRouter(tags=["Clinical Intelligence"])

class PubMedRequest(BaseModel):
    content: str

@router.post("/pubmed-extract")
async def pubmed_extract(req: PubMedRequest, current_user: models.User = Depends(get_current_user)):
    """
    Extrait des clinical pearls d'un contenu PubMed ou texte scientifique.
    """
    result = await clinical_intel.extract_pubmed_pearls(req.content)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result
