FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src

COPY src/ ./src/

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin warden \
    && chown -R warden:warden /app

USER warden

EXPOSE 8000 8080

CMD ["python", "-m", "warden.cli", "agent"]
