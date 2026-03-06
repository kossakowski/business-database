--
-- PostgreSQL database dump
--

\restrict o8yb6off8dbMqMQL5qxPXPfZJwUqlKRYejYJ763ob835uJswfJgwnObD3dMK3Kb

-- Dumped from database version 16.11 (Debian 16.11-1.pgdg13+1)
-- Dumped by pg_dump version 16.11 (Debian 16.11-1.pgdg13+1)

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
    is_deceased boolean DEFAULT false NOT NULL
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
-- Data for Name: ui_enum_metadata; Type: TABLE DATA; Schema: meta; Owner: admin
--

COPY meta.ui_enum_metadata (enum_key, enum_value, label_pl, tooltip_pl, suffix_default, is_suffix_applicable, display_order) FROM stdin;
entity_type	PHYSICAL_PERSON	Osoba fizyczna	Człowiek (np. klient, członek zarządu, wierzyciel).	\N	\N	10
entity_type	LEGAL_PERSON	Podmiot prawny	Podmiot niebędący osobą fizyczną (spółka, fundacja, spółdzielnia, wspólnota itd.).	\N	\N	20
legal_kind	SPOLKA_JAWNA	Spółka jawna	Spółka osobowa. Często używa skrótu w nazwie.	sp. j.	t	10
legal_kind	SPOLKA_PARTNERSKA	Spółka partnerska	Spółka osobowa dla wolnych zawodów.	sp.p.	t	20
legal_kind	SPOLKA_KOMANDYTOWA	Spółka komandytowa	Spółka osobowa.	sp.k.	t	30
legal_kind	SPOLKA_KOMANDYTOWO_AKCYJNA	Spółka komandytowo-akcyjna	Spółka hybrydowa.	S.K.A.	t	40
legal_kind	SPOLKA_Z_OO	Spółka z ograniczoną odpowiedzialnością	Spółka kapitałowa.	sp. z o.o.	t	50
legal_kind	SPOLKA_AKCYJNA	Spółka akcyjna	Spółka kapitałowa.	S.A.	t	60
legal_kind	PROSTA_SPOLKA_AKCYJNA	Prosta spółka akcyjna	Spółka kapitałowa.	P.S.A.	t	70
legal_kind	FUNDACJA	Fundacja	Zwykle bez sufiksu skrótowego; nazwa formalna wynika z aktu/rejestru.	\N	f	80
legal_kind	STOWARZYSZENIE	Stowarzyszenie	Zwykle bez sufiksu skrótowego; nazwa formalna wynika z rejestru/statutu.	\N	f	90
legal_kind	FUNDACJA_RODZINNA	Fundacja rodzinna	Podmiot szczególny (RFR). W praktyce używa się pełnego określenia.	\N	f	100
legal_kind	SPOLDZIELNIA	Spółdzielnia	Nazwa zwykle zawiera “spółdzielnia/spółdzielczy”; brak typowego sufiksu jak sp.k.	\N	f	110
legal_kind	SPOLDZIELNIA_MIESZKANIOWA	Spółdzielnia mieszkaniowa	Rodzaj spółdzielni; brak typowego sufiksu.	\N	f	120
legal_kind	WSPOLNOTA_MIESZKANIOWA	Wspólnota mieszkaniowa	Zwykle brak KRS; istotne bywają NIP/REGON i adres nieruchomości.	\N	f	130
legal_kind	SPOLKA_CYWILNA	Spółka cywilna	Umowa cywilna między wspólnikami; w praktyce bywa identyfikowana NIP/REGON “s.c.”.	\N	f	140
legal_kind	OTHER	Inny	Użyj gdy brak dopasowania do listy.	\N	f	999
affiliation_type	MANAGEMENT_BOARD_MEMBER	Członek zarządu	Funkcja w organie zarządzającym spółki/podmiotu.	\N	\N	10
affiliation_type	SUPERVISORY_BOARD_MEMBER	Członek rady nadzorczej	Funkcja nadzorcza (jeśli dotyczy).	\N	\N	20
affiliation_type	LIQUIDATOR	Likwidator	Osoba prowadząca likwidację podmiotu.	\N	\N	30
affiliation_type	PROXY_PROKURENT	Prokurent	Prokurent ujawniony w rejestrze (zakres w polu “Zakres”).	\N	\N	40
affiliation_type	REPRESENTATIVE	Uprawniony do reprezentacji	Ogólne uprawnienie do reprezentacji wg rejestru.	\N	\N	50
affiliation_type	CIVIL_PARTNERSHIP_PARTNER	Wspólnik spółki cywilnej	Powiązanie osoby z podmiotem “spółka cywilna”.	\N	\N	60
affiliation_type	OTHER_REGISTRY_ROLE	Inna rola rejestrowa	Rola nietypowa – doprecyzuj w polu “Funkcja / tytuł”.	\N	\N	999
\.


