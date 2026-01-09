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
    """Update an entity."""
    available, message = check_entities_available()
    if not available:
        print_error(message)
        return
    
    try:
        # Get existing entity
        existing = get_entity(entity_id)
        entity_type = existing["entity_type"]
        
        console.print()
        console.print(f"[bold cyan]═══ Update Entity: {existing['canonical_label']} ═══[/bold cyan]")
        console.print("[dim]Press Enter to keep current value, or type a new value.[/dim]")
        
        # Prompt for updates
        entity_data = prompt_entity_fields(entity_type, existing_data=existing)
        
        # Confirm
        console.print()
        if not click.confirm("Save changes?", default=True):
            print_warning("Cancelled.")
            return
        
        update_entity(entity_id, entity_data)
        print_success("Entity updated successfully!")
        
    except EntityNotFoundError:
        print_error(f"Entity not found: {entity_id}")
    except Exception as e:
        print_error(f"Failed to update entity: {e}")


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
