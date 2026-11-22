import http.client
import json
import os
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer

from warden.serve import Handler


class TestServe(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.page = os.path.join(self.directory.name, "index.html")
        self.report = os.path.join(self.directory.name, "report.json")
        with open(self.page, "w", encoding="utf-8") as handle:
            handle.write("<html>ok</html>")
        with open(self.report, "w", encoding="utf-8") as handle:
            json.dump({"status": "quiet"}, handle)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.page_path = self.page
        self.server.report_path = self.report
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.directory.cleanup()

    def _request(self, method, path):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        connection.request(method, path)
        response = connection.getresponse()
        body = response.read()
        headers = dict(response.getheaders())
        connection.close()
        return response.status, body, headers

    def test_get_routes(self):
        for path, expected, content_type in [
            ("/", 200, "text/html"),
            ("/index.html", 200, "text/html"),
            ("/report.json", 200, "application/json"),
            ("/healthz", 200, "application/json"),
            ("/missing", 404, "text/plain"),
        ]:
            status, body, headers = self._request("GET", path)
            self.assertEqual(status, expected, path)
            self.assertIn(content_type, headers["Content-Type"])

    def test_head_has_no_body(self):
        status, body, _ = self._request("HEAD", "/healthz")
        self.assertEqual(status, 200)
        self.assertEqual(body, b"")

    def test_write_methods_are_rejected(self):
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            status, body, _ = self._request(method, "/report.json")
            self.assertEqual(status, 405, method)
            self.assertIn(b"read-only", body)

    def test_security_headers(self):
        _, _, headers = self._request("GET", "/")
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("default-src 'self'", headers["Content-Security-Policy"])

    def test_invalid_report_returns_503(self):
        with open(self.report, "w", encoding="utf-8") as handle:
            handle.write("not json")
        status, _, _ = self._request("GET", "/report.json")
        self.assertEqual(status, 503)


if __name__ == "__main__":
    unittest.main()
