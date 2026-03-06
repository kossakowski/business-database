-- Migration: Remove obsolete status column from entities table
-- Date: 2026-02-18
-- Reason: Status column removed in commit 6ea2d37 but still present in schema.sql
--
-- This migration removes the status column and its index from the entities table.
-- The application no longer uses this column for entity lifecycle management.

-- Drop the index first (must be done before dropping the column)
DROP INDEX IF EXISTS idx_entities_status;

-- Drop the status column
ALTER TABLE entities DROP COLUMN IF EXISTS status;
