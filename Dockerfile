FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src

COPY src/ ./src/

EXPOSE 8000 8080

CMD ["python", "-m", "warden.cli", "agent"]
