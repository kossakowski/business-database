"""Entity CRUD operations with transaction support."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from psycopg2 import IntegrityError
from psycopg2.extras import RealDictCursor

from lawfirm_cli.db import get_connection, transaction
from lawfirm_cli.schema import require_entity_tables, get_schema_status


@dataclass
class EntityNotFoundError(Exception):
    """Raised when an entity is not found."""
    entity_id: str
    
    def __str__(self):
        return f"Entity not found: {self.entity_id}"


@dataclass
class DuplicateIdentifierError(Exception):
    """Raised when a duplicate identifier is detected."""
    identifier_type: str
    identifier_value: str
    
    def __str__(self):
        return f"Duplicate {self.identifier_type}: {self.identifier_value}"


def check_entities_available(test: bool = False) -> Tuple[bool, str]:
    """Check if entity tables are available.
    
    Args:
        test: If True, use test database.
        
    Returns:
        Tuple of (available, message).
    """
    status = get_schema_status(test=test)
    
    if not status.meta_ready:
        return False, "Meta tables are missing. Run ui_metadata.sql first."
    
    if not status.entities_ready:
        missing = ", ".join(status.missing_entity_tables)
        return False, (
            f"Entity tables are not yet created.\n"
            f"Missing: {missing}\n\n"
            f"You can still explore metadata using:\n"
            f"  lawfirm-cli meta fields\n"
            f"  lawfirm-cli meta enums entity_type"
        )
    
    return True, "OK"


def create_entity(
    entity_type: str,
    entity_data: Dict[str, Any],
    identifiers: List[Dict[str, str]] = None,
    address: Optional[Dict[str, Any]] = None,
    contacts: List[Dict[str, str]] = None,
    test: bool = False,
) -> str:
    """Create a new entity with all related data.
    
    All operations are wrapped in a transaction - either everything
    succeeds or nothing is created.
    
    Args:
        entity_type: 'PHYSICAL_PERSON' or 'LEGAL_PERSON'.
        entity_data: Core entity and type-specific data.
        identifiers: List of {'type': ..., 'value': ...} dicts.
        address: Address data dict.
        contacts: List of {'type': ..., 'value': ...} dicts.
        test: If True, use test database.
        
    Returns:
        Created entity ID.
        
    Raises:
        DuplicateIdentifierError: If an identifier already exists.
        RuntimeError: If entity tables don't exist.
    """
    require_entity_tables(test=test)
    
    entity_id = str(uuid4())
    now = datetime.utcnow()
    
    with transaction(test=test) as conn:
        cursor = conn.cursor()
        
        try:
            # 1. Create base entity
            cursor.execute("""
                INSERT INTO entities (
                    id, entity_type, canonical_label, status, notes,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                entity_id,
                entity_type,
                entity_data.get("canonical_label"),
                entity_data.get("notes"),
                now,
                now,
            ))
            
            # 2. Create type-specific record
            if entity_type == "PHYSICAL_PERSON":
                cursor.execute("""
                    INSERT INTO physical_persons (
                        entity_id, first_name, middle_names, last_name,
                        date_of_birth, citizenship_country, is_deceased
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    entity_id,
                    entity_data.get("first_name"),
                    entity_data.get("middle_names"),
                    entity_data.get("last_name"),
                    entity_data.get("date_of_birth"),
                    entity_data.get("citizenship_country"),
                    entity_data.get("is_deceased", False),
                ))
            elif entity_type == "LEGAL_PERSON":
                cursor.execute("""
                    INSERT INTO legal_persons (
                        entity_id, registered_name, short_name, legal_kind,
                        legal_nature, legal_form_suffix, country
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    entity_id,
                    entity_data.get("registered_name"),
                    entity_data.get("short_name"),
                    entity_data.get("legal_kind"),
                    entity_data.get("legal_nature"),
                    entity_data.get("legal_form_suffix"),
                    entity_data.get("country", "PL"),
                ))
            
            # 3. Create identifiers
            if identifiers:
                for ident in identifiers:
                    cursor.execute("""
                        INSERT INTO identifiers (
                            id, entity_id, identifier_type, identifier_value,
                            registry_name, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        str(uuid4()),
                        entity_id,
                        ident["type"],
                        ident["value"],
                        ident.get("registry_name"),
                        now,
                    ))
            
            # 4. Create address
            if address:
                cursor.execute("""
                    INSERT INTO addresses (
                        id, entity_id, address_type, country, city,
                        postal_code, street, building_no, unit_no,
                        created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    str(uuid4()),
                    entity_id,
                    address.get("address_type", "MAIN"),
                    address.get("country", "PL"),
                    address.get("city"),
                    address.get("postal_code"),
                    address.get("street"),
                    address.get("building_no"),
                    address.get("unit_no"),
                    now,
                ))
            
            # 5. Create contacts
            if contacts:
                for contact in contacts:
                    cursor.execute("""
                        INSERT INTO contacts (
                            id, entity_id, contact_type, contact_value,
                            created_at
                        ) VALUES (%s, %s, %s, %s, %s)
                    """, (
                        str(uuid4()),
                        entity_id,
                        contact["type"],
                        contact["value"],
                        now,
                    ))
            
            cursor.close()
            return entity_id
            
        except IntegrityError as e:
            cursor.close()
            error_msg = str(e)
            if "identifiers" in error_msg and "unique" in error_msg.lower():
                # Extract identifier info from error if possible
                raise DuplicateIdentifierError("UNKNOWN", "value")
            raise