--
-- Data for Name: ui_field_metadata; Type: TABLE DATA; Schema: meta; Owner: admin
--

COPY meta.ui_field_metadata (field_key, label_pl, tooltip_pl, placeholder, example_value, input_type, privacy_level, source_hint, validation_hint, validation_rule, display_group, display_order, is_user_editable) FROM stdin;
entity.entity_type	Typ podmiotu	Wybierz: osoba fizyczna albo podmiot niebędący osobą fizyczną (np. spółka, fundacja, wspólnota).	—	OSOBA_FIZYCZNA	select	INTERNAL	MANUAL	\N	\N	Podmiot	10	t
person.date_of_birth	Data urodzenia	\N	YYYY-MM-DD	1987-10-01	date	SENSITIVE	MANUAL	\N	\N	Osoba fizyczna	40	t
entity.canonical_label	Etykieta	Krótka etykieta do wyszukiwania i list (np. “Kowalski Jan”, “ABC sp. z o.o.”). Nie musi być formalną nazwą z rejestru.	Kowalski Jan	ABC sp. z o.o.	text	INTERNAL	MANUAL	\N	\N	Podmiot	20	t
entity.status	Status rekordu	Status w systemie (np. aktywny/nieaktywny). Nie mylić ze statusem w KRS/CEIDG.	AKTYWNY	AKTYWNY	select	INTERNAL	MANUAL	\N	\N	Podmiot	30	t
entity.notes	Notatki wewnętrzne	Notatki robocze zespołu (nie są “prawdą rejestrową”). Warto wpisywać źródło lub kontekst.	Notatka…	\N	textarea	INTERNAL	MANUAL	\N	\N	Podmiot	90	t
person.first_name	Imię	Imię zgodne z dokumentem / rejestrem.	Jan	Anna	text	INTERNAL	MANUAL	\N	\N	Osoba fizyczna	10	t
person.middle_names	Drugie imię / imiona	Opcjonalnie. Wpisuj tylko jeśli ma znaczenie w dokumentach.	Maria	\N	text	INTERNAL	MANUAL	\N	\N	Osoba fizyczna	20	t
person.last_name	Nazwisko	Nazwisko zgodne z dokumentem / rejestrem.	Kowalski	Nowak	text	INTERNAL	MANUAL	\N	\N	Osoba fizyczna	30	t
person.citizenship_country	Obywatelstwo (kraj)	Kod kraju (np. PL, DE). Przydatne przy danych z CEIDG lub dokumentów.	PL	PL	text	INTERNAL	MANUAL	2-literowy kod kraju	\N	Osoba fizyczna	50	t
person.is_deceased	Zmarły	Zaznacz tylko jeśli masz wiarygodną informację (np. akt zgonu/PESEL).	\N	\N	boolean	SENSITIVE	MANUAL	\N	\N	Osoba fizyczna	60	t
legal.registered_name	Nazwa formalna	Pełna nazwa formalna (najlepiej dokładnie jak w KRS/CEIDG/umowie).	ABC sp. z o.o.	Fundacja Rodzinna XYZ	text	INTERNAL	KRS/CEIDG	\N	\N	Podmiot prawny	10	t
legal.short_name	Nazwa skrócona	Opcjonalnie: nazwa skrócona/marketingowa używana w korespondencji.	ABC	\N	text	INTERNAL	MANUAL	\N	\N	Podmiot prawny	20	t
legal.legal_kind	Rodzaj podmiotu	Wybierz typ podmiotu (np. sp. z o.o., S.A., fundacja, wspólnota). Ułatwia formatowanie nazwy i walidację sufiksu.	SPOLKA_Z_OO	FUNDACJA	select	INTERNAL	MANUAL	\N	\N	Podmiot prawny	30	t
legal.legal_form_suffix	Sufiks / skrót formy	Skrót formy prawnej, jeśli ma zastosowanie (np. “sp. z o.o.”, “sp.k.”, “S.A.”). Dla części podmiotów nie stosuje się sufiksu — wtedy zostaw puste.	sp. z o.o.	sp.k.	text	INTERNAL	MANUAL	Ustal wg formy prawnej	\N	Podmiot prawny	50	t
legal.country	Kraj rejestracji	Zwykle PL. Jeśli podmiot zagraniczny, wpisz kod kraju (np. DE, CZ).	PL	PL	text	INTERNAL	MANUAL	2-literowy kod kraju	\N	Podmiot prawny	60	t
id.PESEL	PESEL	Numer PESEL osoby fizycznej. Pole wrażliwe. Jeśli pochodzi z dokumentu lub rejestru — preferuj automatyczne zasilanie / wpisuj bez spacji.	11 cyfr	8710109374	text	SENSITIVE	CEIDG/MANUAL	11 cyfr	{"pattern": "^[0-9]{11}$"}	Identyfikatory	10	t
id.NIP	NIP	Numer NIP (osoba lub podmiot). Wpisuj bez spacji i kresek.	10 cyfr	5222837149	text	SENSITIVE	KRS/CEIDG/MANUAL	10 cyfr	{"pattern": "^[0-9]{10}$"}	Identyfikatory	20	t
id.REGON	REGON	REGON (9 lub 14 cyfr). Wpisuj bez spacji.	9 lub 14 cyfr	012345678	text	INTERNAL	KRS/CEIDG/MANUAL	9 lub 14 cyfr	{"pattern": "^[0-9]{9}([0-9]{5})?$"}	Identyfikatory	30	t
id.KRS	KRS	Numer KRS (zwykle 10 cyfr). Jeśli znany, pozwala automatycznie pobrać dane z KRS OpenAPI.	10 cyfr	0000123456	text	INTERNAL	KRS	10 cyfr	{"pattern": "^[0-9]{10}$"}	Identyfikatory	40	t
id.RFR	Numer RFR	Numer rejestru fundacji rodzinnych (RFR), jeśli dotyczy.	—	\N	text	INTERNAL	MANUAL/AUTO	\N	\N	Identyfikatory	50	t
id.OTHER_REGISTRY_NUMBER	Inny numer rejestrowy	Numer z innego rejestru (np. zagraniczny numer, numer ewidencyjny). Uzupełnij też nazwę rejestru.	—	\N	text	INTERNAL	MANUAL	\N	\N	Identyfikatory	60	t
id.OTHER_REGISTRY_NAME	Nazwa rejestru	Nazwa rejestru dla “Innego numeru rejestrowego” (np. “Handelsregister”, “Companies House”).	—	Companies House	text	INTERNAL	MANUAL	\N	\N	Identyfikatory	70	t
contact.EMAIL	E-mail	Adres e-mail (najlepiej służbowy). W CEIDG może się pojawiać automatycznie.	kontakt@firma.pl	kontakt@abc.pl	text	INTERNAL	CEIDG/MANUAL	Poprawny format e-mail	\N	Kontakt	10	t
contact.PHONE	Telefon	Numer telefonu kontaktowego.	+48 600 000 000	+48 601 234 567	text	INTERNAL	CEIDG/MANUAL	\N	\N	Kontakt	20	t
contact.WEBSITE	Strona WWW	Adres strony internetowej.	https://…	https://example.pl	text	INTERNAL	CEIDG/MANUAL	\N	\N	Kontakt	30	t
contact.EPUAP	ePUAP	Identyfikator skrzynki ePUAP, jeśli używany do doręczeń.	/XYZ/SkrytkaESP	\N	text	INTERNAL	MANUAL	\N	\N	Kontakt	40	t
contact.OTHER	Inny kontakt	Dowolny inny kanał (np. fax, komunikator) – wpisz w notatce co to jest.	Fax: …	\N	text	INTERNAL	MANUAL	\N	\N	Kontakt	90	t
addr.address_type	Typ adresu	Wybierz rodzaj adresu (np. siedziba, do doręczeń, miejsce prowadzenia działalności). W CEIDG typy często wynikają z danych rejestrowych.	SIEDZIBA	\N	select	INTERNAL	CEIDG/KRS/MANUAL	\N	\N	Adresy	5	t
addr.country	Kraj	Kod kraju (np. PL).	PL	PL	text	INTERNAL	MANUAL	2-literowy kod kraju	\N	Adresy	10	t
addr.voivodeship	Województwo	Wpisz województwo (np. “mazowieckie”). Przy automatycznym imporcie może wypełniać się z kodów.	mazowieckie	\N	text	INTERNAL	CEIDG/MANUAL	\N	\N	Adresy	20	t
addr.county	Powiat	Opcjonalnie.	Warszawa	\N	text	INTERNAL	CEIDG/MANUAL	\N	\N	Adresy	30	t
addr.gmina	Gmina	Opcjonalnie.	Bemowo	\N	text	INTERNAL	CEIDG/MANUAL	\N	\N	Adresy	40	t
addr.city	Miejscowość	Miasto/miejscowość.	Warszawa	Poznań	text	INTERNAL	CEIDG/KRS/MANUAL	\N	\N	Adresy	50	t
addr.postal_code	Kod pocztowy	Wpisz w formacie 00-000.	00-000	00-815	text	INTERNAL	CEIDG/KRS/MANUAL	Format 00-000	\N	Adresy	60	t
addr.post_office	Poczta	Opcjonalnie (czasem inna niż miejscowość).	Warszawa 50	\N	text	INTERNAL	CEIDG/MANUAL	\N	\N	Adresy	70	t
addr.street	Ulica	Ulica bez numeru budynku.	Sienna	Chłodna	text	INTERNAL	CEIDG/KRS/MANUAL	\N	\N	Adresy	80	t
addr.building_no	Nr budynku	Numer budynku (czasem z literą).	86	2A	text	INTERNAL	CEIDG/KRS/MANUAL	\N	\N	Adresy	90	t
addr.unit_no	Nr lokalu	Numer lokalu (jeśli dotyczy).	137	44	text	INTERNAL	CEIDG/KRS/MANUAL	\N	\N	Adresy	100	t
addr.additional_line	Dodatkowa linia	Np. piętro, “c/o”, uwagi do lokalizacji.	lok. 1	\N	text	INTERNAL	MANUAL	\N	\N	Adresy	110	t
addr.teryt_terc	TERC (opcjonalnie)	Kod TERYT TERC jeśli dostępny z automatycznego importu (nie wpisuj ręcznie, jeśli nie musisz).	\N	\N	text	INTERNAL	AUTO	\N	\N	Adresy	200	f
addr.teryt_simc	SIMC (opcjonalnie)	Kod TERYT SIMC z importu. Zwykle pole techniczne.	\N	\N	text	INTERNAL	AUTO	\N	\N	Adresy	210	f
addr.teryt_ulic	ULIC (opcjonalnie)	Kod TERYT ULIC z importu. Zwykle pole techniczne.	\N	\N	text	INTERNAL	AUTO	\N	\N	Adresy	220	f
addr.freeform_note	Opis lokalizacji nietypowej	Gdy adres nie pasuje do standardu (np. działka, bez ulicy) – krótki opis.	np. “działka nr …”	\N	textarea	INTERNAL	MANUAL	\N	\N	Adresy	300	t
krs.krs_number	KRS (profil)	Pole techniczne profilu KRS. Zasilane automatycznie po pobraniu danych z KRS.	0000000000	0000123456	text	INTERNAL	KRS	\N	\N	Rejestry – KRS	10	f
krs.registry_status	Status w KRS	Status wynikający z danych KRS (np. aktywna, w likwidacji). Nie edytuj ręcznie.	—	\N	text	INTERNAL	KRS	\N	\N	Rejestry – KRS	20	f
krs.pkds	PKD (KRS)	Kody PKD z KRS. Nie edytuj ręcznie (źródło: KRS).	\N	\N	multiselect	INTERNAL	KRS	\N	\N	Rejestry – KRS	30	f
krs.payload	Dane surowe KRS	Pełny surowy payload z KRS (do audytu i ponownego parsowania).	—	\N	textarea	INTERNAL	KRS	\N	\N	Rejestry – KRS	99	f
ceidg.unique_id	Identyfikator wpisu CEIDG	Pole techniczne z CEIDG. Nie edytuj ręcznie.	\N	\N	text	INTERNAL	CEIDG	\N	\N	Rejestry – CEIDG	10	f
ceidg.status	Status CEIDG	Status działalności wg CEIDG (aktywny/zawieszony/zakończony). Nie edytuj ręcznie.	\N	\N	text	INTERNAL	CEIDG	\N	\N	Rejestry – CEIDG	20	f
ceidg.business_name	Firma (CEIDG)	Nazwa firmy osoby fizycznej wg CEIDG. Zasilane automatycznie.	\N	\N	text	INTERNAL	CEIDG	\N	\N	Rejestry – CEIDG	30	f
ceidg.start_date	Data rozpoczęcia działalności	\N	YYYY-MM-DD	\N	date	INTERNAL	CEIDG	\N	\N	Rejestry – CEIDG	40	f
ceidg.end_date	Data zakończenia działalności	\N	YYYY-MM-DD	\N	date	INTERNAL	CEIDG	\N	\N	Rejestry – CEIDG	50	f
ceidg.suspension_date	Data zawieszenia	\N	YYYY-MM-DD	\N	date	INTERNAL	CEIDG	\N	\N	Rejestry – CEIDG	60	f
ceidg.resume_date	Data wznowienia	\N	YYYY-MM-DD	\N	date	INTERNAL	CEIDG	\N	\N	Rejestry – CEIDG	70	f
ceidg.pkds	PKD (CEIDG)	Kody PKD z CEIDG. Nie edytuj ręcznie.	\N	\N	multiselect	INTERNAL	CEIDG	\N	\N	Rejestry – CEIDG	80	f
ceidg.payload	Dane surowe CEIDG	Pełny surowy payload z CEIDG (do audytu i ponownego parsowania).	—	\N	textarea	INTERNAL	CEIDG	\N	\N	Rejestry – CEIDG	99	f
snapshot.lookup_key	Klucz pobrania	Klucz użyty do pobrania danych (np. KRS, NIP, CEIDG uniqueId). Pole techniczne.	—	\N	text	INTERNAL	AUTO	\N	\N	Rejestry – Snapshot	10	f
snapshot.fetched_at	Data pobrania	Kiedy pobrano dane z rejestru. Pole techniczne.	\N	\N	date	INTERNAL	AUTO	\N	\N	Rejestry – Snapshot	20	f
snapshot.payload_format	Format payloadu	JSON lub XML. Pole techniczne.	\N	\N	text	INTERNAL	AUTO	\N	\N	Rejestry – Snapshot	30	f
snapshot.payload_hash	Hash payloadu	Używane do wykrywania zmian bez porównywania całej treści. Pole techniczne.	\N	\N	text	INTERNAL	AUTO	\N	\N	Rejestry – Snapshot	40	f
snapshot.payload_raw	Payload surowy	Surowa odpowiedź z rejestru do audytu. Pole techniczne.	\N	\N	textarea	INTERNAL	AUTO	\N	\N	Rejestry – Snapshot	50	f
aff.subject_entity	Podmiot (osoba/podmiot)	Osoba lub podmiot pełniący funkcję (np. członek zarządu, prokurent). Zwykle zasilane z KRS/CEIDG.	\N	\N	text	INTERNAL	KRS/CEIDG	\N	\N	Powiązania rejestrowe	10	f
aff.object_entity	Podmiot docelowy	Podmiot, którego dotyczy funkcja (np. spółka, w której osoba jest członkiem zarządu).	\N	\N	text	INTERNAL	KRS/CEIDG	\N	\N	Powiązania rejestrowe	20	f
aff.affiliation_type	Typ powiązania	Rodzaj roli/powiązania pochodzący z rejestru (np. członek zarządu, prokurent, wspólnik s.c.).	\N	\N	select	INTERNAL	KRS/CEIDG	\N	\N	Powiązania rejestrowe	30	f
aff.function_title	Funkcja / tytuł	Dokładna funkcja z rejestru (np. “Prezes Zarządu”, “Członek Zarządu”).	Prezes Zarządu	\N	text	INTERNAL	KRS/CEIDG	\N	\N	Powiązania rejestrowe	40	f
aff.representation_mode	Sposób reprezentacji	Jeśli rejestr podaje zasady reprezentacji (np. “dwóch członków zarządu łącznie”).	\N	\N	textarea	INTERNAL	KRS	\N	\N	Powiązania rejestrowe	50	f
aff.scope	Zakres	Zakres roli, jeśli dotyczy (np. rodzaj prokury).	\N	\N	text	INTERNAL	KRS/CEIDG	\N	\N	Powiązania rejestrowe	60	f
aff.valid_from	Obowiązuje od	\N	YYYY-MM-DD	\N	date	INTERNAL	KRS/CEIDG	\N	\N	Powiązania rejestrowe	70	f
aff.valid_to	Obowiązuje do	\N	YYYY-MM-DD	\N	date	INTERNAL	KRS/CEIDG	\N	\N	Powiązania rejestrowe	80	f
aff.is_current	Aktualne	Czy jest aktualne wg ostatniego pobrania rejestru.	\N	\N	boolean	INTERNAL	AUTO	\N	\N	Powiązania rejestrowe	90	f
aff.status	Status powiązania	ACTIVE/ENDED/UNKNOWN – stan techniczny w systemie na podstawie kolejnych pobrań.	\N	\N	select	INTERNAL	AUTO	\N	\N	Powiązania rejestrowe	100	f
aff.confidence	Pewność	Używane gdy parsowanie jest niepewne (np. OCR). Zwykle 100 przy danych API.	\N	\N	text	INTERNAL	AUTO	\N	\N	Powiązania rejestrowe	110	f
\.


