import unittest
from types import SimpleNamespace
from unittest.mock import patch

from warden.investigate import investigate

CFG = SimpleNamespace(llm_model="test-model", max_steps=4, token_budget=10000)

FINISH = '{"tool":"finish","status":"explained","summary":"Deploy 4f2a9c dropped a config key.","confidence":0.86,"evidence":["KeyError: DATABASE_URL"]}'
QUIET = '{"tool":"finish","status":"quiet","summary":"No matching error logs were found.","confidence":0.9,"evidence":[]}'


class TestLoop(unittest.TestCase):
    def test_finish_stops_the_loop(self):
        with patch("warden.investigate.chat", return_value=(FINISH, 10, 5)) as call:
            report = investigate(CFG)
        self.assertEqual(report["status"], "explained")
        self.assertAlmostEqual(report["confidence"], 0.86)
        self.assertEqual(call.call_count, 1)

    def test_invalid_json_gets_one_retry(self):
        answers = [("not json", 1, 1), (FINISH, 1, 1)]
        with patch("warden.investigate.chat", side_effect=answers) as call:
            report = investigate(CFG)
        self.assertEqual(report["status"], "explained")
        self.assertEqual(call.call_count, 2)

    def test_tool_then_finish_records_trace(self):
        answers = [
            ('{"tool":"loki_query","args":{"query":"error"}}', 10, 2),
            (FINISH, 10, 2),
        ]
        with patch("warden.investigate.chat", side_effect=answers), patch(
            "warden.investigate.run_tool", return_value="INFO: request handled"
        ):
            report = investigate(CFG)
        self.assertEqual(len(report["trace"]), 1)
        self.assertEqual(report["trace"][0]["tool"], "loki_query")
        self.assertIn("4f2a9c", report["summary"])

    def test_quiet_status_is_preserved(self):
        with patch("warden.investigate.chat", return_value=(QUIET, 5, 3)):
            report = investigate(CFG)
        self.assertEqual(report["status"], "quiet")
        self.assertIn("No matching error logs", report["summary"])

    def test_budget_exhaustion_publishes_gathered_evidence(self):
        cfg = SimpleNamespace(llm_model="test-model", max_steps=10, token_budget=12, logql='{namespace="apps"}')
        answer = ('{"tool":"loki_query","args":{"query":"x"}}', 10, 2)
        with patch("warden.investigate.chat", return_value=answer) as call, patch(
            "warden.investigate.run_tool", return_value="ERROR demo: database connection refused"
        ):
            report = investigate(cfg)
        self.assertEqual(call.call_count, 1)
        self.assertEqual(report["status"], "explained")
        self.assertIn("database connection refused", report["summary"])
        self.assertTrue(report["evidence"])

    def test_budget_is_enforced_on_invalid_json_path(self):
        cfg = SimpleNamespace(llm_model="test-model", max_steps=10, token_budget=12, logql='{namespace="apps"}')
        with patch("warden.investigate.chat", return_value=("not json", 10, 2)) as call:
            report = investigate(cfg)
        self.assertEqual(call.call_count, 1)
        self.assertEqual(report["status"], "incomplete")

    def test_bad_confidence_and_non_string_content_do_not_crash(self):
        bad = '{"tool":"finish","status":"explained","summary":"x","confidence":"high"}'
        with patch("warden.investigate.chat", return_value=(bad, 1, 1)):
            self.assertEqual(investigate(CFG)["confidence"], 0.0)
        with patch("warden.investigate.chat", return_value=(None, 1, 1)) as call:
            report = investigate(CFG)
        self.assertEqual(call.call_count, 4)
        self.assertEqual(report["status"], "incomplete")


if __name__ == "__main__":
    unittest.main()
