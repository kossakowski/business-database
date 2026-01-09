"""CLI commands using Click framework."""

import click
from rich.console import Console

from lawfirm_cli.schema import get_schema_status
from lawfirm_cli.metadata import (
    load_all_field_metadata,
    load_all_enum_options,
    get_field_metadata,
    get_enum_options,
    get_all_display_groups,
    get_all_enum_keys,
    get_fields_by_group,
)
from lawfirm_cli.entities import (
    check_entities_available,
    create_entity,
    list_entities,
    get_entity,
    update_entity,
    delete_entity,
    get_related_counts,
    add_identifier,
    update_identifier,
    remove_identifier,
    add_address,
    update_address,
    remove_address,
    add_contact,
    update_contact,
    remove_contact,
    EntityNotFoundError,
    DuplicateIdentifierError,
)
from lawfirm_cli.prompts import (
    prompt_entity_type,
    prompt_entity_fields,
    prompt_identifiers,
    prompt_address,
    prompt_contacts,
    prompt_delete_confirmation,
)
from lawfirm_cli.render import (
    console,
    print_error,
    print_success,
    print_warning,
    print_info,
    print_section_header,
    render_table,
    render_field_list,
    render_enum_options,
    render_entity_detail,
    render_schema_status,
)


@click.group()
@click.version_option(version="0.1.0", prog_name="lawfirm-cli")
def cli():
    """Law Firm CLI - Entity Management Tool.
    
    A command-line tool for managing entities (persons and legal entities)
    in the law firm database.
    """
    pass


# =============================================================================
# Entity Commands
# =============================================================================

@cli.group()
def entity():
    """Manage entities (create, list, view, update, delete)."""
    pass


@entity.command("create")
def entity_create():
    """Create a new entity."""
    # Check if tables are available
    available, message = check_entities_available()
    if not available:
        print_error(message)
        return
    
    try:
        console.print()
        console.print("[bold cyan]═══ Create New Entity ═══[/bold cyan]")
        
        # Step 1: Select entity type
        entity_type = prompt_entity_type()
        
        # Step 2: Get entity fields
        entity_data = prompt_entity_fields(entity_type)
        
        # Step 3: Get identifiers
        identifiers = prompt_identifiers(entity_type)
        
        # Step 4: Get address (optional)
        address = prompt_address()
        
        # Step 5: Get contacts (optional)
        contacts = prompt_contacts()
        
        # Confirm and create
        console.print()
        console.print("[bold]Summary:[/bold]")
        console.print(f"  Type: {entity_type}")
        console.print(f"  Label: {entity_data.get('canonical_label')}")
        console.print(f"  Identifiers: {len(identifiers)}")
        console.print(f"  Address: {'Yes' if address else 'No'}")
        console.print(f"  Contacts: {len(contacts)}")
        console.print()
        
        if not click.confirm("Create this entity?", default=True):
            print_warning("Cancelled.")
            return
        
        entity_id = create_entity(
            entity_type=entity_type,
            entity_data=entity_data,
            identifiers=identifiers,
            address=address,
            contacts=contacts,
        )
        
        print_success(f"Entity created successfully!")
        console.print(f"  ID: [cyan]{entity_id}[/cyan]")
        
    except DuplicateIdentifierError as e:
        print_error(f"Duplicate identifier: {e}")
    except Exception as e:
        print_error(f"Failed to create entity: {e}")


@entity.command("list")
@click.option("--type", "-t", "entity_type", 
              type=click.Choice(["PHYSICAL_PERSON", "LEGAL_PERSON"]),
              help="Filter by entity type")
