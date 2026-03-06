# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **law firm master data management system** - a PostgreSQL-backed CLI application for managing entities (physical persons and legal entities) with Polish business registry integration (KRS and CEIDG). The system emphasizes data integrity, audit trails, and human-in-the-loop data enrichment.

**Current Phase:** Entity CRUD with registry enrichment
**Future Phases:** Client management, case/matter tracking, billing

## Tech Stack

- **Language:** Python 3.10+
- **Database:** PostgreSQL 16 (running via Docker Compose)
- **CLI Framework:** Click
- **Terminal UI:** Rich
- **Testing:** pytest with coverage
- **Database Driver:** psycopg2-binary
- **HTTP Client:** requests

## Development Setup

### Database

Start PostgreSQL container:
```bash
docker compose up -d
```

Database credentials:
- Host: localhost:5432
- Database: lawfirm
- Admin user: admin (password set in `.env`)
- App user: app_user (optional, conditionally granted in migration 001 if the role exists)

### Python Environment

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and update with your credentials:
```
POSTGRES_USER=admin
POSTGRES_PASSWORD=your_password_here
POSTGRES_DB=lawfirm
DATABASE_URL=postgresql://admin:your_password_here@localhost:5432/lawfirm
CEIDG_API_TOKEN=your_token_here  # Optional, for CEIDG integration
```

### Initialize Database

```bash
# Load schema (source of truth)
psql -h localhost -p 5432 -U admin -d lawfirm -f db/schema.sql

# Load UI metadata (Polish labels and tooltips)
psql -h localhost -p 5432 -U admin -d lawfirm -f ui_metadata.sql

# Initialize registry tables
python -m lawfirm_cli.main registry init-schema
```

## Running the CLI

All CLI commands use the module form:
```bash
python -m lawfirm_cli.main [COMMAND]
```

Common commands:
- `status` - Check database connectivity and schema status
- `menu` - Start interactive main menu
- `entity list` - List entities (supports `--search`, `--nip`, `--krs`, `--regon`, `--pesel`, `--type`, `--limit`)
- `entity create` - Create new entity (interactive)
- `entity view <ID>` - View entity details
- `entity update <ID>` - Update entity (interactive menu)
- `entity delete <ID>` - Delete entity (requires confirmation)
- `entity enrich <ID>` - Enrich from KRS/CEIDG (supports `--source`, `--krs`, `--nip`, `--regon`, `--apply-all`)
- `registry init-schema` - Create registry tables (snapshots, profiles, affiliations)
- `registry status` - Check registry subsystem status
- `meta fields` - List all field metadata
- `meta enums` - List all enum options
- `meta field-detail <KEY>` - View detailed metadata for a specific field

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=lawfirm_cli

# Run specific test file
pytest tests/test_entities.py -v

# Run specific test
pytest tests/test_entities.py::test_create_entity -v
```

Set `DATABASE_URL` environment variable before running tests.

## Architecture

### Module Structure

```
lawfirm_cli/
├── main.py           # Entry point (delegates to commands.py)
├── commands.py       # Click command definitions and orchestration
├── db.py             # Database connection management
├── schema.py         # Schema status checks
├── metadata.py       # Load UI metadata from meta.* tables
├── entities.py       # Entity CRUD business logic
├── prompts.py        # Tooltip-driven interactive prompts
├── render.py         # Rich-based terminal rendering
├── company_names.py  # Company name parsing utilities
└── registry/         # Registry integration subsystem
    ├── models.py         # Data models (profiles, proposals, addresses)
    ├── krs_client.py     # KRS API client
    ├── ceidg_client.py   # CEIDG API client
    ├── proposals.py      # Diff/proposal generation logic
    ├── storage.py        # Snapshot and profile DB storage
    └── ui.py             # Registry-specific UI rendering
