# Pinned base plus apk upgrade: the pinned tag still ships OS packages with
# open CVEs, so the upgrade is part of the security gate, not a convenience.
FROM python:3.12-alpine@sha256:c5ba3deef00c7758561a0f03c26f44f10589263d40e732b8748e0d1f38f6dd89

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src

RUN apk upgrade --no-cache \
    && addgroup -g 10001 -S warden \
    && adduser -u 10001 -S -G warden warden

COPY src/ ./src/

RUN chown -R warden:warden /app

USER warden

EXPOSE 8000 8080

CMD ["python", "-m", "warden.cli", "agent"]
