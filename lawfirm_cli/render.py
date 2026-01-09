"""Rendering utilities for terminal output."""

from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from lawfirm_cli.metadata import (
    FieldMetadata, 
    EnumOption,
    get_enum_label,
    get_field_metadata,
)


# Global console instance
console = Console()


def print_error(message: str):
    """Print an error message."""
    console.print(f"[bold red]Error:[/bold red] {message}")


def print_success(message: str):
    """Print a success message."""
    console.print(f"[bold green]Success:[/bold green] {message}")


def print_warning(message: str):
    """Print a warning message."""
    console.print(f"[bold yellow]Warning:[/bold yellow] {message}")


def print_info(message: str):
    """Print an info message."""
    console.print(f"[bold blue]Info:[/bold blue] {message}")


def print_section_header(title: str):
    """Print a section header."""
    console.print()
    console.print(f"[bold cyan]═══ {title} ═══[/bold cyan]")
    console.print()


def render_table(
    columns: List[Tuple[str, str]],
    rows: List[Dict[str, Any]],
    title: Optional[str] = None,
    show_row_numbers: bool = False,
):
    """Render a formatted table.
    
    Args:
        columns: List of (key, header_label) tuples.
        rows: List of row dictionaries.
        title: Optional table title.
        show_row_numbers: If True, show row numbers.
    """
    table = Table(
        title=title,
        box=box.ROUNDED,
        header_style="bold magenta",
        row_styles=["", "dim"],
    )
    
    if show_row_numbers:
        table.add_column("#", justify="right", style="dim")
    
    for key, header in columns:
        table.add_column(header, overflow="fold")
    
    for i, row in enumerate(rows, 1):
        values = []
        if show_row_numbers:
            values.append(str(i))
        for key, _ in columns:
            val = row.get(key, "")
            values.append(str(val) if val is not None else "—")
        table.add_row(*values)
    
    console.print(table)


def render_field_list(fields: List[FieldMetadata], title: Optional[str] = None):
    """Render a list of field metadata.
    
    Args:
        fields: List of FieldMetadata objects.
        title: Optional title.
    """
    table = Table(
        title=title,
        box=box.ROUNDED,
        header_style="bold magenta",
    )
    
    table.add_column("Field Key", style="cyan")
    table.add_column("Label (PL)")
    table.add_column("Type")
    table.add_column("Group")
    table.add_column("Editable")
    
    for f in fields:
        editable = "[green]Yes[/green]" if f.is_user_editable else "[red]No[/red]"
        table.add_row(
            f.field_key,
            f.label_pl,
            f.input_type,
            f.display_group,
            editable,
        )
    
    console.print(table)


def render_enum_options(options: List[EnumOption], enum_key: str):
    """Render enum options.
    
    Args:
        options: List of EnumOption objects.
        enum_key: The enum key name.
    """
    table = Table(
        title=f"Enum: {enum_key}",
        box=box.ROUNDED,
        header_style="bold magenta",
    )
    
    table.add_column("Value", style="cyan")
    table.add_column("Label (PL)")
    table.add_column("Tooltip")
    table.add_column("Suffix")
    
    for opt in options:
        table.add_row(
            opt.enum_value,
            opt.label_pl,
            opt.tooltip_pl or "—",
            opt.suffix_default or "—",
        )
    
    console.print(table)


