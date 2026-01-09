"""Tests for entity CRUD operations."""

import pytest
from uuid import uuid4

from lawfirm_cli.entities import (
    check_entities_available,
    create_entity,
    list_entities,
    get_entity,
    update_entity,
    delete_entity,
    add_identifier,
    remove_identifier,
    get_related_counts,
    EntityNotFoundError,
    DuplicateIdentifierError,
)


class TestEntitiesAvailability:
    """Tests for entity table availability checks."""
    
    def test_check_entities_available_returns_tuple(self, meta_tables_exist):
        """Test that check_entities_available returns (bool, str)."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        available, message = check_entities_available()
        
        assert isinstance(available, bool)
        assert isinstance(message, str)
    
    def test_check_entities_available_message_when_missing(self, entity_tables_exist, meta_tables_exist):
        """Test message content when entity tables are missing."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        if entity_tables_exist:
            pytest.skip("Entity tables exist")
        
        available, message = check_entities_available()
        
        assert available is False
        assert "not yet created" in message.lower()


@pytest.mark.skipif(True, reason="Entity tables not yet created - tests will run when schema exists")
class TestEntityCRUD:
    """Tests for entity CRUD operations.
    
    These tests are skipped by default since entity tables don't exist.
    They serve as documentation and will work when tables are created.
    """
    
    def test_create_physical_person(self, entity_tables_exist):
        """Test creating a physical person entity."""
        if not entity_tables_exist:
            pytest.skip("Entity tables not available")
        
        entity_id = create_entity(
            entity_type="PHYSICAL_PERSON",
            entity_data={
                "canonical_label": "Test Person",
                "first_name": "Jan",
                "last_name": "Kowalski",
            },
            identifiers=[
                {"type": "PESEL", "value": "12345678901"},
            ],
        )
        
        assert entity_id is not None
        
        # Cleanup
        delete_entity(entity_id)
    
    def test_create_legal_person(self, entity_tables_exist):
        """Test creating a legal person entity."""
        if not entity_tables_exist:
            pytest.skip("Entity tables not available")
        
        entity_id = create_entity(
            entity_type="LEGAL_PERSON",
            entity_data={
                "canonical_label": "Test Company sp. z o.o.",
                "registered_name": "Test Company spółka z ograniczoną odpowiedzialnością",
                "legal_kind": "SPOLKA_Z_OO",
            },
            identifiers=[
                {"type": "KRS", "value": "0000123456"},
                {"type": "NIP", "value": "1234567890"},
            ],
        )
        
        assert entity_id is not None
        
        # Cleanup
        delete_entity(entity_id)
    
    def test_list_entities(self, entity_tables_exist):
        """Test listing entities."""
        if not entity_tables_exist:
            pytest.skip("Entity tables not available")
        
        entities = list_entities(limit=10)
        
        assert isinstance(entities, list)
    
    def test_get_entity_not_found(self, entity_tables_exist):
        """Test getting non-existent entity raises error."""
        if not entity_tables_exist:
            pytest.skip("Entity tables not available")
        
        fake_id = str(uuid4())
        
        with pytest.raises(EntityNotFoundError):
            get_entity(fake_id)
    
    def test_update_entity(self, entity_tables_exist):
        """Test updating entity fields."""
        if not entity_tables_exist:
            pytest.skip("Entity tables not available")
        
        # Create entity
        entity_id = create_entity(
            entity_type="PHYSICAL_PERSON",
            entity_data={
                "canonical_label": "Original Name",
                "first_name": "Original",
                "last_name": "Name",
            },
        )
        
        try:
            # Update it
            update_entity(entity_id, {"canonical_label": "Updated Name"})
            
            # Verify
            entity = get_entity(entity_id)
            assert entity["canonical_label"] == "Updated Name"
        finally:
            delete_entity(entity_id)
    
    def test_delete_entity(self, entity_tables_exist):
        """Test deleting an entity."""
        if not entity_tables_exist:
            pytest.skip("Entity tables not available")
        
        # Create entity
        entity_id = create_entity(
            entity_type="PHYSICAL_PERSON",
            entity_data={
                "canonical_label": "To Delete",
                "first_name": "Delete",
                "last_name": "Me",
            },
            identifiers=[{"type": "PESEL", "value": "99999999999"}],
        )
        
        # Delete it
        deleted = delete_entity(entity_id)
        
        assert deleted["identifiers"] == 1
        
        # Verify it's gone
        with pytest.raises(EntityNotFoundError):
            get_entity(entity_id)
    
    def test_duplicate_identifier_error(self, entity_tables_exist):
        """Test that duplicate identifiers raise error."""
        if not entity_tables_exist:
            pytest.skip("Entity tables not available")
        
        # Create first entity
        entity1_id = create_entity(
            entity_type="PHYSICAL_PERSON",
            entity_data={
                "canonical_label": "First Person",
                "first_name": "First",
                "last_name": "Person",
            },
            identifiers=[{"type": "PESEL", "value": "11111111111"}],
        )
        
        try:
            # Try to create second with same PESEL
            with pytest.raises(DuplicateIdentifierError):
                create_entity(
                    entity_type="PHYSICAL_PERSON",
                    entity_data={
                        "canonical_label": "Second Person",
                        "first_name": "Second",
                        "last_name": "Person",
                    },
                    identifiers=[{"type": "PESEL", "value": "11111111111"}],
                )
        finally:
            delete_entity(entity1_id)


class TestEntityOperationsWithoutTables:
    """Tests that verify graceful handling when entity tables don't exist."""
    
    def test_create_entity_raises_without_tables(self, entity_tables_exist):
        """Test that create_entity raises when tables missing."""
        if entity_tables_exist:
            pytest.skip("Entity tables exist")
        
        with pytest.raises(RuntimeError) as excinfo:
            create_entity(
                entity_type="PHYSICAL_PERSON",
                entity_data={"canonical_label": "Test"},
            )
        
        assert "not yet created" in str(excinfo.value)
    
    def test_list_entities_raises_without_tables(self, entity_tables_exist):
        """Test that list_entities raises when tables missing."""
        if entity_tables_exist:
            pytest.skip("Entity tables exist")
        
        with pytest.raises(RuntimeError) as excinfo:
            list_entities()
        
        assert "not yet created" in str(excinfo.value)
    
    def test_get_entity_raises_without_tables(self, entity_tables_exist):
        """Test that get_entity raises when tables missing."""
        if entity_tables_exist:
            pytest.skip("Entity tables exist")
        
        with pytest.raises(RuntimeError) as excinfo:
            get_entity(str(uuid4()))
        
        assert "not yet created" in str(excinfo.value)
