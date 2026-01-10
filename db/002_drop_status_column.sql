-- Migration: Remove status column from entities table
-- This removes the status field as it's no longer needed

BEGIN;

-- Drop the index first (required before dropping column)
DROP INDEX IF EXISTS idx_entities_status;

-- Drop the column
ALTER TABLE entities DROP COLUMN IF EXISTS status;

COMMIT;