```

### Database Schema

The database uses **three schemas**:

1. **`public`** - Main application tables
   - `entities` - Core entity records (UUID primary keys)
   - `physical_persons` - Physical person details (name, DOB, citizenship)
   - `legal_persons` - Legal person details (registered name, legal kind, country)
   - `identifiers` - Business identifiers (KRS, NIP, REGON, PESEL, RFR)
   - `addresses` - Entity addresses (MAIN, CORRESPONDENCE, REGISTERED_SEAT)
   - `contacts` - Contact information (EMAIL, PHONE, WEBSITE)
   - `registry_snapshots` - Immutable raw API responses (created via `registry init-schema`)
   - `registry_profiles_krs` - Normalized KRS data per entity (created via `registry init-schema`)
   - `registry_profiles_ceidg` - Normalized CEIDG data per entity (created via `registry init-schema`)
   - `affiliations` - Entity relationships (created via `registry init-schema`, future use)

2. **`meta`** - UI metadata (Polish labels, tooltips, enums)
   - `ui_field_metadata` - Field labels, tooltips, validation hints
   - `ui_enum_metadata` - Enum value labels and descriptions

3. **`courts`** - Court registry (separate concern)
   - Contains Polish court hierarchy data for future case management
   - Tables:
     - `courts.courts` - Hierarchical court structure (4 tiers)
     - `courts.regional_court_lookup` - Lookup table for regional courts
   - Hierarchy: Supreme Court → 11 Appeal Courts → 47 District Courts → 300+ Regional Courts
   - Initialized via migration: `db/migrations/20260115_create_courts.sql`
   - Future use: Case/matter tracking will reference courts for jurisdiction

**Important:** `db/schema.sql` is the **source of truth** for the database schema. Migrations use two naming conventions (see Database Migration workflow below).

### Key Architectural Patterns

#### 1. Metadata-Driven UI

The CLI loads Polish-language labels, tooltips, and validation hints from the `meta` schema. This allows non-technical users to understand field meanings and provides context-sensitive help.

- `metadata.py` loads metadata from DB
- `prompts.py` uses metadata to create rich interactive prompts
- All user-facing text is in Polish

#### 2. Registry Integration (Human-in-the-Loop)

The system integrates with Polish public registries:
- **KRS** (Krajowy Rejestr Sądowy) - National Court Register for companies
- **CEIDG** (Centralna Ewidencja i Informacja o Działalności Gospodarczej) - Register for sole proprietorships

**Critical principle:** Registry data is **NEVER silently overwritten**. The workflow is:
1. Fetch raw data from registry API
2. Store raw response in `registry_snapshots` (immutable audit trail)
3. Normalize data into structured profile
4. Generate **proposal** by diffing against existing entity data
5. Present proposal to user for review
6. User approves/rejects each proposed change
7. Apply approved changes transactionally

This is implemented in the `registry/` module:
- `*_client.py` - Fetch and normalize registry data
- `proposals.py` - Generate diffs and proposals
- `storage.py` - Persist snapshots and profiles
- `ui.py` - Render proposals for user review

#### 3. Data Safety

- **UUID primary keys** for all entities
- **Parameterized queries** (`%s` placeholders) to prevent SQL injection
- **Unique constraints** on identifiers (e.g., one entity per KRS number)
- **Transactions** for multi-step operations
- **Explicit confirmations** for destructive operations (delete requires typing "DELETE")

#### 4. Entity Lifecycle

Entities can be created in two ways:

**A. Registry-first creation** (recommended for legal entities):
1. User provides KRS/NIP/REGON
2. System fetches data from registry
3. User reviews and confirms pre-filled data
4. Entity created with registry snapshot linked

**B. Manual creation**:
1. User enters all fields interactively
2. Entity created without registry link
3. Can be enriched later via `entity enrich` command

## Database Conventions

### Identifiers

Polish business identifiers are stored in the `identifiers` table:
- **KRS** - Court register number (e.g., "0000012345")
- **NIP** - Tax identification number (10 digits)
- **REGON** - Statistical number (9 or 14 digits)
- **PESEL** - Personal identification number (11 digits)
- **RFR** - Registry of Financial Restructuring number

Each identifier type has a unique constraint per entity (enforced by a partial unique index on identifier_type + identifier_value for KRS, NIP, REGON, PESEL, and RFR).

### Address Types

- `MAIN` - Primary address
- `CORRESPONDENCE` - Mailing address
- `REGISTERED_SEAT` - Legal seat (for companies)

### Contact Types

- `EMAIL`
- `PHONE`
- `WEBSITE`

### Entity Types

- `PHYSICAL_PERSON` - Natural person
- `LEGAL_PERSON` - Legal entity (company, foundation, etc.)

### Courts Subsystem

The `courts` schema stores the hierarchical structure of Polish courts for future case management functionality.

**Structure:**
- **4-tier hierarchy:**
  1. Supreme Court (Sąd Najwyższy)
  2. Appeal Courts (Sądy Apelacyjne) - 11 courts
  3. District Courts (Sądy Okręgowe) - 47 courts
  4. Regional Courts (Sądy Rejonowe) - 300+ courts

**Tables:**
- `courts.courts` - Main hierarchical table with self-referential `parent_id`
- `courts.regional_court_lookup` - Helper table for regional court lookups

**Fields:**
- `court_id` - UUID primary key
- `name` - Full court name (Polish)
- `court_type` - SUPREME, APPEAL, DISTRICT, or REGIONAL
- `parent_id` - Reference to parent court (null for Supreme Court)
- `code` - Official court code (for legal references)

**Future use:** When case/matter tracking is implemented, cases will reference courts to:
- Determine jurisdiction
- Track which court is handling a case
- Generate proper legal citations

**Note:** The courts subsystem is fully initialized and separate from entity management. It resides in its own schema to keep concerns separated.

## Code Conventions

### Database Queries

**ALWAYS use parameterized queries:**
```python
# CORRECT
cursor.execute("SELECT * FROM entities WHERE id = %s", (entity_id,))