@click.option("--search", "-s", help="Search in entity labels")
@click.option("--limit", "-l", default=20, help="Maximum results")
def entity_list(entity_type, search, limit):
    """List entities."""
    available, message = check_entities_available()
    if not available:
        print_error(message)
        return
    
    try:
        entities = list_entities(
            entity_type=entity_type,
            search=search,
            limit=limit,
        )
        
        if not entities:
            print_info("No entities found.")
            return
        
        columns = [
            ("id", "ID"),
            ("entity_type", "Type"),
            ("canonical_label", "Label"),
            ("primary_identifier", "Primary ID"),
            ("status", "Status"),
        ]
        
        # Shorten IDs for display
        for e in entities:
            e["id"] = e["id"][:8] + "..."
            e["entity_type"] = "Person" if e["entity_type"] == "PHYSICAL_PERSON" else "Legal"
        
        render_table(columns, entities, title="Entities", show_row_numbers=True)
        console.print(f"\n[dim]Showing {len(entities)} entities[/dim]")
        
    except Exception as e:
        print_error(f"Failed to list entities: {e}")


@entity.command("view")
@click.argument("entity_id")
def entity_view(entity_id):
    """View entity details."""
    available, message = check_entities_available()
    if not available:
        print_error(message)
        return
    
    try:
        entity = get_entity(entity_id)
        
        render_entity_detail(
            entity=entity,
            identifiers=entity.get("identifiers", []),
            addresses=entity.get("addresses", []),
            contacts=entity.get("contacts", []),
        )
        
    except EntityNotFoundError:
        print_error(f"Entity not found: {entity_id}")
    except Exception as e:
        print_error(f"Failed to view entity: {e}")


@entity.command("update")
@click.argument("entity_id")
def entity_update(entity_id):
    """Update an entity (interactive menu)."""
    available, message = check_entities_available()
    if not available:
        print_error(message)
        return
    
    try:
        # Get existing entity
        existing = get_entity(entity_id)
        
        while True:
            console.print()
            console.print(f"[bold cyan]═══ Update Entity: {existing['canonical_label']} ═══[/bold cyan]")
            console.print()
            console.print("[bold]What would you like to update?[/bold]")
            console.print()
            console.print("  [cyan]1.[/cyan] Core fields (name, status, notes)")
            console.print("  [cyan]2.[/cyan] Person/Company details")
            console.print("  [cyan]3.[/cyan] Identifiers (PESEL, NIP, KRS, etc.)")
            console.print("  [cyan]4.[/cyan] Addresses")
            console.print("  [cyan]5.[/cyan] Contacts (email, phone, etc.)")
            console.print("  [cyan]0.[/cyan] Done - exit")
            console.print()
            
            choice = console.input("[bold]Select option (0-5):[/bold] ").strip()
            
            if choice == "0":
                print_info("Update complete.")
                break
            elif choice == "1":
                _update_core_fields(entity_id, existing)
                existing = get_entity(entity_id)  # Refresh
            elif choice == "2":
                _update_type_specific_fields(entity_id, existing)
                existing = get_entity(entity_id)  # Refresh
            elif choice == "3":
                _manage_identifiers(entity_id, existing)
                existing = get_entity(entity_id)  # Refresh
            elif choice == "4":
                _manage_addresses(entity_id, existing)
                existing = get_entity(entity_id)  # Refresh
            elif choice == "5":
                _manage_contacts(entity_id, existing)
                existing = get_entity(entity_id)  # Refresh
            else:
                print_warning("Invalid option. Please enter 0-5.")
        
    except EntityNotFoundError:
        print_error(f"Entity not found: {entity_id}")
    except Exception as e:
        print_error(f"Failed to update entity: {e}")


def _update_core_fields(entity_id: str, existing: dict):
    """Update core entity fields."""
    from lawfirm_cli.prompts import prompt_field
    
    console.print()
    console.print("[bold magenta]── Update Core Fields ──[/bold magenta]")
    console.print("[dim]Press Enter to keep current value.[/dim]")
    
    data = {}
    data["canonical_label"] = prompt_field("entity.canonical_label", existing.get("canonical_label"))
    data["status"] = prompt_field("entity.status", existing.get("status"))
    data["notes"] = prompt_field("entity.notes", existing.get("notes"))
    
    # Filter out None values (unchanged)
    data = {k: v for k, v in data.items() if v is not None}
    
    if data:
        update_entity(entity_id, data)
        print_success("Core fields updated!")
    else:
        print_info("No changes made.")


