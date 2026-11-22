import unittest

from warden.sanitize import clean_text, sanitize


class TestSanitize(unittest.TestCase):
    def test_internal_detail_is_removed(self):
        text = (
            'pod=auth-api-7d9f2a1b err at 10.0.3.14 '
            'svc=http://loki.monitoring.svc.cluster.local:3100 '
            'token=abc123DEF user@internal.local'
        )
        clean = clean_text(text)
        self.assertNotIn("10.0.3.14", clean)
        self.assertNotIn("svc.cluster.local", clean)
        self.assertNotIn("abc123DEF", clean)
        self.assertNotIn("user@internal.local", clean)
        self.assertIn("[internal-ip]", clean)

    def test_json_and_bearer_credentials_are_removed(self):
        text = '{"api_key": "supersecret"} Authorization: Bearer eyJhbGciOi token: plain123'
        clean = clean_text(text)
        self.assertNotIn("supersecret", clean)
        self.assertNotIn("eyJhbGciOi", clean)
        self.assertNotIn("plain123", clean)

    def test_ipv6_and_arbitrary_internal_hosts_are_removed(self):
        clean = clean_text("peer fd00::1 via node-1.internal and db.local")
        self.assertNotIn("fd00::1", clean)
        self.assertNotIn("node-1.internal", clean)
        self.assertNotIn("db.local", clean)

    def test_iso_timestamp_is_preserved(self):
        stamp = "2026-11-22T08:18:58Z"
        self.assertEqual(clean_text(stamp), stamp)

    def test_nested_keys_and_values_are_cleaned(self):
        report = {
            "schema": "warden.report/v1",
            "trace": [{"step": 1, "args": {"api_key": "abc123", "query": "10.0.0.5"}}],
            "sanitized": False,
        }
        clean = sanitize(report)
        dumped = str(clean)
        self.assertNotIn("abc123", dumped)
        self.assertNotIn("10.0.0.5", dumped)
        self.assertIn("api_key", dumped)
        self.assertTrue(clean["sanitized"])

    def test_sanitize_is_idempotent(self):
        report = {"summary": "ip 10.1.2.3", "sanitized": False}
        once = sanitize(report)
        twice = sanitize(once)
        self.assertEqual(once, twice)
        self.assertTrue(twice["sanitized"])

    def test_already_flagged_report_is_recleaned(self):
        report = {"summary": "token=hunter2", "sanitized": True}
        self.assertNotIn("hunter2", str(sanitize(report)))


if __name__ == "__main__":
    unittest.main()
