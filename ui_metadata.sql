BEGIN;

CREATE SCHEMA IF NOT EXISTS meta;

-- Field-level metadata (labels, tooltips, examples, UI hints)
CREATE TABLE IF NOT EXISTS meta.ui_field_metadata (
  field_key         text PRIMARY KEY,
  label_pl          text NOT NULL,
  tooltip_pl        text NULL,
  placeholder       text NULL,
  example_value     text NULL,
  input_type        text NOT NULL DEFAULT 'text',   -- text/date/select/multiselect/boolean/textarea
  privacy_level     text NOT NULL DEFAULT 'INTERNAL', -- PUBLIC/INTERNAL/SENSITIVE
  source_hint       text NULL, -- e.g. 'KRS', 'CEIDG', 'MANUAL', 'AUTO'
  validation_hint   text NULL,
  validation_rule   jsonb NULL,
  display_group     text NOT NULL DEFAULT 'General',
  display_order     int  NOT NULL DEFAULT 1000,
  is_user_editable  boolean NOT NULL DEFAULT true
);

-- Enum value metadata (friendly labels + tooltips for selectable values)
CREATE TABLE IF NOT EXISTS meta.ui_enum_metadata (
  enum_key          text NOT NULL,
  enum_value        text NOT NULL,
  label_pl          text NOT NULL,
  tooltip_pl        text NULL,
  suffix_default    text NULL,
  is_suffix_applicable boolean NULL,
  display_order     int  NOT NULL DEFAULT 1000,
  PRIMARY KEY (enum_key, enum_value)
);

-- Helper: upsert pattern using ON CONFLICT
-- (No function needed; we use INSERT ... ON CONFLICT directly.)

/* =========================
   UI FIELD METADATA
   ========================= */

-- Entity (core)
INSERT INTO meta.ui_field_metadata
(field_key,label_pl,tooltip_pl,placeholder,example_value,input_type,privacy_level,source_hint,validation_hint,display_group,display_order,is_user_editable)
VALUES
('entity.entity_type','Typ podmiotu','Wybierz: osoba fizyczna albo podmiot niebędący osobą fizyczną (np. spółka, fundacja, wspólnota).','—','OSOBA_FIZYCZNA','select','INTERNAL','MANUAL',NULL,'Podmiot',10,true),

('entity.canonical_label','Etykieta','Krótka etykieta do wyszukiwania i list (np. “Kowalski Jan”, “ABC sp. z o.o.”). Nie musi być formalną nazwą z rejestru.','Kowalski Jan','ABC sp. z o.o.','text','INTERNAL','MANUAL',NULL,'Podmiot',20,true),

('entity.status','Status rekordu','Status w systemie (np. aktywny/nieaktywny). Nie mylić ze statusem w KRS/CEIDG.','AKTYWNY','AKTYWNY','select','INTERNAL','MANUAL',NULL,'Podmiot',30,true),

('entity.notes','Notatki wewnętrzne','Notatki robocze zespołu (nie są “prawdą rejestrową”). Warto wpisywać źródło lub kontekst.','Notatka…',NULL,'textarea','INTERNAL','MANUAL',NULL,'Podmiot',90,true)
ON CONFLICT (field_key) DO UPDATE SET
  label_pl=EXCLUDED.label_pl,
  tooltip_pl=EXCLUDED.tooltip_pl,
  placeholder=EXCLUDED.placeholder,
  example_value=EXCLUDED.example_value,
  input_type=EXCLUDED.input_type,
  privacy_level=EXCLUDED.privacy_level,
  source_hint=EXCLUDED.source_hint,
  validation_hint=EXCLUDED.validation_hint,
  display_group=EXCLUDED.display_group,
  display_order=EXCLUDED.display_order,
  is_user_editable=EXCLUDED.is_user_editable;

