"""Entrypoints: agent (loop), serve (public read-only), once (local smoke test)."""

import json
import sys
import time

from . import metrics
from .config import Config
from .investigate import investigate
from .report import InvalidReport, publish
from .sanitize import sanitize
from .serve import start_server


def run_once(cfg: Config) -> dict:
    report = sanitize(investigate(cfg))
    try:
        publish(report, cfg.report_path)
        metrics.inc("runs")
        metrics.set_gauge("warden_last_confidence", float(report["confidence"]))
    except InvalidReport as exc:
        metrics.inc("failures")
        print("publish rejected: " + str(exc), file=sys.stderr)
    metrics.set_gauge("warden_last_run_timestamp_seconds", time.time())
    return report


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "agent"
    cfg = Config.from_env(require_key=(mode != "serve"))

    if mode == "serve":
        start_server(cfg.serve_port, cfg.page_path, cfg.report_path)
    elif mode == "once":
        print(json.dumps(run_once(cfg), indent=2))
    elif mode == "agent":
        metrics.start_server(cfg.metrics_port)
        while True:
            try:
                report = run_once(cfg)
                metrics.add_tokens("warden_tokens_in_total", report["cost"]["tokens_in"])
                metrics.add_tokens("warden_tokens_out_total", report["cost"]["tokens_out"])
            except Exception as exc:  # keep the loop alive
                metrics.inc("failures")
                print("run failed: " + repr(exc), file=sys.stderr)
            time.sleep(cfg.interval_seconds)
    else:
        raise SystemExit("unknown mode: " + mode)


if __name__ == "__main__":
    main()
