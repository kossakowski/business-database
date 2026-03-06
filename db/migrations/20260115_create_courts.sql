/*
 * Migration: Create Courts Structure
 * Date: 2026-01-15
 * Description: Establishes the 'courts' schema, enums for court kinds and specific courts, 
 *              and the main 'courts' table with hierarchical constraints.
 * 
 * Sources:
 * - List of Courts of Appeal and District Courts: Wikipedia "Sądownictwo powszechne w Polsce" (Retrieved 2026-01-15)
 * - Hierarchy mapping: https://pl.wikipedia.org/wiki/S%C4%85dy_powszechne (Retrieved 2026-01-15)
 * 
 * Design Decisions:
 * - 'courts' schema used to isolate domain logic.
 * - Enums used for fixed lists (Supreme, Appeal, District).
 * - Lookup table used for Regional courts (300+ items, volatile).
 * - Constraints ensure strict hierarchy (Regional -> District -> Appeal).
 */

BEGIN;

-- 1. Create Schema
CREATE SCHEMA IF NOT EXISTS courts;

-- 2. Create Enums
CREATE TYPE courts.court_kind AS ENUM ('supreme', 'appeal', 'district', 'regional');

-- Supreme Court (Singleton Enum)
CREATE TYPE courts.supreme_court_enum AS ENUM ('sad_najwyzszy');

-- Appeal Courts (11 items)
CREATE TYPE courts.appeal_court_enum AS ENUM (
    'sad_apelacyjny_bialystok',
    'sad_apelacyjny_gdansk',
    'sad_apelacyjny_katowice',
    'sad_apelacyjny_krakow',
    'sad_apelacyjny_lublin',
    'sad_apelacyjny_lodz',
    'sad_apelacyjny_poznan',
    'sad_apelacyjny_rzeszow',
    'sad_apelacyjny_szczecin',
    'sad_apelacyjny_warszawa',
    'sad_apelacyjny_wroclaw'
);

-- District Courts (47 items)
CREATE TYPE courts.district_court_enum AS ENUM (
    -- Białystok
    'sad_okregowy_bialystok', 'sad_okregowy_lomza', 'sad_okregowy_olsztyn', 'sad_okregowy_ostroleka', 'sad_okregowy_suwalki',
    -- Gdańsk
    'sad_okregowy_bydgoszcz', 'sad_okregowy_elblag', 'sad_okregowy_gdansk', 'sad_okregowy_slupsk', 'sad_okregowy_torun', 'sad_okregowy_wloclawek',
    -- Katowice
    'sad_okregowy_bielsko_biala', 'sad_okregowy_czestochowa', 'sad_okregowy_gliwice', 'sad_okregowy_katowice', 'sad_okregowy_rybnik', 'sad_okregowy_sosnowiec',
    -- Kraków
    'sad_okregowy_kielce', 'sad_okregowy_krakow', 'sad_okregowy_nowy_sacz', 'sad_okregowy_tarnow',
    -- Lublin
    'sad_okregowy_lublin', 'sad_okregowy_radom', 'sad_okregowy_siedlce', 'sad_okregowy_zamosc',
    -- Łódź
    'sad_okregowy_kalisz', 'sad_okregowy_lodz', 'sad_okregowy_piotrkow_trybunalski', 'sad_okregowy_plock', 'sad_okregowy_sieradz',
    -- Poznań
    'sad_okregowy_konin', 'sad_okregowy_poznan', 'sad_okregowy_zielona_gora',
    -- Rzeszów
    'sad_okregowy_krosno', 'sad_okregowy_przemysl', 'sad_okregowy_rzeszow', 'sad_okregowy_tarnobrzeg',
    -- Szczecin
    'sad_okregowy_gorzow_wielkopolski', 'sad_okregowy_koszalin', 'sad_okregowy_szczecin',
    -- Warszawa
    'sad_okregowy_warszawa', 'sad_okregowy_warszawa_praga',
    -- Wrocław
    'sad_okregowy_jelenia_gora', 'sad_okregowy_legnica', 'sad_okregowy_opole', 'sad_okregowy_swidnica', 'sad_okregowy_wroclaw'
);

