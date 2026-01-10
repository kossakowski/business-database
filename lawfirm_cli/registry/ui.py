"""UI components for registry enrichment.

Handles rendering of proposals and user prompts for applying changes.
"""

from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from lawfirm_cli.registry.models import (
    EnrichmentProposal,
    ProposalAction,
    IdentifierProposal,
    ContactProposal,
    AddressProposal,
)

console = Console()


def print_registry_info(message: str):
    """Print an info message."""
    console.print(f"[bold blue]Registry:[/bold blue] {message}")


def print_registry_warning(message: str):
    """Print a warning message."""
    console.print(f"[bold yellow]Warning:[/bold yellow] {message}")


def print_registry_error(message: str):
    """Print an error message."""
    console.print(f"[bold red]Error:[/bold red] {message}")


def print_registry_success(message: str):
    """Print a success message."""
    console.print(f"[bold green]Success:[/bold green] {message}")


def render_proposal_summary(proposal: EnrichmentProposal) -> None:
    """Render a summary of the enrichment proposal.
    
    Args:
        proposal: EnrichmentProposal to display.
    """
    console.print()
    console.print(Panel(
        f"[bold]Registry Enrichment Proposal[/bold]\n"
        f"Source: [cyan]{proposal.source_system}[/cyan] | "
        f"ID: [cyan]{proposal.external_id}[/cyan]",
        border_style="blue",
    ))
    
    if not proposal.has_any_proposals():
        console.print()
        console.print("[dim]No changes proposed - entity data matches registry.[/dim]")
        return
    
    # Warnings
    if proposal.warnings:
        console.print()
        console.print("[bold yellow]⚠ Warnings:[/bold yellow]")
        for warning in proposal.warnings:
            console.print(f"  [yellow]• {warning}[/yellow]")
    
    # Info messages
    if proposal.info_messages:
        console.print()
        console.print("[dim]ℹ Notes:[/dim]")
        for msg in proposal.info_messages:
            console.print(f"  [dim]• {msg}[/dim]")
    
    # Core updates
    if proposal.core_updates:
        console.print()
        console.print("[bold cyan]Core Field Updates:[/bold cyan]")
        for field, value in proposal.core_updates.items():
            console.print(f"  • {field}: [green]{value}[/green]")
    
    # Type-specific updates
    if proposal.type_specific_updates:
        console.print()
        console.print("[bold cyan]Entity-Specific Updates:[/bold cyan]")
        for field, value in proposal.type_specific_updates.items():
            console.print(f"  • {field}: [green]{value}[/green]")
    
    # Identifiers
    if proposal.identifiers_to_add:
        console.print()
        console.print("[bold cyan]Identifiers:[/bold cyan]")
        for ident in proposal.identifiers_to_add:
            if ident.action == ProposalAction.ADD:
                console.print(
                    f"  [green]+ ADD[/green] {ident.identifier_type}: "
                    f"[bold]{ident.identifier_value}[/bold]"
                )
            elif ident.action == ProposalAction.SKIP:
                console.print(
                    f"  [yellow]⊘ SKIP[/yellow] {ident.identifier_type}: "
                    f"{ident.identifier_value} ({ident.reason})"
                )
    
    # Contacts
    if proposal.contacts_to_add:
        console.print()
        console.print("[bold cyan]Contacts:[/bold cyan]")
        for contact in proposal.contacts_to_add:
            console.print(
                f"  [green]+ ADD[/green] {contact.contact_type}: "
                f"[bold]{contact.contact_value}[/bold]"
            )
    
    # Addresses
    if proposal.address_proposals:
        console.print()
        console.print("[bold cyan]Addresses:[/bold cyan]")
        for addr_prop in proposal.address_proposals:
            addr = addr_prop.address
            action_text = "[green]+ ADD[/green]" if addr_prop.action == ProposalAction.ADD else "[yellow]↻ UPDATE[/yellow]"
            console.print(f"  {action_text} {addr.address_type}:")
            console.print(f"    {addr.format_oneline()}")


