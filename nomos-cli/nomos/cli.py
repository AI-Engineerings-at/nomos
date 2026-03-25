"""NomOS CLI — Agent Lifecycle Management.

Commands:
    nomos hire    — Create a new AI agent with full compliance
    nomos verify  — Verify compliance of an agent
    nomos fleet   — List all agents in the local fleet
    nomos audit   — Show or verify audit trail
    nomos pause   — Pause a running agent
    nomos resume  — Resume a paused agent
    nomos retire  — Gracefully retire an agent
    nomos forget  — DSGVO Art. 17 — delete personal data
    nomos assign  — Assign a task to an agent
    nomos costs   — Show cost overview (all or single agent)
    nomos incidents — List all incidents
    nomos workspace — Mount/unmount collections
"""

from __future__ import annotations

import json as json_module
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from nomos.core import api
from nomos.core.compliance_engine import check_compliance
from nomos.core.forge import forge_agent
from nomos.core.hash_chain import HashChain, verify_chain
from nomos.core.manifest_validator import compute_manifest_hash, load_manifest, validate_manifest

console = Console()


# ---------------------------------------------------------------------------
# Helpers for v2 commands
# ---------------------------------------------------------------------------

def _print_result(result: dict[str, Any], *, json_flag: bool, success_msg: str) -> None:
    """Print the result of an API call — human-readable or JSON."""
    if json_flag:
        console.print(json_module.dumps(result, indent=2, ensure_ascii=False))
        return

    if result["success"]:
        console.print(f"[green]{success_msg}[/green]")
    else:
        console.print(f"[red]Fehler:[/red] {result['error']}")
        raise SystemExit(1)


@click.group()
@click.version_option(version="0.1.0", prog_name="nomos")
def main() -> None:
    """NomOS — The agentic framework that enforces EU AI Act compliance."""


@main.command()
@click.option("--name", required=True, help="Agent name (e.g. 'Mani Ruf')")
@click.option("--role", required=True, help="Agent role (e.g. 'external-secretary')")
@click.option("--company", required=True, help="Company name")
@click.option("--email", required=True, help="Agent email address")
@click.option("--risk-class", default="limited", type=click.Choice(["minimal", "limited", "high"]))
@click.option("--output-dir", required=True, type=click.Path(), help="Output directory for agent files")
def hire(name: str, role: str, company: str, email: str, risk_class: str, output_dir: str) -> None:
    """Hire a new AI agent with full compliance."""
    out = Path(output_dir)
    result = forge_agent(
        agent_name=name,
        agent_role=role,
        company=company,
        email=email,
        output_dir=out,
        risk_class=risk_class,
    )

    if not result.success:
        console.print(f"[red]Error:[/red] {result.error}")
        raise SystemExit(1)

    manifest = load_manifest(out / "manifest.yaml")
    compliance = check_compliance(manifest, out / "compliance")

    console.print(
        Panel(
            f"[bold green]Agent created:[/bold green] {name}\n"
            f"ID: {manifest.agent.id}\n"
            f"Role: {role}\n"
            f"Risk Class: {risk_class}\n"
            f"Manifest Hash: {result.manifest_hash[:16]}...\n"
            f"Compliance: {compliance.status.value}\n"
            f"Directory: {out}",
            title="nomos hire",
        )
    )

    if compliance.missing_documents:
        console.print(f"\n[yellow]Missing documents:[/yellow] {', '.join(compliance.missing_documents)}")
        console.print("Run compliance gate to generate required documents.")


