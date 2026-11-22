"""Property tests with the standard library only.

For any hostile-looking input, clean_text must stay a bounded string and must
not leave an IP address, a bearer token, or a credential assignment behind.
The checks below are written independently of the production regexes.
"""

import random
import re
import unittest

from warden.sanitize import clean_text

FRAGMENTS = [
    "10.0.0.1", "192.168.1.20", "fd00::1", "auth-api-7d9f2a1b",
    "loki.monitoring.svc.cluster.local", "node-1.internal",
    "token=abc", "api_key: hunter2", "Bearer eyJhbGciOi", "https://user:pass@host",
    "a@b.local", "{}", "\n", "emoji 🚀", "x" * 200,
]
IPV4_TOKEN = re.compile(r"(?<![\d.])\d{1,3}(?:\.\d{1,3}){3}(?![\d.])")
IPV6_TOKEN = re.compile(r"(?<![\w:])(?:[0-9a-f]{1,4}:){2,}[0-9a-f]{0,4}(?![\w:])", re.IGNORECASE)
BEARER_TOKEN = re.compile(r"Bearer\s+[A-Za-z0-9._-]{8,}", re.IGNORECASE)
ASSIGNMENT = re.compile(r"(?i)(?:token|api_key|password|secret)\s*[=:]\s*[A-Za-z0-9]{4,}")


class TestProperties(unittest.TestCase):
    def test_clean_text_total(self):
        rng = random.Random(20261118)
        for _ in range(500):
            value = "".join(rng.choice(FRAGMENTS) for _ in range(rng.randint(1, 8)))
            clean = clean_text(value)
            self.assertIsInstance(clean, str)
            self.assertLessEqual(len(clean), 4000)
            self.assertIsNone(IPV4_TOKEN.search(clean), clean)
            self.assertIsNone(IPV6_TOKEN.search(clean), clean)
            self.assertIsNone(BEARER_TOKEN.search(clean), clean)
            self.assertIsNone(ASSIGNMENT.search(clean), clean)


if __name__ == "__main__":
    unittest.main()
