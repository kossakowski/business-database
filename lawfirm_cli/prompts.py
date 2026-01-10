"""Tooltip-driven input prompts with validation."""

from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from lawfirm_cli.metadata import (
    FieldMetadata,
    EnumOption,
    get_field_metadata,
    get_enum_options,
    get_editable_fields,
)


console = Console()


def prompt_field(
    field_key: str,
    current_value: Optional[str] = None,
    required: bool = False,
    test: bool = False,
) -> Optional[str]:
    """Prompt user for a field value with tooltip guidance.
    
    Args:
        field_key: Field key (e.g., 'entity.entity_type', 'id.PESEL').
        current_value: Current value (for updates).
        required: If True, don't allow empty input.
        test: If True, use test database for metadata.
        
    Returns:
        User input value, or None if skipped.
    """
    meta = get_field_metadata(field_key, test=test)
    
    if not meta:
        # Fallback if no metadata
        return Prompt.ask(f"Enter {field_key}", default=current_value or "")
    
    if not meta.is_user_editable:
        if current_value:
            console.print(f"[dim]{meta.label_pl}: {current_value} (read-only)[/dim]")
        return current_value
    
    # Display field info
    _display_field_prompt(meta, current_value)
    
    # Handle different input types
    if meta.input_type == "select":
        return _prompt_select(meta, current_value, required, test)
    elif meta.input_type == "multiselect":
        return _prompt_multiselect(meta, current_value, test)
    elif meta.input_type == "boolean":
        return _prompt_boolean(meta, current_value)
    elif meta.input_type == "textarea":
        return _prompt_textarea(meta, current_value, required)
    else:
        return _prompt_text(meta, current_value, required)


def _display_field_prompt(meta: FieldMetadata, current_value: Optional[str] = None):
    """Display field information before prompting."""
    console.print()
    
    # Label and tooltip
    label_text = f"[bold cyan]{meta.label_pl}[/bold cyan]"
    if meta.tooltip_pl:
        label_text += f"\n[dim]{meta.tooltip_pl}[/dim]"
    
    # Example/placeholder
    hints = []
    if meta.example_value:
        hints.append(f"Example: {meta.example_value}")
    if meta.placeholder and meta.placeholder != meta.example_value:
        hints.append(f"Format: {meta.placeholder}")
    if meta.validation_hint:
        hints.append(f"Validation: {meta.validation_hint}")
    
    if hints:
        label_text += f"\n[dim italic]{' | '.join(hints)}[/dim italic]"
    
    if current_value:
        label_text += f"\n[yellow]Current: {current_value}[/yellow]"
    
    console.print(Panel(label_text, border_style="blue", padding=(0, 1)))


def _prompt_text(
    meta: FieldMetadata,
    current_value: Optional[str] = None,
    required: bool = False,
) -> Optional[str]:
    """Prompt for text input with validation."""
    while True:
        default = current_value or ""
        value = Prompt.ask(
            f"Enter value",
            default=default,
            show_default=bool(default),
        )
        
        value = value.strip()
        
        if not value:
            if required:
                console.print("[red]This field is required.[/red]")
                continue
            return None
        
        # Validate
        is_valid, error = meta.validate(value)
        if not is_valid:
            console.print(f"[red]Invalid: {error}[/red]")
            continue
        
        return value


def _prompt_textarea(
    meta: FieldMetadata,
    current_value: Optional[str] = None,
    required: bool = False,
) -> Optional[str]:
    """Prompt for multi-line text input."""
    console.print("[dim]Enter text (press Enter twice to finish):[/dim]")
    
    lines = []
    empty_count = 0
    
    while True:
        line = console.input("> ")
        if line == "":
            empty_count += 1
            if empty_count >= 2:
                break
            lines.append("")
        else:
            empty_count = 0
            lines.append(line)
    
    # Remove trailing empty lines
    while lines and lines[-1] == "":
        lines.pop()
    
    value = "\n".join(lines).strip()
    
    if not value:
        if required:
            console.print("[red]This field is required.[/red]")
            return _prompt_textarea(meta, current_value, required)
        return current_value
    
    return value