@main.command()
@click.option("--agent-dir", required=True, type=click.Path(exists=True), help="Agent directory")
def verify(agent_dir: str) -> None:
    """Verify compliance of an agent."""
    agent_path = Path(agent_dir)
    manifest_file = agent_path / "manifest.yaml"

    if not manifest_file.exists():
        console.print(f"[red]Error:[/red] No manifest.yaml found in {agent_path}")
        raise SystemExit(1)

    manifest = load_manifest(manifest_file)
    errors = validate_manifest(manifest)
    compliance = check_compliance(manifest, agent_path / "compliance")

    hash_file = agent_path / "manifest.sha256"
    hash_ok = False
    if hash_file.exists():
        stored_hash = hash_file.read_text(encoding="utf-8").strip()
        computed_hash = compute_manifest_hash(manifest)
        hash_ok = stored_hash == computed_hash

    chain_result = verify_chain(agent_path / "audit")

    table = Table(title=f"Compliance Report: {manifest.agent.name}")
    table.add_column("Check", style="bold")
    table.add_column("Status")
    table.add_column("Detail")

    table.add_row(
        "Manifest Schema",
        "[green]PASS[/green]" if not errors else "[red]FAIL[/red]",
        "; ".join(errors) if errors else "Valid",
    )
    table.add_row(
        "Compliance Gate",
        f"[green]{compliance.status.value}[/green]"
        if compliance.status.value == "passed"
        else f"[red]{compliance.status.value}[/red]",
        "; ".join(compliance.errors)
        if compliance.errors
        else "; ".join(compliance.warnings)
        if compliance.warnings
        else "All documents present",
    )
    table.add_row(
        "Manifest Hash",
        "[green]PASS[/green]" if hash_ok else "[red]FAIL[/red]",
        "Integrity verified" if hash_ok else "Hash mismatch or missing",
    )
    table.add_row(
        "Audit Chain",
        "[green]PASS[/green]" if chain_result.valid else "[red]FAIL[/red]",
        f"{chain_result.entries_checked} entries verified" if chain_result.valid else "; ".join(chain_result.errors),
    )

    console.print(table)

    if compliance.missing_documents:
        console.print(f"\n[yellow]Missing:[/yellow] {', '.join(compliance.missing_documents)}")

    if compliance.status.value == "blocked" or not hash_ok or not chain_result.valid:
        raise SystemExit(1)


@main.command()
@click.option("--agents-dir", default="./data/agents", type=click.Path(), help="Agents directory")
def fleet(agents_dir: str) -> None:
    """List all agents in the local fleet."""
    agents_path = Path(agents_dir)

    if not agents_path.exists():
        console.print("No agents directory found. Run [bold]nomos hire[/bold] to create one.")
        return

    agent_dirs = [d for d in agents_path.iterdir() if d.is_dir() and (d / "manifest.yaml").exists()]

    if not agent_dirs:
        console.print("No agents found. Run [bold]nomos hire[/bold] to create one.")
        return

    table = Table(title=f"NomOS Fleet ({len(agent_dirs)} agents)")
    table.add_column("ID", style="bold")
    table.add_column("Name")
    table.add_column("Role")
    table.add_column("Risk")
    table.add_column("Compliance")

    for agent_dir in sorted(agent_dirs):
        try:
            manifest = load_manifest(agent_dir / "manifest.yaml")
            compliance = check_compliance(manifest, agent_dir / "compliance")
            table.add_row(
                manifest.agent.id,
                manifest.agent.name,
                manifest.agent.role,
                manifest.agent.risk_class.value,
                compliance.status.value,
            )
        except Exception as exc:
            table.add_row(agent_dir.name, "?", "?", "?", f"[red]Error: {exc}[/red]")

    console.print(table)


@main.command()
@click.option("--agent-dir", required=True, type=click.Path(exists=True), help="Agent directory")
def gate(agent_dir: str) -> None:
    """Generate compliance documents for an agent (Compliance Gate)."""
    agent_path = Path(agent_dir)
    manifest_file = agent_path / "manifest.yaml"

    if not manifest_file.exists():
        console.print(f"[red]Error:[/red] No manifest.yaml found in {agent_path}")
        raise SystemExit(1)

    manifest = load_manifest(manifest_file)

    from nomos.core.gate import generate_compliance_docs, load_compliance_status

    # Check status before
    status_before = load_compliance_status(agent_path)
    if status_before["complete"]:
        console.print("[green]All compliance documents already exist.[/green]")
        return

    # Generate
    docs = generate_compliance_docs(manifest, agent_path / "compliance")

    console.print(
        Panel(
            f"[bold green]Compliance Gate: {len(docs)} documents generated[/bold green]\n\n"
            + "\n".join(f"  [green]V[/green] {d.title} ({d.path.name})" for d in docs)
            + f"\n\nAgent: {manifest.agent.name}\n"
            f"Directory: {agent_path / 'compliance'}",
            title="nomos gate",
        )
    )

    # Verify compliance now passes
    compliance = check_compliance(manifest, agent_path / "compliance")
    if compliance.status.value == "passed":
        console.print("\n[bold green]Compliance Status: PASSED[/bold green] — Agent is ready for deployment.")
    else:
        console.print(f"\n[yellow]Compliance Status: {compliance.status.value}[/yellow]")
        if compliance.missing_documents:
            console.print(f"Still missing: {', '.join(compliance.missing_documents)}")


