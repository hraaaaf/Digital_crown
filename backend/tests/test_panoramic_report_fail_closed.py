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


def test_report_uses_structured_professional_sections_without_count_summary():
    report = PanoramicReportEngine().generate_markdown(
        manual_anomalies={
            "16": ["carie_dentinaire"],
            "36": ["alveolyse_v"],
            "46": ["implant"],
            "26": ["opacite_sinus"],
        },
        global_findings=["alveolyse_gen_legere"],
    )

    assert "### TECHNIQUE" in report
    assert "### LÉSIONS CARIEUSES" in report
    assert "### PARODONTE ET SUPPORT OSSEUX" in report
    assert "### RESTAURATIONS / PROTHÈSES / IMPLANTS" in report
    assert "### SINUS MAXILLAIRES" in report
    assert "### CONSTATATIONS GÉNÉRALES" in report
    assert "### SYNTHÈSE" in report
    assert "Carie dentinaire — la dent 16." in report
    assert "Alvéolyse verticale (défaut angulaire) — la dent 36." in report
    assert "Implant dentaire — la dent 46." in report
    assert "Opacité sinusienne — la dent 26." in report
    assert "observation(s)" not in report
    assert "constat(s)" not in report


def test_report_preserves_custom_practitioner_text_without_upgrading_it():
    report = PanoramicReportEngine().generate_markdown(
        manual_anomalies={"11": ["Image radio-opaque à corréler cliniquement"]},
        global_findings=[],
    )

    assert "### AUTRES OBSERVATIONS DOCUMENTÉES" in report
    assert "Image radio-opaque à corréler cliniquement — la dent 11." in report
    assert "diagnostic" not in report.lower() or "interprétation diagnostique" in report.lower()


def test_report_is_deterministic_for_same_input():
    engine = PanoramicReportEngine()
    payload = {
        "manual_anomalies": {"26": ["opacite_sinus"], "16": ["carie_dentinaire"]},
        "global_findings": ["denture_mixte", "alveolyse_gen_legere"],
    }

    first = engine.generate_markdown(**payload)
    second = engine.generate_markdown(**payload)

    assert first == second


def test_structured_context_renders_only_explicit_practitioner_normal_states():
    report = PanoramicReportEngine().generate_markdown(
        manual_anomalies={},
        global_findings=[],
        report_context={
            "clinical_question": "Recherche de foyer infectieux avant traitement médical.",
            "image_quality": "diagnostic",
            "caries": {"status": "normal", "note": None},
            "jawbone": {"status": "normal", "note": None},
            "tmj": {"status": "not_assessed", "note": None},
        },
    )

    assert "### QUESTION CLINIQUE" in report
    assert "Recherche de foyer infectieux avant traitement médical." in report
    assert "Qualité jugée suffisante par le praticien" in report
    assert "Pas d'autre image carieuse documentée." in report
    assert "Pas d'anomalie osseuse maxillo-mandibulaire documentée." in report
    assert "Pas d'anomalie osseuse condylienne" not in report
    assert "Articulations temporo-mandibulaires" in report
    assert "Domaines non évalués explicitement" in report


def test_structured_context_abnormal_note_is_preserved_without_diagnostic_upgrade():
    report = PanoramicReportEngine().generate_markdown(
        manual_anomalies={},
        global_findings=[],
        report_context={
            "image_quality": "limited",
            "image_quality_note": "Superposition cervicale antérieure.",
            "sinuses": {
                "status": "abnormal",
                "note": "Voile radio-opaque du sinus maxillaire gauche à corréler au contexte clinique.",
            },
        },
    )

    assert "Qualité limitée pour la lecture panoramique. Superposition cervicale antérieure." in report
    assert "Sinus maxillaires : Voile radio-opaque du sinus maxillaire gauche à corréler au contexte clinique." in report
    assert "diagnostic automatique" not in report.lower()


def test_empty_structured_context_never_creates_negative_findings():
    report = PanoramicReportEngine().generate_markdown(
        manual_anomalies={},
        global_findings=[],
        report_context={},
    )

    assert "Pas d'autre image carieuse documentée." not in report
    assert "Pas d'anomalie osseuse maxillo-mandibulaire documentée." not in report
    assert "Pas d'anomalie sinusienne" not in report
