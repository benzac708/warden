"""Typed report contract and atomic publish."""

import json
import os

REQUIRED = {"schema", "generated_at", "status", "summary", "confidence", "trace", "evidence", "cost", "sanitized"}


class InvalidReport(ValueError):
    pass


def validate(report: dict) -> None:
    if not isinstance(report, dict):
        raise InvalidReport("report is not an object")
    missing = REQUIRED - set(report)
    if missing:
        raise InvalidReport("missing keys: " + ", ".join(sorted(missing)))
    if report["schema"] != "warden.report/v1":
        raise InvalidReport("unknown schema")
    if report["status"] not in {"explained", "incomplete", "error", "quiet"}:
        raise InvalidReport("unknown status")
    if not isinstance(report["summary"], str) or not report["summary"].strip():
        raise InvalidReport("empty summary")
    if len(report["summary"]) > 4000:
        raise InvalidReport("summary too long")
    confidence = report["confidence"]
    if not isinstance(confidence, (int, float)) or not 0.0 <= float(confidence) <= 1.0:
        raise InvalidReport("confidence out of range")
    if report["sanitized"] is not True:
        raise InvalidReport("report was not sanitized")


def publish(report: dict, path: str) -> None:
    """Validate, then replace the report atomically. A bad run never removes the last good one."""
    validate(report)
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(temporary, path)


def read(path: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
