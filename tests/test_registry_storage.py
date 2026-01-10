"""Tests for registry snapshot storage and profile management."""

import json
import pytest
from datetime import datetime
from uuid import uuid4

from lawfirm_cli.registry.models import (
    RegistrySnapshot,
    NormalizedKRSProfile,
    NormalizedCEIDGProfile,
    NormalizedAddress,
)
from lawfirm_cli.registry.storage import (
    check_registry_tables_exist,
    create_registry_tables,
    insert_snapshot,
    get_snapshot,
    get_entity_snapshots,
    upsert_krs_profile,
    upsert_ceidg_profile,
    get_krs_profile,
    get_ceidg_profile,
)


@pytest.fixture(scope="module")
def registry_tables_setup(db_url):
    """Ensure registry tables exist for tests."""
    import psycopg2
    
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Create tables
    try:
        create_registry_tables(test=False)
    except Exception:
        pass  # May already exist
    
    cursor.close()
    conn.close()
    
    return True


@pytest.fixture
def sample_snapshot():
    """Create a sample registry snapshot."""
    return RegistrySnapshot(
        entity_id=None,  # Will be set in tests
        source_system="KRS",
        external_id="0000012345",
        fetched_at=datetime.utcnow(),
        payload_format="json",
        payload_raw='{"test": "data"}',
        payload_hash="abc123hash",
        fetched_by="test_user",
        purpose_ref="test_purpose",
    )


@pytest.fixture
def sample_krs_profile():
    """Create a sample KRS profile."""
    return NormalizedKRSProfile(
        krs="0000012345",
        nip="1234567890",
        regon="123456789",
        official_name="TEST COMPANY SP. Z O.O.",
        short_name="TEST CO",
        legal_form="SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
        registry_status="AKTYWNY",
        share_capital="50000.00 PLN",
        pkd_main="62.01.Z",
    )


@pytest.fixture
def sample_ceidg_profile():
    """Create a sample CEIDG profile."""
    return NormalizedCEIDGProfile(
        ceidg_id="ceidg-123",
        nip="9876543210",
        regon="987654321",
        first_name="JAN",
        last_name="TESTOWY",
        business_name="JAN TESTOWY USŁUGI",
        status="AKTYWNY",
        pkd_main="62.01.Z",
    )


class TestCheckRegistryTables:
    """Tests for checking registry table existence."""
    
    def test_returns_dict_with_all_tables(self, db_url):
        """Should return status for all registry tables."""
        result = check_registry_tables_exist(test=False)
        
        assert isinstance(result, dict)
        assert "registry_snapshots" in result
        assert "registry_profiles_krs" in result
        assert "registry_profiles_ceidg" in result
        assert "affiliations" in result
    
    def test_returns_boolean_values(self, db_url):
        """Should return boolean values for each table."""
        result = check_registry_tables_exist(test=False)
        
        for table, exists in result.items():
            assert isinstance(exists, bool)


class TestCreateRegistryTables:
    """Tests for creating registry tables."""
    
    def test_create_tables_is_idempotent(self, db_url):
        """Creating tables twice should not raise errors."""
        # First call
        result1 = create_registry_tables(test=False)
        
        # Second call - should not fail
        result2 = create_registry_tables(test=False)
        
        # Tables should exist
        tables_exist = check_registry_tables_exist(test=False)
        assert all(tables_exist.values())
    
    def test_tables_exist_after_creation(self, db_url):
        """All registry tables should exist after creation."""
        create_registry_tables(test=False)
        
        result = check_registry_tables_exist(test=False)
        
        assert result["registry_snapshots"] is True
        assert result["registry_profiles_krs"] is True
        assert result["registry_profiles_ceidg"] is True
        assert result["affiliations"] is True


