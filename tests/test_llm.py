import io
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

from warden.llm import LLMError, _post, chat


class _Cfg:
    llm_model = "test-model"
    llm_base_url = "https://api.example.com/v1"
    llm_api_key = "key"


def _http_error(code, body=b'{"error":"bad"}', headers=None):
    return urllib.error.HTTPError(
        "https://api.example.com/v1/chat/completions",
        code,
        "error",
        headers or {},
        io.BytesIO(body),
    )


def _ok(body):
    response = MagicMock()
    response.__enter__.return_value.read.return_value = body
    return response


class TestRetry(unittest.TestCase):
    def test_429_is_retried(self):
        rate_limit = _http_error(429, b'{"error":"rate limit"}', {"Retry-After": "0"})
        with patch("warden.llm.urllib.request.urlopen", side_effect=[rate_limit, _ok(b'{"choices":[]}')]) as call, patch(
            "warden.llm.time.sleep"
        ):
            body = _post("https://api.example.com/v1", "key", {"model": "test"})
        self.assertIn("choices", body)
        self.assertEqual(call.call_count, 2)

    def test_429_retries_are_bounded(self):
        with patch("warden.llm.urllib.request.urlopen", side_effect=_http_error(429)) as call, patch("warden.llm.time.sleep"):
            with self.assertRaises(LLMError):
                _post("https://api.example.com/v1", "key", {"model": "test"})
            self.assertEqual(call.call_count, 3)

    def test_400_fallback_drops_response_format(self):
        responses = [_http_error(400), _ok(b'{"choices":[{"message":{"content":"{}"}}],"usage":{}}')]
        with patch("warden.llm.urllib.request.urlopen", side_effect=responses) as call:
            content, tokens_in, tokens_out = chat(_Cfg(), [])
        self.assertEqual(content, "{}")
        self.assertEqual((tokens_in, tokens_out), (0, 0))
        self.assertEqual(call.call_count, 2)
        second_payload = call.call_args_list[1].args[0].data
        self.assertNotIn(b"response_format", second_payload)

    def test_unrelated_400_in_body_does_not_trigger_fallback(self):
        error = _http_error(500, b'{"error":"max 400 characters"}')
        with patch("warden.llm.urllib.request.urlopen", side_effect=error):
            with self.assertRaises(LLMError) as ctx:
                chat(_Cfg(), [])
        self.assertEqual(ctx.exception.code, 500)

    def test_non_string_content_becomes_empty_string(self):
        with patch("warden.llm.urllib.request.urlopen", return_value=_ok(b'{"choices":[{"message":{"content":null}}]}')):
            content, _, _ = chat(_Cfg(), [])
        self.assertEqual(content, "")

    def test_unexpected_response_shape_raises(self):
        with patch("warden.llm.urllib.request.urlopen", return_value=_ok(b'{"unexpected":true}')):
            with self.assertRaises(LLMError):
                chat(_Cfg(), [])


if __name__ == "__main__":
    unittest.main()