-- 3. Regional Courts Lookup Table
-- Justification: Too many entries for an ENUM, subject to administrative changes.
CREATE TABLE courts.regional_court_lookup (
    code VARCHAR(100) PRIMARY KEY, -- canonical slug e.g. 'sad_rejonowy_lublin_zachod'
    name TEXT NOT NULL,
    district_code courts.district_court_enum NOT NULL, -- Logical link to parent district type
    city TEXT,
    voivodeship TEXT,
    official_url TEXT
);

-- 4. Main Courts Table
CREATE TABLE courts.courts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kind courts.court_kind NOT NULL,
    
    -- Specific Identifiers (One must be set based on kind)
    specific_supreme courts.supreme_court_enum NULL,
    specific_appeal courts.appeal_court_enum NULL,
    specific_district courts.district_court_enum NULL,
    specific_regional_code VARCHAR(100) NULL REFERENCES courts.regional_court_lookup(code),
    
    -- Hierarchy
    parent_id UUID NULL REFERENCES courts.courts(id),
    
    -- Metadata
    name TEXT NOT NULL,
    city TEXT,
    voivodeship TEXT,
    address JSONB DEFAULT '{}'::jsonb,
    contact JSONB DEFAULT '{}'::jsonb,
    active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    -- Constraint: Specific Column matching Kind
    CONSTRAINT check_kind_columns CHECK (
        (kind = 'supreme'  AND specific_supreme IS NOT NULL AND specific_appeal IS NULL AND specific_district IS NULL AND specific_regional_code IS NULL) OR
        (kind = 'appeal'   AND specific_supreme IS NULL AND specific_appeal IS NOT NULL AND specific_district IS NULL AND specific_regional_code IS NULL) OR
        (kind = 'district' AND specific_supreme IS NULL AND specific_appeal IS NULL AND specific_district IS NOT NULL AND specific_regional_code IS NULL) OR
        (kind = 'regional' AND specific_supreme IS NULL AND specific_appeal IS NULL AND specific_district IS NULL AND specific_regional_code IS NOT NULL)
    ),

    -- Constraint: Parent Rules (Basic checks, strict enforcement via Trigger)
    CONSTRAINT check_parent_logic CHECK (
        (kind = 'supreme' AND parent_id IS NULL) OR
        (kind = 'appeal'  AND parent_id IS NULL) OR -- Appeal courts have no structural parent in this graph (Ministry is external)
        (kind = 'district' AND parent_id IS NOT NULL) OR
        (kind = 'regional' AND parent_id IS NOT NULL)
    ),
    
    -- Uniqueness Constraints (Prevent duplicates)
    CONSTRAINT uniq_specific_supreme UNIQUE (specific_supreme),
    CONSTRAINT uniq_specific_appeal UNIQUE (specific_appeal),
    CONSTRAINT uniq_specific_district UNIQUE (specific_district),
    CONSTRAINT uniq_specific_regional UNIQUE (specific_regional_code)
);

-- 5. Trigger for Deep Validation (Parent-Child Relationships)
CREATE OR REPLACE FUNCTION courts.validate_court_hierarchy()
RETURNS TRIGGER AS $$
DECLARE
    parent_kind courts.court_kind;
    parent_appeal courts.appeal_court_enum;
    parent_district courts.district_court_enum;
    
    -- For Regional lookup validation
    expected_district courts.district_court_enum;
BEGIN
    IF NEW.parent_id IS NOT NULL THEN
        SELECT kind, specific_appeal, specific_district 
        INTO parent_kind, parent_appeal, parent_district
        FROM courts.courts WHERE id = NEW.parent_id;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Parent court not found';
        END IF;

        -- District -> Parent must be Appeal
        IF NEW.kind = 'district' THEN
            IF parent_kind != 'appeal' THEN
                RAISE EXCEPTION 'District court must belong to an Appeal court';
            END IF;
            -- (Optional: Validation against hardcoded map if strictly required, but pure FK is usually enough here)
        END IF;

        -- Regional -> Parent must be District
        IF NEW.kind = 'regional' THEN
            IF parent_kind != 'district' THEN
                RAISE EXCEPTION 'Regional court must belong to a District court';
            END IF;
            
            -- Verify consistency with lookup table
            SELECT district_code INTO expected_district 
            FROM courts.regional_court_lookup 
            WHERE code = NEW.specific_regional_code;
            
            IF expected_district IS DISTINCT FROM parent_district THEN
                 RAISE EXCEPTION 'Regional court parent (%) does not match the district defined in lookup table (%)', parent_district, expected_district;
            END IF;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_court_hierarchy
