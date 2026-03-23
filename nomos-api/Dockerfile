FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY nomos-cli /app/nomos-cli
COPY nomos-api/pyproject.toml /app/
COPY nomos-api/nomos_api /app/nomos_api/

ENV PYTHONPATH="/app/nomos-cli:${PYTHONPATH}"

RUN uv pip install --system ".[dev]"

EXPOSE 8000

CMD ["uvicorn", "nomos_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
