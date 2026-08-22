import uuid
import enum
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import String, Boolean, Float, DateTime, ForeignKey, Enum as SQLEnum, Text, JSON, func, Integer, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models_base import Base

class AgendaMode(str, enum.Enum):
    EXACT = "EXACT"
    BLOCK = "BLOCK"

# ==============================================================================
# --- PHASE 6 : CROWN BOT SESSIONS (CHAT HISTORY) ---
# ==============================================================================

class BotSession(Base):
    """
    Historique des sessions du chatbot par utilisateur (isolation stricte).
    employer_id = tenant du cabinet, user_id = auteur de la session.
    """
    __tablename__ = "bot_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    # Contexte patient : si la conversation est ouverte depuis un dossier patient,
    # elle est rattachée à ce patient (historique par patient + injection auto de l'entité).
    patient_id: Mapped[Optional[int]] = mapped_column(ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Nouvelle Conversation")
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    
    messages: Mapped[List["BotMessage"]] = relationship("BotMessage", back_populates="session", cascade="all, delete-orphan", order_by="BotMessage.created_at")

class BotMessage(Base):
    """
    Messages individuels au sein d'une session de bot.
    """
    __tablename__ = "bot_messages"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(ForeignKey("bot_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    sender: Mapped[str] = mapped_column(String(20), nullable=False) # 'user' or 'bot'
    text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # JSON pour stocker action_type, suggestions, et pending_action
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    session: Mapped["BotSession"] = relationship("BotSession", back_populates="messages")


class BotPendingAction(Base):
    """
    Action bot stockee cote serveur — seul l'ID est expose au client.
    Le frontend ne peut pas forger l'action, seulement la confirmer par ID.
    Expire automatiquement apres 30 minutes (non execute = dead).
    """
    __tablename__ = "bot_pending_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(
        ForeignKey("bot_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    employer_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    params_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # pending | executed | expired | cancelled
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

class CabinetSettings(Base):
    __tablename__ = "cabinet_settings"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True, default=1)
    
    # Horaires
    opening_time_morning: Mapped[Optional[str]] = mapped_column(String(5), default="09:00")
    closing_time_morning: Mapped[Optional[str]] = mapped_column(String(5), default="13:00")
    opening_time_afternoon: Mapped[Optional[str]] = mapped_column(String(5), default="14:00")
    closing_time_afternoon: Mapped[Optional[str]] = mapped_column(String(5), default="18:00")
    is_continuous: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Configuration Agenda
    agenda_mode: Mapped[AgendaMode] = mapped_column(SQLEnum(AgendaMode), default=AgendaMode.EXACT)
    use_tickets: Mapped[bool] = mapped_column(Boolean, default=False)

class AgendaException(Base):
    __tablename__ = "agenda_exceptions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    is_holiday: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
