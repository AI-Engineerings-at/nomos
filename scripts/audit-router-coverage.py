"""CI-gate: every state-changing route under nomos-api/.../routers/ must
be guarded by ``require_admin``, ``require_agent_actor``, or carry a
call to ``authorize_agent_action`` inside its body.

Background — see LEARNINGS.md L035 + L043: the v0.2.0 audit found 7 of
19 routers had been left unguarded because PR #5 hardened "the
important ones". This script makes that mistake impossible to repeat:
on every PR, CI calls

    python scripts/audit-router-coverage.py

which AST-parses every router file, enumerates routes whose HTTP method
mutates state, and FAILS with a non-zero exit if any of them does NOT
have one of the recognised AuthZ markers.

False positives can be silenced with an inline marker (commit-grade
deliberate skip):

    # router-coverage-skip: <reason>
    @router.post("/...")

Marker MUST sit on the line directly above the decorator and explain
WHY the route is intentionally unauthenticated. Three legitimate
patterns today: ``/api/auth/login``, ``/api/auth/recovery``,
``/api/users/bootstrap`` — those carry the marker explicitly.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROUTERS_DIR = (
    Path(__file__).resolve().parent.parent / "nomos-api" / "nomos_api" / "routers"
)
STATE_CHANGING = {"post", "patch", "delete", "put"}
AUTHZ_DEP_NAMES = {"require_admin", "require_agent_actor", "_require_admin"}
AUTHZ_BODY_CALLS = {"authorize_agent_action", "check_agent_access"}
SKIP_MARKER = "router-coverage-skip"


def _decorator_method_and_path(dec: ast.AST) -> tuple[str, str] | None:
    """Return (lower-case method, path) for ``@router.<method>('...')``;
    None otherwise. Tolerates ``@router.<method>('...', response_model=...)``.
    """
    if not isinstance(dec, ast.Call):
        return None
    fn = dec.func
    if not isinstance(fn, ast.Attribute):
        return None
    method = fn.attr.lower()
    if method not in STATE_CHANGING:
        return None
    if not dec.args:
        return None
    first = dec.args[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return method, first.value
    return None


def _depends_uses_authz(default_node: ast.AST) -> bool:
    """``Depends(require_admin)`` / ``Depends(require_agent_actor)`` ?"""
    if not isinstance(default_node, ast.Call):
        return False
    fn = default_node.func
    if not (isinstance(fn, ast.Name) and fn.id == "Depends"):
        return False
    if not default_node.args:
        return False
    arg = default_node.args[0]
    if isinstance(arg, ast.Name) and arg.id in AUTHZ_DEP_NAMES:
        return True
    return False


def _body_calls_authorize_agent_action(
    handler: ast.AsyncFunctionDef | ast.FunctionDef,
) -> bool:
    """Scan the handler body for ``authorize_agent_action(...)`` or
    ``check_agent_access(...)`` — either inline-RBAC pattern counts."""
    for node in ast.walk(handler):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name) and fn.id in AUTHZ_BODY_CALLS:
                return True
    return False


def _has_authz_dependency(handler: ast.AsyncFunctionDef | ast.FunctionDef) -> bool:
    for default in handler.args.kw_defaults + handler.args.defaults:
        if default is None:
            continue
        if _depends_uses_authz(default):
            return True
    return False


def _has_skip_marker(src_lines: list[str], decorator_lineno: int) -> tuple[bool, str]:
    # Look upward from the decorator for the marker; skip blank/decorator lines.
    for i in range(decorator_lineno - 2, max(decorator_lineno - 5, -1), -1):
        if i < 0:
            break
        line = src_lines[i].strip()
        if not line or line.startswith("@"):
            continue
        if line.startswith("#") and SKIP_MARKER in line:
            return True, line
        # Stop at first non-comment, non-decorator, non-blank line.
        return False, ""
    return False, ""


def audit_router_file(path: Path) -> list[str]:
    """Return a list of human-readable violation strings for *path*."""
    src = path.read_text(encoding="utf-8")
    src_lines = src.splitlines()
    tree = ast.parse(src, filename=str(path))
    violations: list[str] = []
    for node in tree.body:
        if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            continue
        for dec in node.decorator_list:
            mp = _decorator_method_and_path(dec)
            if mp is None:
                continue
            method, route_path = mp
            if _has_authz_dependency(node) or _body_calls_authorize_agent_action(node):
                continue
            skipped, reason = _has_skip_marker(src_lines, dec.lineno)
            if skipped:
                continue
            violations.append(
                f"  {path.relative_to(ROUTERS_DIR.parent.parent.parent)}:{dec.lineno} "
                f"{method.upper()} {route_path!r} handler={node.name!r} "
                f"— missing require_admin / require_agent_actor / authorize_agent_action"
            )
    return violations


def main() -> int:
    if not ROUTERS_DIR.exists():
        print(f"ERROR: routers dir not found: {ROUTERS_DIR}", file=sys.stderr)
        return 2
    total = 0
    files_with_violations = 0
    print(f"audit-router-coverage: scanning {ROUTERS_DIR}")
    for py in sorted(ROUTERS_DIR.glob("*.py")):
        if py.name.startswith("__"):
            continue
        violations = audit_router_file(py)
        if violations:
            files_with_violations += 1
            total += len(violations)
            print(f"FAIL {py.name}")
            for v in violations:
                print(v)
    if total == 0:
        print("OK — every state-changing route is AuthZ-guarded.")
        return 0
    print(
        f"\nFAIL — {total} unguarded state-changing route(s) across "
        f"{files_with_violations} file(s). See LEARNINGS.md L035 + L043."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