@main.command()
@click.option("--agent-dir", required=True, type=click.Path(exists=True), help="Agent directory")
@click.option("--verify", "do_verify", is_flag=True, default=False, help="Verify chain integrity")
def audit(agent_dir: str, do_verify: bool) -> None:
    """Show or verify audit trail for an agent."""
    agent_path = Path(agent_dir)
    audit_dir = agent_path / "audit"

    if not audit_dir.exists():
        console.print(f"[red]Error:[/red] No audit directory in {agent_path}")
        raise SystemExit(1)

    if do_verify:
        result = verify_chain(audit_dir)
        if result.valid:
            console.print(f"[green]Audit chain VALID[/green] — {result.entries_checked} entries verified")
        else:
            console.print("[red]Audit chain INVALID[/red]")
            for error in result.errors:
                console.print(f"  [red]•[/red] {error}")
            raise SystemExit(1)
    else:
        chain = HashChain(storage_dir=audit_dir)
        if len(chain) == 0:
            console.print("No audit entries.")
            return

        table = Table(title="Audit Trail")
        table.add_column("#", style="dim")
        table.add_column("Event")
        table.add_column("Agent")
        table.add_column("Timestamp")
        table.add_column("Hash", style="dim")

        for entry in chain.entries:
            table.add_row(
                str(entry.sequence),
                entry.event_type,
                entry.agent_id,
                entry.timestamp[:19],
                entry.hash[:16] + "...",
            )

        console.print(table)


# ═══════════════════════════════════════════════════════════════════════════
# CLI v2 — API-backed commands
# ═══════════════════════════════════════════════════════════════════════════


@main.command()
@click.argument("agent_id")
@click.option("--json", "json_flag", is_flag=True, default=False, help="Machine-readable JSON output")
def pause(agent_id: str, json_flag: bool) -> None:
    """Pause a running agent."""
    result = api.pause_agent(agent_id)
    if not json_flag and result["success"]:
        data = result["data"]
        _print_result(result, json_flag=False, success_msg=f"Agent {data['name']} ({agent_id}) pausiert.")
    else:
        _print_result(result, json_flag=json_flag, success_msg="")


@main.command()
@click.argument("agent_id")
@click.option("--json", "json_flag", is_flag=True, default=False, help="Machine-readable JSON output")
def resume(agent_id: str, json_flag: bool) -> None:
    """Resume a paused agent."""
    result = api.resume_agent(agent_id)
    if not json_flag and result["success"]:
        data = result["data"]
        _print_result(result, json_flag=False, success_msg=f"Agent {data['name']} ({agent_id}) laeuft wieder.")
    else:
        _print_result(result, json_flag=json_flag, success_msg="")


@main.command()
@click.argument("agent_id")
@click.option("--json", "json_flag", is_flag=True, default=False, help="Machine-readable JSON output")
def retire(agent_id: str, json_flag: bool) -> None:
    """Gracefully retire an agent — revoke access, archive data."""
    result = api.retire_agent(agent_id)
    if not json_flag and result["success"]:
        data = result["data"]
        _print_result(result, json_flag=False, success_msg=f"Agent {data['name']} ({agent_id}) wurde in den Ruhestand versetzt.")
    else:
        _print_result(result, json_flag=json_flag, success_msg="")


@main.command()
@click.argument("email")
@click.option("--json", "json_flag", is_flag=True, default=False, help="Machine-readable JSON output")
def forget(email: str, json_flag: bool) -> None:
    """DSGVO Art. 17 — delete all personal data for an email address."""
    result = api.forget_email(email)
    if not json_flag and result["success"]:
        data = result["data"]
        deleted = data.get("deleted_messages", 0)
        _print_result(
            result,
            json_flag=False,
            success_msg=f"DSGVO Loeschung: {deleted} Nachrichten fuer {email} geloescht.",
        )
    else:
        _print_result(result, json_flag=json_flag, success_msg="")


@main.command()
@click.argument("agent_id")
@click.option("--task", required=True, help="Task description")
@click.option("--priority", default="normal", type=click.Choice(["low", "normal", "high", "urgent"]))
@click.option("--timeout", "timeout_minutes", default=60, type=int, help="Timeout in minutes")
@click.option("--json", "json_flag", is_flag=True, default=False, help="Machine-readable JSON output")
def assign(agent_id: str, task: str, priority: str, timeout_minutes: int, json_flag: bool) -> None:
    """Assign a task to an agent."""
    result = api.create_task(agent_id, task, priority=priority, timeout_minutes=timeout_minutes)
    if not json_flag and result["success"]:
        data = result["data"]
        _print_result(
            result,
            json_flag=False,
            success_msg=f"Task {data['id']} erstellt fuer Agent {agent_id}: {task}",
        )
    else:
        _print_result(result, json_flag=json_flag, success_msg="")


