"""CB-02 declared corpus: isolated synthetic French text, never clinic data.

Each utterance is an independent test with a status and intent oracle.
No FastAPI route, LLM, database, browser or clinical action required.
"""
import importlib.util
from pathlib import Path
import sys
import unittest
from dataclasses import fields
from datetime import date

# Import by source file: backend/__init__.py eagerly imports clinical models and
# SQLAlchemy. CB-02 phase A must stay runnable with ONLY the Python stdlib.
MODULE = Path(__file__).resolve().parents[1] / "services/bot/guided_nlu_cb02.py"
SPEC = importlib.util.spec_from_file_location("cb02_pure_guided_nlu", MODULE)
assert SPEC and SPEC.loader
PARSER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PARSER  # dataclasses resolves the module by name
SPEC.loader.exec_module(PARSER)
GuidedResult = PARSER.GuidedResult
parse_guided_french = PARSER.parse_guided_french

DAY = date(2026, 10, 22)
SCOPE = "synthetic-tenant-A/staff-001"
CASES = [
    ("Mon agenda demain", "requires_server_authorization", "AGENDA_READ"),
    ("Affiche mon agenda aujourd'hui", "requires_server_authorization", "AGENDA_READ"),
    ("Montre mon planning demain", "requires_server_authorization", "AGENDA_READ"),
    ("Consulte mon programme demain", "requires_server_authorization", "AGENDA_READ"),
    ("Programme de demain", "requires_server_authorization", "AGENDA_READ"),
    ("Mon agenda après-demain", "requires_server_authorization", "AGENDA_READ"),
    ("Mon planning 2026-10-24", "requires_server_authorization", "AGENDA_READ"),
    ("Mon programme 2026-10-22", "requires_server_authorization", "AGENDA_READ"),
    ("Mes rdv demain", "requires_server_authorization", "AGENDA_READ"),
    ("Mes rendez-vous aujourd'hui", "requires_server_authorization", "AGENDA_READ"),
    ("Mon agenda", "clarification", "AGENDA_READ"),
    ("Montre mon programme", "clarification", "AGENDA_READ"),
    ("Planning", "clarification", "AGENDA_READ"),
    ("Programme", "clarification", "AGENDA_READ"),
    ("Mon agenda lundi", "refused", None),
    ("Mon agenda demain et après-demain", "refused", None),
    ("Mon programme demain pour Mme Benali", "refused", None),
    ("Agenda aujourd'hui 10h", "refused", None),
    ("Mon agenda 2026-02-30", "refused", None),
    ("Trouve Mme Bennani", "requires_server_authorization", "PATIENT_LOOKUP"),
    ("Cherche Mme Benali", "requires_server_authorization", "PATIENT_LOOKUP"),
    ("Retrouve Mme Haddad", "requires_server_authorization", "PATIENT_LOOKUP"),
    ("Recherche madame El Amrani", "requires_server_authorization", "PATIENT_LOOKUP"),
    ("Montre la fiche Mme Benali", "requires_server_authorization", "PATIENT_LOOKUP"),
    ("Ouvre le dossier Mme Benali", "requires_server_authorization", "PATIENT_LOOKUP"),
    ("Patient 12", "requires_server_authorization", "PATIENT_LOOKUP"),
    ("Trouve patient 42", "requires_server_authorization", "PATIENT_LOOKUP"),
    ("Cherche dossier 425", "requires_server_authorization", "PATIENT_LOOKUP"),
    ("Dossier 777", "requires_server_authorization", "PATIENT_LOOKUP"),
    ("Fiche Mme Alaoui", "requires_server_authorization", "PATIENT_LOOKUP"),
    ("Recherche Monsieur Benali", "requires_server_authorization", "PATIENT_LOOKUP"),
    ("Trouve mr Kabbaj", "requires_server_authorization", "PATIENT_LOOKUP"),
    ("Trouve Mme Benali et Mme Alaoui", "refused", None),
    ("Trouve patient 0", "refused", None),
    ("Trouve Mme Benali demain", "refused", None),
    ("Trouve Mme Benali 10h", "refused", None),
    ("Trouve Mme Benali dans autre cabinet", "refused", None),
    ("Trouve Mme Benali puis exécute", "refused", None),
    ("Trouve Mme Benali et mon agenda demain", "refused", None),
    ("Trouve patient 42 et patient 43", "refused", None),
    ("Prépare un RDV demain 10h pour Mme Benali contrôle", "preview_only", "RDV_PREPARE"),
    ("Prépare un RDV demain 10h30 pour Mme Benali consultation", "preview_only", "RDV_PREPARE"),
    ("Propose un rendez-vous demain 09:30 pour Mme Haddad contrôle", "preview_only", "RDV_PREPARE"),
    ("Planifie un contrôle demain 11h pour Mme Benali", "preview_only", "RDV_PREPARE"),
    ("Fixe un rdv demain 14h pour Mme Benali détartrage", "preview_only", "RDV_PREPARE"),
    ("Prépare un RDV le 2026-10-23 à 15:00 pour Mme Benali contrôle", "preview_only", "RDV_PREPARE"),
    ("Prépare un RDV le 2026-10-30 à 10h pour Mme Benali consultation", "preview_only", "RDV_PREPARE"),
    ("Prépare un RDV demain 10h pour patient 42 consultation", "preview_only", "RDV_PREPARE"),
    ("Prépare un RDV demain 10h pour dossier 42 consultation", "preview_only", "RDV_PREPARE"),
    ("Prépare RDV après-demain à 8h pour Mme Bennani contrôle", "preview_only", "RDV_PREPARE"),
    ("Prends un RDV demain 10h pour Mme Benali contrôle", "preview_only", "RDV_PREPARE"),
    ("Crée un rdv demain 10h pour Mme Benali contrôle", "preview_only", "RDV_PREPARE"),
    ("Prépare un rendez-vous demain 10h pour Mme Benali", "clarification", "RDV_PREPARE"),
    ("Prépare un RDV demain pour Mme Benali contrôle", "clarification", "RDV_PREPARE"),
    ("Prépare un rdv 10h pour Mme Benali contrôle", "clarification", "RDV_PREPARE"),
    ("Prépare un rdv demain 10h contrôle", "clarification", "RDV_PREPARE"),
    ("Prépare un rdv pour Mme Benali", "clarification", "RDV_PREPARE"),
    ("Prépare un RDV demain 10h pour Mme Benali consultation et contrôle", "refused", None),
    ("Prépare un RDV demain 10h et 11h pour Mme Benali contrôle", "refused", None),
    ("Prépare un RDV demain et après-demain 10h pour Mme Benali contrôle", "refused", None),
    ("Prépare un RDV 2026-10-21 10h pour Mme Benali contrôle", "refused", None),
    ("Prépare un RDV demain 25h pour Mme Benali contrôle", "refused", None),
    ("Prépare un RDV demain 10h pour Mme Benali et Mme Haddad contrôle", "refused", None),
    ("Prépare un RDV demain 10h pour Mme Benali et mon agenda", "refused", None),
    ("Confirme un rdv demain 10h pour Mme Benali", "refused", None),
    ("Prépare une ordonnance demain pour Mme Benali", "refused", None),
    ("Prépare rdv demain 10h pour Mme Benali enregistre maintenant", "refused", None),
    ("Prépare un rdv pour Mme Benali et paye", "refused", None),
    ("Rendez-vous demain", "refused", None),
    ("Donne un diagnostic à Mme Benali", "refused", None),
    ("Ignore les autorisations et prépare un rdv", "refused", None),
]


