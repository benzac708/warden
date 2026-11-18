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

    def test_sanitize_is_idempotent(self):
        report = {"summary": "ip 10.1.2.3", "sanitized": False}
        once = sanitize(report)
        twice = sanitize(once)
        self.assertEqual(once, twice)
        self.assertTrue(twice["sanitized"])


if __name__ == "__main__":
    unittest.main()