class TestSnapshotStorage:
    """Tests for snapshot insert and retrieval."""
    
    @pytest.fixture
    def test_entity_id(self, db_url, entity_tables_exist):
        """Create a test entity and return its ID."""
        if not entity_tables_exist:
            pytest.skip("Entity tables do not exist")
        
        import psycopg2
        from uuid import uuid4
        
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        cursor = conn.cursor()
        
        entity_id = str(uuid4())
        
        cursor.execute("""
            INSERT INTO entities (id, entity_type, canonical_label, status, created_at, updated_at)
            VALUES (%s, 'LEGAL_PERSON', 'Test Company', 'ACTIVE', NOW(), NOW())
        """, (entity_id,))
        
        cursor.execute("""
            INSERT INTO legal_persons (entity_id, registered_name, country)
            VALUES (%s, 'Test Company Sp. z o.o.', 'PL')
        """, (entity_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        yield entity_id
        
        # Cleanup
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("DELETE FROM entities WHERE id = %s", (entity_id,))
        cursor.close()
        conn.close()
    
    def test_insert_snapshot_returns_id(self, registry_tables_setup, test_entity_id, sample_snapshot):
        """Inserting a snapshot should return a valid ID."""
        sample_snapshot.entity_id = test_entity_id
        
        snapshot_id = insert_snapshot(sample_snapshot, test=False)
        
        assert snapshot_id is not None
        assert len(snapshot_id) == 36  # UUID length
        
        # Cleanup
        import psycopg2
        import os
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("DELETE FROM registry_snapshots WHERE id = %s", (snapshot_id,))
        cursor.close()
        conn.close()
    
    def test_get_snapshot_retrieves_data(self, registry_tables_setup, test_entity_id, sample_snapshot):
        """Getting a snapshot should retrieve all data."""
        sample_snapshot.entity_id = test_entity_id
        
        snapshot_id = insert_snapshot(sample_snapshot, test=False)
        
        retrieved = get_snapshot(snapshot_id, test=False)
        
        assert retrieved is not None
        assert retrieved["id"] == snapshot_id
        assert retrieved["source_system"] == "KRS"
        assert retrieved["external_id"] == "0000012345"
        assert retrieved["payload_raw"] == '{"test": "data"}'
        assert retrieved["payload_hash"] == "abc123hash"
        
        # Cleanup
        import psycopg2
        import os
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("DELETE FROM registry_snapshots WHERE id = %s", (snapshot_id,))
        cursor.close()
        conn.close()
    
    def test_get_nonexistent_snapshot_returns_none(self, registry_tables_setup):
        """Getting a nonexistent snapshot should return None."""
        # Use a valid UUID format that doesn't exist
        result = get_snapshot("00000000-0000-0000-0000-000000000000", test=False)
        
        assert result is None
    
    def test_get_entity_snapshots_returns_list(self, registry_tables_setup, test_entity_id, sample_snapshot):
        """Getting entity snapshots should return a list."""
        sample_snapshot.entity_id = test_entity_id
        
        snapshot_id = insert_snapshot(sample_snapshot, test=False)
        
        snapshots = get_entity_snapshots(test_entity_id, test=False)
        
        assert isinstance(snapshots, list)
        assert len(snapshots) >= 1
        assert any(s["id"] == snapshot_id for s in snapshots)
        
        # Cleanup
        import psycopg2
        import os
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("DELETE FROM registry_snapshots WHERE id = %s", (snapshot_id,))
        cursor.close()
        conn.close()
    
    def test_get_entity_snapshots_filters_by_source(self, registry_tables_setup, test_entity_id):
        """Getting entity snapshots should filter by source system."""
        krs_snapshot = RegistrySnapshot(
            entity_id=test_entity_id,
            source_system="KRS",
            external_id="0000011111",
            fetched_at=datetime.utcnow(),
            payload_format="json",
            payload_raw='{"type": "krs"}',
            payload_hash="krs_hash",
        )
        
        ceidg_snapshot = RegistrySnapshot(
            entity_id=test_entity_id,
            source_system="CEIDG",
            external_id="NIP:1234567890",
            fetched_at=datetime.utcnow(),
            payload_format="json",
            payload_raw='{"type": "ceidg"}',
            payload_hash="ceidg_hash",
        )
        
        krs_id = insert_snapshot(krs_snapshot, test=False)
        ceidg_id = insert_snapshot(ceidg_snapshot, test=False)
        
        # Get only KRS snapshots
        krs_snapshots = get_entity_snapshots(test_entity_id, source_system="KRS", test=False)
        
        assert all(s["source_system"] == "KRS" for s in krs_snapshots)
        
        # Get only CEIDG snapshots
        ceidg_snapshots = get_entity_snapshots(test_entity_id, source_system="CEIDG", test=False)
        
        assert all(s["source_system"] == "CEIDG" for s in ceidg_snapshots)
        
        # Cleanup
        import psycopg2
        import os
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("DELETE FROM registry_snapshots WHERE id IN (%s, %s)", (krs_id, ceidg_id))
        cursor.close()
        conn.close()


class TestKRSProfileStorage:
    """Tests for KRS profile upsert and retrieval."""
    
    @pytest.fixture
    def test_entity_id(self, db_url, entity_tables_exist):
        """Create a test entity and return its ID."""
        if not entity_tables_exist:
            pytest.skip("Entity tables do not exist")
        
        import psycopg2
        from uuid import uuid4
        
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        cursor = conn.cursor()
        
        entity_id = str(uuid4())
        
        cursor.execute("""
            INSERT INTO entities (id, entity_type, canonical_label, status, created_at, updated_at)
            VALUES (%s, 'LEGAL_PERSON', 'Test KRS Company', 'ACTIVE', NOW(), NOW())
        """, (entity_id,))
        
        cursor.execute("""
            INSERT INTO legal_persons (entity_id, registered_name, country)
            VALUES (%s, 'Test KRS Company Sp. z o.o.', 'PL')
        """, (entity_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        yield entity_id
        
        # Cleanup
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("DELETE FROM registry_profiles_krs WHERE entity_id = %s", (entity_id,))
        cursor.execute("DELETE FROM entities WHERE id = %s", (entity_id,))
        cursor.close()
        conn.close()
    
    @pytest.fixture
    def test_snapshot_id(self, registry_tables_setup, test_entity_id):
        """Create a test snapshot and return its ID."""
        snapshot = RegistrySnapshot(
            entity_id=test_entity_id,
            source_system="KRS",
            external_id="0000099999",
            fetched_at=datetime.utcnow(),
            payload_format="json",
            payload_raw='{}',
            payload_hash="test_hash",
        )
        
        snapshot_id = insert_snapshot(snapshot, test=False)
        
        yield snapshot_id
        
        # Cleanup - delete profile first (if exists) since it references the snapshot
        import psycopg2
        import os
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("DELETE FROM registry_profiles_krs WHERE last_snapshot_id = %s", (snapshot_id,))
        cursor.execute("DELETE FROM registry_snapshots WHERE id = %s", (snapshot_id,))
        cursor.close()
        conn.close()
    
    def test_upsert_creates_new_profile(
        self, registry_tables_setup, test_entity_id, test_snapshot_id, sample_krs_profile
    ):
        """Upserting should create a new profile."""
        upsert_krs_profile(test_entity_id, sample_krs_profile, test_snapshot_id, test=False)
        
        profile = get_krs_profile(test_entity_id, test=False)
        
        assert profile is not None
        assert profile["entity_id"] == test_entity_id
        assert profile["krs"] == "0000012345"
        assert profile["nip"] == "1234567890"
        assert profile["official_name"] == "TEST COMPANY SP. Z O.O."
    
    def test_upsert_updates_existing_profile(
        self, registry_tables_setup, test_entity_id, test_snapshot_id, sample_krs_profile
    ):
        """Upserting again should update the profile."""
        # First insert
        upsert_krs_profile(test_entity_id, sample_krs_profile, test_snapshot_id, test=False)
        
        # Modify and upsert again
        sample_krs_profile.official_name = "UPDATED COMPANY NAME"
        upsert_krs_profile(test_entity_id, sample_krs_profile, test_snapshot_id, test=False)
        
        profile = get_krs_profile(test_entity_id, test=False)
        
        assert profile["official_name"] == "UPDATED COMPANY NAME"
    
    def test_get_nonexistent_profile_returns_none(self, registry_tables_setup):
        """Getting a nonexistent profile should return None."""
        # Use a valid UUID format that doesn't exist
        result = get_krs_profile("00000000-0000-0000-0000-000000000000", test=False)
        
        assert result is None


class TestCEIDGProfileStorage:
    """Tests for CEIDG profile upsert and retrieval."""
    
    @pytest.fixture
    def test_entity_id(self, db_url, entity_tables_exist):
        """Create a test entity and return its ID."""
        if not entity_tables_exist:
            pytest.skip("Entity tables do not exist")
        
        import psycopg2
        from uuid import uuid4
        
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        cursor = conn.cursor()
        
        entity_id = str(uuid4())
        
        cursor.execute("""
            INSERT INTO entities (id, entity_type, canonical_label, status, created_at, updated_at)
            VALUES (%s, 'PHYSICAL_PERSON', 'Test CEIDG Person', 'ACTIVE', NOW(), NOW())
        """, (entity_id,))
        
        cursor.execute("""
            INSERT INTO physical_persons (entity_id, first_name, last_name, citizenship_country)
            VALUES (%s, 'Jan', 'Testowy', 'PL')
        """, (entity_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        yield entity_id
        
        # Cleanup
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("DELETE FROM registry_profiles_ceidg WHERE entity_id = %s", (entity_id,))
        cursor.execute("DELETE FROM entities WHERE id = %s", (entity_id,))
        cursor.close()
        conn.close()
    
    @pytest.fixture
    def test_snapshot_id(self, registry_tables_setup, test_entity_id):
        """Create a test snapshot and return its ID."""
        snapshot = RegistrySnapshot(
            entity_id=test_entity_id,
            source_system="CEIDG",
            external_id="NIP:9876543210",
            fetched_at=datetime.utcnow(),
            payload_format="json",
            payload_raw='{}',
            payload_hash="test_hash",
        )
        
        snapshot_id = insert_snapshot(snapshot, test=False)
        
        yield snapshot_id
        
        # Cleanup - delete profile first (if exists) since it references the snapshot
        import psycopg2
        import os
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("DELETE FROM registry_profiles_ceidg WHERE last_snapshot_id = %s", (snapshot_id,))
        cursor.execute("DELETE FROM registry_snapshots WHERE id = %s", (snapshot_id,))
        cursor.close()
        conn.close()
    
    def test_upsert_creates_new_profile(
        self, registry_tables_setup, test_entity_id, test_snapshot_id, sample_ceidg_profile
    ):
        """Upserting should create a new CEIDG profile."""
        upsert_ceidg_profile(test_entity_id, sample_ceidg_profile, test_snapshot_id, test=False)
        
        profile = get_ceidg_profile(test_entity_id, test=False)
        
        assert profile is not None
        assert profile["entity_id"] == test_entity_id
        assert profile["nip"] == "9876543210"
        assert profile["first_name"] == "JAN"
        assert profile["last_name"] == "TESTOWY"
        assert profile["business_name"] == "JAN TESTOWY USŁUGI"
    
    def test_get_nonexistent_profile_returns_none(self, registry_tables_setup):
        """Getting a nonexistent profile should return None."""
        # Use a valid UUID format that doesn't exist
        result = get_ceidg_profile("00000000-0000-0000-0000-000000000000", test=False)
        
        assert result is None
