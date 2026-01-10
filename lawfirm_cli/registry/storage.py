"""Database storage for registry snapshots and profiles."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from psycopg2.extras import RealDictCursor

from lawfirm_cli.db import transaction, execute_query
from lawfirm_cli.registry.models import (
    RegistrySnapshot,
    NormalizedKRSProfile,
    NormalizedCEIDGProfile,
)


def check_registry_tables_exist(test: bool = False) -> Dict[str, bool]:
    """Check which registry tables exist.
    
    Args:
        test: If True, use test database.
        
    Returns:
        Dict mapping table name to existence boolean.
    """
    tables = [
        "registry_snapshots",
        "registry_profiles_krs",
        "registry_profiles_ceidg",
        "affiliations",
    ]
    
    result = {}
    for table in tables:
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            )
        """
        rows = execute_query(query, (table,), test=test)
        result[table] = rows[0]["exists"] if rows else False
    
    return result


def create_registry_tables(test: bool = False) -> List[str]:
    """Create registry tables if they don't exist.
    
    This is idempotent - tables are only created if missing.
    
    Args:
        test: If True, use test database.
        
    Returns:
        List of tables that were created.
    """
    created = []
    
    with transaction(test=test) as conn:
        cursor = conn.cursor()
        
        # Registry snapshots (append-only)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registry_snapshots (
                id              UUID PRIMARY KEY,
                entity_id       UUID REFERENCES entities(id) ON DELETE CASCADE,
                source_system   TEXT NOT NULL,
                external_id     TEXT NOT NULL,
                fetched_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                effective_date  DATE,
                payload_format  TEXT NOT NULL DEFAULT 'json',
                payload         JSONB,
                payload_raw     TEXT,
                payload_hash    TEXT,
                fetched_by      TEXT,
                purpose_ref     TEXT,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        
        # Check if we created it
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'registry_snapshots'
            )
        """)
        if cursor.fetchone()[0]:
            created.append("registry_snapshots")
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_registry_snapshots_entity 
            ON registry_snapshots(entity_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_registry_snapshots_source 
            ON registry_snapshots(source_system, external_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_registry_snapshots_fetched 
            ON registry_snapshots(fetched_at DESC)
        """)
        
        # KRS profiles (normalized view, one per entity)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registry_profiles_krs (
                entity_id           UUID PRIMARY KEY REFERENCES entities(id) ON DELETE CASCADE,
                krs                 TEXT,
                nip                 TEXT,
                regon               TEXT,
                official_name       TEXT,
                short_name          TEXT,
                legal_form          TEXT,
                registry_status     TEXT,
                registration_date   DATE,
                share_capital       TEXT,
                pkd_main            TEXT,
                last_snapshot_id    UUID REFERENCES registry_snapshots(id),
                last_fetched_at     TIMESTAMPTZ,
                created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'registry_profiles_krs'
            )
        """)
        if cursor.fetchone()[0]:
            created.append("registry_profiles_krs")
        
        # CEIDG profiles (normalized view, one per entity)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registry_profiles_ceidg (
                entity_id           UUID PRIMARY KEY REFERENCES entities(id) ON DELETE CASCADE,
                ceidg_id            TEXT,
                nip                 TEXT,
                regon               TEXT,
                first_name          TEXT,
                last_name           TEXT,
                business_name       TEXT,
                status              TEXT,
                start_date          DATE,
                end_date            DATE,
                pkd_main            TEXT,
                last_snapshot_id    UUID REFERENCES registry_snapshots(id),
                last_fetched_at     TIMESTAMPTZ,
                created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'registry_profiles_ceidg'
            )
        """)
        if cursor.fetchone()[0]:
            created.append("registry_profiles_ceidg")
        
        # Affiliations (for future use)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS affiliations (
                id                  UUID PRIMARY KEY,
                entity_id           UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
                affiliated_entity_id UUID REFERENCES entities(id) ON DELETE SET NULL,
                affiliation_type    TEXT NOT NULL,
                role                TEXT,
                start_date          DATE,
                end_date            DATE,
                source_system       TEXT,
                source_snapshot_id  UUID REFERENCES registry_snapshots(id),
                notes               TEXT,
                created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'affiliations'
            )
        """)
        if cursor.fetchone()[0]:
            created.append("affiliations")
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_affiliations_entity 
            ON affiliations(entity_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_affiliations_affiliated 
            ON affiliations(affiliated_entity_id)
        """)
        
        cursor.close()
    
    return created


def insert_snapshot(snapshot: RegistrySnapshot, test: bool = False) -> str:
    """Insert a registry snapshot.
    
    Args:
        snapshot: RegistrySnapshot to insert.
        test: If True, use test database.
        
    Returns:
        Inserted snapshot ID.
    """
    snapshot_id = str(uuid4())
    
    with transaction(test=test) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO registry_snapshots (
                id, entity_id, source_system, external_id, fetched_at,
                effective_date, payload_format, payload_raw, payload_hash,
                fetched_by, purpose_ref, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
            )
        """, (
            snapshot_id,
            snapshot.entity_id,
            snapshot.source_system,
            snapshot.external_id,
            snapshot.fetched_at or datetime.utcnow(),
            snapshot.effective_date,
            snapshot.payload_format,
            snapshot.payload_raw,
            snapshot.payload_hash,
            snapshot.fetched_by,
            snapshot.purpose_ref,
        ))
        cursor.close()
    
    return snapshot_id


def get_snapshot(snapshot_id: str, test: bool = False) -> Optional[Dict[str, Any]]:
    """Get a snapshot by ID.
    
    Args:
        snapshot_id: Snapshot ID.
        test: If True, use test database.
        
    Returns:
        Snapshot dict or None.
    """
    with transaction(test=test) as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT * FROM registry_snapshots WHERE id = %s
        """, (snapshot_id,))
        row = cursor.fetchone()
        cursor.close()
        return dict(row) if row else None