def list_entities(
    entity_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    test: bool = False,
) -> List[Dict[str, Any]]:
    """List entities with optional filtering.
    
    Args:
        entity_type: Filter by type ('PHYSICAL_PERSON' or 'LEGAL_PERSON').
        search: Search in canonical_label.
        limit: Maximum number of results.
        offset: Offset for pagination.
        test: If True, use test database.
        
    Returns:
        List of entity summary dicts.
    """
    require_entity_tables(test=test)
    
    query = """
        SELECT 
            e.id,
            e.entity_type,
            e.canonical_label,
            e.status,
            e.created_at,
            (
                SELECT identifier_value 
                FROM identifiers i 
                WHERE i.entity_id = e.id 
                ORDER BY 
                    CASE identifier_type
                        WHEN 'PESEL' THEN 1
                        WHEN 'KRS' THEN 2
                        WHEN 'NIP' THEN 3
                        ELSE 10
                    END
                LIMIT 1
            ) as primary_identifier
        FROM entities e
        WHERE 1=1
    """
    params = []
    
    if entity_type:
        query += " AND e.entity_type = %s"
        params.append(entity_type)
    
    if search:
        query += " AND e.canonical_label ILIKE %s"
        params.append(f"%{search}%")
    
    query += " ORDER BY e.created_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    with transaction(test=test) as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        return [dict(r) for r in results]


def get_entity(entity_id: str, test: bool = False) -> Dict[str, Any]:
    """Get full entity details.
    
    Args:
        entity_id: Entity ID.
        test: If True, use test database.
        
    Returns:
        Entity dict with all details.
        
    Raises:
        EntityNotFoundError: If entity doesn't exist.
    """
    require_entity_tables(test=test)
    
    with transaction(test=test) as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get base entity
        cursor.execute("""
            SELECT * FROM entities WHERE id = %s
        """, (entity_id,))
        entity = cursor.fetchone()
        
        if not entity:
            cursor.close()
            raise EntityNotFoundError(entity_id)
        
        entity = dict(entity)
        
        # Get type-specific data
        if entity["entity_type"] == "PHYSICAL_PERSON":
            cursor.execute("""
                SELECT * FROM physical_persons WHERE entity_id = %s
            """, (entity_id,))
            person = cursor.fetchone()
            if person:
                entity.update(dict(person))
        elif entity["entity_type"] == "LEGAL_PERSON":
            cursor.execute("""
                SELECT * FROM legal_persons WHERE entity_id = %s
            """, (entity_id,))
            legal = cursor.fetchone()
            if legal:
                entity.update(dict(legal))
        
        # Get identifiers
        cursor.execute("""
            SELECT * FROM identifiers WHERE entity_id = %s
            ORDER BY identifier_type
        """, (entity_id,))
        entity["identifiers"] = [dict(r) for r in cursor.fetchall()]
        
        # Get addresses
        cursor.execute("""
            SELECT * FROM addresses WHERE entity_id = %s
        """, (entity_id,))
        entity["addresses"] = [dict(r) for r in cursor.fetchall()]
        
        # Get contacts
        cursor.execute("""
            SELECT * FROM contacts WHERE entity_id = %s
            ORDER BY contact_type
        """, (entity_id,))
        entity["contacts"] = [dict(r) for r in cursor.fetchall()]
        
        cursor.close()
        return entity


