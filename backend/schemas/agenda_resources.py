from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

AgendaResourceType = Literal["CHAIR", "ROOM", "OTHER"]


class AgendaResourceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, max_length=120)
    resource_type: AgendaResourceType = "CHAIR"


class AgendaResourceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    resource_type: Optional[AgendaResourceType] = None
    is_active: Optional[bool] = None


class AgendaResourceOut(BaseModel):
    id: int
    name: str
    resource_type: AgendaResourceType
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
