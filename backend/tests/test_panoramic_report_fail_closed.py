"""Fail-closed semantic contract for panoramic reporting."""

from backend.services.panoramic_report_engine import PanoramicReportEngine


def test_empty_annotations_do_not_infer_normality_or_treatment():
    report = PanoramicReportEngine().generate_markdown(
        detections=[],
        manual_anomalies={},
        global_findings=[],
    )

    forbidden = (
        "aspect normal",
        "Transparence normale",
        "Absence de lésion osseuse",
        "articulations temporo-mandibulaires respectées",
        "### CONDUITE À TENIR",
        "HBMD",
        "HBFD",
        "HBGD",
        "HBJD",
    )
    for token in forbidden:
        assert token not in report

    assert "non document" in report.lower() or "non évalu" in report.lower()


def test_manual_anomaly_is_reported_as_practitioner_observation_without_ccam():
    report = PanoramicReportEngine().generate_markdown(
        manual_anomalies={"16": ["carie_dentinaire"]},
        global_findings=[],
    )

    assert "carie" in report.lower()
    assert "16" in report
    assert "HBMD042" not in report
    assert "### CONDUITE À TENIR" not in report
    assert "restauration" not in report.lower()


def test_unannotated_domains_are_not_declared_normal_when_another_finding_exists():
    report = PanoramicReportEngine().generate_markdown(
        manual_anomalies={"16": ["opacite_sinus"]},
        global_findings=[],
    )

    assert "Opacité sinusienne" in report
    assert "Transparence normale" not in report
    assert "articulations temporo-mandibulaires respectées" not in report
    assert "Absence de lésion osseuse" not in report


def test_absent_tooth_does_not_generate_rehabilitation_recommendation():
    report = PanoramicReportEngine().generate_markdown(
        manual_anomalies={"36": ["dent_absente"]},
        global_findings=[],
    )

    assert "36" in report
    assert "Réhabilitation prothétique" not in report
    assert "à réhabiliter" not in report
    assert "### CONDUITE À TENIR" not in report
