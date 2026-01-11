-- Migration: Create Entity Tables
-- This creates the core entity tables for the law firm database

BEGIN;

-- =============================================================================
-- Core Entity Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS entities (
    id              UUID PRIMARY KEY,
    entity_type     TEXT NOT NULL CHECK (entity_type IN ('PHYSICAL_PERSON', 'LEGAL_PERSON')),
    canonical_label TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'ACTIVE',
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_label ON entities(canonical_label);
CREATE INDEX IF NOT EXISTS idx_entities_status ON entities(status);

-- =============================================================================
-- Physical Person (extends entity for people)
-- =============================================================================

CREATE TABLE IF NOT EXISTS physical_persons (
    entity_id           UUID PRIMARY KEY REFERENCES entities(id) ON DELETE CASCADE,
    first_name          TEXT NOT NULL,
    middle_names        TEXT,
    last_name           TEXT NOT NULL,
    date_of_birth       DATE,
    citizenship_country TEXT DEFAULT 'PL',
    is_deceased         BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_physical_persons_name 
    ON physical_persons(last_name, first_name);

-- =============================================================================
-- Legal Person (extends entity for organizations)
-- =============================================================================

CREATE TABLE IF NOT EXISTS legal_persons (
    entity_id           UUID PRIMARY KEY REFERENCES entities(id) ON DELETE CASCADE,
    registered_name     TEXT NOT NULL,
    short_name          TEXT,
    legal_kind          TEXT,  -- SPOLKA_Z_OO, SPOLKA_AKCYJNA, FUNDACJA, etc.
    legal_form_suffix   TEXT,  -- sp. z o.o., S.A., etc.
    country             TEXT DEFAULT 'PL'
);

CREATE INDEX IF NOT EXISTS idx_legal_persons_name 
    ON legal_persons(registered_name);
CREATE INDEX IF NOT EXISTS idx_legal_persons_kind 
    ON legal_persons(legal_kind);

-- =============================================================================
-- Identifiers (PESEL, NIP, KRS, REGON, etc.)
-- =============================================================================

CREATE TABLE IF NOT EXISTS identifiers (
    id                  UUID PRIMARY KEY,
    entity_id           UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    identifier_type     TEXT NOT NULL,  -- PESEL, NIP, KRS, REGON, RFR, OTHER
    identifier_value    TEXT NOT NULL,
    registry_name       TEXT,           -- For OTHER type: name of the registry
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Each identifier type should be unique per entity
    UNIQUE (entity_id, identifier_type, identifier_value)
);

-- Unique constraint: same identifier value + type should not exist twice
CREATE UNIQUE INDEX IF NOT EXISTS idx_identifiers_unique_value 
    ON identifiers(identifier_type, identifier_value) 
    WHERE identifier_type IN ('PESEL', 'NIP', 'KRS', 'REGON', 'RFR');

CREATE INDEX IF NOT EXISTS idx_identifiers_entity ON identifiers(entity_id);
CREATE INDEX IF NOT EXISTS idx_identifiers_type ON identifiers(identifier_type);
CREATE INDEX IF NOT EXISTS idx_identifiers_value ON identifiers(identifier_value);

-- =============================================================================
-- Addresses
-- =============================================================================

CREATE TABLE IF NOT EXISTS addresses (
    id              UUID PRIMARY KEY,
    entity_id       UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    address_type    TEXT NOT NULL DEFAULT 'MAIN',  -- MAIN, CORRESPONDENCE, BUSINESS, etc.
    country         TEXT DEFAULT 'PL',
    voivodeship     TEXT,
    county          TEXT,
    gmina           TEXT,
    city            TEXT,
    postal_code     TEXT,
    post_office     TEXT,
    street          TEXT,
    building_no     TEXT,
    unit_no         TEXT,
    additional_line TEXT,
    teryt_terc      TEXT,
    teryt_simc      TEXT,
    teryt_ulic      TEXT,
    freeform_note   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_addresses_entity ON addresses(entity_id);
CREATE INDEX IF NOT EXISTS idx_addresses_city ON addresses(city);

-- =============================================================================
-- Contacts (email, phone, website, etc.)
-- =============================================================================

CREATE TABLE IF NOT EXISTS contacts (
    id              UUID PRIMARY KEY,
    entity_id       UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    contact_type    TEXT NOT NULL,  -- EMAIL, PHONE, WEBSITE, EPUAP, OTHER
    contact_value   TEXT NOT NULL,
    label           TEXT,           -- Optional label like "work", "personal"
    is_primary      BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_contacts_entity ON contacts(entity_id);
CREATE INDEX IF NOT EXISTS idx_contacts_type ON contacts(contact_type);

-- =============================================================================
-- Grant permissions to app_user (if exists)
-- =============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON entities TO app_user;
        GRANT SELECT, INSERT, UPDATE, DELETE ON physical_persons TO app_user;
        GRANT SELECT, INSERT, UPDATE, DELETE ON legal_persons TO app_user;
        GRANT SELECT, INSERT, UPDATE, DELETE ON identifiers TO app_user;
        GRANT SELECT, INSERT, UPDATE, DELETE ON addresses TO app_user;
        GRANT SELECT, INSERT, UPDATE, DELETE ON contacts TO app_user;
    END IF;
END
$$;

COMMIT;
