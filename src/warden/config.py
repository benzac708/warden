"""Environment-driven configuration. No config file is committed."""

import os
from dataclasses import dataclass


def env(name: str, default: str | None = None, required: bool = False) -> str:
    """Read one environment variable."""
    value = os.environ.get(name, default)
    if required and not value:
        raise RuntimeError("missing required env var: " + name)
    return value or ""


@dataclass(frozen=True)
class Config:
    llm_base_url: str
    llm_model: str
    llm_api_key: str
    loki_url: str
    logql: str
    k8s_api: str
    report_path: str
    page_path: str
    max_steps: int
    token_budget: int
    interval_seconds: int
    metrics_port: int
    serve_port: int

    @classmethod
    def from_env(cls, require_key: bool = True) -> "Config":
        return cls(
            llm_base_url=env("WARDEN_LLM_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/"),
            llm_model=env("WARDEN_LLM_MODEL", "qwen/qwen3.8-27b"),
            llm_api_key=env("WARDEN_LLM_API_KEY", required=require_key),
            loki_url=env("WARDEN_LOKI_URL", "http://loki.monitoring.svc.cluster.local:3100").rstrip("/"),
            logql=env("WARDEN_LOGQL", '{namespace="apps"} |= "error"'),
            k8s_api=env("WARDEN_K8S_API", "https://kubernetes.default.svc"),
            report_path=env("WARDEN_REPORT_PATH", "/var/www/warden/report.json"),
            page_path=env("WARDEN_PAGE_PATH", "/www/index.html"),
            max_steps=int(env("WARDEN_MAX_STEPS", "6")),
            token_budget=int(env("WARDEN_TOKEN_BUDGET", "24000")),
            interval_seconds=int(env("WARDEN_INTERVAL_SECONDS", "300")),
            metrics_port=int(env("WARDEN_METRICS_PORT", "8000")),
            serve_port=int(env("WARDEN_SERVE_PORT", "8080")),
        )
