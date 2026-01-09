"""Schema detection and table existence checks."""

from dataclasses import dataclass
from typing import Dict, List, Tuple

from lawfirm_cli.db import execute_query


# Define required tables for entity CRUD operations
REQUIRED_ENTITY_TABLES: List[Tuple[str, str]] = [
    ("public", "entities"),
    ("public", "physical_persons"),
    ("public", "legal_persons"),
    ("public", "identifiers"),
    ("public", "addresses"),
    ("public", "contacts"),
]

# Meta tables (should always exist)
META_TABLES: List[Tuple[str, str]] = [
    ("meta", "ui_field_metadata"),
    ("meta", "ui_enum_metadata"),
]

# Optional tables (registry data)
OPTIONAL_TABLES: List[Tuple[str, str]] = [
    ("public", "registry_profiles_krs"),
    ("public", "registry_profiles_ceidg"),
    ("public", "registry_snapshots"),
    ("public", "affiliations"),
]


@dataclass
class TableStatus:
    """Status of a single table."""
    schema: str
    table: str
    exists: bool
    
    @property
    def full_name(self) -> str:
        """Return fully qualified table name."""
        return f"{self.schema}.{self.table}"


@dataclass
class SchemaStatus:
    """Overall schema status report."""
    meta_tables: List[TableStatus]
    entity_tables: List[TableStatus]
    optional_tables: List[TableStatus]
    
    @property
    def meta_ready(self) -> bool:
        """Check if all meta tables exist."""
        return all(t.exists for t in self.meta_tables)
    
    @property
    def entities_ready(self) -> bool:
        """Check if all required entity tables exist."""
        return all(t.exists for t in self.entity_tables)
    
    @property
    def missing_entity_tables(self) -> List[str]:
        """Get list of missing entity tables."""
        return [t.full_name for t in self.entity_tables if not t.exists]
    
    @property
    def existing_entity_tables(self) -> List[str]:
        """Get list of existing entity tables."""
        return [t.full_name for t in self.entity_tables if t.exists]


def check_table_exists(schema: str, table: str, test: bool = False) -> bool:
    """Check if a specific table exists.
    
    Args:
        schema: Schema name.
        table: Table name.
        test: If True, use test database.
        
    Returns:
        True if table exists, False otherwise.
    """
    query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = %s 
            AND table_name = %s
        )
    """
    result = execute_query(query, (schema, table), test=test)
    return result[0]["exists"] if result else False


def check_tables(
    tables: List[Tuple[str, str]], 
    test: bool = False
) -> List[TableStatus]:
    """Check existence of multiple tables.
    
    Args:
        tables: List of (schema, table) tuples.
        test: If True, use test database.
        
    Returns:
        List of TableStatus objects.
    """
    return [
        TableStatus(
            schema=schema,
            table=table,
            exists=check_table_exists(schema, table, test=test)
        )
        for schema, table in tables
    ]


def get_schema_status(test: bool = False) -> SchemaStatus:
    """Get comprehensive schema status report.
    
    Args:
        test: If True, use test database.
        
    Returns:
        SchemaStatus with status of all tables.
    """
    return SchemaStatus(
        meta_tables=check_tables(META_TABLES, test=test),
        entity_tables=check_tables(REQUIRED_ENTITY_TABLES, test=test),
        optional_tables=check_tables(OPTIONAL_TABLES, test=test),
    )


def require_entity_tables(test: bool = False) -> SchemaStatus:
    """Check if entity tables exist and raise if not.
    
    Args:
        test: If True, use test database.
        
    Returns:
        SchemaStatus if all entity tables exist.
        
    Raises:
        RuntimeError: If required entity tables are missing.
    """
    status = get_schema_status(test=test)
    
    if not status.entities_ready:
        missing = status.missing_entity_tables
        raise RuntimeError(
            f"Entity tables are not yet created in the database.\n"
            f"Missing tables: {', '.join(missing)}\n\n"
            f"Please run the schema migrations first."
        )
    
    return status


def require_meta_tables(test: bool = False) -> SchemaStatus:
    """Check if meta tables exist and raise if not.
    
    Args:
        test: If True, use test database.
        
    Returns:
        SchemaStatus if all meta tables exist.
        
    Raises:
        RuntimeError: If meta tables are missing.
    """
    status = get_schema_status(test=test)
    
    if not status.meta_ready:
        missing = [t.full_name for t in status.meta_tables if not t.exists]
        raise RuntimeError(
            f"Meta tables are missing from the database.\n"
            f"Missing tables: {', '.join(missing)}\n\n"
            f"Please run: psql -f ui_metadata.sql"
        )
    
    return status
