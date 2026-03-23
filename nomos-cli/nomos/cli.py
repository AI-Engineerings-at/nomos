"""NomOS CLI — Agent Lifecycle Management.

Commands:
    nomos hire    — Create a new AI agent with full compliance
    nomos verify  — Verify compliance of an agent
    nomos fleet   — List all agents in the local fleet
    nomos audit   — Show or verify audit trail
"""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from nomos.core.compliance_engine import check_compliance
from nomos.core.forge import forge_agent
from nomos.core.hash_chain import HashChain, verify_chain
from nomos.core.manifest_validator import compute_manifest_hash, load_manifest, validate_manifest

console = Console()


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

        for entry in chain._entries:
            table.add_row(
                str(entry.sequence),
                entry.event_type,
                entry.agent_id,
                entry.timestamp[:19],
                entry.hash[:16] + "...",
            )

        console.print(table)
