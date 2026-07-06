"""Bot service request/response schemas."""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class BotExecuteRequest(BaseModel):
    """Execute a pending bot action by ID only."""
    model_config = ConfigDict(extra="forbid")

    pending_action_id: str = Field(..., min_length=1, max_length=64)


class BotChatRequest(BaseModel):
    """Send a message to the bot."""
    model_config = ConfigDict(extra="forbid")

    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = Field(None, max_length=64)
    patient_id: Optional[int] = None


class BotCancelRequest(BaseModel):
    """Cancel a pending bot action."""
    model_config = ConfigDict(extra="forbid")

    reason: Optional[str] = Field(None, max_length=500)
