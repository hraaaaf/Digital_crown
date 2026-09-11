"""Canonical commercial subscription policy.

License validity remains a separate concern.  This module owns only the
commercial team limits attached to GOLD/PREMIUM/ELITE subscriptions.
"""
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from backend import models


@dataclass(frozen=True)
class TeamLimits:
    dentists: Optional[int]
    secretaries: Optional[int]


@dataclass(frozen=True)
class TeamUsage:
    dentists: int
    secretaries: int
    pending: int


TEAM_LIMITS: dict[str, TeamLimits] = {
    models.SubscriptionPlan.GOLD.value: TeamLimits(dentists=1, secretaries=2),
    models.SubscriptionPlan.PREMIUM.value: TeamLimits(dentists=2, secretaries=6),
    # None means genuinely unlimited. Never replace this with an arbitrary
    # sentinel such as 999: commercial semantics must not depend on a fake cap.
    models.SubscriptionPlan.ELITE.value: TeamLimits(dentists=None, secretaries=None),
}


def normalize_plan(plan: object) -> str:
    if isinstance(plan, models.SubscriptionPlan):
        return plan.value
    if isinstance(plan, str):
        normalized = plan.upper()
        if normalized in TEAM_LIMITS:
            return normalized
    return models.SubscriptionPlan.GOLD.value


def get_team_limits(plan: object) -> TeamLimits:
    return TEAM_LIMITS[normalize_plan(plan)]


def is_limit_reached(used: int, limit: Optional[int]) -> bool:
    return limit is not None and used >= limit


def exceeds_limit(used: int, limit: Optional[int]) -> bool:
    return limit is not None and used > limit


def count_reserved_team_usage(db: Session, employer_id: int) -> TeamUsage:
    """Count quota reservations using the same semantics as team management.

    The owner occupies one dentist seat. Approved and pending team members both
    reserve seats so invitations cannot bypass a later plan downgrade.
    """
    members = db.query(models.User).filter(
        models.User.employer_id == employer_id,
        models.User.approval_status.in_([
            models.ApprovalStatus.APPROVED.value,
            models.ApprovalStatus.PENDING.value,
        ]),
    ).all()
    dentists = 1 + sum(1 for member in members if member.role == models.UserRole.DENTISTE)
    secretaries = sum(1 for member in members if member.role == models.UserRole.SECRETAIRE)
    pending = sum(
        1 for member in members
        if member.approval_status == models.ApprovalStatus.PENDING.value
    )
    return TeamUsage(dentists=dentists, secretaries=secretaries, pending=pending)


def plan_can_accommodate(plan: object, usage: TeamUsage) -> bool:
    limits = get_team_limits(plan)
    return not (
        exceeds_limit(usage.dentists, limits.dentists)
        or exceeds_limit(usage.secretaries, limits.secretaries)
    )
