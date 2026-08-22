from contextvars import ContextVar
from typing import Optional

from sqlalchemy.orm import Session

from backend import models
from backend.services.generators.accounting_gen import AccountingGenerator


class TenantAwareAccountingGenerator(AccountingGenerator):
    """Resolve organization branding from the actor's employer while preserving the actor."""

    _actor_context: ContextVar[Optional[models.User]] = ContextVar(
        "accounting_document_actor", default=None
    )

    @staticmethod
    def _resolve_actor_and_employer(db: Session, user_id: int) -> tuple[models.User, int]:
        actor = db.query(models.User).filter(models.User.id == user_id).first()
        if actor is None:
            raise ValueError(f"Utilisateur introuvable: {user_id}")
        return actor, actor.get_employer_id()

    def _run_with_tenant_context(self, method, patient, data, *, db=None, user_id=None, **kwargs):
        if db is None or user_id is None:
            return method(patient, data, db=db, user_id=user_id, **kwargs)

        actor, employer_id = self._resolve_actor_and_employer(db, user_id)
        token = self._actor_context.set(actor)
        try:
            # The legacy generator resolves CabinetConfig from user_id. Give it the
            # organization owner id, while _build_pdf below restores the real actor.
            return method(patient, data, db=db, user_id=employer_id, **kwargs)
        finally:
            self._actor_context.reset(token)

    def generate_note(self, patient, data, facture_number=None, db=None, user_id=None, **kwargs):
        return self._run_with_tenant_context(
            super().generate_note,
            patient,
            data,
            db=db,
            user_id=user_id,
            facture_number=facture_number,
            **kwargs,
        )

    def generate_devis(self, patient, data, document_number=None, db=None, user_id=None, **kwargs):
        return self._run_with_tenant_context(
            super().generate_devis,
            patient,
            data,
            db=db,
            user_id=user_id,
            document_number=document_number,
            **kwargs,
        )

    def _build_pdf(self, filepath, elements, cloture_text, config=None, user=None, **kwargs):
        actor = self._actor_context.get()
        return super()._build_pdf(
            filepath,
            elements,
            cloture_text,
            config=config,
            user=actor or user,
            **kwargs,
        )
