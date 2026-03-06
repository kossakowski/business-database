# Project Overview

This is a Python-based CLI application backed by a PostgreSQL database, designed to manage **Law Firm Master Data** (Entities).
It focuses on storing Physical and Legal Persons with their identifiers (PESEL, NIP, KRS), contacts, and addresses.
It also features integration with Polish public registries (KRS and CEIDG) to enrich entity data.

## Key Technologies
*   **Language:** Python 3.10+
*   **Database:** PostgreSQL 16 (running via Docker Compose)
*   **Libraries:** `psycopg2` (DB), `click` (CLI), `rich` (UI), `requests` (API), `pytest` (Testing)

## Architecture
The project follows a modular structure:
*   `lawfirm_cli/`: Main Python package.
    *   `main.py`: CLI entry point.
    *   `entities.py`: Business logic for Entity CRUD.
    *   `metadata.py`: Handling of UI metadata (labels, tooltips) stored in the DB.
    *   `registry/`: Sub-module for KRS/CEIDG integration.
*   `db/`: Database schemas and migration scripts.
    *   `schema.sql`: The canonical database schema.
    *   `ui_metadata.sql`: Initial data for UI labels and enums.
*   `tests/`: Pytest suite covering CLI, logic, and registry integrations.

# Building and Running

## Prerequisites
*   Docker & Docker Compose (for the database)
*   Python 3.10+

## Setup
1.  **Database:**
    ```bash
    docker compose up -d
    ```
    This starts a Postgres instance on port 5432.
    Connection URL: `postgresql://admin:123@localhost:5432/lawfirm`

2.  **Environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Configuration:**
    Create a `.env` file or export variables:
    ```bash
    export DATABASE_URL="postgresql://admin:123@localhost:5432/lawfirm"
    ```
    For CEIDG integration, a `CEIDG_API_TOKEN` is required.

4.  **Database Initialization:**
    If starting fresh, load the schema and metadata:
    ```bash
    # (Assuming admin user has permissions)
    psql -h localhost -p 5432 -U admin -d lawfirm -f db/schema.sql
    psql -h localhost -p 5432 -U admin -d lawfirm -f ui_metadata.sql
    
    # Initialize Registry specific tables
    python -m lawfirm_cli.main registry init-schema
    ```

## Usage
Run the CLI via the python module:
```bash
python -m lawfirm_cli.main [COMMAND]
```

**Common Commands:**
*   `status`: Check database connectivity and schema status.
*   `entity list`: List all entities.
*   `entity create`: Interactive wizard to create a new entity.
*   `entity view <ID>`: View details of an entity.
*   `registry status`: Check registry subsystem status.

# Development Conventions

## Code Style
*   **Python:** Follow PEP 8.
*   **Typing:** Type hints should be used where practical.
*   **UI/UX:** Use `rich` for formatted terminal output. Prompts should utilize the metadata system (`lawfirm_cli.metadata`) to fetch Polish labels and tooltips from the database (`meta` schema).

## Database
*   **Schema Authority:** `db/schema.sql` is the source of truth.
*   **Migrations:** SQL files in `db/` (e.g., `001_...sql`) represent changes.
*   **Safety:** Use parameterized queries (`%s` placeholder) for all SQL execution to prevent injection.
*   **Ids:** UUIDs are used for primary keys.

## Testing
*   **Runner:** `pytest`
*   **Coverage:** `pytest --cov=lawfirm_cli`
*   **Fixtures:** Located in `tests/conftest.py` and `tests/fixtures/`.
*   **Mocking:** `responses` is used to mock HTTP requests to external registries (KRS/CEIDG).

## Registry Integration
*   Data from KRS/CEIDG is **never** silently overwritten.
*   The `registry` module handles fetching, normalization, and "proposal" generation (diffing against existing data).
*   Raw API responses should be stored in `registry_snapshots` table for audit capability.
