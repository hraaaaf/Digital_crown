#!/usr/bin/env python3
"""Exact-diff proof for waves 02–06: bounded neutral + semantic status Tailwind changes.

Status shades are mapped only to existing danger/success/warning role tokens;
brand palettes, saturated button fills, chart meaning, printed content and
clinical logic remain unchanged. Dark scrims are deliberately excluded.
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
    "frontend/src/features/admin/DocumentStudio/HouseWizard.tsx",
    "frontend/src/features/admin/DocumentStudio/EliteAssistant.tsx",
    "frontend/src/features/admin/DocumentStudio/StudioFooter.tsx",
    "frontend/src/features/patients/AddPatientForm.tsx",
    "frontend/src/features/patients/CnopsInsuranceSubmissionReview.tsx",
    "frontend/src/features/patients/FarInsuranceSubmissionReview.tsx",
    "frontend/src/features/patients/CnssInsuranceSubmissionReview.tsx",
    "frontend/src/pages/RegisterPage.tsx",
    "frontend/src/features/agenda/AgendaStudio.tsx",
    "frontend/src/features/patients/EditPatientForm.tsx",
    "frontend/src/pages/Dashboard.tsx",
    "frontend/src/features/patients/PatientDetailsInner.tsx",
    "frontend/src/features/patients/components/ClinicalHubCore.tsx",
    "frontend/src/features/patients/components/PatientMediaTimeline.tsx",
    "frontend/src/features/patients/components/MotifSelector.tsx",
    "frontend/src/components/odontogram/TreatmentSelector.tsx",
    "frontend/src/features/patients/PatientDocuments.tsx",
    "frontend/src/features/admin/DocumentStudio/Forms/CertificateFormInner.tsx",
    "frontend/src/features/admin/DocumentStudio/Forms/LibreForm.tsx",
    "frontend/src/features/admin/DocumentStudio/Forms/PrescriptionGuideModal.tsx",
    "frontend/src/features/admin/DocumentStudio/Forms/PrescriptionPresetBar.tsx",
    "frontend/src/features/admin/DocumentStudio/TreatmentPlanStudio.tsx",
    "frontend/src/features/admin/DocumentStudio/StudioTabs.tsx",
    "frontend/src/features/admin/DocumentStudio/DocumentHubDialogs.tsx",
    "frontend/src/features/admin/DocumentStudio/Forms/TemplateOverwriteDialog.tsx",
    "frontend/src/features/admin/DocumentStudio/Forms/PrescriptionForm.tsx",
    "frontend/src/features/patients/components/wizards/AssistantExamenComplet.tsx",
    "frontend/src/features/admin/DocumentStudio/Forms/InstallmentStudioInner.tsx",
    "frontend/src/features/admin/DocumentStudio/StudioHeader.tsx",
    "frontend/src/features/patients/components/InstallmentPlanModal.tsx",
    "frontend/src/features/mobile/Dashboard/views/AgendaView.tsx",
)
STATUS_FILES = (
    "frontend/src/features/admin/AccountingStudioLegacy.tsx",
    "frontend/src/features/superadmin/SuperAdminDashboard.tsx",
    "frontend/src/features/agenda/AgendaModal.tsx",
    "frontend/src/pages/AccountingPage.tsx",
    "frontend/src/features/admin/TeamManager.tsx",
    "frontend/src/features/admin/Settings/tabs/CatalogTab.tsx",
    "frontend/src/pages/StockPage.tsx",
    "frontend/src/components/LabJobsBoard.tsx",
    "frontend/src/pages/Analytics.tsx",
    "frontend/src/features/patients/components/ClinicalHubCore.tsx",
    "frontend/src/features/admin/Settings/tabs/SecurityTab.tsx",
    "frontend/src/features/patients/CnssInsuranceSubmissionReview.tsx",
    "frontend/src/features/patients/AddPatientForm.tsx",
    "frontend/src/features/patients/PatientDocuments.tsx",
    "frontend/src/features/patients/components/PatientFinances.tsx",
    "frontend/src/features/patients/PatientList.tsx",
    "frontend/src/features/patients/EditPatientForm.tsx",
    "frontend/src/features/patients/components/PatientCompanionPanel.tsx",
    "frontend/src/features/patients/components/PatientJourney.tsx",
    "frontend/src/features/patients/components/MotifSelector.tsx",
    "frontend/src/features/admin/Settings/tabs/AgendaTab.tsx",
    "frontend/src/features/agenda/AgendaStudio.tsx",
    "frontend/src/pages/PatientCompanionPage.tsx",
    "frontend/src/pages/PartnerCatalogAdminPage.tsx",
    "frontend/src/pages/Dashboard.tsx",
    "frontend/src/pages/LoginPage.tsx",
    "frontend/src/features/admin/DocumentStudio/HouseWizard.tsx",
)
STATUS = re.compile(r"(?<![\w/-])((?:[\w-]+:)*)(bg|text|border)-(red|rose|emerald|green|amber|orange)-(\d{2,3})(/\d+)?(?![\w/-])")

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



def migrate_status(src: str) -> str:
    """Unambiguous semantic statuses only: no saturated fills or dark charts."""
    def replace(m: re.Match[str]) -> str:
        prefix, utility, shade_name, shade, alpha = m.groups()
        role = ("danger" if shade_name in ("red", "rose")
                else "success" if shade_name in ("emerald", "green") else "warning")
        level = int(shade)
        new = None
        if utility == "text" and level >= 300:
            new = "text-" + role
        elif utility == "border" and level <= 300:
            new = "border-" + role + "-border"
        elif utility == "bg" and level <= 100:
            new = "bg-" + role + "-surface"
        return prefix + new + (alpha or "") if new else m.group(0)
    return STATUS.sub(replace, src)


def test_exact_diff() -> int:
    # Verifies text *byte-for-byte* after the finite, whitelisted palette
    # mapping: no API, auth, patient, calculation or TSX expression edit can pass.
    results: list[tuple[str, int]] = []
    for file in sorted(set(FILES) | set(STATUS_FILES)):
        original = subprocess.check_output(["git", "show", BASE + ":" + file], cwd=ROOT).decode("utf-8")
        current = (ROOT / file).read_text(encoding="utf-8")
        neutral_expected = migrate(original) if file in FILES else original
        expected = migrate_status(neutral_expected) if file in STATUS_FILES else neutral_expected
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
        count = 0
        if file in FILES:
            count += len(NEUTRAL.findall(original)) + len(WHITE.findall(original))
            count -= len(NEUTRAL.findall(neutral_expected)) + len(WHITE.findall(neutral_expected))
        if file in STATUS_FILES:
            count += len(STATUS.findall(neutral_expected)) - len(STATUS.findall(current))
        results.append((file, count))

    total = sum(x[1] for x in results)
    if total < 3090:
        print("THEME_NEUTRAL_BATCH_REDUCTION_TOO_SMALL", total)
        return 1
    css = (ROOT / "frontend/src/index.css").read_text(encoding="utf-8")
    for role in ("--color-background:", "--color-card:", "--color-input-field:",
                 "--color-text-main:", "--color-text-muted:", "--color-border-main:",
                 "--color-border-hover:", "--color-success:", "--color-success-border:",
                 "--color-success-surface:", "--color-danger:", "--color-danger-border:",
                 "--color-danger-surface:", "--color-warning:", "--color-warning-border:",
                 "--color-warning-surface:"):
        if role not in css:
            print("THEME_NEUTRAL_BATCH_MISSING_ROLE", role)
            return 1
    for theme in ("emerald", "rose", "ocean", "graphite", "prestige", "dark", "high-contrast"):
        if "[data-theme='" + theme + "']" not in css:
            print("THEME_NEUTRAL_BATCH_MISSING_THEME", theme)
            return 1
    print("THEME_NEUTRAL_AND_STATUS_WAVES02_TO_06_PASS", {"files": len(results), "semanticColorsRemoved": total, "statusOnlyFiles": len(set(STATUS_FILES) - set(FILES)),
                                       "noBehaviorOrStructureChanges": True})
    return 0


if __name__ == "__main__":
    sys.exit(test_exact_diff())