# WRONG - SQL injection vulnerability
cursor.execute(f"SELECT * FROM entities WHERE id = '{entity_id}'")
```

### Error Handling

**General rules:**
- No silent failures — every error must be logged or propagated.
- Never swallow exceptions with bare `except: pass`.
- All external API calls (KRS, CEIDG) must be wrapped in try/except with structured error reporting.

**Custom exceptions** are defined in business logic modules:
- `EntityNotFoundError` - Entity does not exist
- `DuplicateIdentifierError` - Identifier already exists on another entity
- `KRSClientError` - Base KRS error
  - `KRSNotFoundError` - KRS number not found (404)
  - `KRSConnectionError` - Network/timeout error
  - `KRSParseError` - Malformed KRS response
- `CEIDGClientError` - Base CEIDG error
  - `CEIDGNotConfiguredError` - Missing CEIDG_API_TOKEN
  - `CEIDGNotFoundError` - NIP/REGON not found (404)
  - `CEIDGConnectionError` - Network/timeout error
  - `CEIDGParseError` - Malformed CEIDG response

### Polish Language

- All user-facing text (labels, tooltips, prompts, messages) should be in Polish
- Code comments, docstrings, and variable names are in English
- Field keys in `meta.ui_field_metadata` use dotted notation (e.g., `entity.canonical_label`)

### Registry Client Behavior

When fetching from registries:
1. **KRS** - Public API, no authentication required
   - Endpoint: `https://api-krs.ms.gov.pl/api/krs/OdpisPelny/{krs}?rejestr=P&format=json`
   - Returns full company record as JSON

2. **CEIDG** - Requires API token
   - Token must be set in `.env` as `CEIDG_API_TOKEN`
   - Endpoint: `https://dane.biznes.gov.pl/api/ceidg/v3/firmy`
   - Can query by NIP or REGON

Both clients handle:
- Network timeouts (configurable via env vars)
- Not found errors (404)
- Connection errors
- Malformed responses

### Company Name Parsing

The `company_names.py` module provides utilities for parsing Polish company names to extract legal forms and generate standardized name variations. This is critical for KRS registry integration.

**Key functions:**
- `extract_legal_form_from_name(name)` - Parse company names to extract legal form (e.g., "sp. z o.o.", "S.A.")
- `parse_krs_company_data(krs_data)` - Main entry point for processing KRS API responses
- `suggest_short_name(full_name, legal_form)` - Generate abbreviated company names
- `get_legal_kind_from_krs_code(krs_code)` - Map KRS legal form codes to internal enum values

**Supported legal forms:**
- All Polish commercial entities (S.A., sp. z o.o., sp. k., sp. j., etc.)
- Foundations and associations
- Cooperative societies
- Various other legal forms recognized in Polish law

