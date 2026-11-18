"""Read-only tools. Every tool returns plain text for the model to inspect."""

import json
import ssl
import urllib.parse
import urllib.request


SA_TOKEN = "/var/run/secrets/kubernetes.io/serviceaccount/token"
SA_CA = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"


def loki_query(cfg, query: str, limit: int = 20) -> str:
    params = urllib.parse.urlencode({"query": query, "limit": limit, "since": "15m"})
    url = cfg.loki_url + "/loki/api/v1/query_range?" + params
    with urllib.request.urlopen(url, timeout=20) as response:
        body = json.loads(response.read().decode("utf-8"))

    lines: list[str] = []
    for stream in body.get("data", {}).get("result", []):
        for _ts, text in stream.get("values", []):
            lines.append(str(text))
    if not lines:
        return "NO_MATCHING_LOGS"
    return "\n".join(lines[-limit:])[:4000]


def k8s_get_pods(cfg, namespace: str = "apps") -> str:
    """List pods through the in-cluster API using a read-only ServiceAccount."""
    with open(SA_TOKEN, "r", encoding="utf-8") as handle:
        token = handle.read().strip()
    context = ssl.create_default_context(cafile=SA_CA)
    url = cfg.k8s_api + "/api/v1/namespaces/" + urllib.parse.quote(namespace) + "/pods"
    request = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(request, timeout=20, context=context) as response:
        body = json.loads(response.read().decode("utf-8"))

    rows = []
    for pod in body.get("items", []):
        name = pod.get("metadata", {}).get("name", "?")
        phase = pod.get("status", {}).get("phase", "?")
        rows.append(name + " " + phase)
    return "\n".join(rows[:30])[:2000] if rows else "NO_PODS"


TOOLS = {
    "loki_query": lambda cfg, args: loki_query(cfg, str(args.get("query", ""))),
    "k8s_get_pods": lambda cfg, args: k8s_get_pods(cfg, str(args.get("namespace", "apps"))),
}


def run_tool(cfg, name: str, args: dict) -> str:
    if name not in TOOLS:
        return "UNKNOWN_TOOL: " + name
    try:
        return TOOLS[name](cfg, args)
    except Exception as exc:  # keep the loop alive; surface the error as evidence
        return "TOOL_ERROR: " + type(exc).__name__ + ": " + str(exc)[:300]