-- Physical person
INSERT INTO meta.ui_field_metadata
(field_key,label_pl,tooltip_pl,placeholder,example_value,input_type,privacy_level,source_hint,validation_hint,display_group,display_order,is_user_editable)
VALUES
('person.first_name','Imię','Imię zgodne z dokumentem / rejestrem.','Jan','Anna','text','INTERNAL','MANUAL',NULL,'Osoba fizyczna',10,true),
('person.middle_names','Drugie imię / imiona','Opcjonalnie. Wpisuj tylko jeśli ma znaczenie w dokumentach.','Maria',NULL,'text','INTERNAL','MANUAL',NULL,'Osoba fizyczna',20,true),
('person.last_name','Nazwisko','Nazwisko zgodne z dokumentem / rejestrem.','Kowalski','Nowak','text','INTERNAL','MANUAL',NULL,'Osoba fizyczna',30,true),
('person.date_of_birth','Data urodzenia',NULL,'YYYY-MM-DD','1987-10-01','date','SENSITIVE','MANUAL',NULL,'Osoba fizyczna',40,true),
('person.citizenship_country','Obywatelstwo (kraj)','Kod kraju (np. PL, DE). Przydatne przy danych z CEIDG lub dokumentów.','PL','PL','text','INTERNAL','MANUAL','2-literowy kod kraju','Osoba fizyczna',50,true),
('person.is_deceased','Zmarły','Zaznacz tylko jeśli masz wiarygodną informację (np. akt zgonu/PESEL).',NULL,NULL,'boolean','SENSITIVE','MANUAL',NULL,'Osoba fizyczna',60,true)
ON CONFLICT (field_key) DO UPDATE SET
  label_pl=EXCLUDED.label_pl, tooltip_pl=EXCLUDED.tooltip_pl, placeholder=EXCLUDED.placeholder,
  example_value=EXCLUDED.example_value, input_type=EXCLUDED.input_type, privacy_level=EXCLUDED.privacy_level,
  source_hint=EXCLUDED.source_hint, validation_hint=EXCLUDED.validation_hint, display_group=EXCLUDED.display_group,
  display_order=EXCLUDED.display_order, is_user_editable=EXCLUDED.is_user_editable;

-- Legal person
INSERT INTO meta.ui_field_metadata
(field_key,label_pl,tooltip_pl,placeholder,example_value,input_type,privacy_level,source_hint,validation_hint,display_group,display_order,is_user_editable)
VALUES
('legal.registered_name','Nazwa formalna','Pełna nazwa formalna (najlepiej dokładnie jak w KRS/CEIDG/umowie).','ABC sp. z o.o.','Fundacja Rodzinna XYZ','text','INTERNAL','KRS/CEIDG',NULL,'Podmiot prawny',10,true),
('legal.short_name','Nazwa skrócona','Opcjonalnie: nazwa skrócona/marketingowa używana w korespondencji.','ABC',NULL,'text','INTERNAL','MANUAL',NULL,'Podmiot prawny',20,true),
('legal.legal_kind','Rodzaj podmiotu','Wybierz typ podmiotu (np. sp. z o.o., S.A., fundacja, wspólnota). Ułatwia formatowanie nazwy i walidację sufiksu.','SPOLKA_Z_OO','FUNDACJA','select','INTERNAL','MANUAL',NULL,'Podmiot prawny',30,true),
('legal.legal_form_suffix','Sufiks / skrót formy','Skrót formy prawnej, jeśli ma zastosowanie (np. “sp. z o.o.”, “sp.k.”, “S.A.”). Dla części podmiotów nie stosuje się sufiksu — wtedy zostaw puste.','sp. z o.o.','sp.k.','text','INTERNAL','MANUAL','Ustal wg formy prawnej','Podmiot prawny',50,true),
('legal.country','Kraj rejestracji','Zwykle PL. Jeśli podmiot zagraniczny, wpisz kod kraju (np. DE, CZ).','PL','PL','text','INTERNAL','MANUAL','2-literowy kod kraju','Podmiot prawny',60,true)
ON CONFLICT (field_key) DO UPDATE SET
  label_pl=EXCLUDED.label_pl, tooltip_pl=EXCLUDED.tooltip_pl, placeholder=EXCLUDED.placeholder,
  example_value=EXCLUDED.example_value, input_type=EXCLUDED.input_type, privacy_level=EXCLUDED.privacy_level,
  source_hint=EXCLUDED.source_hint, validation_hint=EXCLUDED.validation_hint, display_group=EXCLUDED.display_group,
  display_order=EXCLUDED.display_order, is_user_editable=EXCLUDED.is_user_editable;

