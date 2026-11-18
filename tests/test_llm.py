import io
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

from warden.llm import _post


class TestRetry(unittest.TestCase):
    def test_429_is_retried(self):
        rate_limit = urllib.error.HTTPError(
            "https://api.groq.com/openai/v1/chat/completions",
            429,
            "too many requests",
            {"Retry-After": "0"},
            io.BytesIO(b'{"error":"rate limit"}'),
        )
        ok = MagicMock()
        ok.__enter__.return_value.read.return_value = b'{"choices":[{"message":{"content":"{}"}}]}'
        with patch("warden.llm.urllib.request.urlopen", side_effect=[rate_limit, ok]) as call, patch(
            "warden.llm.time.sleep"
        ):
            body = _post("https://api.groq.com/openai/v1", "key", {"model": "test"})
        self.assertIn("choices", body)
        self.assertEqual(call.call_count, 2)


if __name__ == "__main__":
    unittest.main()