def _update_type_specific_fields(entity_id: str, existing: dict):
    """Update type-specific fields."""
    from lawfirm_cli.prompts import prompt_field
    
    entity_type = existing["entity_type"]
    
    console.print()
    console.print("[bold magenta]── Update Details ──[/bold magenta]")
    console.print("[dim]Press Enter to keep current value.[/dim]")
    
    data = {}
    
    if entity_type == "PHYSICAL_PERSON":
        data["first_name"] = prompt_field("person.first_name", existing.get("first_name"))
        data["middle_names"] = prompt_field("person.middle_names", existing.get("middle_names"))
        data["last_name"] = prompt_field("person.last_name", existing.get("last_name"))
        data["date_of_birth"] = prompt_field("person.date_of_birth", existing.get("date_of_birth"))
        data["citizenship_country"] = prompt_field("person.citizenship_country", existing.get("citizenship_country"))
        is_deceased = prompt_field("person.is_deceased", str(existing.get("is_deceased", False)).lower())
        if is_deceased is not None:
            data["is_deceased"] = is_deceased == "true"
    else:
        data["registered_name"] = prompt_field("legal.registered_name", existing.get("registered_name"))
        data["short_name"] = prompt_field("legal.short_name", existing.get("short_name"))
        data["legal_kind"] = prompt_field("legal.legal_kind", existing.get("legal_kind"))
        data["legal_nature"] = prompt_field("legal.legal_nature", existing.get("legal_nature"))
        data["legal_form_suffix"] = prompt_field("legal.legal_form_suffix", existing.get("legal_form_suffix"))
        data["country"] = prompt_field("legal.country", existing.get("country"))
    
    # Filter out None values
    data = {k: v for k, v in data.items() if v is not None}
    
    if data:
        update_entity(entity_id, data)
        print_success("Details updated!")
    else:
        print_info("No changes made.")


def _manage_identifiers(entity_id: str, existing: dict):
    """Manage entity identifiers (add/edit/delete)."""
    from lawfirm_cli.prompts import prompt_field
    from rich.prompt import Prompt
    
    identifiers = existing.get("identifiers", [])
    
    while True:
        console.print()
        console.print("[bold magenta]── Manage Identifiers ──[/bold magenta]")
        console.print()
        
        if identifiers:
            console.print("[bold]Current identifiers:[/bold]")
            for i, ident in enumerate(identifiers, 1):
                console.print(f"  [cyan]{i}.[/cyan] {ident['identifier_type']}: {ident['identifier_value']}")
        else:
            console.print("[dim]No identifiers.[/dim]")
        
        console.print()
        console.print("  [cyan]A.[/cyan] Add new identifier")
        if identifiers:
            console.print("  [cyan]E.[/cyan] Edit identifier")
            console.print("  [cyan]D.[/cyan] Delete identifier")
        console.print("  [cyan]0.[/cyan] Back to main menu")
        console.print()
        
        choice = console.input("[bold]Select option:[/bold] ").strip().upper()
        
        if choice == "0":
            break
        elif choice == "A":
            _add_identifier_prompt(entity_id, existing["entity_type"])
            identifiers = get_entity(entity_id).get("identifiers", [])
        elif choice == "E" and identifiers:
            _edit_identifier_prompt(identifiers)
            identifiers = get_entity(entity_id).get("identifiers", [])
        elif choice == "D" and identifiers:
            _delete_identifier_prompt(identifiers)
            identifiers = get_entity(entity_id).get("identifiers", [])
        else:
            print_warning("Invalid option.")