def _prompt_boolean(
    meta: FieldMetadata,
    current_value: Optional[str] = None,
) -> str:
    """Prompt for boolean input."""
    default = current_value == "true" if current_value else False
    result = Confirm.ask("Yes/No", default=default)
    return "true" if result else "false"


def _prompt_select(
    meta: FieldMetadata,
    current_value: Optional[str] = None,
    required: bool = False,
    test: bool = False,
) -> Optional[str]:
    """Prompt for select (single choice) input."""
    # Derive enum_key from field_key
    # e.g., 'entity.entity_type' -> 'entity_type'
    # e.g., 'legal.legal_kind' -> 'legal_kind'
    parts = meta.field_key.split(".")
    enum_key = parts[-1] if len(parts) > 1 else meta.field_key
    
    options = get_enum_options(enum_key, test=test)
    
    if not options:
        console.print(f"[yellow]No options found for {enum_key}[/yellow]")
        return _prompt_text(meta, current_value, required)
    
    # Display options
    console.print()
    console.print("[bold]Options:[/bold]")
    for i, opt in enumerate(options, 1):
        current_marker = " [yellow](current)[/yellow]" if opt.enum_value == current_value else ""
        tooltip = f" - [dim]{opt.tooltip_pl}[/dim]" if opt.tooltip_pl else ""
        console.print(f"  {i}. {opt.label_pl}{tooltip}{current_marker}")
    
    if not required:
        console.print(f"  0. [dim]Skip (no selection)[/dim]")
    
    # Get selection
    while True:
        choice = Prompt.ask("Select option number")
        
        try:
            idx = int(choice)
            if idx == 0 and not required:
                return None
            if 1 <= idx <= len(options):
                return options[idx - 1].enum_value
            console.print(f"[red]Please enter a number between 1 and {len(options)}[/red]")
        except ValueError:
            # Allow typing the value directly
            for opt in options:
                if choice.upper() == opt.enum_value or choice.lower() == opt.label_pl.lower():
                    return opt.enum_value
            console.print("[red]Invalid selection. Enter a number or exact value.[/red]")


def _prompt_multiselect(
    meta: FieldMetadata,
    current_value: Optional[str] = None,
    test: bool = False,
) -> Optional[str]:
    """Prompt for multiselect input."""
    # Similar to select but allows multiple choices
    parts = meta.field_key.split(".")
    enum_key = parts[-1] if len(parts) > 1 else meta.field_key
    
    options = get_enum_options(enum_key, test=test)
    
    if not options:
        return _prompt_text(meta, current_value, False)
    
    current_list = current_value.split(",") if current_value else []
    
    console.print()
    console.print("[bold]Options (enter numbers separated by commas):[/bold]")
    for i, opt in enumerate(options, 1):
        selected = "[green]✓[/green]" if opt.enum_value in current_list else " "
        console.print(f"  {selected} {i}. {opt.label_pl}")
    
    console.print("  0. Done / Skip")
    
    choices = Prompt.ask("Select options (e.g., 1,3,5)", default="")
    
    if not choices or choices == "0":
        return current_value
    
    selected = []
    for part in choices.split(","):
        try:
            idx = int(part.strip())
            if 1 <= idx <= len(options):
                selected.append(options[idx - 1].enum_value)
        except ValueError:
            continue
    
    return ",".join(selected) if selected else None


