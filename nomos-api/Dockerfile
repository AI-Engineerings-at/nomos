# Digest-pinned 2026-05-19 for reproducible builds (still python:3.12-slim, no version change)
FROM python:3.14-slim@sha256:a24bfbc0bd39cfa24de47147ada92b65916ad693e6ab5034636ef21f5663ef13

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

# Logging is configured by nomos_api.main._force_json_stdout_logging()
# (at import + re-applied in lifespan startup, AFTER uvicorn's own
# dictConfig). Single source of truth in Python; no external JSON.
CMD ["uvicorn", "nomos_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
