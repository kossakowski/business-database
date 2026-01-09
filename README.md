# Business Database App (Law Firm)

A local database-backed application for maintaining a **general-purpose law firm data store**.

**Current scope:** only the **Entities** schema (master data for people and legal entities).  
**Future scope:** the same database will be extended to store:
- **Client information** (engagements, contacts, preferences, documents)
- **Case / matter information** (proceedings, parties, roles, courts, deadlines, events)
- **Billing** (time entries, fees, invoices, payments, cost tracking)

The goal is to build a reliable system of record that can grow gradually without redesigning everything.

---

## Scope (Phase 1)

Phase 1 goal: implement a reliable CRUD for **master data**.

In Phase 1 we store:
- **Entities**: PHYSICAL_PERSON and LEGAL_PERSON
- identifiers (PESEL/NIP/REGON/KRS/...)
- names/labels
- contacts
- addresses
- registry snapshots and registry-derived affiliations (objective roles from KRS/CEIDG)
- UI metadata (tooltips + enum labels) in `meta.*`

We do **NOT** store (yet):
- case/matter context (plaintiff/defendant/creditor/etc.)
- client engagements and billing objects

Those will be added in later phases.

---

## Database

- PostgreSQL 16 running locally in Docker
- Database name: `lawfirm`
- Admin user (maintenance/migrations): `admin`
- App user (CRUD): `app_user` (recommended)

Connection string is provided via `.env`:
- `DATABASE_URL=postgresql://app_user:...@localhost:5432/lawfirm`

### Quick checks

Check connectivity:
```bash
psql -h localhost -p 5432 -U admin -d lawfirm -c "SELECT 1;"
```

Start database (Docker):
```bash
docker compose up -d
```

---

## CLI Tool Installation

### Prerequisites

- Python 3.10+
- PostgreSQL database running (via Docker Compose)

### Setup

1. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure database connection:**
   
   Create a `.env` file in the project root:
   ```
   DATABASE_URL=postgresql://admin:123@localhost:5432/lawfirm
   ```
   
   Or export as environment variable:
   ```bash
   export DATABASE_URL="postgresql://admin:123@localhost:5432/lawfirm"
   ```

4. **Load UI metadata (if not already done):**
   ```bash
   psql -h localhost -p 5432 -U admin -d lawfirm -f ui_metadata.sql
   ```

---

## CLI Usage

Run the CLI using:
```bash
python -m lawfirm_cli.main [COMMAND]
```

Or create an alias:
```bash
alias lawfirm-cli="python -m lawfirm_cli.main"
```

### Available Commands

#### Check Schema Status

```bash
python -m lawfirm_cli.main status
```

Shows which database tables exist and which are missing.

#### Explore Metadata

**List all field definitions:**
```bash
python -m lawfirm_cli.main meta fields
```

**Filter fields by prefix:**
```bash
python -m lawfirm_cli.main meta fields --prefix "id."
python -m lawfirm_cli.main meta fields --prefix "entity."
python -m lawfirm_cli.main meta fields --group "Identyfikatory"
```

**View single field details:**
```bash
python -m lawfirm_cli.main meta field entity.entity_type
```

**List all enum keys:**
```bash
python -m lawfirm_cli.main meta enums
```

**View enum options:**
```bash
python -m lawfirm_cli.main meta enums entity_type
python -m lawfirm_cli.main meta enums legal_kind
```

#### Entity CRUD Operations

> **Note:** Entity tables must be created first. The CLI will show a helpful message if they don't exist.

**Create a new entity:**
```bash
python -m lawfirm_cli.main entity create
```
Interactive prompts will guide you through:
- Selecting entity type (PHYSICAL_PERSON or LEGAL_PERSON)
- Entering fields with Polish labels and tooltips
- Adding identifiers (PESEL, NIP, KRS, etc.)
- Adding address and contacts

**List entities:**
```bash
python -m lawfirm_cli.main entity list
python -m lawfirm_cli.main entity list --type PHYSICAL_PERSON
python -m lawfirm_cli.main entity list --search "Kowalski"
```

**View entity details:**
```bash
python -m lawfirm_cli.main entity view <entity-id>
```

**Update an entity:**
```bash
python -m lawfirm_cli.main entity update <entity-id>
```

**Delete an entity:**
```bash
python -m lawfirm_cli.main entity delete <entity-id>
```
Requires typing "DELETE" to confirm.

---

## Running Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Set database URL
export DATABASE_URL="postgresql://admin:123@localhost:5432/lawfirm"

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=lawfirm_cli

# Run specific test file
pytest tests/test_metadata.py -v
```

### Test Categories

- `test_metadata.py` - Tests for loading tooltips and enum values from meta tables
- `test_schema.py` - Tests for schema detection and table existence checks  
- `test_entities.py` - Tests for entity CRUD operations (some skipped until tables exist)
- `test_cli.py` - Integration tests for CLI commands

---

## Project Structure

```
business-database/
├── lawfirm_cli/
│   ├── __init__.py
│   ├── main.py          # Entry point
│   ├── commands.py      # CLI command definitions
│   ├── db.py            # Database connection
│   ├── schema.py        # Table existence checks
│   ├── metadata.py      # Load tooltips/enums from meta tables
│   ├── entities.py      # Entity CRUD operations
│   ├── prompts.py       # Tooltip-driven input prompts
│   └── render.py        # Terminal output formatting
├── tests/
│   ├── conftest.py      # Pytest fixtures
│   ├── test_metadata.py
│   ├── test_schema.py
│   ├── test_entities.py
│   └── test_cli.py
├── db/
│   └── schema.sql       # Schema dump (source of truth)
├── docker-compose.yml
├── requirements.txt
├── ui_metadata.sql      # UI metadata definitions
└── README.md
```

---

## Features

### Tooltip-Driven Prompts

The CLI uses database-stored metadata to provide rich prompts:
- Polish labels (`label_pl`)
- Contextual tooltips (`tooltip_pl`)
- Example values and placeholders
- Validation hints and patterns
- Privacy level indicators

### Graceful Degradation

When entity tables don't exist yet, the CLI:
- Shows clear status of which tables are missing
- Allows full exploration of metadata
- Provides helpful guidance on next steps

### Safe Operations

- All CRUD operations use parameterized queries (no SQL injection)
- Transactions ensure all-or-nothing creation
- Delete requires explicit confirmation
- Unique constraints show user-friendly errors
