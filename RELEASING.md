# Releasing NomOS

> Internal runbook for cutting a NomOS release. Component-versioned
> per SemVer: `nomos-api`, `nomos-cli`, `nomos-console` march in
> lockstep; `nomos-plugin` is on its own track because it follows
> OpenClaw's plugin-contract major.

## Cadence

No fixed cadence. Cut a release when:

- An EU AI Act enforcement date is approaching and changes are
  ready (e.g. Art. 12 → `0.2.0` shipped 2026-05-20 ahead of
  2026-08-02).
- A user-visible feature, breaking change, or important fix is
  merged to `main` and is being asked for by downstream operators.
- Security advisories require a patch release (use the `0.x.Y`
  patch slot, never amend an existing release).

## Numbering

| Component | Track | Notes |
|---|---|---|
| `nomos-api` | `0.MAJOR.MINOR` | Bump together with `nomos-cli` and `nomos-console`. Same version across the trio. |
| `nomos-cli` | `0.MAJOR.MINOR` | Same as `nomos-api`. |
| `nomos-console` | `0.MAJOR.MINOR` | Same as `nomos-api`. |
| `nomos-plugin` | `MAJOR.MINOR.PATCH` (currently `2.x`) | Independent — tracks OpenClaw plugin contract. |

Pre-1.0: bumps are minor-on-`0.x` (`0.1.0 → 0.2.0`). Major bumps post-1.0 follow standard SemVer.

## Pre-flight checklist

Before opening the release PR:

- [ ] All planned PRs merged to `main`.
- [ ] CI green on `main`.
- [ ] No open `needs-triage` issues marked `blocker`.
- [ ] `docs/hardening-*/PLAN.md` (if a phased rollout) marks the relevant phases ✓ SHIPPED.
- [ ] `CHANGELOG.md` has a complete unreleased section ready to be dated.

## Procedure

1. **Bump versions** in three files (CLI/API/Console marching together):
   ```bash
   # in three separate edits — see CHANGELOG.md for past examples
   nomos-api/pyproject.toml       # version = "X.Y.Z"
   nomos-cli/pyproject.toml       # version = "X.Y.Z"
   nomos-console/package.json     # "version": "X.Y.Z"
   # plugin: only if its track also moves
   nomos-plugin/package.json
   ```

2. **Date the CHANGELOG section.** Move `[Unreleased]` to
   `[X.Y.Z] — YYYY-MM-DD`. Verify every bullet has a PR link.

3. **Open the release PR** from `chore/release-X.Y.Z-CHANGELOG-YYYY-MM-DD`.

4. **Merge** the release PR to `main`.

5. **Tag and push:**
   ```bash
   git fetch origin main
   git checkout origin/main
   git tag -a vX.Y.Z -m "NomOS X.Y.Z"
   git push origin vX.Y.Z
   ```

6. **GitHub Release.** The `.github/workflows/release.yml` workflow
   fires on tag push, extracts the matching section from `CHANGELOG.md`,
   and publishes a GitHub Release with those notes. If the workflow
   doesn't exist (or fails), create the release manually:
   ```bash
   gh release create vX.Y.Z --title "NomOS X.Y.Z" \
     --notes-file <(awk '/^## \[X.Y.Z\]/{p=1;next} /^## \[/{p=0} p' CHANGELOG.md)
   ```

7. **Post-release smoke.** Pull the tag in a clean dir and run the
   live-eval procedure from
   [`docs/hardening-2026-05-20/EVAL-2026-05-20.md`](docs/hardening-2026-05-20/EVAL-2026-05-20.md)
   — verifies the audit-trail v2 invariants from a regulator's seat.

8. **Announce.** Tag the relevant downstream operators / write a
   release post if needed. No-ops for ordinary patch releases.

## Hotfix releases

For a critical security or compliance fix:

1. Branch from the tag: `git checkout -b chore/release-X.Y.(Z+1)-hotfix vX.Y.Z`
2. Cherry-pick the fix commit(s) only.
3. Bump only the patch number.
4. Add a CHANGELOG entry under `[X.Y.Z+1] — YYYY-MM-DD`.
5. PR → merge → tag → release as above.

## Yanking a release

A release should be yanked, not deleted. To yank `vX.Y.Z`:

```bash
gh release edit vX.Y.Z --prerelease --notes "YANKED: $reason. Use vX.Y.(Z+1)."
```

Yanking does NOT remove the git tag — that would break checksums for
anyone who already pinned it. Always ship a follow-up with the same
fix and document the yank in the next CHANGELOG entry.