def prompt_apply_proposal(proposal: EnrichmentProposal) -> Dict[str, Any]:
    """Prompt user to select which proposals to apply.
    
    Args:
        proposal: EnrichmentProposal to prompt for.
        
    Returns:
        Dict with selected items:
            - apply_core: bool
            - apply_type_specific: bool
            - identifiers: List[IdentifierProposal] to apply
            - contacts: List[ContactProposal] to apply
            - addresses: List[AddressProposal] to apply
    """
    result = {
        "apply_core": False,
        "apply_type_specific": False,
        "identifiers": [],
        "contacts": [],
        "addresses": [],
    }
    
    if not proposal.has_any_proposals():
        return result
    
    console.print()
    console.print("[bold]Select changes to apply:[/bold]")
    console.print("[dim](Enter 'y' to apply, 'n' to skip, 'a' for all, 'q' to quit)[/dim]")
    console.print()
    
    # Ask for all at once option first
    response = console.input("[bold]Apply all safe additions? (y/n/q):[/bold] ").strip().lower()
    
    if response == "q":
        return result
    
    apply_all = response in ("y", "yes", "a", "all")
    
    # Core updates
    if proposal.core_updates:
        if apply_all:
            result["apply_core"] = True
        else:
            console.print()
            console.print("[cyan]Core updates:[/cyan]")
            for field, value in proposal.core_updates.items():
                console.print(f"  {field}: {value}")
            response = console.input("Apply core updates? (y/n): ").strip().lower()
            result["apply_core"] = response in ("y", "yes")
    
    # Type-specific updates
    if proposal.type_specific_updates:
        if apply_all:
            result["apply_type_specific"] = True
        else:
            console.print()
            console.print("[cyan]Entity-specific updates:[/cyan]")
            for field, value in proposal.type_specific_updates.items():
                console.print(f"  {field}: {value}")
            response = console.input("Apply entity-specific updates? (y/n): ").strip().lower()
            result["apply_type_specific"] = response in ("y", "yes")
    
    # Identifiers
    for ident in proposal.identifiers_to_add:
        if ident.action == ProposalAction.SKIP:
            continue
        
        if apply_all:
            result["identifiers"].append(ident)
        else:
            response = console.input(
                f"Add {ident.identifier_type} {ident.identifier_value}? (y/n): "
            ).strip().lower()
            if response in ("y", "yes"):
                result["identifiers"].append(ident)
    
    # Contacts
    for contact in proposal.contacts_to_add:
        if apply_all:
            result["contacts"].append(contact)
        else:
            response = console.input(
                f"Add {contact.contact_type} {contact.contact_value}? (y/n): "
            ).strip().lower()
            if response in ("y", "yes"):
                result["contacts"].append(contact)
    
    # Addresses
    for addr_prop in proposal.address_proposals:
        if addr_prop.action == ProposalAction.ADD:
            if apply_all:
                result["addresses"].append(addr_prop)
            else:
                response = console.input(
                    f"Add {addr_prop.address.address_type} address ({addr_prop.address.format_oneline()})? (y/n): "
                ).strip().lower()
                if response in ("y", "yes"):
                    result["addresses"].append(addr_prop)
        else:
            # Updates require explicit confirmation even in apply_all mode
            console.print()
            console.print(f"[yellow]Address update for {addr_prop.address.address_type}:[/yellow]")
            console.print(f"  New: {addr_prop.address.format_oneline()}")
            response = console.input("Apply address update? (y/n): ").strip().lower()
            if response in ("y", "yes"):
                result["addresses"].append(addr_prop)
    
    return result


def render_apply_result(
    applied: Dict[str, int],
    errors: List[str],
) -> None:
    """Render results of applying a proposal.
    
    Args:
        applied: Dict with counts of applied items.
        errors: List of error messages.
    """
    console.print()
    
    if errors:
        console.print("[bold red]Errors occurred:[/bold red]")
        for error in errors:
            console.print(f"  [red]• {error}[/red]")
        console.print()
    
    total = sum(applied.values())
    if total > 0:
        console.print("[bold green]Applied changes:[/bold green]")
        if applied.get("core"):
            console.print(f"  ✓ {applied['core']} core field(s) updated")
        if applied.get("type_specific"):
            console.print(f"  ✓ {applied['type_specific']} entity-specific field(s) updated")
        if applied.get("identifiers"):
            console.print(f"  ✓ {applied['identifiers']} identifier(s) added")
        if applied.get("contacts"):
            console.print(f"  ✓ {applied['contacts']} contact(s) added")
        if applied.get("addresses"):
            console.print(f"  ✓ {applied['addresses']} address(es) added/updated")
    else:
        console.print("[dim]No changes applied.[/dim]")


