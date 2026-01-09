"""Database connection management for Law Firm CLI."""

import os
from contextlib import contextmanager
from typing import Generator, Optional

import psycopg2
from psycopg2.extensions import connection as Connection
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


def get_database_url(test: bool = False) -> str:
    """Get database URL from environment.
    
    Args:
        test: If True, prefer DATABASE_URL_TEST over DATABASE_URL.
        
    Returns:
        Database connection URL.
        
    Raises:
        ValueError: If DATABASE_URL is not set.
    """
    if test:
        url = os.environ.get("DATABASE_URL_TEST") or os.environ.get("DATABASE_URL")
    else:
        url = os.environ.get("DATABASE_URL")
    
    if not url:
        raise ValueError(
            "DATABASE_URL environment variable is not set.\n"
            "Please create a .env file with:\n"
            "  DATABASE_URL=postgresql://user:password@localhost:5432/lawfirm"
        )
    return url


def get_connection(test: bool = False) -> Connection:
    """Create a new database connection.
    
    Args:
        test: If True, use test database URL.
        
    Returns:
        Database connection object.
    """
    url = get_database_url(test=test)
    return psycopg2.connect(url)


@contextmanager
def get_cursor(
    conn: Optional[Connection] = None,
    dict_cursor: bool = True,
    autocommit: bool = False,
    test: bool = False,
) -> Generator:
    """Context manager for database cursor.
    
    Args:
        conn: Existing connection to use. If None, creates a new one.
        dict_cursor: If True, use RealDictCursor for dict-like row access.
        autocommit: If True, commit after each operation.
        test: If True, use test database URL.
        
    Yields:
        Database cursor.
    """
    own_connection = conn is None
    if own_connection:
        conn = get_connection(test=test)
        if autocommit:
            conn.autocommit = True
    
    cursor_factory = RealDictCursor if dict_cursor else None
    cursor = conn.cursor(cursor_factory=cursor_factory)
    
    try:
        yield cursor
        if not autocommit and own_connection:
            conn.commit()
    except Exception:
        if own_connection:
            conn.rollback()
        raise
    finally:
        cursor.close()
        if own_connection:
            conn.close()


@contextmanager
def transaction(test: bool = False) -> Generator[Connection, None, None]:
    """Context manager for database transactions.
    
    All operations within the context are wrapped in a transaction.
    Commits on success, rolls back on exception.
    
    Args:
        test: If True, use test database URL.
        
    Yields:
        Database connection with active transaction.
    """
    conn = get_connection(test=test)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_query(
    query: str,
    params: tuple = (),
    fetch: bool = True,
    test: bool = False,
) -> Optional[list]:
    """Execute a query and optionally fetch results.
    
    Args:
        query: SQL query with %s placeholders.
        params: Query parameters.
        fetch: If True, fetch and return all results.
        test: If True, use test database URL.
        
    Returns:
        List of result rows if fetch=True, None otherwise.
    """
    with get_cursor(test=test) as cursor:
        cursor.execute(query, params)
        if fetch:
            return cursor.fetchall()
        return None


def execute_one(
    query: str,
    params: tuple = (),
    test: bool = False,
) -> Optional[dict]:
    """Execute a query and fetch one result.
    
    Args:
        query: SQL query with %s placeholders.
        params: Query parameters.
        test: If True, use test database URL.
        
    Returns:
        Single result row as dict, or None if no results.
    """
    with get_cursor(test=test) as cursor:
        cursor.execute(query, params)
        return cursor.fetchone()
