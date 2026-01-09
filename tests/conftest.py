"""Pytest fixtures and test configuration."""

import os
import pytest
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor

# Set test database URL if not already set
if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql://admin:123@localhost:5432/lawfirm"


@pytest.fixture(scope="session")
def db_url():
    """Get database URL for tests."""
    return os.environ.get("DATABASE_URL_TEST") or os.environ.get("DATABASE_URL")


@pytest.fixture(scope="function")
def db_connection(db_url):
    """Create a database connection that rolls back after each test."""
    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    yield conn
    conn.rollback()
    conn.close()


@pytest.fixture(scope="function")
def db_cursor(db_connection):
    """Create a cursor that uses dict rows."""
    cursor = db_connection.cursor(cursor_factory=RealDictCursor)
    yield cursor
    cursor.close()


@pytest.fixture(scope="session")
def meta_tables_exist(db_url):
    """Check if meta tables exist (required for metadata tests)."""
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'meta' 
            AND table_name = 'ui_field_metadata'
        )
    """)
    result = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return result


@pytest.fixture(scope="session")
def entity_tables_exist(db_url):
    """Check if entity tables exist (required for CRUD tests)."""
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


@pytest.fixture
def clear_metadata_cache():
    """Clear the metadata cache before and after test."""
    from lawfirm_cli.metadata import clear_cache
    clear_cache()
    yield
    clear_cache()


@contextmanager
def rollback_transaction(db_url):
    """Context manager that provides a connection and rolls back on exit."""
    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()


# Markers for conditional test skipping
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "requires_meta_tables: mark test as requiring meta tables"
    )
    config.addinivalue_line(
        "markers", "requires_entity_tables: mark test as requiring entity tables"
    )