-- Identifiers (logical fields as seen by the user)
INSERT INTO meta.ui_field_metadata
(field_key,label_pl,tooltip_pl,placeholder,example_value,input_type,privacy_level,source_hint,validation_hint,validation_rule,display_group,display_order,is_user_editable)
VALUES
('id.PESEL','PESEL','Numer PESEL osoby fizycznej. Pole wrażliwe. Jeśli pochodzi z dokumentu lub rejestru — preferuj automatyczne zasilanie / wpisuj bez spacji.','11 cyfr','8710109374','text','SENSITIVE','CEIDG/MANUAL','11 cyfr', '{"pattern":"^[0-9]{11}$"}','Identyfikatory',10,true),
('id.NIP','NIP','Numer NIP (osoba lub podmiot). Wpisuj bez spacji i kresek.','10 cyfr','5222837149','text','SENSITIVE','KRS/CEIDG/MANUAL','10 cyfr', '{"pattern":"^[0-9]{10}$"}','Identyfikatory',20,true),
('id.REGON','REGON','REGON (9 lub 14 cyfr). Wpisuj bez spacji.','9 lub 14 cyfr','012345678','text','INTERNAL','KRS/CEIDG/MANUAL','9 lub 14 cyfr', '{"pattern":"^[0-9]{9}([0-9]{5})?$"}','Identyfikatory',30,true),
('id.KRS','KRS','Numer KRS (zwykle 10 cyfr). Jeśli znany, pozwala automatycznie pobrać dane z KRS OpenAPI.','10 cyfr','0000123456','text','INTERNAL','KRS','10 cyfr', '{"pattern":"^[0-9]{10}$"}','Identyfikatory',40,true),
('id.RFR','Numer RFR','Numer rejestru fundacji rodzinnych (RFR), jeśli dotyczy.','—',NULL,'text','INTERNAL','MANUAL/AUTO',NULL,NULL,'Identyfikatory',50,true),
('id.OTHER_REGISTRY_NUMBER','Inny numer rejestrowy','Numer z innego rejestru (np. zagraniczny numer, numer ewidencyjny). Uzupełnij też nazwę rejestru.','—',NULL,'text','INTERNAL','MANUAL',NULL,NULL,'Identyfikatory',60,true),
('id.OTHER_REGISTRY_NAME','Nazwa rejestru','Nazwa rejestru dla “Innego numeru rejestrowego” (np. “Handelsregister”, “Companies House”).','—','Companies House','text','INTERNAL','MANUAL',NULL,NULL,'Identyfikatory',70,true)
ON CONFLICT (field_key) DO UPDATE SET
  label_pl=EXCLUDED.label_pl, tooltip_pl=EXCLUDED.tooltip_pl, placeholder=EXCLUDED.placeholder,
  example_value=EXCLUDED.example_value, input_type=EXCLUDED.input_type, privacy_level=EXCLUDED.privacy_level,
  source_hint=EXCLUDED.source_hint, validation_hint=EXCLUDED.validation_hint, validation_rule=EXCLUDED.validation_rule,
  display_group=EXCLUDED.display_group, display_order=EXCLUDED.display_order, is_user_editable=EXCLUDED.is_user_editable;

