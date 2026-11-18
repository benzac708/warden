import unittest
from types import SimpleNamespace
from unittest.mock import patch

from warden.investigate import investigate

CFG = SimpleNamespace(llm_model="test-model", max_steps=4, token_budget=10000)

FINISH = '{"tool":"finish","summary":"Deploy 4f2a9c dropped a config key.","confidence":0.86,"evidence":["KeyError: DATABASE_URL"]}'


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
            "warden.investigate.run_tool", return_value="NO_MATCHING_LOGS"
        ):
            report = investigate(CFG)
        self.assertEqual(len(report["trace"]), 1)
        self.assertEqual(report["trace"][0]["tool"], "loki_query")


if __name__ == "__main__":
    unittest.main()
