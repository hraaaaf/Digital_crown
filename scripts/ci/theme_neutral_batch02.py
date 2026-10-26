#!/usr/bin/env python3
"""Exact-diff proof for waves 02+03: only bounded neutral Tailwind classes changed.

No semantic status colors, chart meaning, printed content or clinical logic is
transformed by this codemod; it deliberately leaves dark/neutrals used as
scrims and low-opacity white overlays for subsequent targeted review.
"""
from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = "72302ecd6fcddd526a76370ce04af55ff2b41eab"
FILES = (
    "frontend/src/features/admin/AccountingStudioLegacy.tsx",
    "frontend/src/features/superadmin/SuperAdminDashboard.tsx",
    "frontend/src/features/agenda/AgendaModal.tsx",
    "frontend/src/pages/AccountingPage.tsx",
    "frontend/src/features/admin/TeamManager.tsx",
    "frontend/src/features/admin/Settings/tabs/CatalogTab.tsx",
    "frontend/src/pages/LandingPage.tsx",
    "frontend/src/pages/Analytics.tsx",
    "frontend/src/pages/StockPage.tsx",
    "frontend/src/features/admin/Settings/tabs/AgendaTab.tsx",
    "frontend/src/components/LabJobsBoard.tsx",
    "frontend/src/features/admin/Settings/tabs/SecurityTab.tsx",
    "frontend/src/features/accounting/components/TreasuryPanel.tsx",
    "frontend/src/pages/ActivateTrialPage.tsx",
    "frontend/src/pages/PatientCompanionPage.tsx",
    "frontend/src/features/agenda/MultiPractitionerTimelineView.tsx",
    "frontend/src/features/agenda/WeeklyView.tsx",
    "frontend/src/features/agenda/DailyView.tsx",
    "frontend/src/features/admin/Settings/tabs/PractitionerAvailabilityPanel.tsx",
    "frontend/src/features/admin/Security/MobileSecurity.tsx",
    "frontend/src/features/admin/Security/AuditLogViewer.tsx",
    "frontend/src/pages/WaitingRoomPage.tsx",
    "frontend/src/features/admin/Settings/tabs/ProfileTab.tsx",
    "frontend/src/pages/LoginPage.tsx",
    "frontend/src/pages/PartnerCatalogAdminPage.tsx",
    "frontend/src/features/admin/DocumentStudio/Forms/QuickEntryBar.tsx",
    "frontend/src/features/admin/DocumentStudio/VigilanceRadar.tsx",
    "frontend/src/features/patients/components/PatientJourney.tsx",
    "frontend/src/features/agenda/MonthlyView.tsx",
)
NEUTRAL = re.compile(r"(?<![\w/-])((?:[\w-]+:)*)(bg|text|border|divide|placeholder)-(slate|gray|zinc)-(\d{2,3})(/\d+)?(?![\w/-])")
WHITE = re.compile(r"(?<![\w/-])((?:[\w-]+:)*)bg-white(/(\d{1,3}))?(?![\w/-])")


def migrate(src: str) -> str:
    def replace_neutral(m: re.Match[str]) -> str:
        prefix, role, _, shade, alpha = m.groups()
        n = int(shade)
        dest = None
        if role in ("text", "placeholder"):
            dest = role + "-text-" + ("main" if n >= 650 else "muted")
        elif role in ("border", "divide"):
            dest = role + "-border-" + ("hover" if n >= 300 else "main")
        elif role == "bg" and n <= 200:
            dest = "bg-" + ("input-field" if n >= 100 else "background")
        return prefix + dest + (alpha or "") if dest else m.group(0)

    result = NEUTRAL.sub(replace_neutral, src)

    def replace_white(m: re.Match[str]) -> str:
        prefix, alpha, value = m.groups()
        return prefix + "bg-card" + (alpha or "") if not alpha or int(value) >= 30 else m.group(0)

    return WHITE.sub(replace_white, result)


def test_exact_diff() -> int:
    # Verifies text *byte-for-byte* after the finite, whitelisted palette
    # mapping: no API, auth, patient, calculation or TSX expression edit can pass.
    results: list[tuple[str, int]] = []
    for file in FILES:
        original = subprocess.check_output(["git", "show", BASE + ":" + file], cwd=ROOT).decode("utf-8")
        current = (ROOT / file).read_text(encoding="utf-8")
        expected = migrate(original)
        if current != expected:
            print("THEME_NEUTRAL_BATCH_NONCOSMETIC_DIFF_REFUSED", file)
            return 1
        if current == original:
            print("THEME_NEUTRAL_BATCH_UNCHANGED_FILE_REFUSED", file)
            return 1
        # Count only transformed semantic classes, not non-thematic exceptions.
        from difflib import SequenceMatcher
        # Measurable count = old palette class count minus new palette class count,
        # using exactly the two source regexes, matching the migration's audit.
        count = len(NEUTRAL.findall(original)) + len(WHITE.findall(original))
        count -= len(NEUTRAL.findall(current)) + len(WHITE.findall(current))
        results.append((file, count))

    total = sum(x[1] for x in results)
    if total < 1550:
        print("THEME_NEUTRAL_BATCH_REDUCTION_TOO_SMALL", total)
        return 1
    css = (ROOT / "frontend/src/index.css").read_text(encoding="utf-8")
    for role in ("--color-background:", "--color-card:", "--color-input-field:",
                 "--color-text-main:", "--color-text-muted:", "--color-border-main:",
                 "--color-border-hover:"):
        if role not in css:
            print("THEME_NEUTRAL_BATCH_MISSING_ROLE", role)
            return 1
    for theme in ("emerald", "rose", "ocean", "graphite", "prestige", "dark", "high-contrast"):
        if "[data-theme='" + theme + "']" not in css:
            print("THEME_NEUTRAL_BATCH_MISSING_THEME", theme)
            return 1
    print("THEME_NEUTRAL_WAVES02_03_PASS", {"files": len(results), "neutralClassesRemoved": total,
                                       "noBehaviorOrStructureChanges": True})
    return 0


if __name__ == "__main__":
    sys.exit(test_exact_diff())