def _add_identifier_prompt(entity_id: str, entity_type: str):
    """Prompt to add a new identifier."""
    from lawfirm_cli.prompts import prompt_field
    from rich.prompt import Prompt
    
    console.print()
    if entity_type == "PHYSICAL_PERSON":
        id_types = ["PESEL", "NIP", "REGON", "OTHER"]
    else:
        id_types = ["KRS", "NIP", "REGON", "RFR", "OTHER"]
    
    console.print("[bold]Select identifier type:[/bold]")
    for i, t in enumerate(id_types, 1):
        console.print(f"  {i}. {t}")
    
    type_choice = Prompt.ask("Enter number")
    try:
        id_type = id_types[int(type_choice) - 1]
    except (ValueError, IndexError):
        print_warning("Invalid selection.")
        return
    
    value = prompt_field(f"id.{id_type}", required=True)
    if not value:
        print_warning("Cancelled.")
        return
    
    registry_name = None
    if id_type == "OTHER":
        registry_name = prompt_field("id.OTHER_REGISTRY_NAME")
    
    try:
        add_identifier(entity_id, id_type, value, registry_name)
        print_success(f"Added {id_type}: {value}")
    except DuplicateIdentifierError:
        print_error(f"This {id_type} already exists in the system.")


def _edit_identifier_prompt(identifiers: list):
    """Prompt to edit an identifier."""
    from lawfirm_cli.prompts import prompt_field
    from rich.prompt import Prompt
    
    console.print()
    num = Prompt.ask("Enter identifier number to edit")
    try:
        idx = int(num) - 1
        ident = identifiers[idx]
    except (ValueError, IndexError):
        print_warning("Invalid selection.")
        return
    
    console.print(f"\nEditing {ident['identifier_type']}: {ident['identifier_value']}")
    
    new_value = prompt_field(f"id.{ident['identifier_type']}", ident['identifier_value'])
    if new_value and new_value != ident['identifier_value']:
        update_identifier(ident['id'], new_value, ident.get('registry_name'))
        print_success(f"Updated to: {new_value}")
    else:
        print_info("No changes made.")


def _delete_identifier_prompt(identifiers: list):
    """Prompt to delete an identifier."""
    from rich.prompt import Prompt, Confirm
    
    console.print()
    num = Prompt.ask("Enter identifier number to delete")
    try:
        idx = int(num) - 1
        ident = identifiers[idx]
    except (ValueError, IndexError):
        print_warning("Invalid selection.")
        return
    
    if Confirm.ask(f"Delete {ident['identifier_type']}: {ident['identifier_value']}?", default=False):
        remove_identifier(ident['id'])
        print_success("Identifier deleted.")
    else:
        print_info("Cancelled.")


def _manage_addresses(entity_id: str, existing: dict):
    """Manage entity addresses (add/edit/delete)."""
    addresses = existing.get("addresses", [])
    
    while True:
        console.print()
        console.print("[bold magenta]── Manage Addresses ──[/bold magenta]")
        console.print()
        
        if addresses:
            console.print("[bold]Current addresses:[/bold]")
            for i, addr in enumerate(addresses, 1):
                addr_str = f"{addr.get('street', '')} {addr.get('building_no', '')}".strip()
                addr_str += f", {addr.get('postal_code', '')} {addr.get('city', '')}".strip(", ")
                console.print(f"  [cyan]{i}.[/cyan] [{addr.get('address_type', 'MAIN')}] {addr_str}")
        else:
            console.print("[dim]No addresses.[/dim]")
        
        console.print()
        console.print("  [cyan]A.[/cyan] Add new address")
        if addresses:
            console.print("  [cyan]E.[/cyan] Edit address")
            console.print("  [cyan]D.[/cyan] Delete address")
        console.print("  [cyan]0.[/cyan] Back to main menu")
        console.print()
        
        choice = console.input("[bold]Select option:[/bold] ").strip().upper()
        
        if choice == "0":
            break
        elif choice == "A":
            _add_address_prompt(entity_id)
            addresses = get_entity(entity_id).get("addresses", [])
        elif choice == "E" and addresses:
            _edit_address_prompt(addresses)
            addresses = get_entity(entity_id).get("addresses", [])
        elif choice == "D" and addresses:
            _delete_address_prompt(addresses)
            addresses = get_entity(entity_id).get("addresses", [])
        else:
            print_warning("Invalid option.")