-- Contact points
INSERT INTO meta.ui_field_metadata
(field_key,label_pl,tooltip_pl,placeholder,example_value,input_type,privacy_level,source_hint,validation_hint,display_group,display_order,is_user_editable)
VALUES
('contact.EMAIL','E-mail','Adres e-mail (najlepiej służbowy). W CEIDG może się pojawiać automatycznie.','kontakt@firma.pl','kontakt@abc.pl','text','INTERNAL','CEIDG/MANUAL','Poprawny format e-mail','Kontakt',10,true),
('contact.PHONE','Telefon','Numer telefonu kontaktowego.','+48 600 000 000','+48 601 234 567','text','INTERNAL','CEIDG/MANUAL',NULL,'Kontakt',20,true),
('contact.WEBSITE','Strona WWW','Adres strony internetowej.','https://…','https://example.pl','text','INTERNAL','CEIDG/MANUAL',NULL,'Kontakt',30,true),
('contact.EPUAP','ePUAP','Identyfikator skrzynki ePUAP, jeśli używany do doręczeń.','/XYZ/SkrytkaESP',NULL,'text','INTERNAL','MANUAL',NULL,'Kontakt',40,true),
('contact.OTHER','Inny kontakt','Dowolny inny kanał (np. fax, komunikator) – wpisz w notatce co to jest.','Fax: …',NULL,'text','INTERNAL','MANUAL',NULL,'Kontakt',90,true)
ON CONFLICT (field_key) DO UPDATE SET
  label_pl=EXCLUDED.label_pl, tooltip_pl=EXCLUDED.tooltip_pl, placeholder=EXCLUDED.placeholder,
  example_value=EXCLUDED.example_value, input_type=EXCLUDED.input_type, privacy_level=EXCLUDED.privacy_level,
  source_hint=EXCLUDED.source_hint, validation_hint=EXCLUDED.validation_hint,
  display_group=EXCLUDED.display_group, display_order=EXCLUDED.display_order, is_user_editable=EXCLUDED.is_user_editable;

-- Addresses (logical fields)
INSERT INTO meta.ui_field_metadata
(field_key,label_pl,tooltip_pl,placeholder,example_value,input_type,privacy_level,source_hint,validation_hint,display_group,display_order,is_user_editable)
VALUES
('addr.address_type','Typ adresu','Wybierz rodzaj adresu (np. siedziba, do doręczeń, miejsce prowadzenia działalności). W CEIDG typy często wynikają z danych rejestrowych.','SIEDZIBA',NULL,'select','INTERNAL','CEIDG/KRS/MANUAL',NULL,'Adresy',5,true),

('addr.country','Kraj','Kod kraju (np. PL).','PL','PL','text','INTERNAL','MANUAL','2-literowy kod kraju','Adresy',10,true),
('addr.voivodeship','Województwo','Wpisz województwo (np. “mazowieckie”). Przy automatycznym imporcie może wypełniać się z kodów.','mazowieckie',NULL,'text','INTERNAL','CEIDG/MANUAL',NULL,'Adresy',20,true),
('addr.county','Powiat','Opcjonalnie.','Warszawa',NULL,'text','INTERNAL','CEIDG/MANUAL',NULL,'Adresy',30,true),
('addr.gmina','Gmina','Opcjonalnie.','Bemowo',NULL,'text','INTERNAL','CEIDG/MANUAL',NULL,'Adresy',40,true),
('addr.city','Miejscowość','Miasto/miejscowość.','Warszawa','Poznań','text','INTERNAL','CEIDG/KRS/MANUAL',NULL,'Adresy',50,true),
('addr.postal_code','Kod pocztowy','Wpisz w formacie 00-000.','00-000','00-815','text','INTERNAL','CEIDG/KRS/MANUAL','Format 00-000','Adresy',60,true),
('addr.post_office','Poczta','Opcjonalnie (czasem inna niż miejscowość).','Warszawa 50',NULL,'text','INTERNAL','CEIDG/MANUAL',NULL,'Adresy',70,true),
('addr.street','Ulica','Ulica bez numeru budynku.','Sienna','Chłodna','text','INTERNAL','CEIDG/KRS/MANUAL',NULL,'Adresy',80,true),
('addr.building_no','Nr budynku','Numer budynku (czasem z literą).','86','2A','text','INTERNAL','CEIDG/KRS/MANUAL',NULL,'Adresy',90,true),
('addr.unit_no','Nr lokalu','Numer lokalu (jeśli dotyczy).','137','44','text','INTERNAL','CEIDG/KRS/MANUAL',NULL,'Adresy',100,true),
('addr.additional_line','Dodatkowa linia','Np. piętro, “c/o”, uwagi do lokalizacji.','lok. 1',NULL,'text','INTERNAL','MANUAL',NULL,'Adresy',110,true),
('addr.teryt_terc','TERC (opcjonalnie)','Kod TERYT TERC jeśli dostępny z automatycznego importu (nie wpisuj ręcznie, jeśli nie musisz).',NULL,NULL,'text','INTERNAL','AUTO',NULL,'Adresy',200,false),
('addr.teryt_simc','SIMC (opcjonalnie)','Kod TERYT SIMC z importu. Zwykle pole techniczne.',NULL,NULL,'text','INTERNAL','AUTO',NULL,'Adresy',210,false),
('addr.teryt_ulic','ULIC (opcjonalnie)','Kod TERYT ULIC z importu. Zwykle pole techniczne.',NULL,NULL,'text','INTERNAL','AUTO',NULL,'Adresy',220,false),
('addr.freeform_note','Opis lokalizacji nietypowej','Gdy adres nie pasuje do standardu (np. działka, bez ulicy) – krótki opis.', 'np. “działka nr …”',NULL,'textarea','INTERNAL','MANUAL',NULL,'Adresy',300,true)
ON CONFLICT (field_key) DO UPDATE SET
  label_pl=EXCLUDED.label_pl, tooltip_pl=EXCLUDED.tooltip_pl, placeholder=EXCLUDED.placeholder,
  example_value=EXCLUDED.example_value, input_type=EXCLUDED.input_type, privacy_level=EXCLUDED.privacy_level,
  source_hint=EXCLUDED.source_hint, validation_hint=EXCLUDED.validation_hint,
  display_group=EXCLUDED.display_group, display_order=EXCLUDED.display_order, is_user_editable=EXCLUDED.is_user_editable;