def update_entity(
    entity_id: str,
    entity_data: Dict[str, Any],
    test: bool = False,
) -> None:
    """Update entity core fields.
    
    Args:
        entity_id: Entity ID.
        entity_data: Fields to update.
        test: If True, use test database.
        
    Raises:
        EntityNotFoundError: If entity doesn't exist.
    """
    require_entity_tables(test=test)
    
    # First get existing entity to know its type
    existing = get_entity(entity_id, test=test)
    entity_type = existing["entity_type"]
    
    with transaction(test=test) as conn:
        cursor = conn.cursor()
        
        # Update base entity
        updates = []
        params = []
        
        if "canonical_label" in entity_data:
            updates.append("canonical_label = %s")
            params.append(entity_data["canonical_label"])
        if "status" in entity_data:
            updates.append("notes = %s")
            params.append(entity_data["notes"])
        
        if updates:
            updates.append("updated_at = %s")
            params.append(datetime.utcnow())
            params.append(entity_id)
            
            cursor.execute(f"""
                UPDATE entities SET {', '.join(updates)} WHERE id = %s
            """, params)
        
        # Update type-specific table
        if entity_type == "PHYSICAL_PERSON":
            type_updates = []
            type_params = []
            
            for field in ["first_name", "middle_names", "last_name", 
                         "date_of_birth", "citizenship_country", "is_deceased"]:
                if field in entity_data:
                    type_updates.append(f"{field} = %s")
                    type_params.append(entity_data[field])
            
            if type_updates:
                type_params.append(entity_id)
                cursor.execute(f"""
                    UPDATE physical_persons SET {', '.join(type_updates)} 
                    WHERE entity_id = %s
                """, type_params)
                
        elif entity_type == "LEGAL_PERSON":
            type_updates = []
            type_params = []
            
            for field in ["registered_name", "short_name", "legal_kind",
                         "legal_nature", "legal_form_suffix", "country"]:
                if field in entity_data:
                    type_updates.append(f"{field} = %s")
                    type_params.append(entity_data[field])
            
            if type_updates:
                type_params.append(entity_id)
                cursor.execute(f"""
                    UPDATE legal_persons SET {', '.join(type_updates)} 
                    WHERE entity_id = %s
                """, type_params)
        
        cursor.close()


def add_identifier(
    entity_id: str,
    identifier_type: str,
    identifier_value: str,
    registry_name: Optional[str] = None,
    test: bool = False,
) -> str:
    """Add an identifier to an entity.
    
    Args:
        entity_id: Entity ID.
        identifier_type: Type (PESEL, NIP, KRS, etc.).
        identifier_value: The identifier value.
        registry_name: Optional registry name for OTHER type.
        test: If True, use test database.
        
    Returns:
        Created identifier ID.
        
    Raises:
        DuplicateIdentifierError: If identifier already exists.
    """
    require_entity_tables(test=test)
    
    identifier_id = str(uuid4())
    
    with transaction(test=test) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO identifiers (
                    id, entity_id, identifier_type, identifier_value,
                    registry_name, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                identifier_id,
                entity_id,
                identifier_type,
                identifier_value,
                registry_name,
                datetime.utcnow(),
            ))
            cursor.close()
            return identifier_id
        except IntegrityError:
            cursor.close()
            raise DuplicateIdentifierError(identifier_type, identifier_value)