def _add_address_prompt(entity_id: str):
    """Prompt to add a new address."""
    from lawfirm_cli.prompts import prompt_field
    
    console.print()
    console.print("[bold]Add New Address[/bold]")
    
    addr = {}
    addr["address_type"] = prompt_field("addr.address_type") or "MAIN"
    addr["country"] = prompt_field("addr.country") or "PL"
    addr["city"] = prompt_field("addr.city", required=True)
    if not addr["city"]:
        print_warning("City is required. Cancelled.")
        return
    addr["postal_code"] = prompt_field("addr.postal_code")
    addr["street"] = prompt_field("addr.street")
    addr["building_no"] = prompt_field("addr.building_no")
    addr["unit_no"] = prompt_field("addr.unit_no")
    
    add_address(entity_id, addr)
    print_success("Address added!")


def _edit_address_prompt(addresses: list):
    """Prompt to edit an address."""
    from lawfirm_cli.prompts import prompt_field
    from rich.prompt import Prompt
    
    console.print()
    num = Prompt.ask("Enter address number to edit")
    try:
        idx = int(num) - 1
        addr = addresses[idx]
    except (ValueError, IndexError):
        print_warning("Invalid selection.")
        return
    
    console.print(f"\n[bold]Editing address (press Enter to keep current value)[/bold]")
    
    data = {}
    data["address_type"] = prompt_field("addr.address_type", addr.get("address_type"))
    data["country"] = prompt_field("addr.country", addr.get("country"))
    data["city"] = prompt_field("addr.city", addr.get("city"))
    data["postal_code"] = prompt_field("addr.postal_code", addr.get("postal_code"))
    data["street"] = prompt_field("addr.street", addr.get("street"))
    data["building_no"] = prompt_field("addr.building_no", addr.get("building_no"))
    data["unit_no"] = prompt_field("addr.unit_no", addr.get("unit_no"))
    
    # Filter out None values
    data = {k: v for k, v in data.items() if v is not None}
    
    if data:
        update_address(addr['id'], data)
        print_success("Address updated!")
    else:
        print_info("No changes made.")


def _delete_address_prompt(addresses: list):
    """Prompt to delete an address."""
    from rich.prompt import Prompt, Confirm
    
    console.print()
    num = Prompt.ask("Enter address number to delete")
    try:
        idx = int(num) - 1
        addr = addresses[idx]
    except (ValueError, IndexError):
        print_warning("Invalid selection.")
        return
    
    addr_str = f"{addr.get('city', '')} {addr.get('street', '')}".strip()
    if Confirm.ask(f"Delete address: {addr_str}?", default=False):
        remove_address(addr['id'])
        print_success("Address deleted.")
    else:
        print_info("Cancelled.")


def _manage_contacts(entity_id: str, existing: dict):
    """Manage entity contacts (add/edit/delete)."""
    contacts = existing.get("contacts", [])
    
    while True:
        console.print()
        console.print("[bold magenta]── Manage Contacts ──[/bold magenta]")
        console.print()
        
        if contacts:
            console.print("[bold]Current contacts:[/bold]")
            for i, contact in enumerate(contacts, 1):
                console.print(f"  [cyan]{i}.[/cyan] {contact['contact_type']}: {contact['contact_value']}")
        else:
            console.print("[dim]No contacts.[/dim]")
        
        console.print()
        console.print("  [cyan]A.[/cyan] Add new contact")
        if contacts:
            console.print("  [cyan]E.[/cyan] Edit contact")
            console.print("  [cyan]D.[/cyan] Delete contact")
        console.print("  [cyan]0.[/cyan] Back to main menu")
        console.print()
        
        choice = console.input("[bold]Select option:[/bold] ").strip().upper()
        
        if choice == "0":
            break
        elif choice == "A":
            _add_contact_prompt(entity_id)
            contacts = get_entity(entity_id).get("contacts", [])
        elif choice == "E" and contacts:
            _edit_contact_prompt(contacts)
            contacts = get_entity(entity_id).get("contacts", [])
        elif choice == "D" and contacts:
            _delete_contact_prompt(contacts)
            contacts = get_entity(entity_id).get("contacts", [])
        else:
            print_warning("Invalid option.")