-- Registry profiles (mostly auto-filled)
INSERT INTO meta.ui_field_metadata
(field_key,label_pl,tooltip_pl,placeholder,example_value,input_type,privacy_level,source_hint,validation_hint,display_group,display_order,is_user_editable)
VALUES
('krs.krs_number','KRS (profil)','Pole techniczne profilu KRS. Zasilane automatycznie po pobraniu danych z KRS.','0000000000','0000123456','text','INTERNAL','KRS',NULL,'Rejestry – KRS',10,false),
('krs.registry_status','Status w KRS','Status wynikający z danych KRS (np. aktywna, w likwidacji). Nie edytuj ręcznie.','—',NULL,'text','INTERNAL','KRS',NULL,'Rejestry – KRS',20,false),
('krs.pkds','PKD (KRS)','Kody PKD z KRS. Nie edytuj ręcznie (źródło: KRS).',NULL,NULL,'multiselect','INTERNAL','KRS',NULL,'Rejestry – KRS',30,false),
('krs.payload','Dane surowe KRS','Pełny surowy payload z KRS (do audytu i ponownego parsowania).','—',NULL,'textarea','INTERNAL','KRS',NULL,'Rejestry – KRS',99,false),

('ceidg.unique_id','Identyfikator wpisu CEIDG','Pole techniczne z CEIDG. Nie edytuj ręcznie.',NULL,NULL,'text','INTERNAL','CEIDG',NULL,'Rejestry – CEIDG',10,false),
('ceidg.status','Status CEIDG','Status działalności wg CEIDG (aktywny/zawieszony/zakończony). Nie edytuj ręcznie.',NULL,NULL,'text','INTERNAL','CEIDG',NULL,'Rejestry – CEIDG',20,false),
('ceidg.business_name','Firma (CEIDG)','Nazwa firmy osoby fizycznej wg CEIDG. Zasilane automatycznie.',NULL,NULL,'text','INTERNAL','CEIDG',NULL,'Rejestry – CEIDG',30,false),
('ceidg.start_date','Data rozpoczęcia działalności',NULL,'YYYY-MM-DD',NULL,'date','INTERNAL','CEIDG',NULL,'Rejestry – CEIDG',40,false),
('ceidg.end_date','Data zakończenia działalności',NULL,'YYYY-MM-DD',NULL,'date','INTERNAL','CEIDG',NULL,'Rejestry – CEIDG',50,false),
('ceidg.suspension_date','Data zawieszenia',NULL,'YYYY-MM-DD',NULL,'date','INTERNAL','CEIDG',NULL,'Rejestry – CEIDG',60,false),
('ceidg.resume_date','Data wznowienia',NULL,'YYYY-MM-DD',NULL,'date','INTERNAL','CEIDG',NULL,'Rejestry – CEIDG',70,false),
('ceidg.pkds','PKD (CEIDG)','Kody PKD z CEIDG. Nie edytuj ręcznie.',NULL,NULL,'multiselect','INTERNAL','CEIDG',NULL,'Rejestry – CEIDG',80,false),
('ceidg.payload','Dane surowe CEIDG','Pełny surowy payload z CEIDG (do audytu i ponownego parsowania).','—',NULL,'textarea','INTERNAL','CEIDG',NULL,'Rejestry – CEIDG',99,false)
ON CONFLICT (field_key) DO UPDATE SET
  label_pl=EXCLUDED.label_pl, tooltip_pl=EXCLUDED.tooltip_pl, placeholder=EXCLUDED.placeholder,
  example_value=EXCLUDED.example_value, input_type=EXCLUDED.input_type, privacy_level=EXCLUDED.privacy_level,
  source_hint=EXCLUDED.source_hint, validation_hint=EXCLUDED.validation_hint,
  display_group=EXCLUDED.display_group, display_order=EXCLUDED.display_order, is_user_editable=EXCLUDED.is_user_editable;

