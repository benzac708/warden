"""Property tests with the standard library only.

Property: clean_text never raises, never grows past its cap, and never leaves a
private IPv4 address for any string made of hostile-looking fragments.
"""

import random
import re
import unittest

from warden.sanitize import clean_text

FRAGMENTS = [
    "10.0.0.1", "192.168.1.20", "auth-api-7d9f2a1b", "loki.monitoring.svc.cluster.local",
    "token=abc", "password: hunter2", "https://user:pass@host", "a@b.local", "{}", "\n", "emoji 🚀", "x" * 200,
]
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b(?!\d)")


def is_private(address: str) -> bool:
    parts = [int(part) for part in address.split(".")]
    return (
        parts[0] == 10
        or (parts[0] == 192 and parts[1] == 168)
        or (parts[0] == 172 and 16 <= parts[1] <= 31)
    )


class TestProperties(unittest.TestCase):
    def test_clean_text_total(self):
        rng = random.Random(20261118)
        for _ in range(500):
            value = "".join(rng.choice(FRAGMENTS) for _ in range(rng.randint(1, 8)))
            clean = clean_text(value)
            self.assertIsInstance(clean, str)
            self.assertLessEqual(len(clean), 4000)
            for match in IPV4.finditer(clean):
                self.assertFalse(is_private(match.group()), clean)


if __name__ == "__main__":
    unittest.main()
