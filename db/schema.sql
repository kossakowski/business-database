--
-- PostgreSQL database dump
--

\restrict 2gie7NjsI1ZjtR4BBiB79vdgIcP7RZZkDhmZlrAx1YH21kC1bOc9iy47ImBRPnN

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
-- PostgreSQL database dump complete
--

\unrestrict 2gie7NjsI1ZjtR4BBiB79vdgIcP7RZZkDhmZlrAx1YH21kC1bOc9iy47ImBRPnN