--
-- Data for Name: addresses; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.addresses (id, entity_id, address_type, country, voivodeship, county, gmina, city, postal_code, post_office, street, building_no, unit_no, additional_line, teryt_terc, teryt_simc, teryt_ulic, freeform_note, created_at, updated_at) FROM stdin;
efaa4eef-62a0-46b4-9495-a1e139081790	b677c056-d93f-490f-ba2e-1163a56d4242	MAIN	PL	\N	\N	\N	Warszawa	04-078	\N	Garibaldiego	4	177	\N	\N	\N	\N	\N	2026-01-09 21:01:24.715277+00	2026-01-09 22:48:19.315692+00
a8870a85-7b1b-4e33-a5f4-c3ec7e2103d0	c9b6d16d-753c-44ab-a6cc-f4841ff283fa	MAIN	PL	\N	\N	\N	Warszawa	02-001	\N	Aleje Jerozolimskie	81	\N	\N	\N	\N	\N	\N	2026-01-09 23:15:18.406882+00	2026-01-09 23:15:18.416295+00
93762271-f5fd-40e5-bc6d-98e57f5f5e44	6618c252-5a52-44e5-b05f-1160234bde4a	MAIN	POLSKA	\N	\N	\N	WARSZAWA	02-001	\N	AL. ALEJE JEROZOLIMSKIE	81	X P.	\N	\N	\N	\N	\N	2026-01-11 10:43:01.270228+00	2026-01-11 10:43:01.279355+00
29dda64d-9842-49dd-b0a2-912080891f73	58496215-e857-4afa-b593-6d2d04fad4ae	MAIN	PL	\N	\N	\N	Warszawa	00-815	\N	Sienna	86	137	\N	\N	\N	\N	\N	2026-01-11 12:25:52.880123+00	2026-01-11 12:25:52.889081+00
\.