def remove_identifier(identifier_id: str, test: bool = False) -> None:
    """Remove an identifier.
    
    Args:
        identifier_id: Identifier ID to remove.
        test: If True, use test database.
    """
    require_entity_tables(test=test)
    
    with transaction(test=test) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM identifiers WHERE id = %s", (identifier_id,))
        cursor.close()


def update_identifier(
    identifier_id: str,
    identifier_value: str,
    registry_name: Optional[str] = None,
    test: bool = False,
) -> None:
    """Update an identifier value.
    
    Args:
        identifier_id: Identifier ID.
        identifier_value: New value.
        registry_name: Optional new registry name.
        test: If True, use test database.
    """
    require_entity_tables(test=test)
    
    with transaction(test=test) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE identifiers 
            SET identifier_value = %s, registry_name = %s
            WHERE id = %s
        """, (identifier_value, registry_name, identifier_id))
        cursor.close()


# =============================================================================
# Address CRUD
# =============================================================================

def add_address(
    entity_id: str,
    address_data: Dict[str, Any],
    test: bool = False,
) -> str:
    """Add an address to an entity.
    
    Args:
        entity_id: Entity ID.
        address_data: Address fields.
        test: If True, use test database.
        
    Returns:
        Created address ID.
    """
    require_entity_tables(test=test)
    
    address_id = str(uuid4())
    now = datetime.utcnow()
    
    with transaction(test=test) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO addresses (
                id, entity_id, address_type, country, voivodeship,
                county, gmina, city, postal_code, post_office,
                street, building_no, unit_no, additional_line,
                freeform_note, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            address_id,
            entity_id,
            address_data.get("address_type", "MAIN"),
            address_data.get("country", "PL"),
            address_data.get("voivodeship"),
            address_data.get("county"),
            address_data.get("gmina"),
            address_data.get("city"),
            address_data.get("postal_code"),
            address_data.get("post_office"),
            address_data.get("street"),
            address_data.get("building_no"),
            address_data.get("unit_no"),
            address_data.get("additional_line"),
            address_data.get("freeform_note"),
            now,
            now,
        ))
        cursor.close()
        return address_id


def update_address(
    address_id: str,
    address_data: Dict[str, Any],
    test: bool = False,
) -> None:
    """Update an address.
    
    Args:
        address_id: Address ID.
        address_data: Fields to update.
        test: If True, use test database.
    """
    require_entity_tables(test=test)
    
    fields = [
        "address_type", "country", "voivodeship", "county", "gmina",
        "city", "postal_code", "post_office", "street", "building_no",
        "unit_no", "additional_line", "freeform_note"
    ]
    
    updates = []
    params = []
    
    for field in fields:
        if field in address_data:
            updates.append(f"{field} = %s")
            params.append(address_data[field])
    
    if updates:
        updates.append("updated_at = %s")
        params.append(datetime.utcnow())
        params.append(address_id)
        
        with transaction(test=test) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE addresses SET {', '.join(updates)} WHERE id = %s
            """, params)
            cursor.close()


def remove_address(address_id: str, test: bool = False) -> None:
    """Remove an address.
    
    Args:
        address_id: Address ID to remove.
        test: If True, use test database.
    """
    require_entity_tables(test=test)
    
    with transaction(test=test) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM addresses WHERE id = %s", (address_id,))
        cursor.close()


# =============================================================================
# Contact CRUD
# =============================================================================

