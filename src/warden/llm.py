"""Thin OpenAI-compatible chat client using only the standard library."""

import json
import time
import urllib.error
import urllib.request


class LLMError(RuntimeError):
    pass


def _post(base_url: str, api_key: str, payload: dict, timeout: int = 90, retries: int = 2) -> dict:
    request = urllib.request.Request(
        base_url + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
            "User-Agent": "warden/0.1",
        },
        method="POST",
    )
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:400]
            if exc.code == 429 and attempt < retries:
                try:
                    delay = float(exc.headers.get("Retry-After", 2 ** (attempt + 1)))
                except (TypeError, ValueError):
                    delay = 2 ** (attempt + 1)
                time.sleep(min(delay, 30))
                continue
            raise LLMError("llm http " + str(exc.code) + ": " + detail) from exc
        except urllib.error.URLError as exc:
            raise LLMError("llm network error: " + str(exc.reason)) from exc
    raise LLMError("llm retries exhausted")


def chat(cfg, messages: list[dict], max_tokens: int = 800) -> tuple[str, int, int]:
    """Call the model. Retry without response_format if the provider rejects it."""
    payload = {
        "model": cfg.llm_model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    try:
        body = _post(cfg.llm_base_url, cfg.llm_api_key, payload)
    except LLMError as exc:
        if "400" not in str(exc):
            raise
        payload.pop("response_format", None)
        body = _post(cfg.llm_base_url, cfg.llm_api_key, payload)

    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise LLMError("unexpected llm response shape") from exc

    usage = body.get("usage", {})
    return content, int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0))
