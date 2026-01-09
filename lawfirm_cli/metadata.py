"""Metadata loading from meta.ui_field_metadata and meta.ui_enum_metadata."""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from lawfirm_cli.db import execute_query, execute_one


@dataclass
class FieldMetadata:
    """Metadata for a single field."""
    field_key: str
    label_pl: str
    tooltip_pl: Optional[str] = None
    placeholder: Optional[str] = None
    example_value: Optional[str] = None
    input_type: str = "text"
    privacy_level: str = "INTERNAL"
    source_hint: Optional[str] = None
    validation_hint: Optional[str] = None
    validation_rule: Optional[dict] = None
    display_group: str = "General"
    display_order: int = 1000
    is_user_editable: bool = True
    
    def validate(self, value: str) -> tuple[bool, Optional[str]]:
        """Validate a value against the field's validation rule.
        
        Args:
            value: Value to validate.
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        if not value:
            return True, None  # Empty values are allowed (optional fields)
        
        if self.validation_rule and "pattern" in self.validation_rule:
            pattern = self.validation_rule["pattern"]
            if not re.match(pattern, value):
                hint = self.validation_hint or f"Must match pattern: {pattern}"
                return False, hint
        
        return True, None


@dataclass
class EnumOption:
    """A single enum option with Polish label and tooltip."""
    enum_key: str
    enum_value: str
    label_pl: str
    tooltip_pl: Optional[str] = None
    suffix_default: Optional[str] = None
    is_suffix_applicable: Optional[bool] = None
    display_order: int = 1000


@dataclass
class MetadataCache:
    """Cache for field and enum metadata."""
    fields: Dict[str, FieldMetadata] = field(default_factory=dict)
    enums: Dict[str, List[EnumOption]] = field(default_factory=dict)
    _loaded: bool = False


# Global cache instance
_cache = MetadataCache()


def load_all_field_metadata(test: bool = False, force: bool = False) -> Dict[str, FieldMetadata]:
    """Load all field metadata from database.
    
    Args:
        test: If True, use test database.
        force: If True, reload even if cached.
        
    Returns:
        Dict mapping field_key to FieldMetadata.
    """
    global _cache
    
    if _cache.fields and not force:
        return _cache.fields
    
    query = """
        SELECT 
            field_key, label_pl, tooltip_pl, placeholder, example_value,
            input_type, privacy_level, source_hint, validation_hint,
            validation_rule, display_group, display_order, is_user_editable
        FROM meta.ui_field_metadata
        ORDER BY display_group, display_order
    """
    
    rows = execute_query(query, test=test)
    
    _cache.fields = {
        row["field_key"]: FieldMetadata(
            field_key=row["field_key"],
            label_pl=row["label_pl"],
            tooltip_pl=row["tooltip_pl"],
            placeholder=row["placeholder"],
            example_value=row["example_value"],
            input_type=row["input_type"],
            privacy_level=row["privacy_level"],
            source_hint=row["source_hint"],
            validation_hint=row["validation_hint"],
            validation_rule=row["validation_rule"],
            display_group=row["display_group"],
            display_order=row["display_order"],
            is_user_editable=row["is_user_editable"],
        )
        for row in rows
    }
    
    return _cache.fields


def get_field_metadata(field_key: str, test: bool = False) -> Optional[FieldMetadata]:
    """Get metadata for a specific field.
    
    Args:
        field_key: Field key (e.g., 'entity.entity_type', 'id.PESEL').
        test: If True, use test database.
        
    Returns:
        FieldMetadata or None if not found.
    """
    fields = load_all_field_metadata(test=test)
    return fields.get(field_key)


def get_fields_by_group(group: str, test: bool = False) -> List[FieldMetadata]:
    """Get all fields in a display group.
    
    Args:
        group: Display group name.
        test: If True, use test database.
        
    Returns:
        List of FieldMetadata sorted by display_order.
    """
    fields = load_all_field_metadata(test=test)
    return sorted(
        [f for f in fields.values() if f.display_group == group],
        key=lambda f: f.display_order
    )


def get_fields_by_prefix(prefix: str, test: bool = False) -> List[FieldMetadata]:
    """Get all fields matching a key prefix.
    
    Args:
        prefix: Field key prefix (e.g., 'entity.', 'id.', 'addr.').
        test: If True, use test database.
        
    Returns:
        List of FieldMetadata sorted by display_order.
    """
    fields = load_all_field_metadata(test=test)
    return sorted(
        [f for f in fields.values() if f.field_key.startswith(prefix)],
        key=lambda f: f.display_order
    )


def get_editable_fields(prefix: str, test: bool = False) -> List[FieldMetadata]:
    """Get editable fields matching a prefix.
    
    Args:
        prefix: Field key prefix.
        test: If True, use test database.
        
    Returns:
        List of editable FieldMetadata.
    """
    return [f for f in get_fields_by_prefix(prefix, test=test) if f.is_user_editable]


def load_all_enum_options(test: bool = False, force: bool = False) -> Dict[str, List[EnumOption]]:
    """Load all enum options from database.
    
    Args:
        test: If True, use test database.
        force: If True, reload even if cached.
        
    Returns:
        Dict mapping enum_key to list of EnumOption.
    """
    global _cache
    
    if _cache.enums and not force:
        return _cache.enums
    
    query = """
        SELECT 
            enum_key, enum_value, label_pl, tooltip_pl,
            suffix_default, is_suffix_applicable, display_order
        FROM meta.ui_enum_metadata
        ORDER BY enum_key, display_order
    """
    
    rows = execute_query(query, test=test)
    
    _cache.enums = {}
    for row in rows:
        key = row["enum_key"]
        option = EnumOption(
            enum_key=row["enum_key"],
            enum_value=row["enum_value"],
            label_pl=row["label_pl"],
            tooltip_pl=row["tooltip_pl"],
            suffix_default=row["suffix_default"],
            is_suffix_applicable=row["is_suffix_applicable"],
            display_order=row["display_order"],
        )
        if key not in _cache.enums:
            _cache.enums[key] = []
        _cache.enums[key].append(option)
    
    return _cache.enums


def get_enum_options(enum_key: str, test: bool = False) -> List[EnumOption]:
    """Get enum options for a specific key.
    
    Args:
        enum_key: Enum key (e.g., 'entity_type', 'legal_kind').
        test: If True, use test database.
        
    Returns:
        List of EnumOption sorted by display_order.
    """
    enums = load_all_enum_options(test=test)
    return enums.get(enum_key, [])


def get_enum_label(enum_key: str, enum_value: str, test: bool = False) -> str:
    """Get the Polish label for an enum value.
    
    Args:
        enum_key: Enum key.
        enum_value: Enum value.
        test: If True, use test database.
        
    Returns:
        Polish label or the value itself if not found.
    """
    options = get_enum_options(enum_key, test=test)
    for opt in options:
        if opt.enum_value == enum_value:
            return opt.label_pl
    return enum_value


def get_all_display_groups(test: bool = False) -> List[str]:
    """Get all unique display groups.
    
    Args:
        test: If True, use test database.
        
    Returns:
        List of display group names.
    """
    fields = load_all_field_metadata(test=test)
    groups = sorted(set(f.display_group for f in fields.values()))
    return groups


def get_all_enum_keys(test: bool = False) -> List[str]:
    """Get all unique enum keys.
    
    Args:
        test: If True, use test database.
        
    Returns:
        List of enum key names.
    """
    enums = load_all_enum_options(test=test)
    return sorted(enums.keys())


def clear_cache():
    """Clear the metadata cache."""
    global _cache
    _cache = MetadataCache()