-- Registry snapshots (internal only)
INSERT INTO meta.ui_field_metadata
(field_key,label_pl,tooltip_pl,placeholder,example_value,input_type,privacy_level,source_hint,validation_hint,display_group,display_order,is_user_editable)
VALUES
('snapshot.lookup_key','Klucz pobrania','Klucz użyty do pobrania danych (np. KRS, NIP, CEIDG uniqueId). Pole techniczne.','—',NULL,'text','INTERNAL','AUTO',NULL,'Rejestry – Snapshot',10,false),
('snapshot.fetched_at','Data pobrania','Kiedy pobrano dane z rejestru. Pole techniczne.',NULL,NULL,'date','INTERNAL','AUTO',NULL,'Rejestry – Snapshot',20,false),
('snapshot.payload_format','Format payloadu','JSON lub XML. Pole techniczne.',NULL,NULL,'text','INTERNAL','AUTO',NULL,'Rejestry – Snapshot',30,false),
('snapshot.payload_hash','Hash payloadu','Używane do wykrywania zmian bez porównywania całej treści. Pole techniczne.',NULL,NULL,'text','INTERNAL','AUTO',NULL,'Rejestry – Snapshot',40,false),
('snapshot.payload_raw','Payload surowy','Surowa odpowiedź z rejestru do audytu. Pole techniczne.',NULL,NULL,'textarea','INTERNAL','AUTO',NULL,'Rejestry – Snapshot',50,false)
ON CONFLICT (field_key) DO UPDATE SET
  label_pl=EXCLUDED.label_pl, tooltip_pl=EXCLUDED.tooltip_pl, placeholder=EXCLUDED.placeholder,
  example_value=EXCLUDED.example_value, input_type=EXCLUDED.input_type, privacy_level=EXCLUDED.privacy_level,
  source_hint=EXCLUDED.source_hint, validation_hint=EXCLUDED.validation_hint,
  display_group=EXCLUDED.display_group, display_order=EXCLUDED.display_order, is_user_editable=EXCLUDED.is_user_editable;

