"""Redact internal detail before anything is published.

Every pattern is deliberately broad: a false positive hides a harmless log
line, while a false negative publishes internal data on a public page.
"""

import re

URL_CREDS = re.compile(r"[a-z][a-z0-9+.-]*://[^\s/@]+:[^\s@]+@", re.IGNORECASE)
JSON_SECRET = re.compile(r'("(?:api[_-]?key|token|secret|password|authorization)"\s*:\s*")[^"\n]*(")', re.IGNORECASE)
BEARER = re.compile(r"Bearer\s+\S+", re.IGNORECASE)
SECRET = re.compile(r"(token|api[_-]?key|secret|password|authorization)\s*[=:]\s*\S+", re.IGNORECASE)
SVC = re.compile(r"[a-z0-9-]+(?:\.[a-z0-9-]+)*\.svc\.cluster\.local", re.IGNORECASE)
HOST = re.compile(r"\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:internal|local|lan|home\.arpa)\b", re.IGNORECASE)
POD = re.compile(r"\b[a-z0-9][a-z0-9-]*-[a-z0-9]{5,}\b")
IPV6 = re.compile(r"\b(?:[0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\b")
IP = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
SECRET_KEY = re.compile(r"(?i)(?:^|[_-])(?:api[_-]?key|token|secret|password|authorization)(?:$|[_-])")


def clean_text(value: str) -> str:
    value = URL_CREDS.sub("[redacted]@", value)
    value = JSON_SECRET.sub(r"\1[redacted]\2", value)
    value = BEARER.sub("[redacted]", value)
    value = SECRET.sub(r"\1=[redacted]", value)
    value = SVC.sub("[internal-host]", value)
    value = HOST.sub("[internal-host]", value)
    value = POD.sub("[pod]", value)
    value = IP.sub("[internal-ip]", value)
    value = IPV6.sub("[internal-ip]", value)
    value = EMAIL.sub("[redacted]", value)
    return value[:4000]


def sanitize(report: dict) -> dict:
    """Return a deep copy with every string field redacted. Idempotent."""
    out: dict = {}
    for key, value in report.items():
        out[key] = _clean_pair(key, value)
    out["sanitized"] = True
    return out


def _clean_pair(key, value):
    if SECRET_KEY.search(str(key).strip("\"'")) and isinstance(value, (str, int, float)):
        return "[redacted]"
    if isinstance(value, str):
        return clean_text(value)
    if isinstance(value, list):
        return [_clean_nested(item) for item in value]
    if isinstance(value, dict):
        return _clean_nested(value)
    return value


def _clean_nested(value):
    if isinstance(value, str):
        return clean_text(value)
    if isinstance(value, list):
        return [_clean_nested(item) for item in value]
    if isinstance(value, dict):
        return {clean_text(str(key)): _clean_pair(key, item) for key, item in value.items()}
    return value