BEFORE INSERT OR UPDATE ON courts.courts
FOR EACH ROW EXECUTE FUNCTION courts.validate_court_hierarchy();


-- 6. Data Population

-- A. Supreme Court
INSERT INTO courts.courts (kind, specific_supreme, name, city)
VALUES ('supreme', 'sad_najwyzszy', 'Sąd Najwyższy', 'Warszawa');

-- B. Appeal Courts & District Courts
DO $$
DECLARE
    v_appeal_id UUID;
BEGIN
    -- 1. Białystok
    INSERT INTO courts.courts (kind, specific_appeal, name, city) VALUES ('appeal', 'sad_apelacyjny_bialystok', 'Sąd Apelacyjny w Białymstoku', 'Białystok') RETURNING id INTO v_appeal_id;
    INSERT INTO courts.courts (kind, specific_district, name, city, parent_id) VALUES 
        ('district', 'sad_okregowy_bialystok', 'Sąd Okręgowy w Białymstoku', 'Białystok', v_appeal_id),
        ('district', 'sad_okregowy_lomza', 'Sąd Okręgowy w Łomży', 'Łomża', v_appeal_id),
        ('district', 'sad_okregowy_olsztyn', 'Sąd Okręgowy w Olsztynie', 'Olsztyn', v_appeal_id),
        ('district', 'sad_okregowy_ostroleka', 'Sąd Okręgowy w Ostrołęce', 'Ostrołęka', v_appeal_id),
        ('district', 'sad_okregowy_suwalki', 'Sąd Okręgowy w Suwałkach', 'Suwałki', v_appeal_id);

    -- 2. Gdańsk
    INSERT INTO courts.courts (kind, specific_appeal, name, city) VALUES ('appeal', 'sad_apelacyjny_gdansk', 'Sąd Apelacyjny w Gdańsku', 'Gdańsk') RETURNING id INTO v_appeal_id;
    INSERT INTO courts.courts (kind, specific_district, name, city, parent_id) VALUES 
        ('district', 'sad_okregowy_bydgoszcz', 'Sąd Okręgowy w Bydgoszczy', 'Bydgoszcz', v_appeal_id),
        ('district', 'sad_okregowy_elblag', 'Sąd Okręgowy w Elblągu', 'Elbląg', v_appeal_id),
        ('district', 'sad_okregowy_gdansk', 'Sąd Okręgowy w Gdańsku', 'Gdańsk', v_appeal_id),
        ('district', 'sad_okregowy_slupsk', 'Sąd Okręgowy w Słupsku', 'Słupsk', v_appeal_id),
        ('district', 'sad_okregowy_torun', 'Sąd Okręgowy w Toruniu', 'Toruń', v_appeal_id),
        ('district', 'sad_okregowy_wloclawek', 'Sąd Okręgowy we Włocławku', 'Włocławek', v_appeal_id);

    -- 3. Katowice
    INSERT INTO courts.courts (kind, specific_appeal, name, city) VALUES ('appeal', 'sad_apelacyjny_katowice', 'Sąd Apelacyjny w Katowicach', 'Katowice') RETURNING id INTO v_appeal_id;
    INSERT INTO courts.courts (kind, specific_district, name, city, parent_id) VALUES 
        ('district', 'sad_okregowy_bielsko_biala', 'Sąd Okręgowy w Bielsku-Białej', 'Bielsko-Biała', v_appeal_id),
        ('district', 'sad_okregowy_czestochowa', 'Sąd Okręgowy w Częstochowie', 'Częstochowa', v_appeal_id),
        ('district', 'sad_okregowy_gliwice', 'Sąd Okręgowy w Gliwicach', 'Gliwice', v_appeal_id),
        ('district', 'sad_okregowy_katowice', 'Sąd Okręgowy w Katowicach', 'Katowice', v_appeal_id),
        ('district', 'sad_okregowy_rybnik', 'Sąd Okręgowy w Rybniku', 'Rybnik', v_appeal_id),
        ('district', 'sad_okregowy_sosnowiec', 'Sąd Okręgowy w Sosnowcu', 'Sosnowiec', v_appeal_id);

    -- 4. Kraków
    INSERT INTO courts.courts (kind, specific_appeal, name, city) VALUES ('appeal', 'sad_apelacyjny_krakow', 'Sąd Apelacyjny w Krakowie', 'Kraków') RETURNING id INTO v_appeal_id;
    INSERT INTO courts.courts (kind, specific_district, name, city, parent_id) VALUES 
        ('district', 'sad_okregowy_kielce', 'Sąd Okręgowy w Kielcach', 'Kielce', v_appeal_id),
        ('district', 'sad_okregowy_krakow', 'Sąd Okręgowy w Krakowie', 'Kraków', v_appeal_id),
        ('district', 'sad_okregowy_nowy_sacz', 'Sąd Okręgowy w Nowym Sączu', 'Nowy Sącz', v_appeal_id),
        ('district', 'sad_okregowy_tarnow', 'Sąd Okręgowy w Tarnowie', 'Tarnów', v_appeal_id);

    -- 5. Lublin
    INSERT INTO courts.courts (kind, specific_appeal, name, city) VALUES ('appeal', 'sad_apelacyjny_lublin', 'Sąd Apelacyjny w Lublinie', 'Lublin') RETURNING id INTO v_appeal_id;
    INSERT INTO courts.courts (kind, specific_district, name, city, parent_id) VALUES 
        ('district', 'sad_okregowy_lublin', 'Sąd Okręgowy w Lublinie', 'Lublin', v_appeal_id),
        ('district', 'sad_okregowy_radom', 'Sąd Okręgowy w Radomiu', 'Radom', v_appeal_id),
        ('district', 'sad_okregowy_siedlce', 'Sąd Okręgowy w Siedlcach', 'Siedlce', v_appeal_id),
        ('district', 'sad_okregowy_zamosc', 'Sąd Okręgowy w Zamościu', 'Zamość', v_appeal_id);

    -- 6. Łódź
    INSERT INTO courts.courts (kind, specific_appeal, name, city) VALUES ('appeal', 'sad_apelacyjny_lodz', 'Sąd Apelacyjny w Łodzi', 'Łódź') RETURNING id INTO v_appeal_id;
    INSERT INTO courts.courts (kind, specific_district, name, city, parent_id) VALUES 
        ('district', 'sad_okregowy_kalisz', 'Sąd Okręgowy w Kaliszu', 'Kalisz', v_appeal_id),
        ('district', 'sad_okregowy_lodz', 'Sąd Okręgowy w Łodzi', 'Łódź', v_appeal_id),
        ('district', 'sad_okregowy_piotrkow_trybunalski', 'Sąd Okręgowy w Piotrkowie Trybunalskim', 'Piotrków Trybunalski', v_appeal_id),
        ('district', 'sad_okregowy_plock', 'Sąd Okręgowy w Płocku', 'Płock', v_appeal_id),
        ('district', 'sad_okregowy_sieradz', 'Sąd Okręgowy w Sieradzu', 'Sieradz', v_appeal_id);

    -- 7. Poznań
    INSERT INTO courts.courts (kind, specific_appeal, name, city) VALUES ('appeal', 'sad_apelacyjny_poznan', 'Sąd Apelacyjny w Poznaniu', 'Poznań') RETURNING id INTO v_appeal_id;
    INSERT INTO courts.courts (kind, specific_district, name, city, parent_id) VALUES 
        ('district', 'sad_okregowy_konin', 'Sąd Okręgowy w Koninie', 'Konin', v_appeal_id),
        ('district', 'sad_okregowy_poznan', 'Sąd Okręgowy w Poznaniu', 'Poznań', v_appeal_id),
        ('district', 'sad_okregowy_zielona_gora', 'Sąd Okręgowy w Zielonej Górze', 'Zielona Góra', v_appeal_id);

    -- 8. Rzeszów
    INSERT INTO courts.courts (kind, specific_appeal, name, city) VALUES ('appeal', 'sad_apelacyjny_rzeszow', 'Sąd Apelacyjny w Rzeszowie', 'Rzeszów') RETURNING id INTO v_appeal_id;
    INSERT INTO courts.courts (kind, specific_district, name, city, parent_id) VALUES 
        ('district', 'sad_okregowy_krosno', 'Sąd Okręgowy w Krośnie', 'Krosno', v_appeal_id),
        ('district', 'sad_okregowy_przemysl', 'Sąd Okręgowy w Przemyślu', 'Przemyśl', v_appeal_id),
        ('district', 'sad_okregowy_rzeszow', 'Sąd Okręgowy w Rzeszowie', 'Rzeszów', v_appeal_id),
        ('district', 'sad_okregowy_tarnobrzeg', 'Sąd Okręgowy w Tarnobrzegu', 'Tarnobrzeg', v_appeal_id);

    -- 9. Szczecin
    INSERT INTO courts.courts (kind, specific_appeal, name, city) VALUES ('appeal', 'sad_apelacyjny_szczecin', 'Sąd Apelacyjny w Szczecinie', 'Szczecin') RETURNING id INTO v_appeal_id;
    INSERT INTO courts.courts (kind, specific_district, name, city, parent_id) VALUES 
        ('district', 'sad_okregowy_gorzow_wielkopolski', 'Sąd Okręgowy w Gorzowie Wielkopolskim', 'Gorzów Wielkopolski', v_appeal_id),
        ('district', 'sad_okregowy_koszalin', 'Sąd Okręgowy w Koszalinie', 'Koszalin', v_appeal_id),
        ('district', 'sad_okregowy_szczecin', 'Sąd Okręgowy w Szczecinie', 'Szczecin', v_appeal_id);

    -- 10. Warszawa
    INSERT INTO courts.courts (kind, specific_appeal, name, city) VALUES ('appeal', 'sad_apelacyjny_warszawa', 'Sąd Apelacyjny w Warszawie', 'Warszawa') RETURNING id INTO v_appeal_id;
    INSERT INTO courts.courts (kind, specific_district, name, city, parent_id) VALUES 
        ('district', 'sad_okregowy_warszawa', 'Sąd Okręgowy w Warszawie', 'Warszawa', v_appeal_id),
        ('district', 'sad_okregowy_warszawa_praga', 'Sąd Okręgowy Warszawa-Praga', 'Warszawa', v_appeal_id);

    -- 11. Wrocław
    INSERT INTO courts.courts (kind, specific_appeal, name, city) VALUES ('appeal', 'sad_apelacyjny_wroclaw', 'Sąd Apelacyjny we Wrocławiu', 'Wrocław') RETURNING id INTO v_appeal_id;
    INSERT INTO courts.courts (kind, specific_district, name, city, parent_id) VALUES 
        ('district', 'sad_okregowy_jelenia_gora', 'Sąd Okręgowy w Jeleniej Górze', 'Jelenia Góra', v_appeal_id),
        ('district', 'sad_okregowy_legnica', 'Sąd Okręgowy w Legnicy', 'Legnica', v_appeal_id),
        ('district', 'sad_okregowy_opole', 'Sąd Okręgowy w Opolu', 'Opole', v_appeal_id),
        ('district', 'sad_okregowy_swidnica', 'Sąd Okręgowy w Świdnicy', 'Świdnica', v_appeal_id),
        ('district', 'sad_okregowy_wroclaw', 'Sąd Okręgowy we Wrocławiu', 'Wrocław', v_appeal_id);