**Usage:** The module is automatically used during KRS enrichment to:
1. Extract legal form from official company name
2. Suggest short name for user review
3. Map KRS legal form codes to internal `legal_kind` enum

### Proposal Generation

When generating proposals (`registry/proposals.py`):
- **Add** - Identifier/address/contact not present on entity
- **Update** - Value differs from existing (requires user confirmation)
- **Skip** - Value already matches or user declines

**Collision detection:**
- If proposed identifier exists on another entity, show warning
- If proposed name differs from entity's canonical_label, show warning

## Testing Strategy

Test files correspond to modules:
- `test_entities.py` - Entity CRUD operations
- `test_metadata.py` - Metadata loading
- `test_schema.py` - Schema detection
- `test_cli.py` - CLI command tests
- `test_company_names.py` - Company name parsing
- `test_ceidg.py` - Comprehensive CEIDG integration tests (82 tests)
- `test_registry_normalization.py` - KRS/CEIDG response parsing
- `test_registry_proposals.py` - Proposal diff logic
- `test_registry_storage.py` - Snapshot and profile storage
- `test_registry_cli.py` - End-to-end CLI commands

**Fixtures:**
- `tests/conftest.py` - Shared fixtures
- `tests/fixtures/` - Sample KRS/CEIDG responses (includes v3 API fixtures)

**Mocking:**
- Use `responses` library to mock HTTP requests to registries
- Use pytest fixtures for database connections
- Some tests are skipped if entity tables don't exist (check with `@pytest.mark.skipif`)

**Test Quality Rules:**
- Never mock the thing you're testing. Mocks are only for external dependencies (APIs, databases in unit tests).
- Every test must assert actual output or actual state — not just "function was called".
- Every test must fail if the feature it covers is deleted or broken.
- For bug fixes: add a failing test FIRST, then implement the fix.
- Any skipped test must be explicitly justified.
- Prefer integration tests over unit tests where practical.
- Write at least one test per feature that covers a realistic failure scenario (bad input, missing data, error path).
- **Forbidden test patterns:**
  - `mock.assert_called_once()` as the sole assertion.
  - Testing only that a constructor creates an object.
  - Tests that pass with the implementation deleted (tautological tests).
  - Tests that only check the happy path with trivial inputs.
  - Mocking everything so the test exercises no real logic.

**SQL tests:**
- `tests/sql/` contains SQL-based test files for database validation
- `test_courts.sql` - Validates court hierarchy integrity and structure
- Run manually via psql when needed: `psql -h localhost -p 5432 -U admin -d lawfirm -f tests/sql/test_courts.sql`
- These complement Python tests by validating database constraints and data integrity

## Common Workflows

### Adding a New Field to Entity

1. Add column to `entities` table in `db/schema.sql`
2. Create a migration file `db/00X_add_field.sql`
3. Add metadata to `ui_metadata.sql` (or insert via SQL)
4. Update `entities.py` if business logic is needed
5. Update `prompts.py` if interactive input is needed
6. Add tests in `test_entities.py`

### Adding a New Registry Source

1. Create client module in `lawfirm_cli/registry/` (e.g., `new_registry_client.py`)
2. Implement fetch and normalize functions
3. Define profile model in `registry/models.py`
4. Create profile table in `registry/storage.py`
5. Implement proposal generation in `registry/proposals.py`
6. Add CLI commands in `commands.py`
7. Add UI rendering in `registry/ui.py`
8. Write tests with mocked responses

### Database Migration

**Migration naming conventions:**
Two formats are in use depending on the scope:

- **Core schema changes** (entities, identifiers, etc.): Use numbered format
  - Format: `db/00X_descriptive_name.sql`
  - Example: `db/001_create_entity_tables.sql`

- **Domain subsystems** (courts, future modules): Use date-based format
  - Format: `db/migrations/YYYYMMDD_descriptive_name.sql`
  - Example: `db/migrations/20260115_create_courts.sql`

Both formats are valid; choose based on whether it's core application schema or a domain-specific subsystem.

