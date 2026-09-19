from __future__ import annotations

import hmac
import uuid
from datetime import datetime, timedelta
from typing import Iterator

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from relay.contract import (
    RelayEnvelopeCreate,
    RelayEnvelopeRecord,
    RelayMailboxCredential,
    capability_hash,
    capability_matches,
    new_mailbox_id,
    new_relay_capability,
)

RELAY_MAX_ACTIVE_ENVELOPES_PER_MAILBOX = 1000


class Base(DeclarativeBase):
    pass


class RelayMailbox(Base):
    __tablename__ = "relay_mailboxes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    read_capability_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    write_capability_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class RelayStoredEnvelope(Base):
    __tablename__ = "relay_envelopes"

    envelope_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    mailbox_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("relay_mailboxes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    blob: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)


class RelayMailboxList(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[RelayEnvelopeRecord]


def _extract_capability(value: str | None) -> str:
    prefix = "RelayCap "
    if not value or not value.startswith(prefix):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="relay capability required")
    raw = value[len(prefix):].strip()
    if not raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="relay capability required")
    return raw


def create_relay_app(
    *,
    database_url: str,
    bootstrap_secret: str,
    allowed_origins: tuple[str, ...] = (),
    create_schema: bool = False,
) -> FastAPI:
    if len(bootstrap_secret.encode("utf-8")) < 32:
        raise ValueError("relay bootstrap secret must be at least 32 bytes")

    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, future=True, connect_args=connect_args)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    if create_schema:
        Base.metadata.create_all(bind=engine)

    app = FastAPI(title="Digital Crown Opaque Relay", docs_url=None, redoc_url=None)
    if allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(allowed_origins),
            allow_credentials=False,
            allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type"],
        )

    def get_db() -> Iterator[Session]:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def get_mailbox_or_404(db: Session, mailbox_id: str) -> RelayMailbox:
        mailbox = db.get(RelayMailbox, mailbox_id)
        if mailbox is None or not mailbox.active:
            raise HTTPException(status_code=404, detail="mailbox not found")
        return mailbox

    def require_capability(mailbox: RelayMailbox, raw: str, *, privilege: str) -> None:
        expected = (
            mailbox.read_capability_hash
            if privilege == "read"
            else mailbox.write_capability_hash
        )
        if not capability_matches(raw, expected):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid relay capability")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/mailboxes", response_model=RelayMailboxCredential, status_code=201)
    def provision_mailbox(
        response: Response,
        x_relay_bootstrap: str | None = Header(default=None),
        db: Session = Depends(get_db),
    ) -> RelayMailboxCredential:
        if not x_relay_bootstrap or not hmac.compare_digest(x_relay_bootstrap, bootstrap_secret):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid bootstrap credential")

        mailbox_id = new_mailbox_id()
        read_capability = new_relay_capability()
        write_capability = new_relay_capability()
        row = RelayMailbox(
            id=str(mailbox_id),
            read_capability_hash=capability_hash(read_capability),
            write_capability_hash=capability_hash(write_capability),
            active=True,
        )
        db.add(row)
        db.commit()
        response.headers["Cache-Control"] = "no-store"
        return RelayMailboxCredential(
            mailbox_id=mailbox_id,
            read_capability=read_capability,
            write_capability=write_capability,
        )

    @app.post("/v1/mailboxes/{mailbox_id}/envelopes", response_model=RelayEnvelopeRecord, status_code=201)
    def push_envelope(
        mailbox_id: str,
        body: RelayEnvelopeCreate,
        response: Response,
        authorization: str | None = Header(default=None),
        db: Session = Depends(get_db),
    ) -> RelayEnvelopeRecord:
        mailbox = get_mailbox_or_404(db, mailbox_id)
        require_capability(mailbox, _extract_capability(authorization), privilege="write")
        now = datetime.utcnow()

        db.query(RelayStoredEnvelope).filter(
            RelayStoredEnvelope.mailbox_id == mailbox_id,
            RelayStoredEnvelope.expires_at <= now,
        ).delete(synchronize_session=False)

        active_count = db.query(RelayStoredEnvelope).filter(
            RelayStoredEnvelope.mailbox_id == mailbox_id,
            RelayStoredEnvelope.expires_at > now,
        ).count()
        if active_count >= RELAY_MAX_ACTIVE_ENVELOPES_PER_MAILBOX:
            db.rollback()
            raise HTTPException(status_code=429, detail="mailbox quota exceeded")

        row = RelayStoredEnvelope(
            envelope_id=str(body.envelope_id),
            mailbox_id=mailbox_id,
            blob=body.blob,
            created_at=now,
            expires_at=now + timedelta(seconds=body.ttl_seconds),
        )
        db.add(row)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="duplicate envelope") from None

        response.headers["Cache-Control"] = "no-store"
        return RelayEnvelopeRecord(
            envelope_id=body.envelope_id,
            blob=body.blob,
            created_at=row.created_at,
            expires_at=row.expires_at,
        )

    @app.get("/v1/mailboxes/{mailbox_id}/envelopes", response_model=RelayMailboxList)
    def pull_envelopes(
        mailbox_id: str,
        response: Response,
        authorization: str | None = Header(default=None),
        limit: int = Query(default=100, ge=1, le=200),
        db: Session = Depends(get_db),
    ) -> RelayMailboxList:
        mailbox = get_mailbox_or_404(db, mailbox_id)
        require_capability(mailbox, _extract_capability(authorization), privilege="read")
        now = datetime.utcnow()
        rows = (
            db.query(RelayStoredEnvelope)
            .filter(
                RelayStoredEnvelope.mailbox_id == mailbox_id,
                RelayStoredEnvelope.expires_at > now,
            )
            .order_by(RelayStoredEnvelope.created_at.asc())
            .limit(limit)
            .all()
        )
        response.headers["Cache-Control"] = "no-store"
        return RelayMailboxList(
            items=[
                RelayEnvelopeRecord(
                    envelope_id=uuid.UUID(row.envelope_id),
                    blob=row.blob,
                    created_at=row.created_at,
                    expires_at=row.expires_at,
                )
                for row in rows
            ]
        )

    @app.delete("/v1/mailboxes/{mailbox_id}/envelopes/{envelope_id}", status_code=204)
    def delete_envelope(
        mailbox_id: str,
        envelope_id: uuid.UUID,
        authorization: str | None = Header(default=None),
        db: Session = Depends(get_db),
    ) -> Response:
        mailbox = get_mailbox_or_404(db, mailbox_id)
        require_capability(mailbox, _extract_capability(authorization), privilege="read")
        deleted = db.query(RelayStoredEnvelope).filter(
            RelayStoredEnvelope.mailbox_id == mailbox_id,
            RelayStoredEnvelope.envelope_id == str(envelope_id),
        ).delete(synchronize_session=False)
        db.commit()
        if deleted != 1:
            raise HTTPException(status_code=404, detail="envelope not found")
        return Response(status_code=204)

    @app.delete("/v1/mailboxes/{mailbox_id}", status_code=204)
    def revoke_mailbox(
        mailbox_id: str,
        x_relay_bootstrap: str | None = Header(default=None),
        db: Session = Depends(get_db),
    ) -> Response:
        if not x_relay_bootstrap or not hmac.compare_digest(x_relay_bootstrap, bootstrap_secret):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid bootstrap credential")
        mailbox = get_mailbox_or_404(db, mailbox_id)
        mailbox.active = False
        db.query(RelayStoredEnvelope).filter(
            RelayStoredEnvelope.mailbox_id == mailbox_id
        ).delete(synchronize_session=False)
        db.commit()
        return Response(status_code=204)

    return app
