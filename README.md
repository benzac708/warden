# warden

A small, read-only SRE investigator for the k3d GitOps platform. Warden queries Loki and the Kubernetes API, asks an LLM to explain recent errors, and publishes a sanitized report to a static page.

It is deliberately limited in v1: no writes, no patching, no PRs, no egress beyond Loki, the Kubernetes API and the LLM provider.

- Public page: `https://warden.zachara.dev`
- Config and deploy manifests: [warden-config](https://github.com/benzac708/warden-config)
- Platform: 3-node k3d cluster on the Oracle VPS, Argo CD, Cloudflare Tunnel

## How it works

```
Cloudflare Tunnel -> warden-showcase (static, GET only) -> public page
                          ^
                          | shared emptyDir
warden-agent (internal) --+  Loki + k8s API -> LLM -> sanitize -> report.json
```

One pod, two containers, one shared `emptyDir`. No PVC, so it works on a 3-node cluster without shared storage. Only the showcase container is exposed. The agent container holds the API key; the showcase container has none.

## Provider configuration

Any OpenAI-compatible chat-completions endpoint works. Nothing is hardcoded in the image.

| Provider | `WARDEN_LLM_BASE_URL` | `WARDEN_LLM_MODEL` example | Note |
|---|---|---|---|
| Groq | `https://api.groq.com/openai/v1` | `llama-3.1-8b-instant` | free tier, verify current free models |
| OpenRouter | `https://openrouter.ai/api/v1` | any `:free` model | free tier |
| OpenCode Go | `https://opencode.ai/zen/go/v1` | `glm-5`, `kimi-k2.5` | needs a Go subscription; free-tier models are OpenCode-only |

The key is injected from a Kubernetes Secret named `warden-llm`. Never commit it.

## Local run

```sh
PYTHONPATH=src python -m unittest discover -s tests -v

export WARDEN_LLM_API_KEY=...
export WARDEN_LLM_BASE_URL=https://api.groq.com/openai/v1
export WARDEN_LLM_MODEL=llama-3.1-8b-instant
export WARDEN_REPORT_PATH=/tmp/warden/report.json
PYTHONPATH=src python -m warden.cli once
```

## Environment

| Variable | Default | Purpose |
|---|---|---|
| `WARDEN_LLM_BASE_URL` | Groq | provider endpoint |
| `WARDEN_LLM_MODEL` | `llama-3.1-8b-instant` | model id |
| `WARDEN_LLM_API_KEY` | required | provider key, from Secret |
| `WARDEN_LOKI_URL` | `http://loki.monitoring.svc.cluster.local:3100` | Loki endpoint |
| `WARDEN_LOGQL` | `{namespace="apps"} \|= "error"` | investigation query |
| `WARDEN_MAX_STEPS` | `6` | loop bound |
| `WARDEN_TOKEN_BUDGET` | `24000` | token bound |
| `WARDEN_INTERVAL_SECONDS` | `300` | run cadence |

## Metrics

The agent exposes Prometheus text on `:8000/metrics`: `warden_runs_total`, `warden_failures_total`, `warden_tokens_in_total`, `warden_tokens_out_total`, `warden_last_run_timestamp_seconds`, `warden_last_confidence`.

## Release flow

`git push` to `main` runs tests, builds a `linux/arm64` image to GHCR, tags it with the commit SHA, and bumps the image tag in `warden-config`. Argo CD syncs the cluster. CI never applies to the cluster.
