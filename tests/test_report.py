import json
import os
import tempfile
import unittest

from warden.report import InvalidReport, publish, read, validate


def good_report():
    return {
        "schema": "warden.report/v1",
        "generated_at": "2026-11-18T20:44:12Z",
        "status": "explained",
        "summary": "A config key was missing.",
        "confidence": 0.8,
        "trace": [],
        "evidence": [],
        "cost": {"tokens_in": 1, "tokens_out": 1},
        "sanitized": True,
    }


class TestReport(unittest.TestCase):
    def test_validate_rejects_unsanitized(self):
        report = good_report()
        report["sanitized"] = False
        with self.assertRaises(InvalidReport):
            validate(report)

    def test_validate_rejects_bad_confidence(self):
        report = good_report()
        report["confidence"] = 4.0
        with self.assertRaises(InvalidReport):
            validate(report)

    def test_bad_publish_keeps_last_good_report(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "report.json")
            publish(good_report(), path)
            original = read(path)
            bad = good_report()
            bad["status"] = "not-a-status"
            with self.assertRaises(InvalidReport):
                publish(bad, path)
            self.assertEqual(read(path), original)
            self.assertFalse(os.path.exists(path + ".tmp"))


if __name__ == "__main__":
    unittest.main()
