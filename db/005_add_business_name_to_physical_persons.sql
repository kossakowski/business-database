-- Migration: Add business_name column to physical_persons table
-- Physical persons (sole proprietors) in Poland can have a business name ("firma")
-- registered in CEIDG, e.g. "Jan Kowalski Kancelaria Prawna".
-- This is required for invoicing and registry enrichment.

ALTER TABLE physical_persons
    ADD COLUMN IF NOT EXISTS business_name TEXT;

COMMENT ON COLUMN physical_persons.business_name IS
    'Business name (firma) of a sole proprietor, e.g. from CEIDG. Used for invoicing.';