--
-- Data for Name: affiliations; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.affiliations (id, entity_id, affiliated_entity_id, affiliation_type, role, start_date, end_date, source_system, source_snapshot_id, notes, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: contacts; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.contacts (id, entity_id, contact_type, contact_value, label, is_primary, created_at) FROM stdin;
5376660c-cbc9-4c9b-b792-12ff1e1a4b4d	b677c056-d93f-490f-ba2e-1163a56d4242	EMAIL	r.mlodawski@icloud.com	\N	f	2026-01-09 21:01:24.715277+00
2e80f268-6b97-41a7-a720-5d56cbe59c0b	b677c056-d93f-490f-ba2e-1163a56d4242	PHONE	+48 502 333 375	\N	f	2026-01-09 21:01:24.715277+00
e1da50be-44db-4f0b-a7ce-97b3ccbf7ea2	c9b6d16d-753c-44ab-a6cc-f4841ff283fa	EMAIL	r.mlodawski@biolabinvest.eu	\N	f	2026-01-09 23:15:18.406882+00
1bf63c5c-1a69-47f8-be0b-3875a31e7f75	c9b6d16d-753c-44ab-a6cc-f4841ff283fa	PHONE	+48 502 333 375	\N	f	2026-01-09 23:15:18.406882+00
a1e9f8be-8cb9-4ee4-987b-8739d4e9b164	6618c252-5a52-44e5-b05f-1160234bde4a	WEBSITE	WWW.PROFINANCE.PL	\N	f	2026-01-11 10:43:01.270228+00
69298f6b-e696-4e94-a990-51ebeeac3b57	58496215-e857-4afa-b593-6d2d04fad4ae	EMAIL	kossakowski87@gmail.com	\N	f	2026-01-11 12:25:52.880123+00
e2db2d5d-944f-47d3-bd40-16eab6409ebc	58496215-e857-4afa-b593-6d2d04fad4ae	PHONE	694487149	\N	f	2026-01-11 12:25:52.880123+00
\.


--
-- Data for Name: entities; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.entities (id, entity_type, canonical_label, notes, created_at, updated_at) FROM stdin;
b677c056-d93f-490f-ba2e-1163a56d4242	PHYSICAL_PERSON	Rafał Młodawski	\N	2026-01-09 21:01:24.715277+00	2026-01-09 21:01:24.715277+00
c9b6d16d-753c-44ab-a6cc-f4841ff283fa	LEGAL_PERSON	Biolabinvest	\N	2026-01-09 23:15:18.406882+00	2026-01-09 23:15:18.406882+00
6618c252-5a52-44e5-b05f-1160234bde4a	LEGAL_PERSON	Profinance	\N	2026-01-11 10:43:01.270228+00	2026-01-11 10:43:01.270228+00
58496215-e857-4afa-b593-6d2d04fad4ae	PHYSICAL_PERSON	Łukasz Kossakowski	\N	2026-01-11 12:25:52.880123+00	2026-01-11 12:25:52.880123+00
\.


--
-- Data for Name: identifiers; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.identifiers (id, entity_id, identifier_type, identifier_value, registry_name, created_at) FROM stdin;
26799df0-dbac-4158-b9c2-e91581c68cf1	b677c056-d93f-490f-ba2e-1163a56d4242	PESEL	79012510591	\N	2026-01-09 21:01:24.715277+00
b47b388d-d9d9-4f16-a47b-f4a0edecbf87	c9b6d16d-753c-44ab-a6cc-f4841ff283fa	KRS	0000616546	\N	2026-01-09 23:15:18.406882+00
bb27593e-86c3-4e28-9a2b-edf7cf83d8df	c9b6d16d-753c-44ab-a6cc-f4841ff283fa	NIP	6762506971	\N	2026-01-09 23:15:18.406882+00
985c30ed-3a63-483f-a838-ea1ce7b936cf	c9b6d16d-753c-44ab-a6cc-f4841ff283fa	REGON	364404801	\N	2026-01-09 23:15:18.406882+00
07aed598-9b9a-4adf-8036-40d537949195	6618c252-5a52-44e5-b05f-1160234bde4a	KRS	0000535538	\N	2026-01-11 10:43:01.270228+00
5fab5740-113a-438b-9a0b-1e877190779d	6618c252-5a52-44e5-b05f-1160234bde4a	NIP	7010473531	\N	2026-01-11 10:43:01.270228+00
185f35ae-adc1-4aab-a177-7d858e026fc9	6618c252-5a52-44e5-b05f-1160234bde4a	REGON	36100885500000	\N	2026-01-11 10:43:01.270228+00
d04b5d61-283f-479e-bc3b-9b43e0675a60	58496215-e857-4afa-b593-6d2d04fad4ae	PESEL	87101809374	\N	2026-01-11 12:25:52.880123+00
a8b0d3e8-44f7-42f8-a14b-83bcde09fbd5	58496215-e857-4afa-b593-6d2d04fad4ae	NIP	5222837149	\N	2026-01-11 12:25:52.880123+00
\.


--
-- Data for Name: legal_persons; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.legal_persons (entity_id, registered_name, short_name, legal_kind, legal_form_suffix, country) FROM stdin;
c9b6d16d-753c-44ab-a6cc-f4841ff283fa	Biolabinvest spółka z ograniczoną odpowiedzialnością	Biolabinvest sp.z o.o.	SPOLKA_Z_OO	"sp. z o.o."	PL
6618c252-5a52-44e5-b05f-1160234bde4a	"PROFINANCE" SPÓŁKA AKCYJNA	"PROFINANCE" S.A.	SPOLKA_AKCYJNA	S.A.	PL
\.


--
-- Data for Name: physical_persons; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.physical_persons (entity_id, first_name, middle_names, last_name, date_of_birth, citizenship_country, is_deceased) FROM stdin;
b677c056-d93f-490f-ba2e-1163a56d4242	Rafał	Paweł	Młodawski	1979-01-25	PL	f
58496215-e857-4afa-b593-6d2d04fad4ae	Łukasz	Kossakowski	Kossakowski	1987-10-18	PL	f
\.


--
-- Data for Name: registry_profiles_ceidg; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.registry_profiles_ceidg (entity_id, ceidg_id, nip, regon, first_name, last_name, business_name, status, start_date, end_date, pkd_main, last_snapshot_id, last_fetched_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: registry_profiles_krs; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.registry_profiles_krs (entity_id, krs, nip, regon, official_name, short_name, legal_form, registry_status, registration_date, share_capital, pkd_main, last_snapshot_id, last_fetched_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: registry_snapshots; Type: TABLE DATA; Schema: public; Owner: admin
--

COPY public.registry_snapshots (id, entity_id, source_system, external_id, fetched_at, effective_date, payload_format, payload, payload_raw, payload_hash, fetched_by, purpose_ref, created_at) FROM stdin;
\.


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
-- PostgreSQL database dump complete
--

\unrestrict o8yb6off8dbMqMQL5qxPXPfZJwUqlKRYejYJ763ob835uJswfJgwnObD3dMK3Kb