def _add_contact_prompt(entity_id: str):
    """Prompt to add a new contact."""
    from lawfirm_cli.prompts import prompt_field
    from rich.prompt import Prompt
    
    console.print()
    contact_types = ["EMAIL", "PHONE", "WEBSITE", "EPUAP", "OTHER"]
    
    console.print("[bold]Select contact type:[/bold]")
    for i, t in enumerate(contact_types, 1):
        console.print(f"  {i}. {t}")
    
    type_choice = Prompt.ask("Enter number")
    try:
        c_type = contact_types[int(type_choice) - 1]
    except (ValueError, IndexError):
        print_warning("Invalid selection.")
        return
    
    value = prompt_field(f"contact.{c_type}", required=True)
    if not value:
        print_warning("Cancelled.")
        return
    
    add_contact(entity_id, c_type, value)
    print_success(f"Added {c_type}: {value}")


def _edit_contact_prompt(contacts: list):
    """Prompt to edit a contact."""
    from lawfirm_cli.prompts import prompt_field
    from rich.prompt import Prompt
    
    console.print()
    num = Prompt.ask("Enter contact number to edit")
    try:
        idx = int(num) - 1
        contact = contacts[idx]
    except (ValueError, IndexError):
        print_warning("Invalid selection.")
        return
    
    console.print(f"\nEditing {contact['contact_type']}: {contact['contact_value']}")
    
    new_value = prompt_field(f"contact.{contact['contact_type']}", contact['contact_value'])
    if new_value and new_value != contact['contact_value']:
        update_contact(contact['id'], new_value)
        print_success(f"Updated to: {new_value}")
    else:
        print_info("No changes made.")


def _delete_contact_prompt(contacts: list):
    """Prompt to delete a contact."""
    from rich.prompt import Prompt, Confirm
    
    console.print()
    num = Prompt.ask("Enter contact number to delete")
    try:
        idx = int(num) - 1
        contact = contacts[idx]
    except (ValueError, IndexError):
        print_warning("Invalid selection.")
        return
    
    if Confirm.ask(f"Delete {contact['contact_type']}: {contact['contact_value']}?", default=False):
        remove_contact(contact['id'])
        print_success("Contact deleted.")
    else:
        print_info("Cancelled.")


@entity.command("delete")
@click.argument("entity_id")
def entity_delete(entity_id):
    """Delete an entity."""
    available, message = check_entities_available()
    if not available:
        print_error(message)
        return
    
    try:
        # Get entity info
        entity = get_entity(entity_id)
        related_counts = get_related_counts(entity_id)
        
        # Confirm deletion
        if not prompt_delete_confirmation(entity["canonical_label"], related_counts):
            print_warning("Cancelled.")
            return
        
        # Delete
        deleted = delete_entity(entity_id)
        
        print_success(f"Entity deleted: {entity['canonical_label']}")
        console.print(f"  Deleted {deleted['identifiers']} identifier(s)")
        console.print(f"  Deleted {deleted['addresses']} address(es)")
        console.print(f"  Deleted {deleted['contacts']} contact(s)")
        
    except EntityNotFoundError:
        print_error(f"Entity not found: {entity_id}")
    except Exception as e:
        print_error(f"Failed to delete entity: {e}")


# =============================================================================
# Metadata Commands
# =============================================================================

@cli.group()
def meta():
    """Explore database metadata (field definitions, enums)."""
    pass


