"""Read-only static server. Only two paths exist and no write method exists."""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Cache-Control": "no-store",
    "Content-Security-Policy": "default-src 'self'; style-src 'unsafe-inline'; img-src 'self' data:",
}


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for key, value in HEADERS.items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            try:
                with open(self.server.page_path, "rb") as handle:
                    self._send(200, handle.read(), "text/html; charset=utf-8")
            except OSError:
                self._send(503, b"page unavailable\n", "text/plain; charset=utf-8")
            return
        if path == "/report.json":
            try:
                with open(self.server.report_path, "rb") as handle:
                    json.loads(handle.read())
                with open(self.server.report_path, "rb") as handle:
                    self._send(200, handle.read(), "application/json")
            except (OSError, json.JSONDecodeError):
                self._send(503, b'{"status":"waiting"}\n', "application/json")
            return
        if path == "/healthz":
            self._send(200, b'{"status":"ok"}\n', "application/json")
            return
        self._send(404, b"not found\n", "text/plain; charset=utf-8")

    def do_HEAD(self):
        self.do_GET()

    def do_POST(self):
        self._send(405, b"read-only\n", "text/plain; charset=utf-8")

    do_PUT = do_POST
    do_PATCH = do_POST
    do_DELETE = do_POST

    def log_message(self, *_args):
        return


def start_server(port: int, page_path: str, report_path: str) -> None:
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    server.page_path = page_path
    server.report_path = report_path
    server.serve_forever()
