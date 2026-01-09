--
-- PostgreSQL database dump
--

\restrict oMzncfeWKZGg6asWAMv98ZFi7g9HqxlLG2ezN6kIgsUgsVhjrfMsOQAn7lKftxB

-- Dumped from database version 16.11 (Debian 16.11-1.pgdg13+1)
-- Dumped by pg_dump version 16.11 (Ubuntu 16.11-0ubuntu0.24.04.1)

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
-- Name: meta; Type: SCHEMA; Schema: -; Owner: admin
--

CREATE SCHEMA meta;


ALTER SCHEMA meta OWNER TO admin;

SET default_tablespace = '';

SET default_table_access_method = heap;

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
    status text DEFAULT 'ACTIVE'::text NOT NULL,
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
-- Name: legal_persons; Type: TABLE; Schema: public; Owner: admin
--

CREATE TABLE public.legal_persons (
    entity_id uuid NOT NULL,
    registered_name text NOT NULL,
    short_name text,
    legal_kind text,
    legal_nature text,
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
    is_deceased boolean DEFAULT false NOT NULL
);


ALTER TABLE public.physical_persons OWNER TO admin;

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
-- Name: idx_addresses_city; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_addresses_city ON public.addresses USING btree (city);


--
-- Name: idx_addresses_entity; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_addresses_entity ON public.addresses USING btree (entity_id);


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
-- Name: idx_entities_status; Type: INDEX; Schema: public; Owner: admin
--

CREATE INDEX idx_entities_status ON public.entities USING btree (status);


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
-- Name: addresses addresses_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: admin
--

ALTER TABLE ONLY public.addresses
    ADD CONSTRAINT addresses_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.entities(id) ON DELETE CASCADE;


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
-- PostgreSQL database dump complete
--

\unrestrict oMzncfeWKZGg6asWAMv98ZFi7g9HqxlLG2ezN6kIgsUgsVhjrfMsOQAn7lKftxB