def prompt_entity_type(test: bool = False) -> str:
    """Prompt user to select entity type.
    
    Args:
        test: If True, use test database.
        
    Returns:
        Selected entity type ('PHYSICAL_PERSON' or 'LEGAL_PERSON').
    """
    console.print()
    console.print("[bold cyan]Select Entity Type[/bold cyan]")
    
    options = get_enum_options("entity_type", test=test)
    
    if not options:
        # Fallback if no metadata
        options = [
            type("EnumOption", (), {"enum_value": "PHYSICAL_PERSON", "label_pl": "Osoba fizyczna", "tooltip_pl": "Person"}),
            type("EnumOption", (), {"enum_value": "LEGAL_PERSON", "label_pl": "Podmiot prawny", "tooltip_pl": "Legal entity"}),
        ]
    
    console.print()
    for i, opt in enumerate(options, 1):
        tooltip = f" - {opt.tooltip_pl}" if opt.tooltip_pl else ""
        console.print(f"  {i}. [bold]{opt.label_pl}[/bold]{tooltip}")
    
    while True:
        choice = Prompt.ask("Select type (1 or 2)")
        try:
            idx = int(choice)
            if 1 <= idx <= len(options):
                return options[idx - 1].enum_value
        except ValueError:
            pass
        console.print("[red]Please enter 1 or 2[/red]")


def prompt_entity_fields(
    entity_type: str,
    existing_data: Optional[Dict[str, Any]] = None,
    test: bool = False,
) -> Dict[str, Any]:
    """Prompt for all entity fields based on type.
    
    Args:
        entity_type: 'PHYSICAL_PERSON' or 'LEGAL_PERSON'.
        existing_data: Existing data for updates.
        test: If True, use test database.
        
    Returns:
        Dict of field values.
    """
    data = {}
    existing = existing_data or {}
    
    # Core entity fields
    console.print()
    console.print("[bold magenta]── Core Entity Fields ──[/bold magenta]")
    
    data["canonical_label"] = prompt_field(
        "entity.canonical_label",
        existing.get("canonical_label"),
        required=True,
        test=test,
    )
    
    data["notes"] = prompt_field(
        "entity.notes",
        existing.get("notes"),
        test=test,
    )
    
    # Type-specific fields
    if entity_type == "PHYSICAL_PERSON":
        console.print()
        console.print("[bold magenta]── Physical Person Fields ──[/bold magenta]")
        
        data["first_name"] = prompt_field("person.first_name", existing.get("first_name"), required=True, test=test)
        data["middle_names"] = prompt_field("person.middle_names", existing.get("middle_names"), test=test)
        data["last_name"] = prompt_field("person.last_name", existing.get("last_name"), required=True, test=test)
        data["date_of_birth"] = prompt_field("person.date_of_birth", existing.get("date_of_birth"), test=test)
        data["citizenship_country"] = prompt_field("person.citizenship_country", existing.get("citizenship_country"), test=test)
        
        is_deceased = prompt_field("person.is_deceased", str(existing.get("is_deceased", False)).lower(), test=test)
        data["is_deceased"] = is_deceased == "true"
        
    elif entity_type == "LEGAL_PERSON":
        console.print()
        console.print("[bold magenta]── Legal Person Fields ──[/bold magenta]")
        
        data["registered_name"] = prompt_field("legal.registered_name", existing.get("registered_name"), required=True, test=test)
        data["short_name"] = prompt_field("legal.short_name", existing.get("short_name"), test=test)
        data["legal_kind"] = prompt_field("legal.legal_kind", existing.get("legal_kind"), test=test)
        data["legal_nature"] = prompt_field("legal.legal_nature", existing.get("legal_nature"), test=test)
        data["legal_form_suffix"] = prompt_field("legal.legal_form_suffix", existing.get("legal_form_suffix"), test=test)
        data["country"] = prompt_field("legal.country", existing.get("country", "PL"), test=test) or "PL"
    
    return data


