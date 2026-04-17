--
-- PostgreSQL database dump
--

\restrict iFQOUzEy7TJKPaMkVc6CjAv7UenR2eRY2bU6KMjvqBU2icSSeqYi4pty1XbpsM4

-- Dumped from database version 16.11 (Debian 16.11-1.pgdg13+1)
-- Dumped by pg_dump version 16.13 (Ubuntu 16.13-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: courts; Type: SCHEMA; Schema: -; Owner: admin
--

CREATE SCHEMA courts;


ALTER SCHEMA courts OWNER TO admin;

--
-- Name: meta; Type: SCHEMA; Schema: -; Owner: admin
--

CREATE SCHEMA meta;


ALTER SCHEMA meta OWNER TO admin;

--
-- Name: appeal_court_enum; Type: TYPE; Schema: courts; Owner: admin
--

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


ALTER TYPE courts.appeal_court_enum OWNER TO admin;

--
-- Name: court_kind; Type: TYPE; Schema: courts; Owner: admin
--

CREATE TYPE courts.court_kind AS ENUM (
    'supreme',
    'appeal',
    'district',
    'regional'
);


ALTER TYPE courts.court_kind OWNER TO admin;

--
-- Name: district_court_enum; Type: TYPE; Schema: courts; Owner: admin
--

CREATE TYPE courts.district_court_enum AS ENUM (
    'sad_okregowy_bialystok',
    'sad_okregowy_lomza',
    'sad_okregowy_olsztyn',
    'sad_okregowy_ostroleka',
    'sad_okregowy_suwalki',
    'sad_okregowy_bydgoszcz',
    'sad_okregowy_elblag',
    'sad_okregowy_gdansk',
    'sad_okregowy_slupsk',
    'sad_okregowy_torun',
    'sad_okregowy_wloclawek',
    'sad_okregowy_bielsko_biala',
    'sad_okregowy_czestochowa',
    'sad_okregowy_gliwice',
    'sad_okregowy_katowice',
    'sad_okregowy_rybnik',
    'sad_okregowy_sosnowiec',
    'sad_okregowy_kielce',
    'sad_okregowy_krakow',
    'sad_okregowy_nowy_sacz',
    'sad_okregowy_tarnow',
    'sad_okregowy_lublin',
    'sad_okregowy_radom',
    'sad_okregowy_siedlce',
    'sad_okregowy_zamosc',
    'sad_okregowy_kalisz',
    'sad_okregowy_lodz',
    'sad_okregowy_piotrkow_trybunalski',
    'sad_okregowy_plock',
    'sad_okregowy_sieradz',
    'sad_okregowy_konin',
    'sad_okregowy_poznan',
    'sad_okregowy_zielona_gora',
    'sad_okregowy_krosno',
    'sad_okregowy_przemysl',
    'sad_okregowy_rzeszow',
    'sad_okregowy_tarnobrzeg',
    'sad_okregowy_gorzow_wielkopolski',
    'sad_okregowy_koszalin',
    'sad_okregowy_szczecin',
    'sad_okregowy_warszawa',
    'sad_okregowy_warszawa_praga',
    'sad_okregowy_jelenia_gora',
    'sad_okregowy_legnica',
    'sad_okregowy_opole',
    'sad_okregowy_swidnica',
    'sad_okregowy_wroclaw'
);


ALTER TYPE courts.district_court_enum OWNER TO admin;

--
-- Name: supreme_court_enum; Type: TYPE; Schema: courts; Owner: admin
--

CREATE TYPE courts.supreme_court_enum AS ENUM (
    'sad_najwyzszy'
);


ALTER TYPE courts.supreme_court_enum OWNER TO admin;

--
-- Name: validate_court_hierarchy(); Type: FUNCTION; Schema: courts; Owner: admin
--

CREATE FUNCTION courts.validate_court_hierarchy() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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
$$;


ALTER FUNCTION courts.validate_court_hierarchy() OWNER TO admin;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: courts; Type: TABLE; Schema: courts; Owner: admin
--

CREATE TABLE courts.courts (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    kind courts.court_kind NOT NULL,
    specific_supreme courts.supreme_court_enum,
    specific_appeal courts.appeal_court_enum,
    specific_district courts.district_court_enum,
    specific_regional_code character varying(100),
    parent_id uuid,
    name text NOT NULL,
    city text,
    voivodeship text,
    address jsonb DEFAULT '{}'::jsonb,
    contact jsonb DEFAULT '{}'::jsonb,
    active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT check_kind_columns CHECK ((((kind = 'supreme'::courts.court_kind) AND (specific_supreme IS NOT NULL) AND (specific_appeal IS NULL) AND (specific_district IS NULL) AND (specific_regional_code IS NULL)) OR ((kind = 'appeal'::courts.court_kind) AND (specific_supreme IS NULL) AND (specific_appeal IS NOT NULL) AND (specific_district IS NULL) AND (specific_regional_code IS NULL)) OR ((kind = 'district'::courts.court_kind) AND (specific_supreme IS NULL) AND (specific_appeal IS NULL) AND (specific_district IS NOT NULL) AND (specific_regional_code IS NULL)) OR ((kind = 'regional'::courts.court_kind) AND (specific_supreme IS NULL) AND (specific_appeal IS NULL) AND (specific_district IS NULL) AND (specific_regional_code IS NOT NULL)))),
    CONSTRAINT check_parent_logic CHECK ((((kind = 'supreme'::courts.court_kind) AND (parent_id IS NULL)) OR ((kind = 'appeal'::courts.court_kind) AND (parent_id IS NULL)) OR ((kind = 'district'::courts.court_kind) AND (parent_id IS NOT NULL)) OR ((kind = 'regional'::courts.court_kind) AND (parent_id IS NOT NULL))))
);


ALTER TABLE courts.courts OWNER TO admin;

--
-- Name: regional_court_lookup; Type: TABLE; Schema: courts; Owner: admin
--

CREATE TABLE courts.regional_court_lookup (
    code character varying(100) NOT NULL,
    name text NOT NULL,
    district_code courts.district_court_enum NOT NULL,
    city text,
    voivodeship text,
    official_url text
);


ALTER TABLE courts.regional_court_lookup OWNER TO admin;

--
-- Name: ui_enum_metadata; Type: TABLE; Schema: meta; Owner: admin
--

CREATE TABLE meta.ui_enum_metadata (
    enum_key text NOT NULL,
    enum_value text NOT NULL,
    label_pl text NOT NULL,
    tooltip_pl text,
    suffix_default text,
    is_suffix_applicable boolean,
    display_order integer DEFAULT 1000 NOT NULL
);


ALTER TABLE meta.ui_enum_metadata OWNER TO admin;

--
-- Name: ui_field_metadata; Type: TABLE; Schema: meta; Owner: admin
--

CREATE TABLE meta.ui_field_metadata (
    field_key text NOT NULL,
    label_pl text NOT NULL,
    tooltip_pl text,
    placeholder text,
    example_value text,
    input_type text DEFAULT 'text'::text NOT NULL,
    privacy_level text DEFAULT 'INTERNAL'::text NOT NULL,
    source_hint text,
    validation_hint text,
    validation_rule jsonb,
    display_group text DEFAULT 'General'::text NOT NULL,
    display_order integer DEFAULT 1000 NOT NULL,
    is_user_editable boolean DEFAULT true NOT NULL
);


ALTER TABLE meta.ui_field_metadata OWNER TO admin;

--
-- Name: addresses; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.addresses (
    id uuid NOT NULL,
    entity_id uuid NOT NULL,
    address_type text DEFAULT 'MAIN'::text NOT NULL,
    country text DEFAULT 'PL'::text,
    voivodeship text,
    county text,
    gmina text,
    city text,
    postal_code text,
    post_office text,
    street text,
    building_no text,
    unit_no text,
    additional_line text,
    teryt_terc text,
    teryt_simc text,
    teryt_ulic text,
    freeform_note text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.addresses OWNER TO admin;

--
-- Name: affiliations; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.affiliations (
    id uuid NOT NULL,
    entity_id uuid NOT NULL,
    affiliated_entity_id uuid,
    affiliation_type text NOT NULL,
    role text,
    start_date date,
    end_date date,
    source_system text,
    source_snapshot_id uuid,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.affiliations OWNER TO admin;

--
-- Name: contacts; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.contacts (
    id uuid NOT NULL,
    entity_id uuid NOT NULL,
    contact_type text NOT NULL,
    contact_value text NOT NULL,
    label text,
    is_primary boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.contacts OWNER TO admin;

--
-- Name: entities; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.entities (
    id uuid NOT NULL,
    entity_type text NOT NULL,
    canonical_label text NOT NULL,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT entities_entity_type_check CHECK ((entity_type = ANY (ARRAY['PHYSICAL_PERSON'::text, 'LEGAL_PERSON'::text])))
);


ALTER TABLE public.entities OWNER TO admin;

--
-- Name: identifiers; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.identifiers (
    id uuid NOT NULL,
    entity_id uuid NOT NULL,
    identifier_type text NOT NULL,
    identifier_value text NOT NULL,
    registry_name text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.identifiers OWNER TO admin;

--
-- Name: invoices; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.invoices (
    id integer NOT NULL,
    invoice_number character varying(50) NOT NULL,
    date date NOT NULL,
    client_name character varying(255) NOT NULL,
    client_nip character varying(50),
    items jsonb NOT NULL,
    grand_total numeric(10,2) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    client_street character varying(255),
    client_building_no character varying(50),
    client_unit_no character varying(50),
    client_postal_code character varying(20),
    client_city character varying(255),
    due_date character varying,
    payment_method character varying,
    seller_name character varying,
    seller_address character varying,
    seller_nip character varying,
    seller_email character varying,
    seller_phone character varying,
    seller_bank_account character varying,
    seller_bank_name character varying,
    vat_rate numeric
);


ALTER TABLE public.invoices OWNER TO admin;

--
-- Name: invoices_id_seq; Type: SEQUENCE; Schema: public; Owner: admin
--

CREATE SEQUENCE public.invoices_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.invoices_id_seq OWNER TO admin;

--
-- Name: invoices_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: admin
--

ALTER SEQUENCE public.invoices_id_seq OWNED BY public.invoices.id;


--
-- Name: legal_persons; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.legal_persons (
    entity_id uuid NOT NULL,
    registered_name text NOT NULL,
    short_name text,
    legal_kind text,
    legal_form_suffix text,
    country text DEFAULT 'PL'::text
);


ALTER TABLE public.legal_persons OWNER TO admin;

--
-- Name: physical_persons; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.physical_persons (
    entity_id uuid NOT NULL,
    first_name text NOT NULL,
    middle_names text,
    last_name text NOT NULL,
    date_of_birth date,
    citizenship_country text DEFAULT 'PL'::text,
    is_deceased boolean DEFAULT false NOT NULL,
    business_name text
);


ALTER TABLE public.physical_persons OWNER TO admin;

--
-- Name: registry_profiles_ceidg; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.registry_profiles_ceidg (
    entity_id uuid NOT NULL,
    ceidg_id text,
    nip text,
    regon text,
    first_name text,
    last_name text,
    business_name text,
    status text,
    start_date date,
    end_date date,
    pkd_main text,
    last_snapshot_id uuid,
    last_fetched_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.registry_profiles_ceidg OWNER TO admin;

--
-- Name: registry_profiles_krs; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.registry_profiles_krs (
    entity_id uuid NOT NULL,
    krs text,
    nip text,
    regon text,
    official_name text,
    short_name text,
    legal_form text,
    registry_status text,
    registration_date date,
    share_capital text,
    pkd_main text,
    last_snapshot_id uuid,
    last_fetched_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.registry_profiles_krs OWNER TO admin;

--
-- Name: registry_snapshots; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.registry_snapshots (
    id uuid NOT NULL,
    entity_id uuid,
    source_system text NOT NULL,
    external_id text NOT NULL,
    fetched_at timestamp with time zone DEFAULT now() NOT NULL,
    effective_date date,
    payload_format text DEFAULT 'json'::text NOT NULL,
    payload jsonb,
    payload_raw text,
    payload_hash text,
    fetched_by text,
    purpose_ref text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.registry_snapshots OWNER TO admin;

--
-- Name: invoices id; Type: DEFAULT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.invoices ALTER COLUMN id SET DEFAULT nextval('public.invoices_id_seq'::regclass);


--
-- Name: courts courts_pkey; Type: CONSTRAINT; Schema: courts; Owner: admin
--

ALTER TABLE ONLY courts.courts
    ADD CONSTRAINT courts_pkey PRIMARY KEY (id);


--
-- Name: regional_court_lookup regional_court_lookup_pkey; Type: CONSTRAINT; Schema: courts; Owner: admin
--

ALTER TABLE ONLY courts.regional_court_lookup
    ADD CONSTRAINT regional_court_lookup_pkey PRIMARY KEY (code);


--
-- Name: courts uniq_specific_appeal; Type: CONSTRAINT; Schema: courts; Owner: admin
--

ALTER TABLE ONLY courts.courts
    ADD CONSTRAINT uniq_specific_appeal UNIQUE (specific_appeal);


--
-- Name: courts uniq_specific_district; Type: CONSTRAINT; Schema: courts; Owner: admin
--

ALTER TABLE ONLY courts.courts
    ADD CONSTRAINT uniq_specific_district UNIQUE (specific_district);


--
-- Name: courts uniq_specific_regional; Type: CONSTRAINT; Schema: courts; Owner: admin
--

ALTER TABLE ONLY courts.courts
    ADD CONSTRAINT uniq_specific_regional UNIQUE (specific_regional_code);


--
-- Name: courts uniq_specific_supreme; Type: CONSTRAINT; Schema: courts; Owner: admin
--

ALTER TABLE ONLY courts.courts
    ADD CONSTRAINT uniq_specific_supreme UNIQUE (specific_supreme);


--
-- Name: ui_enum_metadata ui_enum_metadata_pkey; Type: CONSTRAINT; Schema: meta; Owner: admin
--

ALTER TABLE ONLY meta.ui_enum_metadata
    ADD CONSTRAINT ui_enum_metadata_pkey PRIMARY KEY (enum_key, enum_value);


--
-- Name: ui_field_metadata ui_field_metadata_pkey; Type: CONSTRAINT; Schema: meta; Owner: admin
--

ALTER TABLE ONLY meta.ui_field_metadata
    ADD CONSTRAINT ui_field_metadata_pkey PRIMARY KEY (field_key);


--
-- Name: addresses addresses_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.addresses
    ADD CONSTRAINT addresses_pkey PRIMARY KEY (id);


--
-- Name: affiliations affiliations_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.affiliations
    ADD CONSTRAINT affiliations_pkey PRIMARY KEY (id);


--
-- Name: contacts contacts_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_pkey PRIMARY KEY (id);


--
-- Name: entities entities_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.entities
    ADD CONSTRAINT entities_pkey PRIMARY KEY (id);


--
-- Name: identifiers identifiers_entity_id_identifier_type_identifier_value_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.identifiers
    ADD CONSTRAINT identifiers_entity_id_identifier_type_identifier_value_key UNIQUE (entity_id, identifier_type, identifier_value);


--
-- Name: identifiers identifiers_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.identifiers
    ADD CONSTRAINT identifiers_pkey PRIMARY KEY (id);


--
-- Name: invoices invoices_invoice_number_key; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_invoice_number_key UNIQUE (invoice_number);


--
-- Name: invoices invoices_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_pkey PRIMARY KEY (id);


--
-- Name: legal_persons legal_persons_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.legal_persons
    ADD CONSTRAINT legal_persons_pkey PRIMARY KEY (entity_id);


--
-- Name: physical_persons physical_persons_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.physical_persons
    ADD CONSTRAINT physical_persons_pkey PRIMARY KEY (entity_id);


--
-- Name: registry_profiles_ceidg registry_profiles_ceidg_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.registry_profiles_ceidg
    ADD CONSTRAINT registry_profiles_ceidg_pkey PRIMARY KEY (entity_id);


--
-- Name: registry_profiles_krs registry_profiles_krs_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.registry_profiles_krs
    ADD CONSTRAINT registry_profiles_krs_pkey PRIMARY KEY (entity_id);


--
-- Name: registry_snapshots registry_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.registry_snapshots
    ADD CONSTRAINT registry_snapshots_pkey PRIMARY KEY (id);


--
-- Name: idx_addresses_city; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_addresses_city ON public.addresses USING btree (city);


--
-- Name: idx_addresses_entity; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_addresses_entity ON public.addresses USING btree (entity_id);


--
-- Name: idx_affiliations_affiliated; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_affiliations_affiliated ON public.affiliations USING btree (affiliated_entity_id);


--
-- Name: idx_affiliations_entity; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_affiliations_entity ON public.affiliations USING btree (entity_id);


--
-- Name: idx_contacts_entity; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_contacts_entity ON public.contacts USING btree (entity_id);


--
-- Name: idx_contacts_type; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_contacts_type ON public.contacts USING btree (contact_type);


--
-- Name: idx_entities_label; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_entities_label ON public.entities USING btree (canonical_label);


--
-- Name: idx_entities_type; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_entities_type ON public.entities USING btree (entity_type);


--
-- Name: idx_identifiers_entity; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_identifiers_entity ON public.identifiers USING btree (entity_id);


--
-- Name: idx_identifiers_type; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_identifiers_type ON public.identifiers USING btree (identifier_type);


--
-- Name: idx_identifiers_unique_value; Type: INDEX; Schema: public; Owner: admin
--

CREATE UNIQUE INDEX idx_identifiers_unique_value ON public.identifiers USING btree (identifier_type, identifier_value) WHERE (identifier_type = ANY (ARRAY['PESEL'::text, 'NIP'::text, 'KRS'::text, 'REGON'::text, 'RFR'::text]));


--
-- Name: idx_identifiers_value; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_identifiers_value ON public.identifiers USING btree (identifier_value);


--
-- Name: idx_legal_persons_kind; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_legal_persons_kind ON public.legal_persons USING btree (legal_kind);


--
-- Name: idx_legal_persons_name; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_legal_persons_name ON public.legal_persons USING btree (registered_name);


--
-- Name: idx_physical_persons_name; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_physical_persons_name ON public.physical_persons USING btree (last_name, first_name);


--
-- Name: idx_registry_snapshots_entity; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_registry_snapshots_entity ON public.registry_snapshots USING btree (entity_id);


--
-- Name: idx_registry_snapshots_fetched; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_registry_snapshots_fetched ON public.registry_snapshots USING btree (fetched_at DESC);


--
-- Name: idx_registry_snapshots_source; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_registry_snapshots_source ON public.registry_snapshots USING btree (source_system, external_id);


--
-- Name: courts trg_validate_court_hierarchy; Type: TRIGGER; Schema: courts; Owner: admin
--

CREATE TRIGGER trg_validate_court_hierarchy BEFORE INSERT OR UPDATE ON courts.courts FOR EACH ROW EXECUTE FUNCTION courts.validate_court_hierarchy();


--
-- Name: courts courts_parent_id_fkey; Type: FK CONSTRAINT; Schema: courts; Owner: admin
--

ALTER TABLE ONLY courts.courts
    ADD CONSTRAINT courts_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES courts.courts(id);


--
-- Name: courts courts_specific_regional_code_fkey; Type: FK CONSTRAINT; Schema: courts; Owner: admin
--

ALTER TABLE ONLY courts.courts
    ADD CONSTRAINT courts_specific_regional_code_fkey FOREIGN KEY (specific_regional_code) REFERENCES courts.regional_court_lookup(code);


--
-- Name: addresses addresses_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.addresses
    ADD CONSTRAINT addresses_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.entities(id) ON DELETE CASCADE;


--
-- Name: affiliations affiliations_affiliated_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.affiliations
    ADD CONSTRAINT affiliations_affiliated_entity_id_fkey FOREIGN KEY (affiliated_entity_id) REFERENCES public.entities(id) ON DELETE SET NULL;


--
-- Name: affiliations affiliations_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.affiliations
    ADD CONSTRAINT affiliations_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.entities(id) ON DELETE CASCADE;


--
-- Name: affiliations affiliations_source_snapshot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.affiliations
    ADD CONSTRAINT affiliations_source_snapshot_id_fkey FOREIGN KEY (source_snapshot_id) REFERENCES public.registry_snapshots(id);


--
-- Name: contacts contacts_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.contacts
    ADD CONSTRAINT contacts_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.entities(id) ON DELETE CASCADE;


--
-- Name: identifiers identifiers_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.identifiers
    ADD CONSTRAINT identifiers_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.entities(id) ON DELETE CASCADE;


--
-- Name: legal_persons legal_persons_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.legal_persons
    ADD CONSTRAINT legal_persons_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.entities(id) ON DELETE CASCADE;


--
-- Name: physical_persons physical_persons_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.physical_persons
    ADD CONSTRAINT physical_persons_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.entities(id) ON DELETE CASCADE;


--
-- Name: registry_profiles_ceidg registry_profiles_ceidg_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.registry_profiles_ceidg
    ADD CONSTRAINT registry_profiles_ceidg_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.entities(id) ON DELETE CASCADE;


--
-- Name: registry_profiles_ceidg registry_profiles_ceidg_last_snapshot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.registry_profiles_ceidg
    ADD CONSTRAINT registry_profiles_ceidg_last_snapshot_id_fkey FOREIGN KEY (last_snapshot_id) REFERENCES public.registry_snapshots(id);


--
-- Name: registry_profiles_krs registry_profiles_krs_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.registry_profiles_krs
    ADD CONSTRAINT registry_profiles_krs_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.entities(id) ON DELETE CASCADE;


--
-- Name: registry_profiles_krs registry_profiles_krs_last_snapshot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.registry_profiles_krs
    ADD CONSTRAINT registry_profiles_krs_last_snapshot_id_fkey FOREIGN KEY (last_snapshot_id) REFERENCES public.registry_snapshots(id);


--
-- Name: registry_snapshots registry_snapshots_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.registry_snapshots
    ADD CONSTRAINT registry_snapshots_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.entities(id) ON DELETE CASCADE;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: pg_database_owner
--

GRANT USAGE ON SCHEMA public TO invoice_app;


--
-- Name: TABLE addresses; Type: ACL; Schema: public; Owner: admin
--

GRANT SELECT ON TABLE public.addresses TO invoice_app;


--
-- Name: TABLE affiliations; Type: ACL; Schema: public; Owner: admin
--

GRANT SELECT ON TABLE public.affiliations TO invoice_app;


--
-- Name: TABLE contacts; Type: ACL; Schema: public; Owner: admin
--

GRANT SELECT ON TABLE public.contacts TO invoice_app;


--
-- Name: TABLE entities; Type: ACL; Schema: public; Owner: admin
--

GRANT SELECT ON TABLE public.entities TO invoice_app;


--
-- Name: TABLE identifiers; Type: ACL; Schema: public; Owner: admin
--

GRANT SELECT ON TABLE public.identifiers TO invoice_app;


--
-- Name: TABLE invoices; Type: ACL; Schema: public; Owner: admin
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.invoices TO invoice_app;


--
-- Name: SEQUENCE invoices_id_seq; Type: ACL; Schema: public; Owner: admin
--

GRANT SELECT,USAGE ON SEQUENCE public.invoices_id_seq TO invoice_app;


--
-- Name: TABLE legal_persons; Type: ACL; Schema: public; Owner: admin
--

GRANT SELECT ON TABLE public.legal_persons TO invoice_app;


--
-- Name: TABLE physical_persons; Type: ACL; Schema: public; Owner: admin
--

GRANT SELECT ON TABLE public.physical_persons TO invoice_app;


--
-- Name: TABLE registry_profiles_ceidg; Type: ACL; Schema: public; Owner: admin
--

GRANT SELECT ON TABLE public.registry_profiles_ceidg TO invoice_app;


--
-- Name: TABLE registry_profiles_krs; Type: ACL; Schema: public; Owner: admin
--

GRANT SELECT ON TABLE public.registry_profiles_krs TO invoice_app;


--
-- Name: TABLE registry_snapshots; Type: ACL; Schema: public; Owner: admin
--

GRANT SELECT ON TABLE public.registry_snapshots TO invoice_app;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE admin IN SCHEMA public GRANT SELECT ON TABLES TO invoice_app;


--
-- PostgreSQL database dump complete
--

\unrestrict iFQOUzEy7TJKPaMkVc6CjAv7UenR2eRY2bU6KMjvqBU2icSSeqYi4pty1XbpsM4
