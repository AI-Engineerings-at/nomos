# Digest-pinned 2026-05-19 for reproducible builds (still python:3.12-slim, no version change)
FROM python:3.12-slim@sha256:401f6e1a67dad31a1bd78e9ad22d0ee0a3b52154e6bd30e90be696bb6a3d7461

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv

COPY nomos-cli /app/nomos-cli
COPY nomos-api/pyproject.toml /app/
COPY nomos-api/alembic.ini /app/
COPY nomos-api/alembic /app/alembic/
COPY nomos-api/nomos_api /app/nomos_api/

ENV PYTHONPATH="/app/nomos-cli:${PYTHONPATH}"
# Unbuffered stdout/stderr: without this Python block-buffers in the
# container (non-TTY) so request/error logs never reach `docker logs`
# until the buffer fills — invisible runtime observability.
ENV PYTHONUNBUFFERED=1

RUN uv pip install --system "."

RUN adduser --disabled-password --no-create-home --gecos "" nomos \
    && mkdir -p /data/agents \
    && chown nomos:nomos /data/agents
USER nomos

EXPOSE 8000

CMD ["uvicorn", "nomos_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