def get_entity_snapshots(
    entity_id: str,
    source_system: Optional[str] = None,
    limit: int = 10,
    test: bool = False,
) -> List[Dict[str, Any]]:
    """Get snapshots for an entity.
    
    Args:
        entity_id: Entity ID.
        source_system: Optional filter by source (KRS/CEIDG).
        limit: Maximum results.
        test: If True, use test database.
        
    Returns:
        List of snapshot dicts.
    """
    query = """
        SELECT id, source_system, external_id, fetched_at, payload_hash
        FROM registry_snapshots 
        WHERE entity_id = %s
    """
    params = [entity_id]
    
    if source_system:
        query += " AND source_system = %s"
        params.append(source_system)
    
    query += " ORDER BY fetched_at DESC LIMIT %s"
    params.append(limit)
    
    with transaction(test=test) as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        return [dict(r) for r in rows]


def upsert_krs_profile(
    entity_id: str,
    profile: NormalizedKRSProfile,
    snapshot_id: str,
    test: bool = False,
) -> None:
    """Insert or update KRS profile for an entity.
    
    Args:
        entity_id: Entity ID.
        profile: Normalized KRS profile.
        snapshot_id: Associated snapshot ID.
        test: If True, use test database.
    """
    with transaction(test=test) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO registry_profiles_krs (
                entity_id, krs, nip, regon, official_name, short_name,
                legal_form, registry_status, registration_date, share_capital,
                pkd_main, last_snapshot_id, last_fetched_at, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), NOW()
            )
            ON CONFLICT (entity_id) DO UPDATE SET
                krs = EXCLUDED.krs,
                nip = EXCLUDED.nip,
                regon = EXCLUDED.regon,
                official_name = EXCLUDED.official_name,
                short_name = EXCLUDED.short_name,
                legal_form = EXCLUDED.legal_form,
                registry_status = EXCLUDED.registry_status,
                registration_date = EXCLUDED.registration_date,
                share_capital = EXCLUDED.share_capital,
                pkd_main = EXCLUDED.pkd_main,
                last_snapshot_id = EXCLUDED.last_snapshot_id,
                last_fetched_at = NOW(),
                updated_at = NOW()
        """, (
            entity_id,
            profile.krs,
            profile.nip,
            profile.regon,
            profile.official_name,
            profile.short_name,
            profile.legal_form,
            profile.registry_status,
            profile.registration_date,
            profile.share_capital,
            profile.pkd_main,
            snapshot_id,
        ))
        cursor.close()


def upsert_ceidg_profile(
    entity_id: str,
    profile: NormalizedCEIDGProfile,
    snapshot_id: str,
    test: bool = False,
) -> None:
    """Insert or update CEIDG profile for an entity.
    
    Args:
        entity_id: Entity ID.
        profile: Normalized CEIDG profile.
        snapshot_id: Associated snapshot ID.
        test: If True, use test database.
    """
    with transaction(test=test) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO registry_profiles_ceidg (
                entity_id, ceidg_id, nip, regon, first_name, last_name,
                business_name, status, start_date, end_date, pkd_main,
                last_snapshot_id, last_fetched_at, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), NOW()
            )
            ON CONFLICT (entity_id) DO UPDATE SET
                ceidg_id = EXCLUDED.ceidg_id,
                nip = EXCLUDED.nip,
                regon = EXCLUDED.regon,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                business_name = EXCLUDED.business_name,
                status = EXCLUDED.status,
                start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date,
                pkd_main = EXCLUDED.pkd_main,
                last_snapshot_id = EXCLUDED.last_snapshot_id,
                last_fetched_at = NOW(),
                updated_at = NOW()
        """, (
            entity_id,
            profile.ceidg_id,
            profile.nip,
            profile.regon,
            profile.first_name,
            profile.last_name,
            profile.business_name,
            profile.status,
            profile.start_date,
            profile.end_date,
            profile.pkd_main,
            snapshot_id,
        ))
        cursor.close()


def get_krs_profile(entity_id: str, test: bool = False) -> Optional[Dict[str, Any]]:
    """Get KRS profile for an entity.
    
    Args:
        entity_id: Entity ID.
        test: If True, use test database.
        
    Returns:
        Profile dict or None.
    """
    with transaction(test=test) as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT * FROM registry_profiles_krs WHERE entity_id = %s
        """, (entity_id,))
        row = cursor.fetchone()
        cursor.close()
        return dict(row) if row else None


def get_ceidg_profile(entity_id: str, test: bool = False) -> Optional[Dict[str, Any]]:
    """Get CEIDG profile for an entity.
    
    Args:
        entity_id: Entity ID.
        test: If True, use test database.
        
    Returns:
        Profile dict or None.
    """
    with transaction(test=test) as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT * FROM registry_profiles_ceidg WHERE entity_id = %s
        """, (entity_id,))
        row = cursor.fetchone()
        cursor.close()
        return dict(row) if row else None
