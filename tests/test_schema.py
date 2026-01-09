"""Tests for schema detection."""

import pytest
from lawfirm_cli.schema import (
    check_table_exists,
    check_tables,
    get_schema_status,
    require_meta_tables,
    require_entity_tables,
    META_TABLES,
    REQUIRED_ENTITY_TABLES,
    TableStatus,
    SchemaStatus,
)


class TestTableExistence:
    """Tests for table existence checks."""
    
    def test_check_meta_table_exists(self, meta_tables_exist):
        """Test checking for meta.ui_field_metadata table."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        exists = check_table_exists("meta", "ui_field_metadata")
        assert exists is True
    
    def test_check_nonexistent_table(self):
        """Test checking for a table that doesn't exist."""
        exists = check_table_exists("public", "nonexistent_table_xyz123")
        assert exists is False
    
    def test_check_multiple_tables(self, meta_tables_exist):
        """Test checking multiple tables at once."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        tables = [
            ("meta", "ui_field_metadata"),
            ("meta", "ui_enum_metadata"),
            ("public", "nonexistent_table"),
        ]
        
        results = check_tables(tables)
        
        assert len(results) == 3
        assert all(isinstance(r, TableStatus) for r in results)
        assert results[0].exists is True
        assert results[1].exists is True
        assert results[2].exists is False


class TestSchemaStatus:
    """Tests for schema status reporting."""
    
    def test_get_schema_status(self, meta_tables_exist):
        """Test getting comprehensive schema status."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        status = get_schema_status()
        
        assert isinstance(status, SchemaStatus)
        assert len(status.meta_tables) == len(META_TABLES)
        assert len(status.entity_tables) == len(REQUIRED_ENTITY_TABLES)
    
    def test_schema_status_meta_ready(self, meta_tables_exist):
        """Test meta_ready property when meta tables exist."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        status = get_schema_status()
        
        assert status.meta_ready is True
    
    def test_schema_status_missing_tables_list(self, meta_tables_exist, entity_tables_exist):
        """Test missing_entity_tables property."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        status = get_schema_status()
        
        # Since entity tables likely don't exist, this should have entries
        if not entity_tables_exist:
            assert len(status.missing_entity_tables) > 0
        else:
            assert len(status.missing_entity_tables) == 0


class TestRequireStatements:
    """Tests for require_* functions."""
    
    def test_require_meta_tables_success(self, meta_tables_exist):
        """Test require_meta_tables when tables exist."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        # Should not raise
        status = require_meta_tables()
        assert status.meta_ready is True
    
    def test_require_entity_tables_raises_when_missing(self, entity_tables_exist):
        """Test require_entity_tables raises when tables missing."""
        if entity_tables_exist:
            pytest.skip("Entity tables already exist")
        
        with pytest.raises(RuntimeError) as excinfo:
            require_entity_tables()
        
        assert "not yet created" in str(excinfo.value)


class TestTableStatus:
    """Tests for TableStatus dataclass."""
    
    def test_table_status_full_name(self):
        """Test full_name property."""
        status = TableStatus(schema="meta", table="ui_field_metadata", exists=True)
        assert status.full_name == "meta.ui_field_metadata"
    
    def test_table_status_public_schema(self):
        """Test full_name with public schema."""
        status = TableStatus(schema="public", table="entities", exists=False)
        assert status.full_name == "public.entities"
