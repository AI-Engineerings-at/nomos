# Contributing to NomOS

We welcome contributions from the community. This guide explains how to get involved.

## Workflow

1. **Fork** the repository
2. **Create a branch** from `main`: `git checkout -b feat/your-feature`
3. **Make your changes** and commit using the convention below
4. **Open a Pull Request** against `main`

## Commit Convention

All commits must follow this format:

```
type(component): description
```

**Types:** `feat` | `fix` | `docs` | `test` | `chore`

**Components:** `gate` | `api` | `console` | `cli` | `governance` | `docs`

**Examples:**
```
feat(gate): add Article 14 human oversight check
fix(api): correct risk classification for minimal-risk agents
docs(console): update dashboard screenshot
test(cli): add integration tests for agent hiring
chore(ci): update Python version in CI workflow
```

## Code Quality

### Python

```bash
ruff check .
ruff format .
pytest
```

### TypeScript

```bash
npm run lint
npm run build
```

## Pull Request Requirements

- All CI checks must pass
- Follow the commit convention
- Keep PRs focused — one feature or fix per PR
- Update documentation if behavior changes

## Questions?

Open a discussion on GitHub or reach out at kontakt@ai-engineering.at.