def prompt_lookup_key(
    entity_type: str,
    existing_identifiers: List[Dict[str, Any]],
) -> Tuple[Optional[str], Optional[str]]:
    """Prompt user to select or enter a lookup key.
    
    Args:
        entity_type: 'PHYSICAL_PERSON' or 'LEGAL_PERSON'.
        existing_identifiers: List of existing identifiers on entity.
        
    Returns:
        Tuple of (registry_source, lookup_key) or (None, None) if cancelled.
    """
    console.print()
    
    # Determine available sources
    if entity_type == "LEGAL_PERSON":
        sources = ["KRS", "CEIDG"]
        default_source = "KRS"
    else:
        sources = ["CEIDG"]
        default_source = "CEIDG"
    
    console.print(f"[bold]Registry Lookup[/bold]")
    console.print(f"Available sources: {', '.join(sources)}")
    console.print()
    
    # Show existing identifiers
    krs = None
    nip = None
    regon = None
    
    if existing_identifiers:
        console.print("[dim]Existing identifiers:[/dim]")
        for ident in existing_identifiers:
            id_type = ident.get("identifier_type")
            id_value = ident.get("identifier_value")
            console.print(f"  • {id_type}: {id_value}")
            if id_type == "KRS":
                krs = id_value
            elif id_type == "NIP":
                nip = id_value
            elif id_type == "REGON":
                regon = id_value
        console.print()
    
    # Choose source
    if len(sources) > 1:
        source_input = console.input(
            f"Select registry [{'/'.join(sources)}, default={default_source}]: "
        ).strip().upper()
        source = source_input if source_input in sources else default_source
    else:
        source = sources[0]
    
    # Get lookup key based on source
    if source == "KRS":
        if krs:
            use_existing = console.input(
                f"Use existing KRS number ({krs})? (y/n, default=y): "
            ).strip().lower()
            if use_existing != "n":
                return "KRS", krs
        
        # Try NIP/REGON for KRS lookup
        if nip:
            use_nip = console.input(
                f"Try lookup by NIP ({nip})? (y/n): "
            ).strip().lower()
            if use_nip in ("y", "yes"):
                console.print("[yellow]Note: KRS API primarily supports KRS number lookup.[/yellow]")
        
        # Manual entry
        key = console.input("Enter KRS number (10 digits, or 'q' to cancel): ").strip()
        if key.lower() == "q":
            return None, None
        return "KRS", key
    
    else:  # CEIDG
        if nip:
            use_existing = console.input(
                f"Use existing NIP ({nip})? (y/n, default=y): "
            ).strip().lower()
            if use_existing != "n":
                return "CEIDG", f"NIP:{nip}"
        
        if regon:
            use_regon = console.input(
                f"Use existing REGON ({regon})? (y/n): "
            ).strip().lower()
            if use_regon in ("y", "yes"):
                return "CEIDG", f"REGON:{regon}"
        
        # Manual entry
        console.print("Enter lookup key:")
        console.print("  1. NIP (10 digits)")
        console.print("  2. REGON (9 or 14 digits)")
        choice = console.input("Choice (1/2/q): ").strip()
        
        if choice == "q":
            return None, None
        elif choice == "2":
            regon_input = console.input("Enter REGON: ").strip()
            return "CEIDG", f"REGON:{regon_input}"
        else:
            nip_input = console.input("Enter NIP: ").strip()
            return "CEIDG", f"NIP:{nip_input}"


def render_profile_summary(
    profile_type: str,
    profile: Any,
) -> None:
    """Render a summary of fetched registry profile.
    
    Args:
        profile_type: 'KRS' or 'CEIDG'.
        profile: Normalized profile object.
    """
    console.print()
    console.print(Panel(
        f"[bold]Fetched {profile_type} Data[/bold]",
        border_style="green",
    ))
    
    if profile_type == "KRS":
        _render_krs_profile(profile)
    else:
        _render_ceidg_profile(profile)


def _render_krs_profile(profile) -> None:
    """Render KRS profile details."""
    table = Table(box=box.SIMPLE)
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    
    table.add_row("KRS", profile.krs or "—")
    table.add_row("NIP", profile.nip or "—")
    table.add_row("REGON", profile.regon or "—")
    table.add_row("Name", profile.official_name or "—")
    table.add_row("Short Name", profile.short_name or "—")
    table.add_row("Legal Form", profile.legal_form or "—")
    table.add_row("Status", profile.registry_status or "—")
    table.add_row("Registration Date", str(profile.registration_date) if profile.registration_date else "—")
    
    if profile.seat_address:
        table.add_row("Seat Address", profile.seat_address.format_oneline())
    
    if profile.email:
        table.add_row("Email", profile.email)
    if profile.website:
        table.add_row("Website", profile.website)
    if profile.phone:
        table.add_row("Phone", profile.phone)
    
    if profile.pkd_main:
        table.add_row("Main PKD", profile.pkd_main)
    
    if profile.representatives:
        reps = ", ".join(r.get("name", "?") for r in profile.representatives[:3])
        if len(profile.representatives) > 3:
            reps += f" (+{len(profile.representatives) - 3} more)"
        table.add_row("Representatives", reps)
    
    console.print(table)


def _render_ceidg_profile(profile) -> None:
    """Render CEIDG profile details."""
    table = Table(box=box.SIMPLE)
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    
    table.add_row("NIP", profile.nip or "—")
    table.add_row("REGON", profile.regon or "—")
    table.add_row("Owner", f"{profile.first_name or ''} {profile.last_name or ''}".strip() or "—")
    table.add_row("Business Name", profile.business_name or "—")
    table.add_row("Status", profile.status or "—")
    table.add_row("Start Date", str(profile.start_date) if profile.start_date else "—")
    
    if profile.end_date:
        table.add_row("End Date", str(profile.end_date))
    
    if profile.main_address:
        table.add_row("Main Address", profile.main_address.format_oneline())
    
    if profile.email:
        table.add_row("Email", profile.email)
    if profile.website:
        table.add_row("Website", profile.website)
    if profile.phone:
        table.add_row("Phone", profile.phone)
    
    if profile.pkd_main:
        table.add_row("Main PKD", profile.pkd_main)
    
    console.print(table)
