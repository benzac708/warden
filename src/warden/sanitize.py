"""Redact internal detail before anything is published."""

import re

IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b(?!\d)")
POD = re.compile(r"\b[a-z0-9][a-z0-9-]*-[a-f0-9]{8,12}\b")
SVC = re.compile(r"[a-z0-9-]+(?:\.[a-z0-9-]+)*\.svc\.cluster\.local")
SECRET = re.compile(r"(?i)\b(token|api[_-]?key|secret|password)\s*[=:]\s*\S+")
URL_CREDS = re.compile(r"https?://[^\s/@]+:[^\s/@]+@")
EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")


def clean_text(value: str) -> str:
    value = URL_CREDS.sub("[redacted]@", value)
    value = SECRET.sub(r"\1=[redacted]", value)
    value = SVC.sub("[internal-host]", value)
    value = POD.sub("[pod]", value)
    value = IP.sub("[internal-ip]", value)
    value = EMAIL.sub("[redacted]", value)
    return value[:4000]


def sanitize(report: dict) -> dict:
    """Return a copy with all string fields redacted. Idempotent."""
    if report.get("sanitized") is True:
        return dict(report)
    out: dict = {}
    for key, value in report.items():
        if isinstance(value, str):
            out[key] = clean_text(value)
        elif isinstance(value, list):
            out[key] = [clean_text(item) if isinstance(item, str) else _clean_nested(item) for item in value]
        elif isinstance(value, dict):
            out[key] = _clean_nested(value)
        else:
            out[key] = value
    out["sanitized"] = True
    return out


def _clean_nested(value):
    if isinstance(value, str):
        return clean_text(value)
    if isinstance(value, list):
        return [_clean_nested(item) for item in value]
    if isinstance(value, dict):
        return {key: _clean_nested(item) for key, item in value.items()}
    return value
