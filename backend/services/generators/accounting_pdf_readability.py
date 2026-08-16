"""P3-F readability policy for accounting PDFs.

A financial document must never solve layout pressure by shrinking text below
Digital Crown's central readable typography floor. Long content must wrap or
flow to another page instead.
"""

from backend.services.generators.document_typography import MIN_READABLE_SIZE


def readable_accounting_font_floor(requested_min_fs: float | int | None = None) -> float:
    """Return the minimum permitted font size for accounting content.

    A caller may request a stricter/larger floor, but never a smaller one.
    """
    if requested_min_fs is None:
        return float(MIN_READABLE_SIZE)
    try:
        requested = float(requested_min_fs)
    except (TypeError, ValueError):
        return float(MIN_READABLE_SIZE)
    return max(requested, float(MIN_READABLE_SIZE))


def is_readable_accounting_font_size(font_size: float | int) -> bool:
    """True when an accounting font size respects the central readable floor."""
    try:
        return float(font_size) >= float(MIN_READABLE_SIZE)
    except (TypeError, ValueError):
        return False