-- Registry-derived affiliations (mostly auto-filled; optionally allow manual override later)
INSERT INTO meta.ui_field_metadata
(field_key,label_pl,tooltip_pl,placeholder,example_value,input_type,privacy_level,source_hint,validation_hint,display_group,display_order,is_user_editable)
VALUES
('aff.subject_entity','Podmiot (osoba/podmiot)','Osoba lub podmiot pełniący funkcję (np. członek zarządu, prokurent). Zwykle zasilane z KRS/CEIDG.',NULL,NULL,'text','INTERNAL','KRS/CEIDG',NULL,'Powiązania rejestrowe',10,false),
('aff.object_entity','Podmiot docelowy','Podmiot, którego dotyczy funkcja (np. spółka, w której osoba jest członkiem zarządu).',NULL,NULL,'text','INTERNAL','KRS/CEIDG',NULL,'Powiązania rejestrowe',20,false),
('aff.affiliation_type','Typ powiązania','Rodzaj roli/powiązania pochodzący z rejestru (np. członek zarządu, prokurent, wspólnik s.c.).',NULL,NULL,'select','INTERNAL','KRS/CEIDG',NULL,'Powiązania rejestrowe',30,false),
('aff.function_title','Funkcja / tytuł','Dokładna funkcja z rejestru (np. “Prezes Zarządu”, “Członek Zarządu”).', 'Prezes Zarządu',NULL,'text','INTERNAL','KRS/CEIDG',NULL,'Powiązania rejestrowe',40,false),
('aff.representation_mode','Sposób reprezentacji','Jeśli rejestr podaje zasady reprezentacji (np. “dwóch członków zarządu łącznie”).',NULL,NULL,'textarea','INTERNAL','KRS',NULL,'Powiązania rejestrowe',50,false),
('aff.scope','Zakres','Zakres roli, jeśli dotyczy (np. rodzaj prokury).',NULL,NULL,'text','INTERNAL','KRS/CEIDG',NULL,'Powiązania rejestrowe',60,false),
('aff.valid_from','Obowiązuje od',NULL,'YYYY-MM-DD',NULL,'date','INTERNAL','KRS/CEIDG',NULL,'Powiązania rejestrowe',70,false),
('aff.valid_to','Obowiązuje do',NULL,'YYYY-MM-DD',NULL,'date','INTERNAL','KRS/CEIDG',NULL,'Powiązania rejestrowe',80,false),
('aff.is_current','Aktualne','Czy jest aktualne wg ostatniego pobrania rejestru.',NULL,NULL,'boolean','INTERNAL','AUTO',NULL,'Powiązania rejestrowe',90,false),
('aff.status','Status powiązania','ACTIVE/ENDED/UNKNOWN – stan techniczny w systemie na podstawie kolejnych pobrań.',NULL,NULL,'select','INTERNAL','AUTO',NULL,'Powiązania rejestrowe',100,false),
('aff.confidence','Pewność','Używane gdy parsowanie jest niepewne (np. OCR). Zwykle 100 przy danych API.',NULL,NULL,'text','INTERNAL','AUTO',NULL,'Powiązania rejestrowe',110,false)
ON CONFLICT (field_key) DO UPDATE SET
  label_pl=EXCLUDED.label_pl, tooltip_pl=EXCLUDED.tooltip_pl, placeholder=EXCLUDED.placeholder,
  example_value=EXCLUDED.example_value, input_type=EXCLUDED.input_type, privacy_level=EXCLUDED.privacy_level,
  source_hint=EXCLUDED.source_hint, validation_hint=EXCLUDED.validation_hint,
  display_group=EXCLUDED.display_group, display_order=EXCLUDED.display_order, is_user_editable=EXCLUDED.is_user_editable;

/* =========================
   UI ENUM METADATA
   ========================= */

-- entity_type values (as the UI should show them)
INSERT INTO meta.ui_enum_metadata (enum_key, enum_value, label_pl, tooltip_pl, display_order)
VALUES
('entity_type','PHYSICAL_PERSON','Osoba fizyczna','Człowiek (np. klient, członek zarządu, wierzyciel).',10),
('entity_type','LEGAL_PERSON','Podmiot prawny','Podmiot niebędący osobą fizyczną (spółka, fundacja, spółdzielnia, wspólnota itd.).',20)
ON CONFLICT (enum_key, enum_value) DO UPDATE SET
  label_pl=EXCLUDED.label_pl, tooltip_pl=EXCLUDED.tooltip_pl, display_order=EXCLUDED.display_order;

