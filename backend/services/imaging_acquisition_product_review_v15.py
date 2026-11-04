"""LOT06 B06-2: ephemeral staff-bound acquisition review. NO clinical receipt.

The review state is intentionally process-local/volatile: a worker restart,
different worker or loss of session MUST deny rather than persist a patient
association. No durable approval / ClinicalAsset is authorized until B06-3.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import secrets
import threading
import time

from tools.imaging_gateway.native_inventory_protocol_v15 import UnassignedCapture

TTL_SECONDS = 90
MAX_REVIEWS = 64


class ProductReviewDenied(ValueError):
    """Sanitized, non-PHI refusal code."""


@dataclass(frozen=True)
class PendingCaptureReview:
    review_id: str
    challenge_digest: str
    tenant: int
    workstation: str
    staff: int
    session_digest: str
    capture: UnassignedCapture
    patient: int
    expires_at: int


def _fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class ProductReviewStore:
    """Single-process best-effort selection guard; NEVER a durable consent."""

    def __init__(self):
        self._lock = threading.RLock()
        self._pending: dict[str, PendingCaptureReview] = {}
        self._used: set[tuple[int, str, int]] = set()

    @staticmethod
    def _key(review: PendingCaptureReview) -> tuple[int, str, int]:
        return (review.tenant, review.workstation,
                review.capture.id, review.capture.digest)

    def start(self, *, tenant: int, workstation: str, staff: int,
              session: str, capture: UnassignedCapture,
              patient: int) -> tuple[PendingCaptureReview, str]:
        now = int(time.time())
        with self._lock:
            self._pending = {
                k: v for k, v in self._pending.items()
                if v.expires_at > now
            }
            key = (tenant, workstation, capture.id)
            if key in self._used or any(
                self._key(v) == key for v in self._pending.values()
            ):
                raise ProductReviewDenied("CAPTURE_ALREADY_UNDER_REVIEW")
            if len(self._pending) >= MAX_REVIEWS:
                raise ProductReviewDenied("REVIEW_CAPACITY_REACHED")
            review_id, challenge = secrets.token_urlsafe(24), secrets.token_urlsafe(32)
            review = PendingCaptureReview(
                review_id=review_id,
                challenge_digest=_fingerprint(challenge),
                tenant=tenant, workstation=workstation, staff=staff,
                session_digest=_fingerprint(session),
                capture=capture, patient=patient,
                expires_at=now + TTL_SECONDS,
            )
            self._pending[review_id] = review
            return review, challenge

    def require(self, *, review_id: str, tenant: int, workstation: str,
                staff: int, session: str, challenge: str) -> PendingCaptureReview:
        with self._lock:
            review = self._pending.get(review_id)
            if (review is None or review.expires_at <= int(time.time())
                    or review.tenant != tenant or review.workstation != workstation
                    or review.staff != staff
                    or not hmac.compare_digest(
                        review.session_digest, _fingerprint(session)
                    )
                    or not isinstance(challenge, str)
                    or not hmac.compare_digest(
                        review.challenge_digest, _fingerprint(challenge)
                    )):
                raise ProductReviewDenied("REVIEW_SESSION_OR_CHALLENGE_DENIED")
            return review

    def consume(self, *, review_id: str, tenant: int, workstation: str,
                staff: int, session: str, challenge: str) -> PendingCaptureReview:
        with self._lock:
            review = self.require(
                review_id=review_id, tenant=tenant, workstation=workstation,
                staff=staff, session=session, challenge=challenge,
            )
            self._pending.pop(review_id)
            self._used.add(self._key(review))
            return review

    def cancel(self, *, review_id: str, tenant: int, workstation: str,
               staff: int, session: str, challenge: str) -> None:
        with self._lock:
            self.require(
                review_id=review_id, tenant=tenant, workstation=workstation,
                staff=staff, session=session, challenge=challenge,
            )
            self._pending.pop(review_id)