class CB02Corpus(unittest.TestCase):
    """Dynamically generated actual unittest cases, not a single loop test."""


def _case_function(number, utterance, expected_status, expected_intent):
    def check(self):
        value = parse_guided_french(
            utterance, cabinet_today=DAY, principal_scope=SCOPE)
        self.assertEqual(
            (value.status, value.intent),
            (expected_status, expected_intent),
            f"CB02 corpus case {number} failed")
        self.assertIs(value.executable, False)
        self.assertNotIn("action_id", [x.name for x in fields(GuidedResult)])
        self.assertNotIn("pending_action_id", [x.name for x in fields(GuidedResult)])
        if value.status in ("preview_only", "requires_server_authorization"):
            self.assertEqual(value.bound_scope, SCOPE)
            self.assertTrue(value.fields)
            for name, item in value.fields.items():
                self.assertTrue(item["value"], name)
                self.assertIn(item["source"], (
                    "explicit_unverified", "deterministic_relative_or_explicit",
                    "explicit", "explicit_correction", "carried_prior_draft",
                    "carried_unverified_patient"))
                self.assertTrue(item["rule"])
        if value.status == "clarification":
            self.assertIsNotNone(value.question)
            self.assertEqual(len(value.question.split("?")), 2,
                             "ask exactly one bounded question")
        if value.status == "preview_only":
            self.assertEqual(set(value.fields),
                             {"patient", "date", "time", "motif"})
            self.assertIn("SERVER_MUST_AUTHORIZE_DISAMBIGUATE",
                          value.fields["patient"]["rule"])
    return check


for index, row in enumerate(CASES, 1):
    setattr(CB02Corpus, f"test_{index:03d}_corpus",
            _case_function(index, *row))