@meta.command("fields")
@click.option("--group", "-g", help="Filter by display group")
@click.option("--prefix", "-p", help="Filter by field key prefix (e.g., 'entity.', 'id.')")
def meta_fields(group, prefix):
    """List field metadata definitions."""
    try:
        fields = load_all_field_metadata()
        
        if not fields:
            print_warning("No field metadata found. Run ui_metadata.sql first.")
            return
        
        field_list = list(fields.values())
        
        if group:
            field_list = [f for f in field_list if f.display_group == group]
        if prefix:
            field_list = [f for f in field_list if f.field_key.startswith(prefix)]
        
        field_list = sorted(field_list, key=lambda f: (f.display_group, f.display_order))
        
        if not field_list:
            print_info("No fields match the filter criteria.")
            return
        
        render_field_list(field_list, title="Field Metadata")
        
        # Show available groups
        groups = get_all_display_groups()
        console.print()
        console.print("[dim]Available groups: " + ", ".join(groups) + "[/dim]")
        
    except Exception as e:
        print_error(f"Failed to load field metadata: {e}")


@meta.command("enums")
@click.argument("enum_key", required=False)
def meta_enums(enum_key):
    """List enum values for a key, or list all enum keys."""
    try:
        if enum_key:
            options = get_enum_options(enum_key)
            if not options:
                print_warning(f"No enum options found for: {enum_key}")
                return
            render_enum_options(options, enum_key)
        else:
            # List all enum keys
            keys = get_all_enum_keys()
            if not keys:
                print_warning("No enum metadata found.")
                return
            
            console.print()
            console.print("[bold]Available Enum Keys:[/bold]")
            for key in keys:
                options = get_enum_options(key)
                console.print(f"  • [cyan]{key}[/cyan] ({len(options)} options)")
            console.print()
            console.print("[dim]Run: lawfirm-cli meta enums <key> to see options[/dim]")
            
    except Exception as e:
        print_error(f"Failed to load enum metadata: {e}")


@meta.command("field")
@click.argument("field_key")
def meta_field_detail(field_key):
    """Show detailed metadata for a specific field."""
    try:
        field = get_field_metadata(field_key)
        
        if not field:
            print_warning(f"Field not found: {field_key}")
            return
        
        console.print()
        console.print(f"[bold cyan]Field: {field.field_key}[/bold cyan]")
        console.print()
        console.print(f"  [bold]Label (PL):[/bold]     {field.label_pl}")
        console.print(f"  [bold]Tooltip:[/bold]       {field.tooltip_pl or '—'}")
        console.print(f"  [bold]Placeholder:[/bold]   {field.placeholder or '—'}")
        console.print(f"  [bold]Example:[/bold]       {field.example_value or '—'}")
        console.print(f"  [bold]Input Type:[/bold]    {field.input_type}")
        console.print(f"  [bold]Privacy:[/bold]       {field.privacy_level}")
        console.print(f"  [bold]Source Hint:[/bold]   {field.source_hint or '—'}")
        console.print(f"  [bold]Validation:[/bold]    {field.validation_hint or '—'}")
        console.print(f"  [bold]Display Group:[/bold] {field.display_group}")
        console.print(f"  [bold]Display Order:[/bold] {field.display_order}")
        console.print(f"  [bold]Editable:[/bold]      {'Yes' if field.is_user_editable else 'No'}")
        
        if field.validation_rule:
            console.print(f"  [bold]Validation Rule:[/bold]")
            for k, v in field.validation_rule.items():
                console.print(f"    {k}: {v}")
        
    except Exception as e:
        print_error(f"Failed to get field metadata: {e}")


# =============================================================================
# Status Command
# =============================================================================

@cli.command("status")
def status():
    """Show database schema status."""
    try:
        schema_status = get_schema_status()
        render_schema_status(schema_status)
    except Exception as e:
        print_error(f"Failed to check schema status: {e}")


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
