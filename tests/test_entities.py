"""Tests for entity CRUD operations."""

import os
import pytest
from uuid import uuid4

import psycopg2

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


def _check_entity_tables_exist() -> bool:
    """Check if entity tables exist at module load time for skipif."""
    try:
        db_url = os.environ.get("DATABASE_URL_TEST") or os.environ.get("DATABASE_URL")
        if not db_url:
            return False

        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'entities'
            )
        """)
        result = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return result
    except Exception:
        return False


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


@pytest.mark.skipif(not _check_entity_tables_exist(), reason="Entity tables not yet created - run db/schema.sql first")
class TestEntityCRUD:
    """Tests for entity CRUD operations.

    These tests require entity tables to exist in the database.
    Run db/schema.sql to create the necessary tables.
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
    
    def test_create_physical_person_with_business_name(self, entity_tables_exist):
        """Test creating a physical person with business_name."""
        if not entity_tables_exist:
            pytest.skip("Entity tables not available")

        entity_id = create_entity(
            entity_type="PHYSICAL_PERSON",
            entity_data={
                "canonical_label": "Jan Kowalski Kancelaria Prawna",
                "first_name": "Jan",
                "last_name": "Kowalski",
                "business_name": "Jan Kowalski Kancelaria Prawna",
            },
        )

        try:
            entity = get_entity(entity_id)
            assert entity["business_name"] == "Jan Kowalski Kancelaria Prawna"
            assert entity["first_name"] == "Jan"
            assert entity["last_name"] == "Kowalski"
        finally:
            delete_entity(entity_id)

    def test_update_business_name(self, entity_tables_exist):
        """Test updating business_name on a physical person."""
        if not entity_tables_exist:
            pytest.skip("Entity tables not available")

        entity_id = create_entity(
            entity_type="PHYSICAL_PERSON",
            entity_data={
                "canonical_label": "Anna Nowak",
                "first_name": "Anna",
                "last_name": "Nowak",
            },
        )

        try:
            # Verify initially NULL
            entity = get_entity(entity_id)
            assert entity.get("business_name") is None

            # Update it
            update_entity(entity_id, {"business_name": "Anna Nowak Usługi Księgowe"})

            entity = get_entity(entity_id)
            assert entity["business_name"] == "Anna Nowak Usługi Księgowe"
        finally:
            delete_entity(entity_id)

    def test_search_by_business_name(self, entity_tables_exist):
        """Test that list_entities search finds entities by business_name."""
        if not entity_tables_exist:
            pytest.skip("Entity tables not available")

        entity_id = create_entity(
            entity_type="PHYSICAL_PERSON",
            entity_data={
                "canonical_label": "Piotr Wiśniewski Projektowanie",
                "first_name": "Piotr",
                "last_name": "Wiśniewski",
                "business_name": "Piotr Wiśniewski Projektowanie",
            },
        )

        try:
            results = list_entities(search="Projektowanie")
            found_ids = [r["id"] for r in results]
            assert entity_id in found_ids
        finally:
            delete_entity(entity_id)

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
