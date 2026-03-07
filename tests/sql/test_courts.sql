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

    -- Check Regional Courts
    SELECT count(*) INTO cnt FROM courts.courts WHERE kind = 'regional';
    CALL assert(cnt = 319, 'Should have 319 Regional Courts');

    -- Check Regional Court Lookup
    SELECT count(*) INTO cnt FROM courts.regional_court_lookup;
    CALL assert(cnt = 319, 'Lookup table should have 319 entries');

    -- Check Total Courts (1 + 11 + 47 + 319 = 378)
    SELECT count(*) INTO cnt FROM courts.courts;
    CALL assert(cnt = 378, 'Should have 378 total courts (1+11+47+319)');

    -- Check All 47 Districts Have At Least 1 Regional Court
    SELECT count(DISTINCT parent_id) INTO cnt FROM courts.courts WHERE kind = 'regional';
    CALL assert(cnt = 47, 'All 47 districts should have regional courts');

    -- Check Regional Hierarchy (Sample: Białystok Regional -> Białystok District)
    SELECT count(*) INTO cnt
    FROM courts.courts r
    JOIN courts.courts d ON r.parent_id = d.id
    WHERE r.specific_regional_code = 'sad_rejonowy_bialymstoku'
      AND d.specific_district = 'sad_okregowy_bialystok';
    CALL assert(cnt = 1, 'SR Białystok should be child of SO Białystok');

    -- Check Rybnik district reassignment (newer district, est. 2020)
    SELECT count(*) INTO cnt
    FROM courts.courts r
    JOIN courts.courts d ON r.parent_id = d.id
    WHERE r.specific_regional_code = 'sad_rejonowy_rybniku'
      AND d.specific_district = 'sad_okregowy_rybnik';
    CALL assert(cnt = 1, 'SR Rybnik should be child of SO Rybnik');

    -- Check Sosnowiec district reassignment (newer district, est. 2022)
    SELECT count(*) INTO cnt
    FROM courts.courts r
    JOIN courts.courts d ON r.parent_id = d.id
    WHERE r.specific_regional_code = 'sad_rejonowy_sosnowcu'
      AND d.specific_district = 'sad_okregowy_sosnowiec';
    CALL assert(cnt = 1, 'SR Sosnowiec should be child of SO Sosnowiec');

    -- Check No Orphan Regional Courts (all have valid district parent)
    SELECT count(*) INTO cnt
    FROM courts.courts r
    LEFT JOIN courts.courts d ON r.parent_id = d.id
    WHERE r.kind = 'regional' AND (d.id IS NULL OR d.kind != 'district');
    CALL assert(cnt = 0, 'No orphan regional courts');

    -- 3. Negative Testing (Constraints & Triggers)

    -- A. Insert District without Parent (Should Fail)
    BEGIN
        INSERT INTO courts.courts (kind, specific_district, name) VALUES ('district', 'sad_okregowy_warszawa', 'Invalid');
        RAISE EXCEPTION 'Constraint Check Failed: District must have parent';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'PASS: Detected missing parent for District';
    END;

    -- B. Insert Regional with Wrong Parent Kind (Appeal instead of District)
    -- Use a test code not in the lookup table
    BEGIN
        SELECT id INTO v_parent_id FROM courts.courts WHERE kind = 'appeal' LIMIT 1;
        INSERT INTO courts.regional_court_lookup (code, name, district_code, city)
        VALUES ('sad_rejonowy_test_b', 'Test Court B', 'sad_okregowy_warszawa', 'Test');
        INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name)
        VALUES ('regional', 'sad_rejonowy_test_b', v_parent_id, 'Fail');
        RAISE EXCEPTION 'Trigger Check Failed: Regional parent must be District';
    EXCEPTION WHEN raise_exception THEN
        IF SQLERRM LIKE '%Regional court must belong to a District court%' THEN
             RAISE NOTICE 'PASS: Detected wrong parent kind for Regional';
        ELSE
             RAISE EXCEPTION 'Unexpected error message: %', SQLERRM;
        END IF;
    END;

    -- C. Insert Regional with Correct Kind but Wrong Specific District
    -- Use a test code assigned to Lublin but try to attach to Warsaw
    BEGIN
        SELECT id INTO v_parent_id FROM courts.courts WHERE specific_district = 'sad_okregowy_warszawa';
        INSERT INTO courts.regional_court_lookup (code, name, district_code, city)
        VALUES ('sad_rejonowy_test_c', 'Test Court C', 'sad_okregowy_lublin', 'Test');
        INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name)
        VALUES ('regional', 'sad_rejonowy_test_c', v_parent_id, 'Fail');
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
