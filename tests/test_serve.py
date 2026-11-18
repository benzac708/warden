import unittest

from warden.serve import HEADERS


class TestServeHeaders(unittest.TestCase):
    def test_inline_script_is_allowed(self):
        policy = HEADERS["Content-Security-Policy"]
        self.assertIn("script-src", policy)
        self.assertIn("'unsafe-inline'", policy)

    def test_cache_is_disabled(self):
        self.assertEqual(HEADERS["Cache-Control"], "no-store")


if __name__ == "__main__":
    unittest.main()
