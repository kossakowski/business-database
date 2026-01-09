"""Tests for metadata loading from meta tables."""

import pytest
from lawfirm_cli.metadata import (
    load_all_field_metadata,
    get_field_metadata,
    get_fields_by_group,
    get_fields_by_prefix,
    get_editable_fields,
    load_all_enum_options,
    get_enum_options,
    get_enum_label,
    get_all_display_groups,
    get_all_enum_keys,
    clear_cache,
    FieldMetadata,
    EnumOption,
)


class TestFieldMetadata:
    """Tests for field metadata loading."""
    
    def test_load_all_field_metadata(self, meta_tables_exist, clear_metadata_cache):
        """Test loading all field metadata from database."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        fields = load_all_field_metadata()
        
        assert fields is not None
        assert len(fields) > 0
        assert all(isinstance(f, FieldMetadata) for f in fields.values())
    
    def test_get_field_metadata_existing(self, meta_tables_exist, clear_metadata_cache):
        """Test getting metadata for a known field."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        field = get_field_metadata("entity.entity_type")
        
        assert field is not None
        assert field.field_key == "entity.entity_type"
        assert field.label_pl is not None
        assert field.input_type == "select"
    
    def test_get_field_metadata_nonexistent(self, meta_tables_exist, clear_metadata_cache):
        """Test getting metadata for a non-existent field."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        field = get_field_metadata("nonexistent.field")
        
        assert field is None
    
    def test_get_fields_by_group(self, meta_tables_exist, clear_metadata_cache):
        """Test filtering fields by display group."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        fields = get_fields_by_group("Identyfikatory")
        
        assert len(fields) > 0
        assert all(f.display_group == "Identyfikatory" for f in fields)
    
    def test_get_fields_by_prefix(self, meta_tables_exist, clear_metadata_cache):
        """Test filtering fields by key prefix."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        fields = get_fields_by_prefix("id.")
        
        assert len(fields) > 0
        assert all(f.field_key.startswith("id.") for f in fields)
    
    def test_get_editable_fields(self, meta_tables_exist, clear_metadata_cache):
        """Test getting only editable fields."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        editable = get_editable_fields("entity.")
        
        assert all(f.is_user_editable for f in editable)
    
    def test_field_metadata_validation_valid(self, meta_tables_exist, clear_metadata_cache):
        """Test field validation with valid input."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        field = get_field_metadata("id.PESEL")
        
        assert field is not None
        is_valid, error = field.validate("12345678901")  # 11 digits
        assert is_valid is True
        assert error is None
    
    def test_field_metadata_validation_invalid(self, meta_tables_exist, clear_metadata_cache):
        """Test field validation with invalid input."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        field = get_field_metadata("id.PESEL")
        
        assert field is not None
        is_valid, error = field.validate("123")  # Too short
        assert is_valid is False
        assert error is not None
    
    def test_get_all_display_groups(self, meta_tables_exist, clear_metadata_cache):
        """Test getting all display groups."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        groups = get_all_display_groups()
        
        assert len(groups) > 0
        assert "Podmiot" in groups or "Identyfikatory" in groups


class TestEnumMetadata:
    """Tests for enum metadata loading."""
    
    def test_load_all_enum_options(self, meta_tables_exist, clear_metadata_cache):
        """Test loading all enum options."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        enums = load_all_enum_options()
        
        assert enums is not None
        assert len(enums) > 0
        assert "entity_type" in enums
    
    def test_get_enum_options_entity_type(self, meta_tables_exist, clear_metadata_cache):
        """Test getting entity_type enum options."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        options = get_enum_options("entity_type")
        
        assert len(options) == 2
        values = [o.enum_value for o in options]
        assert "PHYSICAL_PERSON" in values
        assert "LEGAL_PERSON" in values
    
    def test_get_enum_options_legal_kind(self, meta_tables_exist, clear_metadata_cache):
        """Test getting legal_kind enum options."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        options = get_enum_options("legal_kind")
        
        assert len(options) > 0
        assert all(isinstance(o, EnumOption) for o in options)
        
        # Check a known value
        values = [o.enum_value for o in options]
        assert "SPOLKA_Z_OO" in values
    
    def test_get_enum_options_nonexistent(self, meta_tables_exist, clear_metadata_cache):
        """Test getting options for non-existent enum."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        options = get_enum_options("nonexistent_enum")
        
        assert options == []
    
    def test_get_enum_label(self, meta_tables_exist, clear_metadata_cache):
        """Test getting Polish label for enum value."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        label = get_enum_label("entity_type", "PHYSICAL_PERSON")
        
        assert label == "Osoba fizyczna"
    
    def test_get_enum_label_fallback(self, meta_tables_exist, clear_metadata_cache):
        """Test that unknown enum value returns the value itself."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        label = get_enum_label("entity_type", "UNKNOWN_VALUE")
        
        assert label == "UNKNOWN_VALUE"
    
    def test_get_all_enum_keys(self, meta_tables_exist, clear_metadata_cache):
        """Test getting all enum keys."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        keys = get_all_enum_keys()
        
        assert len(keys) > 0
        assert "entity_type" in keys
        assert "legal_kind" in keys


class TestMetadataCaching:
    """Tests for metadata caching behavior."""
    
    def test_cache_is_used(self, meta_tables_exist, clear_metadata_cache):
        """Test that subsequent calls use cached data."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        # First call loads from DB
        fields1 = load_all_field_metadata()
        
        # Second call should return same object (cached)
        fields2 = load_all_field_metadata()
        
        assert fields1 is fields2
    
    def test_force_reload(self, meta_tables_exist, clear_metadata_cache):
        """Test that force=True reloads data."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        fields1 = load_all_field_metadata()
        fields2 = load_all_field_metadata(force=True)
        
        # Should be different objects after forced reload
        assert fields1 is not fields2
    
    def test_clear_cache(self, meta_tables_exist):
        """Test clearing the cache."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        # Load data
        load_all_field_metadata()
        load_all_enum_options()
        
        # Clear cache
        clear_cache()
        
        # Next load should fetch fresh data
        fields = load_all_field_metadata()
        assert len(fields) > 0
