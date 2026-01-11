-- Migration: Drop legal_nature column from legal_persons table
-- This field is no longer needed in the application.

BEGIN;

ALTER TABLE legal_persons DROP COLUMN IF EXISTS legal_nature;

-- Remove UI metadata for legal_nature field
DELETE FROM meta.ui_field_metadata WHERE field_key = 'legal.legal_nature';

-- Remove any enum metadata for legal_nature if exists
DELETE FROM meta.ui_enum_metadata WHERE enum_key = 'legal_nature';

COMMIT;
