<!--
Thanks for the PR. Fill the relevant sections; delete the ones that
don't apply. Small PRs welcome.
-->

## Summary

<!-- 1-3 sentences. What does this change, in plain language. -->

## Type

- [ ] feat — new user-visible behaviour
- [ ] fix — bug fix
- [ ] refactor — code-only change, no behaviour difference
- [ ] test — tests only
- [ ] docs — documentation only
- [ ] chore — CI / tooling / deps

## Scope

<!-- Which package(s)? api / cli / console / plugin / docs / ci -->

## Checklist

- [ ] Tests pass locally (`pytest` and/or `vitest run`)
- [ ] Lint passes (`ruff check`, `ruff format --check`, `tsc --noEmit`)
- [ ] No internal IPs (`10.40.10.*`) or hardcoded secrets added
- [ ] CHANGELOG entry added under the next pending version (if user-visible)
- [ ] Per-package README updated if env vars / setup steps changed
- [ ] Browser-tested in a real `docker compose up -d` stack if UI or
      compliance-flow logic changed (Rule 06: integration test required)

## Compliance impact

<!-- If this touches the audit chain, signing keys, retention, gate
     logic, or the EU-AI-Act-Art. 12 event catalog, describe the
     impact. Otherwise: "none". -->

## Notes for the reviewer

<!-- Anything non-obvious: trade-offs, follow-ups, links to issues. -->
