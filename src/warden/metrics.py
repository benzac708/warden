"""Tiny Prometheus text emitter. No dependency on prometheus_client."""

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_LOCK = threading.Lock()
_COUNTERS = {
    "warden_runs_total": 0,
    "warden_failures_total": 0,
    "warden_tokens_in_total": 0,
    "warden_tokens_out_total": 0,
}
_GAUGES = {"warden_last_run_timestamp_seconds": 0.0, "warden_last_confidence": 0.0}


def inc(name: str, amount: int = 1) -> None:
    """Increment a counter. Callers pass the full, documented metric name."""
    if name not in _COUNTERS:
        raise KeyError("unknown counter: " + name)
    with _LOCK:
        _COUNTERS[name] += amount


def add_tokens(name: str, amount: int) -> None:
    inc(name, amount)


def set_gauge(name: str, value: float) -> None:
    with _LOCK:
        _GAUGES[name] = value


def render() -> str:
    lines = []
    with _LOCK:
        for name, value in _COUNTERS.items():
            lines.append("# TYPE " + name + " counter")
            lines.append(name + " " + str(value))
        for name, value in _GAUGES.items():
            lines.append("# TYPE " + name + " gauge")
            lines.append(name + " " + str(value))
    return "\n".join(lines) + "\n"


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = render().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


def start_server(port: int) -> None:
    server = ThreadingHTTPServer(("0.0.0.0", port), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
