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
- `test_registry_normalization.py` - Tests for KRS/CEIDG response parsing
- `test_registry_proposals.py` - Tests for diff/proposal generation logic
- `test_registry_storage.py` - Tests for snapshot and profile storage
- `test_registry_cli.py` - Tests for registry CLI commands (mocked HTTP)

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
│   ├── render.py        # Terminal output formatting
│   └── registry/        # Registry integration module
│       ├── __init__.py
│       ├── models.py        # Data models (profiles, proposals)
│       ├── krs_client.py    # KRS API client
│       ├── ceidg_client.py  # CEIDG API client
│       ├── proposals.py     # Diff/proposal generation
│       ├── storage.py       # Snapshot & profile DB storage
│       └── ui.py            # Registry-specific UI rendering
├── tests/
│   ├── fixtures/
│   │   ├── krs_sample.json      # Sample KRS response
│   │   └── ceidg_sample.json    # Sample CEIDG response
│   ├── conftest.py              # Pytest fixtures
│   ├── test_metadata.py
│   ├── test_schema.py
│   ├── test_entities.py
│   ├── test_cli.py
│   ├── test_registry_normalization.py  # KRS/CEIDG parsing tests
│   ├── test_registry_proposals.py      # Proposal diff logic tests
│   ├── test_registry_storage.py        # Snapshot storage tests
│   └── test_registry_cli.py            # CLI command tests
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

---

## Registry Integration (KRS & CEIDG)

The CLI supports enriching entity data from Polish public registries:

- **KRS** (Krajowy Rejestr Sądowy) - National Court Register for legal entities
- **CEIDG** (Centralna Ewidencja i Informacja o Działalności Gospodarczej) - Central Register for sole proprietorships

### Features

- **Fetch official data**: Retrieve company/person data from registries
- **Human-in-the-loop**: Review proposed changes before applying
- **No silent overwrites**: Existing data is preserved; registry data proposed as additions
- **Provenance**: Raw registry responses stored as immutable snapshots
- **Resilient**: Graceful error handling for network issues and API downtime

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `KRS_API_BASE_URL` | KRS API base URL | `https://api-krs.ms.gov.pl/api/krs` |
| `KRS_REQUEST_TIMEOUT` | Request timeout (seconds) | `30` |
| `CEIDG_API_TOKEN` | CEIDG API token (**required** for CEIDG) | - |
| `CEIDG_API_BASE_URL` | CEIDG API base URL | `https://dane.biznes.gov.pl/api/ceidg/v2` |
| `CEIDG_REQUEST_TIMEOUT` | Request timeout (seconds) | `30` |

### Getting a CEIDG API Token

1. Go to https://dane.biznes.gov.pl
2. Create an account and log in
3. Navigate to API access section
4. Generate an API token
5. Add to your `.env` file:
   ```
   CEIDG_API_TOKEN=your_token_here
   ```

### Initialize Registry Tables

Before using registry features, create the required tables:

```bash
python -m lawfirm_cli.main registry init-schema
```

This creates:
- `registry_snapshots` - Stores raw registry responses
- `registry_profiles_krs` - Normalized KRS data per entity
- `registry_profiles_ceidg` - Normalized CEIDG data per entity
- `affiliations` - Entity relationships (future use)

### Check Registry Status

```bash
python -m lawfirm_cli.main registry status
```

Shows table existence and configuration status.

### Enrich Entity Data

#### Interactive Mode (via update menu)

```bash
python -m lawfirm_cli.main entity update <entity-id>
# Then select option 6: Registry enrichment (KRS/CEIDG)
```

#### Non-Interactive Mode

**By KRS number:**
```bash
python -m lawfirm_cli.main entity enrich <entity-id> --source krs --krs 0000012345
```

**By NIP (CEIDG):**
```bash
python -m lawfirm_cli.main entity enrich <entity-id> --source ceidg --nip 1234567890
```

**By REGON (CEIDG):**
```bash
python -m lawfirm_cli.main entity enrich <entity-id> --source ceidg --regon 123456789
```

**Auto-apply safe additions:**
```bash
python -m lawfirm_cli.main entity enrich <entity-id> --apply-all
```

### What Gets Enriched

| Data Type | KRS | CEIDG |
|-----------|-----|-------|
| KRS number | ✓ | - |
| NIP | ✓ | ✓ |
| REGON | ✓ | ✓ |
| Company/Business name | ✓ | ✓ |
| Person name | - | ✓ |
| Seat/Main address | ✓ | ✓ |
| Correspondence address | ✓ | ✓ |
| Email | ✓ | ✓ |
| Website | ✓ | ✓ |
| Phone | ✓ | ✓ |
| PKD codes | ✓ | ✓ |
| Representatives | ✓ | - |
| Legal form | ✓ | - |

### Proposal Behavior

1. **Adding missing data**: Identifiers, contacts, and addresses not present on the entity are proposed for addition
2. **No silent overwrites**: Existing data is never overwritten without explicit user confirmation
3. **Collision detection**: If an identifier already exists on another entity, a warning is shown
4. **Name mismatches**: If registry name differs from entity name, a warning is shown

### API Reference

**KRS (eKRS Open API)**
- Endpoint: `https://api-krs.ms.gov.pl/api/krs/OdpisPelny/{krs}?rejestr=P&format=json`
- Authentication: None (public API)
- Rate limiting: None documented
- Documentation: https://ekrs.ms.gov.pl

**CEIDG (API v2)**
- Endpoint: `https://dane.biznes.gov.pl/api/ceidg/v2/firmy`
- Authentication: Bearer token
- Rate limiting: Subject to terms of service
- Documentation: https://dane.biznes.gov.pl/dokumentacja
