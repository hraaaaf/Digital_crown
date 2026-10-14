"""Deterministic Crown Bot POC tests. Synthetic IDs only; no DB or network."""

from datetime import date
import unittest

from backend.services.bot.workflow_poc import PocConversation


TODAY = date(2026, 10, 14)


class TestCrownBotZeroLlmPoc(unittest.TestCase):
    def setUp(self):
        self.bot = PocConversation(today=TODAY)

    def send(self, *messages):
        turns = [self.bot.handle(message) for message in messages]
        return turns[-1]

    def test_exact_entry_commands_only(self):
        self.assertEqual(self.send("crée un rendez-vous").status, "help")
        self.assertEqual(self.bot.state, "idle")
        self.assertEqual(self.send("/rdv").status, "clarification")

    def test_patient_lookup_is_read_proposal_only(self):
        turn = self.send("/patient", "42")
        self.assertEqual(turn.status, "read_request")
        self.assertEqual(
            turn.proposal, {"type": "QUERY_PATIENT", "params": {"patient_id": 42}}
        )
        self.assertEqual(self.bot.state, "idle")

    def test_no_implicit_patient_resolution_or_phi(self):
        self.send("/patient")
        self.assertEqual(self.send("Sara").status, "clarification")
        self.assertEqual(self.bot.slots, {})
        self.assertIsNone(self.send(" ").proposal)

    def test_reject_bad_patient_identifiers(self):
        self.send("/patient")
        for value in ["0", "-1", "0012", "12 or 1=1", "1; DROP TABLE", "9" * 15]:
            self.assertEqual(self.send(value).status, "clarification", value)
            self.assertNotIn("patient_id", self.bot.slots)

    def test_complete_appointment_proposal_requires_explicit_confirmation(self):
        turns = [
            self.bot.handle(x)
            for x in ["/rdv", "12", "2026-10-15", "14:30", "30"]
        ]
        self.assertTrue(all(t.proposal is None for t in turns))
        self.assertEqual(turns[-1].status, "confirmation_required")
        self.assertEqual(self.send("oui").status, "confirmation_required")
        final = self.send("CONFIRMER")
        self.assertEqual(final.status, "proposal_only")
        self.assertEqual(
            final.proposal, {
                "type": "CREATE_APPOINTMENT",
                "params": {
                    "patient_id": 12,
                    "datetime_start": "2026-10-15T14:30:00",
                    "duration_minutes": 30,
                },
            },
        )
        self.assertIn("NON exécutée", final.message)
        self.assertEqual(self.bot.state, "idle")
        self.assertIsNone(self.send("CONFIRMER").proposal)

    def test_prevent_silent_date_or_time_defaults(self):
        self.send("/rdv", "3")
        self.assertEqual(self.send("demain").status, "clarification")
        self.assertNotIn("target_date", self.bot.slots)
        self.send("2026-10-15")
        self.assertEqual(self.send("14h").status, "clarification")
        self.assertNotIn("time", self.bot.slots)

    def test_reject_past_and_impossible_dates(self):
        self.send("/rdv", "3")
        for value in ["2026-10-13", "2026-02-30", "14/10/2026"]:
            self.assertEqual(self.send(value).status, "clarification")
            self.assertEqual(self.bot.state, "date")

    def test_today_allowed_and_invalid_times_rejected(self):
        self.send("/rdv", "2", "2026-10-14")
        for value in ["24:00", "14:60", "2:30", "14:30 extra"]:
            self.assertEqual(self.send(value).status, "clarification", value)
            self.assertEqual(self.bot.state, "time")
        self.assertEqual(self.send("09:05").status, "clarification")

    def test_invalid_duration_never_prepares_action(self):
        self.send("/rdv", "2", "2026-10-14", "09:05")
        for value in ["0", "180", "30min", "60.5"]:
            self.assertEqual(self.send(value).status, "clarification", value)
            self.assertEqual(self.bot.state, "duration")

    def test_quote_draft_is_editor_navigation_only(self):
        turn = self.send("/devis", "9", "couronne")
        self.assertEqual(turn.status, "confirmation_required")
        final = self.send("confirmer")
        self.assertEqual(
            final.proposal, {
                "type": "OPEN_DEVIS_EDITOR",
                "params": {
                    "patient_id": 9,
                    "procedure": "COURONNE",
                    "draft_only": True,
                },
            },
        )
        self.assertNotIn("price", final.proposal["params"])
        self.assertEqual(final.status, "proposal_only")

    def test_quote_rejects_unsupported_free_text(self):
        self.send("/devis", "9")
        for value in ["fais un devis", "implant", "500 DH", "<script>"]:
            self.assertEqual(self.send(value).status, "clarification", value)
            self.assertEqual(self.bot.state, "procedure")

    def test_quote_accepts_diacritic_and_no_diacritic(self):
        for term in ["détartrage", "detartrage"]:
            bot = PocConversation(today=TODAY)
            bot.handle("/devis")
            bot.handle("9")
            self.assertEqual(bot.handle(term).status, "confirmation_required")
            self.assertEqual(
                bot.handle("confirmer").proposal["params"]["procedure"],
                "DETARTRAGE",
            )

    def test_cancellation_clears_all_sensitive_slots(self):
        self.send("/rdv", "52", "2026-10-15", "15:00", "30")
        cancelled = self.send("/annuler")
        self.assertEqual(cancelled.status, "cancelled")
        self.assertEqual(self.bot.slots, {})
        self.assertEqual(self.bot.state, "idle")
        self.assertIsNone(self.send("CONFIRMER").proposal)

    def test_new_command_cannot_silently_switch_active_workflow(self):
        self.send("/rdv")
        self.assertEqual(self.send("/devis").status, "clarification")
        self.assertEqual(self.bot.workflow, "rdv")

    def test_distinct_sessions_do_not_share_state(self):
        other = PocConversation(today=TODAY)
        self.send("/patient", "2")
        self.assertEqual(other.state, "idle")
        self.assertEqual(other.slots, {})

    def test_unknown_state_fails_closed(self):
        self.bot.state = "corrupt_state"
        result = self.send("CONFIRMER")
        self.assertEqual(result.status, "error")
        self.assertIsNone(result.proposal)
        self.assertEqual(self.bot.state, "idle")

    def test_nonstring_and_empty_inputs_are_safe(self):
        self.assertEqual(self.bot.handle(None).status, "help")
        self.assertEqual(self.bot.handle("").status, "help")


if __name__ == "__main__":
    unittest.main()