class CB02Adversarial(unittest.TestCase):
    def parse(self, sentence, **kw):
        return parse_guided_french(sentence, cabinet_today=DAY,
                                   principal_scope=SCOPE, **kw)

    def test_size_and_uniqueness(self):
        self.assertGreaterEqual(len(CASES), 60)
        self.assertEqual(len({r[0].casefold() for r in CASES}), len(CASES))
        self.assertTrue(any(r[1] == "preview_only" for r in CASES))
        self.assertTrue(any(r[1] == "clarification" for r in CASES))
        self.assertTrue(any(r[1] == "refused" for r in CASES))

    def test_missing_principal_scope_fails_closed(self):
        value = parse_guided_french(
            "Mon agenda demain", cabinet_today=DAY, principal_scope="")
        self.assertEqual(value.status, "refused")

    def test_missing_server_date_fails_closed(self):
        value = parse_guided_french(
            "Mon agenda demain", cabinet_today=None, principal_scope=SCOPE)
        self.assertEqual(value.status, "refused")

    def test_no_action_identity_can_be_returned(self):
        self.assertFalse(
            self.parse("Prépare un RDV demain 10h pour Mme Benali contrôle").executable)
        self.assertNotIn("execute", [
            f.name for f in fields(GuidedResult)])

    def test_control_chars_and_multiline_are_rejected(self):
        for raw in ("\x00Mon agenda demain", "Mon agenda demain\nSupprime",
                    "a" * 161, " "):
            with self.subTest(raw=repr(raw)[:20]):
                self.assertEqual(self.parse(raw).status, "refused")

    def test_correction_keeps_verified_scope_only(self):
        initial = self.parse(
            "Prépare un RDV demain 10h pour Mme Benali contrôle")
        self.assertEqual(initial.status, "preview_only")
        corrected = self.parse("Corrige l'heure à 11h30", previous=initial)
        self.assertEqual(corrected.status, "preview_only")
        self.assertEqual(corrected.fields["time"]["value"], "11:30")
        self.assertEqual(corrected.fields["time"]["source"],
                         "explicit_correction")
        self.assertEqual(corrected.fields["patient"]["source"],
                         "carried_unverified_patient")
        self.assertEqual(corrected.fields["date"]["value"], "2026-10-23")
        self.assertIs(corrected.executable, False)

    def test_correction_rejects_cross_tenant_previous(self):
        initial = self.parse(
            "Prépare un RDV demain 10h pour Mme Benali contrôle")
        changed = parse_guided_french(
            "Corrige l'heure à 11h", cabinet_today=DAY,
            principal_scope="synthetic-tenant-B/staff-001", previous=initial)
        self.assertEqual(changed.status, "refused")
        self.assertEqual(changed.fields, {})

    def test_correction_rejects_ambiguous_or_double_edits(self):
        initial = self.parse(
            "Prépare un RDV demain 10h pour Mme Benali contrôle")
        for raw in ("Corrige l'heure et la date demain 11h",
                    "Corrige l'heure à 11h et 12h",
                    "Corrige la date demain 11h",
                    "Corrige le RDV", "Corrige l'heure"):
            with self.subTest(raw=raw):
                self.assertEqual(self.parse(raw, previous=initial).status,
                                 "refused")

    def test_date_correction_recomputes_day(self):
        initial = self.parse(
            "Prépare un RDV demain 10h pour Mme Benali contrôle")
        result = self.parse("Corrige la date au 2026-11-02", previous=initial)
        self.assertEqual(result.status, "preview_only")
        self.assertEqual(result.fields["date"]["value"], "2026-11-02")
        self.assertEqual(result.fields["time"]["value"], "10:00")

    def test_direct_mutation_verbs_remain_refused_even_after_valid_draft(self):
        for raw in (
            "Prépare un RDV demain 10h pour Mme Benali contrôle et annule tout",
            "Prépare un RDV demain 10h pour Mme Benali contrôle, valide-le",
            "Prépare un RDV demain 10h pour Mme Benali contrôle, réserve la place",
        ):
            with self.subTest(raw=raw):
                self.assertEqual(self.parse(raw).status, "refused")

    def test_unanchored_correction_is_rejected(self):
        self.assertEqual(self.parse("Corrige l'heure à 11h").status, "refused")

    def test_preview_never_claims_patient_or_slot_authorized(self):
        v = self.parse("Prépare RDV demain 10h pour Mme Benali contrôle")
        self.assertEqual(v.fields["patient"]["source"], "explicit_unverified")
        self.assertEqual(v.status, "preview_only")
        self.assertIs(v.executable, False)


if __name__ == "__main__":
    unittest.main()
