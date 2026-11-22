import json
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from warden import tools

CFG = SimpleNamespace(loki_url="http://loki:3100", k8s_api="https://kubernetes.default.svc")


def _response(payload):
    response = MagicMock()
    response.__enter__.return_value.read.return_value = json.dumps(payload).encode("utf-8")
    return response


class TestTools(unittest.TestCase):
    def test_loki_query_parses_streams(self):
        payload = {"data": {"result": [{"values": [[1, "INFO ok"], [2, "ERROR bad"]]}]}}
        with patch("warden.tools.urllib.request.urlopen", return_value=_response(payload)) as call:
            result = tools.loki_query(CFG, '{namespace="apps"}')
        self.assertIn("ERROR bad", result)
        self.assertIn("INFO ok", result)
        self.assertIn("since=15m", call.call_args.args[0])

    def test_loki_query_no_match(self):
        with patch("warden.tools.urllib.request.urlopen", return_value=_response({"data": {"result": []}})):
            self.assertEqual(tools.loki_query(CFG, "x"), "NO_MATCHING_LOGS")

    def test_k8s_get_pods_uses_service_account_token(self):
        with tempfile.TemporaryDirectory() as directory:
            token_path = os.path.join(directory, "token")
            ca_path = os.path.join(directory, "ca.crt")
            with open(token_path, "w", encoding="utf-8") as handle:
                handle.write("sa-token\n")
            with open(ca_path, "w", encoding="utf-8") as handle:
                handle.write("ca")
            payload = {"items": [
                {"metadata": {"name": "warden-abc"}, "status": {"phase": "Running"}},
            ]}
            with patch.object(tools, "SA_TOKEN", token_path), patch.object(tools, "SA_CA", ca_path), patch(
                "warden.tools.ssl.create_default_context"
            ), patch("warden.tools.urllib.request.urlopen", return_value=_response(payload)) as call:
                result = tools.k8s_get_pods(CFG, "apps")
            self.assertEqual(result, "warden-abc Running")
            request = call.call_args.args[0]
            self.assertEqual(request.get_header("Authorization"), "Bearer sa-token")

    def test_run_tool_allowlist_and_errors(self):
        self.assertEqual(tools.run_tool(CFG, "unknown", {}), "UNKNOWN_TOOL: unknown")
        with patch.dict(tools.TOOLS, {"boom": lambda cfg, args: (_ for _ in ()).throw(ValueError("x"))}):
            self.assertTrue(tools.run_tool(CFG, "boom", {}).startswith("TOOL_ERROR: ValueError"))


if __name__ == "__main__":
    unittest.main()
