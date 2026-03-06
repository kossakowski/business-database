/*
 * Test Suite: Courts Schema & Logic
 * Run with: psql -d lawfirm -f tests/sql/test_courts.sql
 * 
 * Strategy:
 * 1. Verify Structure (Enums, Tables).
 * 2. Verify Data (Pre-populated rows).
 * 3. Verify Constraints (Negative testing).
 */

BEGIN;

-- Helper for assertions
CREATE OR REPLACE PROCEDURE assert(condition boolean, message text) AS $$
BEGIN
    IF NOT condition THEN
        RAISE EXCEPTION 'Assertion Failed: %', message;
    END IF;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
    cnt integer;
    v_id uuid;
    v_parent_id uuid;
BEGIN
    RAISE NOTICE '--- Starting Courts Test Suite ---';

    -- 1. Structural Checks
    -- Check Enums exist
    SELECT count(*) INTO cnt FROM pg_type WHERE typname = 'court_kind' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'courts');
    CALL assert(cnt = 1, 'Enum court_kind should exist');

    -- Check Table exists
    SELECT count(*) INTO cnt FROM pg_tables WHERE schemaname = 'courts' AND tablename = 'courts';
    CALL assert(cnt = 1, 'Table courts.courts should exist');

    -- 2. Data Checks
    -- Check Supreme Court
    SELECT count(*) INTO cnt FROM courts.courts WHERE kind = 'supreme';
    CALL assert(cnt = 1, 'Should have exactly 1 Supreme Court');

    -- Check Appeal Courts
    SELECT count(*) INTO cnt FROM courts.courts WHERE kind = 'appeal';
    CALL assert(cnt = 11, 'Should have 11 Appeal Courts');

    -- Check District Courts
    SELECT count(*) INTO cnt FROM courts.courts WHERE kind = 'district';
    CALL assert(cnt = 47, 'Should have 47 District Courts');

    -- Check Hierarchy (Sample: Warsaw District -> Warsaw Appeal)
    SELECT count(*) INTO cnt 
    FROM courts.courts d
    JOIN courts.courts a ON d.parent_id = a.id
    WHERE d.specific_district = 'sad_okregowy_warszawa' 
      AND a.specific_appeal = 'sad_apelacyjny_warszawa';
    CALL assert(cnt = 1, 'District Warsaw should be child of Appeal Warsaw');

    -- 3. Negative Testing (Constraints & Triggers)
    
    -- A. Insert District without Parent (Should Fail)
    BEGIN
        INSERT INTO courts.courts (kind, specific_district, name) VALUES ('district', 'sad_okregowy_warszawa', 'Invalid');
        RAISE EXCEPTION 'Constraint Check Failed: District must have parent';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'PASS: Detected missing parent for District';
    END;

    -- B. Insert Regional with Wrong Parent Kind (Appeal instead of District)
    BEGIN
        SELECT id INTO v_parent_id FROM courts.courts WHERE kind = 'appeal' LIMIT 1;
        INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name)
        VALUES ('regional', 'sad_rejonowy_warszawa_mokotow', v_parent_id, 'Fail');
        RAISE EXCEPTION 'Trigger Check Failed: Regional parent must be District';
    EXCEPTION WHEN raise_exception THEN
        -- Expected our trigger to raise exception
        IF SQLERRM LIKE '%Regional court must belong to a District court%' THEN
             RAISE NOTICE 'PASS: Detected wrong parent kind for Regional';
        ELSE
             RAISE EXCEPTION 'Unexpected error message: %', SQLERRM;
        END IF;
    END;

    -- C. Insert Regional with Correct Kind but Wrong Specific District
    -- Trying to attach Lublin Regional to Warsaw District
    BEGIN
        SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_warszawa';
        -- 'sad_rejonowy_lublin_zachod' belongs to Lublin District in lookup
        INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name)
        VALUES ('regional', 'sad_rejonowy_lublin_zachod', v_parent_id, 'Fail');
        RAISE EXCEPTION 'Trigger Check Failed: Regional parent must match lookup district';
    EXCEPTION WHEN raise_exception THEN
        IF SQLERRM LIKE '%Regional court parent (%) does not match%' THEN
             RAISE NOTICE 'PASS: Detected mismatch between Parent District and Lookup District';
        ELSE
             RAISE EXCEPTION 'Unexpected error message: %', SQLERRM;
        END IF;
    END;

    -- D. Mixed Kind/Specific Columns (e.g. Kind=Appeal, but specific_district set)
    BEGIN
        INSERT INTO courts.courts (kind, specific_district, name) VALUES ('appeal', 'sad_okregowy_warszawa', 'Fail');
        RAISE EXCEPTION 'Constraint Check Failed: Mismatched Kind/Specific';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'PASS: Detected mismatched Kind/Specific columns';
    END;

    RAISE NOTICE '--- All Tests Passed ---';
END $$;

ROLLBACK; -- Always rollback tests to keep DB clean (or commit if you want to keep test data, but usually rollback)