def prompt_identifiers(
    entity_type: str,
    existing: Optional[List[Dict[str, Any]]] = None,
    test: bool = False,
) -> List[Dict[str, str]]:
    """Prompt for entity identifiers.
    
    Args:
        entity_type: 'PHYSICAL_PERSON' or 'LEGAL_PERSON'.
        existing: Existing identifiers.
        test: If True, use test database.
        
    Returns:
        List of identifier dicts with 'type' and 'value' keys.
    """
    console.print()
    console.print("[bold magenta]── Identifiers ──[/bold magenta]")
    
    identifiers = []
    existing_map = {i["identifier_type"]: i["identifier_value"] for i in (existing or [])}
    
    # Define which identifiers to prompt based on entity type
    if entity_type == "PHYSICAL_PERSON":
        id_types = ["PESEL", "NIP", "REGON"]
    else:
        id_types = ["KRS", "NIP", "REGON", "RFR"]
    
    for id_type in id_types:
        field_key = f"id.{id_type}"
        current = existing_map.get(id_type)
        
        value = prompt_field(field_key, current, test=test)
        if value:
            identifiers.append({"type": id_type, "value": value})
    
    # Prompt for other registry
    console.print()
    if Confirm.ask("Add other registry identifier?", default=False):
        registry_name = prompt_field("id.OTHER_REGISTRY_NAME", test=test)
        registry_number = prompt_field("id.OTHER_REGISTRY_NUMBER", test=test)
        if registry_name and registry_number:
            identifiers.append({
                "type": "OTHER",
                "value": registry_number,
                "registry_name": registry_name,
            })
    
    return identifiers


def prompt_address(
    existing: Optional[Dict[str, Any]] = None,
    test: bool = False,
) -> Optional[Dict[str, Any]]:
    """Prompt for a single address.
    
    Args:
        existing: Existing address data.
        test: If True, use test database.
        
    Returns:
        Address dict or None if skipped.
    """
    console.print()
    console.print("[bold magenta]── Address ──[/bold magenta]")
    
    if not Confirm.ask("Add an address?", default=bool(existing)):
        return None
    
    existing = existing or {}
    
    addr = {}
    addr["address_type"] = prompt_field("addr.address_type", existing.get("address_type", "MAIN"), test=test) or "MAIN"
    addr["country"] = prompt_field("addr.country", existing.get("country", "PL"), test=test) or "PL"
    addr["city"] = prompt_field("addr.city", existing.get("city"), required=True, test=test)
    addr["postal_code"] = prompt_field("addr.postal_code", existing.get("postal_code"), test=test)
    addr["street"] = prompt_field("addr.street", existing.get("street"), test=test)
    addr["building_no"] = prompt_field("addr.building_no", existing.get("building_no"), test=test)
    addr["unit_no"] = prompt_field("addr.unit_no", existing.get("unit_no"), test=test)
    
    return addr


def prompt_contacts(
    existing: Optional[List[Dict[str, Any]]] = None,
    test: bool = False,
) -> List[Dict[str, str]]:
    """Prompt for contact information.
    
    Args:
        existing: Existing contacts.
        test: If True, use test database.
        
    Returns:
        List of contact dicts.
    """
    console.print()
    console.print("[bold magenta]── Contacts ──[/bold magenta]")
    
    contacts = []
    existing_map = {c["contact_type"]: c["contact_value"] for c in (existing or [])}
    
    contact_types = ["EMAIL", "PHONE", "WEBSITE"]
    
    for c_type in contact_types:
        field_key = f"contact.{c_type}"
        current = existing_map.get(c_type)
        
        value = prompt_field(field_key, current, test=test)
        if value:
            contacts.append({"type": c_type, "value": value})
    
    return contacts


def prompt_delete_confirmation(entity_label: str, related_counts: Dict[str, int]) -> bool:
    """Prompt for delete confirmation.
    
    Args:
        entity_label: Label of entity being deleted.
        related_counts: Dict of related record counts.
        
    Returns:
        True if confirmed, False otherwise.
    """
    console.print()
    console.print("[bold red]═══ DELETE CONFIRMATION ═══[/bold red]")
    console.print()
    console.print(f"You are about to delete: [bold]{entity_label}[/bold]")
    console.print()
    
    if any(related_counts.values()):
        console.print("[yellow]This will also delete:[/yellow]")
        for record_type, count in related_counts.items():
            if count > 0:
                console.print(f"  • {count} {record_type}")
        console.print()
    
    console.print(f"Type '[bold]DELETE[/bold]' to confirm, or anything else to cancel:")
    response = console.input("> ").strip()
    
    return response == "DELETE"