END $$;

-- C. Sample Regional Court (Demonstrating usage of Lookup + Main table)
-- 1. Populate Lookup
INSERT INTO courts.regional_court_lookup (code, name, district_code, city) VALUES
('sad_rejonowy_warszawa_mokotow', 'Sąd Rejonowy dla Warszawy-Mokotowa', 'sad_okregowy_warszawa', 'Warszawa'),
('sad_rejonowy_lublin_zachod', 'Sąd Rejonowy Lublin-Zachód w Lublinie', 'sad_okregowy_lublin', 'Lublin');

-- 2. Populate Main Table (linking to lookup)
-- Note: Must find the UUID of the parent district to insert valid rows.
DO $$
DECLARE
    parent_waw_id UUID;
    parent_lub_id UUID;
BEGIN
    SELECT id INTO parent_waw_id FROM courts.courts WHERE specific_district = 'sad_okregowy_warszawa';
    SELECT id INTO parent_lub_id FROM courts.courts WHERE specific_district = 'sad_okregowy_lublin';

    INSERT INTO courts.courts (kind, specific_regional_code, parent_id, name, city)
    VALUES 
    ('regional', 'sad_rejonowy_warszawa_mokotow', parent_waw_id, 'Sąd Rejonowy dla Warszawy-Mokotowa', 'Warszawa'),
    ('regional', 'sad_rejonowy_lublin_zachod', parent_lub_id, 'Sąd Rejonowy Lublin-Zachód w Lublinie', 'Lublin');
END $$;

COMMIT;