@main.command()
@click.argument("agent_id", required=False, default=None)
@click.option("--json", "json_flag", is_flag=True, default=False, help="Machine-readable JSON output")
def costs(agent_id: str | None, json_flag: bool) -> None:
    """Show cost overview — all agents or a single agent."""
    if agent_id:
        result = api.get_agent_costs(agent_id)
        if json_flag:
            _print_result(result, json_flag=True, success_msg="")
            return
        if not result["success"]:
            _print_result(result, json_flag=False, success_msg="")
            return

        data = result["data"]
        table = Table(title=f"Kosten: {agent_id}")
        table.add_column("Agent", style="bold")
        table.add_column("Kosten (EUR)", justify="right")
        table.add_column("Budget (EUR)", justify="right")
        table.add_column("Auslastung", justify="right")
        table.add_column("Status")
        table.add_row(
            data["agent_id"],
            f"{data['total_cost_eur']:.2f}",
            f"{data['budget_limit_eur']:.2f}",
            f"{data['percent_used']:.0f}%",
            data["budget_status"],
        )
        console.print(table)
    else:
        result = api.get_costs()
        if json_flag:
            _print_result(result, json_flag=True, success_msg="")
            return
        if not result["success"]:
            _print_result(result, json_flag=False, success_msg="")
            return

        data = result["data"]
        cost_list = data.get("costs", [])
        if not cost_list:
            console.print("Keine Kostendaten vorhanden.")
            return

        table = Table(title=f"Kostenuebersicht ({data['total']} Agents)")
        table.add_column("Agent", style="bold")
        table.add_column("Kosten (EUR)", justify="right")
        table.add_column("Budget (EUR)", justify="right")
        table.add_column("Auslastung", justify="right")
        table.add_column("Status")
        for c in cost_list:
            table.add_row(
                c["agent_id"],
                f"{c['total_cost_eur']:.2f}",
                f"{c['budget_limit_eur']:.2f}",
                f"{c['percent_used']:.0f}%",
                c["budget_status"],
            )
        console.print(table)


@main.command()
@click.option("--json", "json_flag", is_flag=True, default=False, help="Machine-readable JSON output")
def incidents(json_flag: bool) -> None:
    """List all incidents (Art. 33/34 DSGVO)."""
    result = api.get_incidents()
    if json_flag:
        _print_result(result, json_flag=True, success_msg="")
        return
    if not result["success"]:
        _print_result(result, json_flag=False, success_msg="")
        return

    data = result["data"]
    incident_list = data.get("incidents", [])
    if not incident_list:
        console.print("Keine Incidents vorhanden.")
        return

    table = Table(title=f"Incidents ({data['total']})")
    table.add_column("ID", style="bold")
    table.add_column("Agent")
    table.add_column("Typ")
    table.add_column("Schwere")
    table.add_column("Status")
    table.add_column("Erkannt")
    table.add_column("Meldefrist")
    for inc in incident_list:
        table.add_row(
            str(inc["id"]),
            inc["agent_id"],
            inc["incident_type"],
            inc["severity"],
            inc["status"],
            inc["detected_at"][:19],
            inc["report_deadline"][:19],
        )
    console.print(table)


# --- Workspace sub-group ---


@main.group()
def workspace() -> None:
    """Manage agent workspace collections."""


@workspace.command("mount")
@click.option("--agent", required=True, help="Agent ID")
@click.option("--collection", required=True, help="Collection name")
@click.option("--json", "json_flag", is_flag=True, default=False, help="Machine-readable JSON output")
def workspace_mount(agent: str, collection: str, json_flag: bool) -> None:
    """Mount a collection to an agent's workspace."""
    result = api.mount_collection(agent, collection)
    if not json_flag and result["success"]:
        _print_result(
            result,
            json_flag=False,
            success_msg=f"Collection '{collection}' fuer Agent {agent} gemountet.",
        )
    else:
        _print_result(result, json_flag=json_flag, success_msg="")


@workspace.command("unmount")
@click.option("--agent", required=True, help="Agent ID")
@click.option("--collection", required=True, help="Collection name")
@click.option("--json", "json_flag", is_flag=True, default=False, help="Machine-readable JSON output")
def workspace_unmount(agent: str, collection: str, json_flag: bool) -> None:
    """Unmount a collection from an agent's workspace."""
    result = api.unmount_collection(agent, collection)
    if not json_flag and result["success"]:
        _print_result(
            result,
            json_flag=False,
            success_msg=f"Collection '{collection}' fuer Agent {agent} ausgehaengt.",
        )
    else:
        _print_result(result, json_flag=json_flag, success_msg="")