def add_contact(
    entity_id: str,
    contact_type: str,
    contact_value: str,
    label: Optional[str] = None,
    test: bool = False,
) -> str:
    """Add a contact to an entity.
    
    Args:
        entity_id: Entity ID.
        contact_type: Type (EMAIL, PHONE, WEBSITE, etc.).
        contact_value: The contact value.
        label: Optional label.
        test: If True, use test database.
        
    Returns:
        Created contact ID.
    """
    require_entity_tables(test=test)
    
    contact_id = str(uuid4())
    
    with transaction(test=test) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO contacts (
                id, entity_id, contact_type, contact_value, label, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            contact_id,
            entity_id,
            contact_type,
            contact_value,
            label,
            datetime.utcnow(),
        ))
        cursor.close()
        return contact_id


def update_contact(
    contact_id: str,
    contact_value: Optional[str] = None,
    label: Optional[str] = None,
    test: bool = False,
) -> None:
    """Update a contact.
    
    Args:
        contact_id: Contact ID.
        contact_value: New value.
        label: New label.
        test: If True, use test database.
    """
    require_entity_tables(test=test)
    
    updates = []
    params = []
    
    if contact_value is not None:
        updates.append("contact_value = %s")
        params.append(contact_value)
    if label is not None:
        updates.append("label = %s")
        params.append(label)
    
    if updates:
        params.append(contact_id)
        with transaction(test=test) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE contacts SET {', '.join(updates)} WHERE id = %s
            """, params)
            cursor.close()


def remove_contact(contact_id: str, test: bool = False) -> None:
    """Remove a contact.
    
    Args:
        contact_id: Contact ID to remove.
        test: If True, use test database.
    """
    require_entity_tables(test=test)
    
    with transaction(test=test) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contacts WHERE id = %s", (contact_id,))
        cursor.close()


def delete_entity(entity_id: str, test: bool = False) -> Dict[str, int]:
    """Delete an entity and all related records.
    
    Args:
        entity_id: Entity ID.
        test: If True, use test database.
        
    Returns:
        Dict with counts of deleted records by type.
        
    Raises:
        EntityNotFoundError: If entity doesn't exist.
    """
    require_entity_tables(test=test)
    
    # First verify entity exists
    existing = get_entity(entity_id, test=test)
    entity_type = existing["entity_type"]
    
    deleted_counts = {
        "identifiers": 0,
        "addresses": 0,
        "contacts": 0,
    }
    
    with transaction(test=test) as conn:
        cursor = conn.cursor()
        
        # Delete identifiers
        cursor.execute("DELETE FROM identifiers WHERE entity_id = %s", (entity_id,))
        deleted_counts["identifiers"] = cursor.rowcount
        
        # Delete addresses
        cursor.execute("DELETE FROM addresses WHERE entity_id = %s", (entity_id,))
        deleted_counts["addresses"] = cursor.rowcount
        
        # Delete contacts
        cursor.execute("DELETE FROM contacts WHERE entity_id = %s", (entity_id,))
        deleted_counts["contacts"] = cursor.rowcount
        
        # Delete type-specific record
        if entity_type == "PHYSICAL_PERSON":
            cursor.execute("DELETE FROM physical_persons WHERE entity_id = %s", (entity_id,))
        elif entity_type == "LEGAL_PERSON":
            cursor.execute("DELETE FROM legal_persons WHERE entity_id = %s", (entity_id,))
        
        # Delete base entity
        cursor.execute("DELETE FROM entities WHERE id = %s", (entity_id,))
        
        cursor.close()
        return deleted_counts


def get_related_counts(entity_id: str, test: bool = False) -> Dict[str, int]:
    """Get counts of related records for an entity.
    
    Args:
        entity_id: Entity ID.
        test: If True, use test database.
        
    Returns:
        Dict with counts by record type.
    """
    require_entity_tables(test=test)
    
    with transaction(test=test) as conn:
        cursor = conn.cursor()
        
        counts = {}
        
        cursor.execute("SELECT COUNT(*) FROM identifiers WHERE entity_id = %s", (entity_id,))
        counts["identifiers"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM addresses WHERE entity_id = %s", (entity_id,))
        counts["addresses"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM contacts WHERE entity_id = %s", (entity_id,))
        counts["contacts"] = cursor.fetchone()[0]
        
        cursor.close()
        return counts
