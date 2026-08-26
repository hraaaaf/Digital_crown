from backend.routers.auth import has_permission


FINANCIAL_NOTIFICATION_PREFIXES = (
    "OVERDUE_PAYMENT",
    "HIGH_VALUE_RISK",
    "ORTHO_SEMESTER_",
)


def is_financial_mobile_notification(alert_type: str | None) -> bool:
    value = str(alert_type or "")
    return value.startswith(FINANCIAL_NOTIFICATION_PREFIXES)


def user_can_receive_mobile_notification(user, alert_type: str | None) -> bool:
    """Mirror the in-app mobile notification gate for OS push recipient selection."""
    if not has_permission(user, "patients"):
        return False
    if is_financial_mobile_notification(alert_type):
        return has_permission(user, ["accounting", "payments"])
    return True
