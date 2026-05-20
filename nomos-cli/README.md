# nomos-cli

> Python CLI + the shared `nomos.core` library that powers
> `nomos-api`. Python 3.12, Click, Pydantic v2, `cryptography` for
> Ed25519, `rich` for output.

Top-level overview: [`../README.md`](../README.md).

## 1. Purpose & Boundary

Two roles in one package:

1. **`nomos` CLI** — local operator tool. Standalone subcommands
   (`hire`, `gate`, `verify`, `fleet`, `audit`) work directly on
   filesystem agent directories with no services running. API-backed
   subcommands (`pause`, `resume`, `retire`, `forget`, `assign`,
   `costs`, `incidents`, `workspace`) hit a running nomos-api over
   HTTP.
2. **`nomos.core` library** — imported by `nomos-api`. Contains
   `manifest`, `manifest_validator`, `forge`, `gate`,
   `compliance_engine`, `hash_chain`, `events`, and (since 0.2.0)
   `merkle` (RFC 6962 transparency log). This is the source of
   truth for audit integrity logic.

Does NOT talk to a database or a message broker — those are
nomos-api concerns.

## 2. Prerequisites

- Python 3.12.
- `uv` (or pip).
- Optional: `NOMOS_API_URL` ENV pointing at a running API for the
  API-backed subcommands.
- Standalone subcommands need no services at all.

## 3. Dev Setup

```bash
cd nomos-cli
uv sync --extra dev
uv run nomos --help
# Standalone, no services:
uv run nomos hire --name "Mani" --role external-secretary \
  --company "Acme" --email "mani@acme.at"
uv run nomos verify --agent-dir ./data/agents/mani
uv run nomos audit  --agent-dir ./data/agents/mani --verify
```

## 4. Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `NOMOS_API_URL` | only for API-backed subcommands | `http://localhost:8060` |
| `NOMOS_API_KEY` | only for API-backed subcommands | Matches `NOMOS_PLUGIN_API_KEY` on the server |
| `NOMOS_AGENTS_DIR` | no | Default agent-directory root (overridable per command via `--agent-dir` / `--agents-dir`) |
| `NOMOS_LOG_LEVEL` | no (default `INFO`) | `DEBUG`/`INFO`/`WARNING`/`ERROR` — structured JSON diagnostics on **stderr**; user-facing UX stays on **stdout** |
| `NOMOS_HASHCHAIN_HMAC_KEY` | yes when chains exist | ≥32-byte HMAC key (fail-closed at verify) |
| `NOMOS_AUDIT_SIGNING_KEY` | yes when chains exist | 32-byte hex Ed25519 seed (fail-closed) |

## 5. Tests

```bash
cd nomos-cli
uv run python -m pytest -v               # 239 tests as of 0.2.0
uv run python -m pytest tests/test_hash_chain.py -v
```

The cli package vendors its own `pytest>=8` + `pytest-asyncio>=0.23`
under `[project.optional-dependencies] dev`. `nomos-api` does NOT
satisfy the cli's test deps — they are independent venvs in CI.

## 6. Build & Ship

```bash
uv build                                  # produces wheel + sdist in dist/
```

Version bump: `pyproject.toml` `version`. Bump together with
`nomos-api` (shares `nomos.core`) and `nomos-console`. Update
`CHANGELOG.md`. The cli is not (yet) published to PyPI — install
from the wheel artifact.

## 7. Common Gotchas

- **`ModuleNotFoundError: nomos`** when running tests in `nomos-api`
  — that suite needs `PYTHONPATH="../nomos-cli"`. The cli's own
  tests do not need this; they import directly from the local
  source.
- **`uv run pytest` picking the wrong Python** — on systems with
  Python 3.11 in PATH, `uv run pytest` may select system Python
  instead of the venv's. Use `uv run python -m pytest` to force the
  venv interpreter.
- **stdout vs stderr** — never grep stdout for diagnostics. Logs go
  to stderr; user output (rich tables, JSON dumps) goes to stdout
  on purpose. `2>&1` collapses both and breaks pipes that depend on
  the split.
- **Manifest hash uses canonical JSON** — `sort_keys=True,
  separators=(",", ":")`. Any tool that re-serialises differently
  will get a different `manifest.sha256`. Use
  `manifest_validator.compute_hash` rather than rolling your own.
- **`audit_retention_days < 180`** — manifest validation rejects.
  EU AI Act Art. 12 minimum (6 months). Hard floor, not advisory.