**Migration workflow:**
1. Create migration file using appropriate naming convention
2. Write SQL (prefer idempotent operations with `IF NOT EXISTS` or `CREATE OR REPLACE`)
3. Test on development database
4. Apply: `psql -h localhost -p 5432 -U admin -d lawfirm -f path/to/migration.sql`
5. Update `db/schema.sql` to reflect current state (this is the source of truth)
6. Commit both migration file and updated `schema.sql`

## Development Process

### Execution Workflow

For non-trivial tasks:
1. **Explore:** Read relevant files and summarize current behavior.
2. **Plan:** List exact files/changes and risks.
3. **Implement:** Smallest safe increments.
4. **Verify:** Run tests, update docs if behavior changed.
5. **Report:** Write a conventional commit message, summarize what changed and risks.

### Definition of Done

A task is done only when:
- Acceptance criteria are met.
- Tests added/updated and passing.
- Docs updated if behavior changed.
- Conventional commit message written summarizing changes.
- Risks and follow-ups documented in summary.

### Do / Don't

**Do:**
- Follow existing patterns in the codebase before introducing new ones.
- Prefer the smallest viable change that satisfies requirements.
- Add/update tests when behavior changes.
- Surface assumptions and unresolved risks.
- Ask clarifying questions when requirements are ambiguous.

**Don't:**
- Don't bypass tests or lint silently.
- Don't add dependencies without justification.
- Don't invent architecture patterns not present in the codebase.
- Don't declare completion without running required validations.
- Don't introduce unrelated refactors in task-focused changes.

### Security Non-Negotiables

- Never commit secrets, API keys, tokens, or credentials.
- Never read or print contents of `.env*` files or credential files.
- Never hardcode API keys.
- All user-provided file paths must be validated before processing.

### Bugfix Protocol

1. Reproduce with a failing test or exact repro steps.
2. Identify root cause (not symptom suppression).
3. Apply minimal fix.
4. Re-run failing test + broader affected suite.
5. Add regression test to prevent recurrence.

### Dependency Policy

- Prefer existing dependencies already in the repo.
- New dependency requires clear justification and approval.
- Keep `requirements.txt` in sync with actual usage.
- Remove unused dependencies when practical.

### Post-Change Housekeeping

After every non-trivial code change, before reporting completion:
1. **Update CLAUDE.md**: If the change introduces new modules, alters project structure, changes commands, or shifts architectural patterns, update this file to reflect the new state.
2. **Update schema**: If database schema changed, update `db/schema.sql` (source of truth) and `ui_metadata.sql` if metadata was affected.
3. **Commit**: Stage all modified files (code, docs, schema), create a conventional commit, and push.

### Escalation — Ask Before Proceeding

Stop and ask when:
- Changes would alter database schema or migration strategy.
- Registry integration behavior (KRS/CEIDG) would change.
- Requirements are ambiguous or conflicting.
- A fix requires adding new external dependencies.
- You're unsure how to implement something or which approach to choose — always ask, never guess.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `KRS_API_BASE_URL` | KRS API endpoint | `https://api-krs.ms.gov.pl/api/krs` |
| `KRS_REQUEST_TIMEOUT` | KRS request timeout (seconds) | `30` |
| `CEIDG_API_TOKEN` | CEIDG API token | Required for CEIDG |
| `CEIDG_API_BASE_URL` | CEIDG API endpoint | `https://dane.biznes.gov.pl/api/ceidg/v3` |
| `CEIDG_REQUEST_TIMEOUT` | CEIDG request timeout (seconds) | `30` |

## Important Notes

- **UUIDs:** All primary keys are UUIDs (generated via `uuid.uuid4()`)
- **Timestamps:** Use `timestamp with time zone` for all timestamps
- **Immutability:** Registry snapshots are immutable (never update, only insert)
- **Uniqueness:** Identifiers have unique constraints per type (one KRS per entity)
- **Duplicate Prevention:** The system rejects duplicate identifiers by design. This is intentional to enforce data quality. Future versions may allow admin overrides with audit trails.
- **No ORM:** Direct SQL queries via psycopg2 (no SQLAlchemy/Django ORM)
- **CLI-first:** This is a terminal application, not a web app (may change in future phases)