-- legal_kind (selected key values; extend as you wish)
INSERT INTO meta.ui_enum_metadata (enum_key, enum_value, label_pl, tooltip_pl, suffix_default, is_suffix_applicable, display_order)
VALUES
('legal_kind','SPOLKA_JAWNA','Spółka jawna','Spółka osobowa. Często używa skrótu w nazwie.','sp. j.',true,10),
('legal_kind','SPOLKA_PARTNERSKA','Spółka partnerska','Spółka osobowa dla wolnych zawodów.','sp.p.',true,20),
('legal_kind','SPOLKA_KOMANDYTOWA','Spółka komandytowa','Spółka osobowa.','sp.k.',true,30),
('legal_kind','SPOLKA_KOMANDYTOWO_AKCYJNA','Spółka komandytowo-akcyjna','Spółka hybrydowa.','S.K.A.',true,40),
('legal_kind','SPOLKA_Z_OO','Spółka z ograniczoną odpowiedzialnością','Spółka kapitałowa.','sp. z o.o.',true,50),
('legal_kind','SPOLKA_AKCYJNA','Spółka akcyjna','Spółka kapitałowa.','S.A.',true,60),
('legal_kind','PROSTA_SPOLKA_AKCYJNA','Prosta spółka akcyjna','Spółka kapitałowa.','P.S.A.',true,70),
('legal_kind','FUNDACJA','Fundacja','Zwykle bez sufiksu skrótowego; nazwa formalna wynika z aktu/rejestru.',NULL,false,80),
('legal_kind','STOWARZYSZENIE','Stowarzyszenie','Zwykle bez sufiksu skrótowego; nazwa formalna wynika z rejestru/statutu.',NULL,false,90),
('legal_kind','FUNDACJA_RODZINNA','Fundacja rodzinna','Podmiot szczególny (RFR). W praktyce używa się pełnego określenia.',NULL,false,100),
('legal_kind','SPOLDZIELNIA','Spółdzielnia','Nazwa zwykle zawiera “spółdzielnia/spółdzielczy”; brak typowego sufiksu jak sp.k.',NULL,false,110),
('legal_kind','SPOLDZIELNIA_MIESZKANIOWA','Spółdzielnia mieszkaniowa','Rodzaj spółdzielni; brak typowego sufiksu.',NULL,false,120),
('legal_kind','WSPOLNOTA_MIESZKANIOWA','Wspólnota mieszkaniowa','Zwykle brak KRS; istotne bywają NIP/REGON i adres nieruchomości.',NULL,false,130),
('legal_kind','SPOLKA_CYWILNA','Spółka cywilna','Umowa cywilna między wspólnikami; w praktyce bywa identyfikowana NIP/REGON “s.c.”.',NULL,false,140),
('legal_kind','OTHER','Inny','Użyj gdy brak dopasowania do listy.',NULL,false,999)
ON CONFLICT (enum_key, enum_value) DO UPDATE SET
  label_pl=EXCLUDED.label_pl, tooltip_pl=EXCLUDED.tooltip_pl,
  suffix_default=EXCLUDED.suffix_default, is_suffix_applicable=EXCLUDED.is_suffix_applicable,
  display_order=EXCLUDED.display_order;

-- affiliation_type (starter set; extend later)
INSERT INTO meta.ui_enum_metadata (enum_key, enum_value, label_pl, tooltip_pl, display_order)
VALUES
('affiliation_type','MANAGEMENT_BOARD_MEMBER','Członek zarządu','Funkcja w organie zarządzającym spółki/podmiotu.',10),
('affiliation_type','SUPERVISORY_BOARD_MEMBER','Członek rady nadzorczej','Funkcja nadzorcza (jeśli dotyczy).',20),
('affiliation_type','LIQUIDATOR','Likwidator','Osoba prowadząca likwidację podmiotu.',30),
('affiliation_type','PROXY_PROKURENT','Prokurent','Prokurent ujawniony w rejestrze (zakres w polu “Zakres”).',40),
('affiliation_type','REPRESENTATIVE','Uprawniony do reprezentacji','Ogólne uprawnienie do reprezentacji wg rejestru.',50),
('affiliation_type','CIVIL_PARTNERSHIP_PARTNER','Wspólnik spółki cywilnej','Powiązanie osoby z podmiotem “spółka cywilna”.',60),
('affiliation_type','OTHER_REGISTRY_ROLE','Inna rola rejestrowa','Rola nietypowa – doprecyzuj w polu “Funkcja / tytuł”.',999)
ON CONFLICT (enum_key, enum_value) DO UPDATE SET
  label_pl=EXCLUDED.label_pl, tooltip_pl=EXCLUDED.tooltip_pl, display_order=EXCLUDED.display_order;

COMMIT;