def render_entity_detail(
    entity: Dict[str, Any],
    identifiers: List[Dict[str, Any]] = None,
    addresses: List[Dict[str, Any]] = None,
    contacts: List[Dict[str, Any]] = None,
    test: bool = False,
):
    """Render detailed view of an entity.
    
    Args:
        entity: Entity data dictionary.
        identifiers: List of identifier records.
        addresses: List of address records.
        contacts: List of contact records.
        test: If True, use test database for metadata.
    """
    entity_type = entity.get("entity_type", "UNKNOWN")
    canonical_label = entity.get("canonical_label", "Unknown Entity")
    
    # Header panel
    type_label = get_enum_label("entity_type", entity_type, test=test)
    console.print(Panel(
        f"[bold]{canonical_label}[/bold]\n[dim]{type_label}[/dim]",
        title=f"Entity #{entity.get('id', '?')}",
        border_style="cyan",
    ))
    
    # Core info section
    print_section_header("Core Information")
    _render_key_value_pairs([
        ("ID", entity.get("id")),
        ("Type", type_label),
        ("Label", canonical_label),
        ("Status", entity.get("status", "—")),
        ("Notes", entity.get("notes", "—")),
        ("Created", entity.get("created_at", "—")),
        ("Updated", entity.get("updated_at", "—")),
    ])
    
    # Type-specific info
    if entity_type == "PHYSICAL_PERSON":
        print_section_header("Physical Person Details")
        _render_key_value_pairs([
            ("First Name", entity.get("first_name", "—")),
            ("Middle Names", entity.get("middle_names", "—")),
            ("Last Name", entity.get("last_name", "—")),
            ("Date of Birth", entity.get("date_of_birth", "—")),
            ("Citizenship", entity.get("citizenship_country", "—")),
            ("Deceased", "Yes" if entity.get("is_deceased") else "No"),
        ])
    elif entity_type == "LEGAL_PERSON":
        print_section_header("Legal Person Details")
        legal_kind = entity.get("legal_kind", "—")
        kind_label = get_enum_label("legal_kind", legal_kind, test=test) if legal_kind != "—" else "—"
        _render_key_value_pairs([
            ("Registered Name", entity.get("registered_name", "—")),
            ("Short Name", entity.get("short_name", "—")),
            ("Legal Kind", kind_label),
            ("Legal Nature", entity.get("legal_nature", "—")),
            ("Form Suffix", entity.get("legal_form_suffix", "—")),
            ("Country", entity.get("country", "—")),
        ])
    
    # Identifiers section
    if identifiers:
        print_section_header("Identifiers")
        for ident in identifiers:
            id_type = ident.get("identifier_type", "UNKNOWN")
            id_value = ident.get("identifier_value", "—")
            console.print(f"  [cyan]{id_type}:[/cyan] {id_value}")
    elif identifiers is not None:
        print_section_header("Identifiers")
        console.print("  [dim]No identifiers recorded.[/dim]")
    
    # Addresses section
    if addresses:
        print_section_header("Addresses")
        for addr in addresses:
            addr_type = addr.get("address_type", "ADDRESS")
            lines = _format_address(addr)
            console.print(f"  [cyan]{addr_type}:[/cyan]")
            for line in lines:
                console.print(f"    {line}")
            console.print()
    elif addresses is not None:
        print_section_header("Addresses")
        console.print("  [dim]No addresses recorded.[/dim]")
    
    # Contacts section
    if contacts:
        print_section_header("Contacts")
        for contact in contacts:
            c_type = contact.get("contact_type", "CONTACT")
            c_value = contact.get("contact_value", "—")
            console.print(f"  [cyan]{c_type}:[/cyan] {c_value}")
    elif contacts is not None:
        print_section_header("Contacts")
        console.print("  [dim]No contacts recorded.[/dim]")


def _render_key_value_pairs(pairs: List[Tuple[str, Any]]):
    """Render key-value pairs with aligned formatting."""
    max_key_len = max(len(k) for k, _ in pairs) if pairs else 0
    for key, value in pairs:
        val_str = str(value) if value is not None else "—"
        console.print(f"  [cyan]{key:>{max_key_len}}:[/cyan] {val_str}")


def _format_address(addr: Dict[str, Any]) -> List[str]:
    """Format address fields into display lines."""
    lines = []
    
    street = addr.get("street", "")
    building = addr.get("building_no", "")
    unit = addr.get("unit_no", "")
    
    if street or building:
        street_line = street
        if building:
            street_line += f" {building}"
            if unit:
                street_line += f"/{unit}"
        lines.append(street_line)
    
    postal = addr.get("postal_code", "")
    city = addr.get("city", "")
    if postal or city:
        lines.append(f"{postal} {city}".strip())
    
    country = addr.get("country", "")
    if country and country != "PL":
        lines.append(country)
    
    return lines if lines else ["(no address details)"]


def render_schema_status(status):
    """Render schema status report.
    
    Args:
        status: SchemaStatus object.
    """
    console.print()
    console.print("[bold]Database Schema Status[/bold]")
    console.print()
    
    # Meta tables
    console.print("[cyan]Meta Tables:[/cyan]")
    for t in status.meta_tables:
        icon = "[green]✓[/green]" if t.exists else "[red]✗[/red]"
        console.print(f"  {icon} {t.full_name}")
    
    console.print()
    
    # Entity tables
    console.print("[cyan]Entity Tables:[/cyan]")
    for t in status.entity_tables:
        icon = "[green]✓[/green]" if t.exists else "[red]✗[/red]"
        console.print(f"  {icon} {t.full_name}")
    
    console.print()
    
    # Summary
    if status.entities_ready:
        console.print("[green]All entity tables are ready.[/green]")
    else:
        console.print("[yellow]Entity tables are not yet created.[/yellow]")
        console.print("Run schema migrations to create them.")
    
    console.print()
    console.print("[dim]You can explore metadata using:[/dim]")
    console.print("  lawfirm-cli meta fields")
    console.print("  lawfirm-cli meta enums entity_type")


def confirm_action(message: str, confirm_word: str = "DELETE") -> bool:
    """Ask for confirmation of a destructive action.
    
    Args:
        message: Message to display.
        confirm_word: Word user must type to confirm.
        
    Returns:
        True if user confirmed, False otherwise.
    """
    console.print()
    console.print(f"[bold red]Warning:[/bold red] {message}")
    console.print()
    console.print(f"Type '[bold]{confirm_word}[/bold]' to confirm, or anything else to cancel:")
    
    response = console.input("> ").strip()
    return response == confirm_word
