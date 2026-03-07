"""Collect regional court data from SAOS API and dane.gov.pl.

Fetches court hierarchy from SAOS API and authoritative name list from
dane.gov.pl, merges them, and outputs a JSON file for review.

Usage:
    python scripts/collect_regional_courts.py
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

import requests

SAOS_BASE_URL = "https://www.saos.org.pl/api/dump/commonCourts"
SAOS_PAGE_SIZE = 100
SAOS_MAX_PAGES = 10  # safety limit

DANE_GOV_URL = "https://api.dane.gov.pl/resources/65134,lista-sadow-powszechnych/csv"

OUTPUT_FILE = Path(__file__).parent / "regional_courts_data.json"

# Our 47 district court enum codes (from the migration)
DISTRICT_COURT_ENUMS = [
    "sad_okregowy_bialystok", "sad_okregowy_lomza", "sad_okregowy_olsztyn",
    "sad_okregowy_ostroleka", "sad_okregowy_suwalki",
    "sad_okregowy_bydgoszcz", "sad_okregowy_elblag", "sad_okregowy_gdansk",
    "sad_okregowy_slupsk", "sad_okregowy_torun", "sad_okregowy_wloclawek",
    "sad_okregowy_bielsko_biala", "sad_okregowy_czestochowa", "sad_okregowy_gliwice",
    "sad_okregowy_katowice", "sad_okregowy_rybnik", "sad_okregowy_sosnowiec",
    "sad_okregowy_kielce", "sad_okregowy_krakow", "sad_okregowy_nowy_sacz",
    "sad_okregowy_tarnow",
    "sad_okregowy_lublin", "sad_okregowy_radom", "sad_okregowy_siedlce",
    "sad_okregowy_zamosc",
    "sad_okregowy_kalisz", "sad_okregowy_lodz", "sad_okregowy_piotrkow_trybunalski",
    "sad_okregowy_plock", "sad_okregowy_sieradz",
    "sad_okregowy_konin", "sad_okregowy_poznan", "sad_okregowy_zielona_gora",
    "sad_okregowy_krosno", "sad_okregowy_przemysl", "sad_okregowy_rzeszow",
    "sad_okregowy_tarnobrzeg",
    "sad_okregowy_gorzow_wielkopolski", "sad_okregowy_koszalin", "sad_okregowy_szczecin",
    "sad_okregowy_warszawa", "sad_okregowy_warszawa_praga",
    "sad_okregowy_jelenia_gora", "sad_okregowy_legnica", "sad_okregowy_opole",
    "sad_okregowy_swidnica", "sad_okregowy_wroclaw",
]

# Polish char transliteration
POLISH_TRANS = str.maketrans({
    "ą": "a", "ć": "c", "ę": "e", "ł": "l", "ń": "n",
    "ó": "o", "ś": "s", "ź": "z", "ż": "z",
    "Ą": "A", "Ć": "C", "Ę": "E", "Ł": "L", "Ń": "N",
    "Ó": "O", "Ś": "S", "Ź": "Z", "Ż": "Z",
})


def transliterate(text: str) -> str:
    return text.translate(POLISH_TRANS)


def name_to_slug(name: str) -> str:
    """Convert a regional court name to a canonical slug code.

    Examples:
        'Sąd Rejonowy w Białymstoku' -> 'sad_rejonowy_bialymstoku'
        'Sąd Rejonowy dla Warszawy-Mokotowa' -> 'sad_rejonowy_warszawy_mokotowa'
        'Sąd Rejonowy Gdańsk-Południe w Gdańsku' -> 'sad_rejonowy_gdansk_poludnie'
        'Sąd Rejonowy Lublin-Wschód w Lublinie z siedzibą w Świdniku'
            -> 'sad_rejonowy_lublin_wschod'
    """
    s = name.strip()
    # Remove "Sąd Rejonowy " prefix
    s = re.sub(r'^Sąd Rejonowy\s+', '', s)
    # Remove "z siedzibą w ..." suffix
    s = re.sub(r'\s*z siedzibą w\s+\S+.*$', '', s)

    # Handle compound names with distinctive part before "w/we CityName":
    # e.g. "Gdańsk-Południe w Gdańsku" -> keep "Gdańsk-Południe"
    # e.g. "dla Krakowa-Nowej Huty w Krakowie" -> keep "Krakowa-Nowej Huty"
    # But for simple "w Białymstoku" -> keep "Białymstoku" (the city in locative)
    m = re.match(r'^(dla\s+)?(.+?)\s+w[e]?\s+\S+(\s+\S+)?$', s)
    if m:
        distinctive = m.group(2).strip()
        if distinctive and distinctive not in ("w", "we"):
            s = distinctive
        else:
            # Simple form: "w Białymstoku" -> extract just "Białymstoku"
            m2 = re.match(r'^w[e]?\s+(.+)$', s)
            if m2:
                s = m2.group(1)
    else:
        # No trailing "w/we CityName" — might start with "w/we" directly
        m2 = re.match(r'^w[e]?\s+(.+)$', s)
        if m2:
            s = m2.group(1)

    # Remove "dla " prefix
    s = re.sub(r'^dla\s+', '', s)
    # Remove "miasta stołecznego"
    s = re.sub(r'miasta stołecznego\s*', '', s)
    # Transliterate
    s = transliterate(s)
    # Lowercase
    s = s.lower()
    # Replace hyphens and spaces with underscores
    s = re.sub(r'[-\s]+', '_', s)
    # Remove non-alphanumeric except underscore
    s = re.sub(r'[^a-z0-9_]', '', s)
    # Collapse multiple underscores
    s = re.sub(r'_+', '_', s)
    # Strip leading/trailing underscores
    s = s.strip('_')

    return f"sad_rejonowy_{s}"


def locative_to_nominative(city_loc: str) -> str:
    """Best-effort conversion of Polish city name from locative to nominative case.

    Common patterns (locative → nominative):
      -stoku → -stok, -owie → -ów, -sku → -sk, -niu → -ń/-nio,
      -cu → -ec/-c, -dzie → -d/-da, -rzu → -rz, etc.
    """
    s = city_loc.strip()

    # Hardcoded exceptions (irregular or ambiguous)
    exceptions = {
        "Białymstoku": "Białystok",
        "Bielsku Podlaskim": "Bielsk Podlaski",
        "Bielsku-Białej": "Bielsko-Biała",
        "Białej Podlaskiej": "Biała Podlaska",
        "Bydgoszczy": "Bydgoszcz",
        "Jeleniej Górze": "Jelenia Góra",
        "Zielonej Górze": "Zielona Góra",
        "Nowym Sączu": "Nowy Sącz",
        "Nowym Targu": "Nowy Targ",
        "Nowym Dworze Mazowieckim": "Nowy Dwór Mazowiecki",
        "Nowym Mieście Lubawskim": "Nowe Miasto Lubawskie",
        "Starym Sączu": "Stary Sącz",
        "Jastrzębiu-Zdroju": "Jastrzębie-Zdrój",
        "Busku-Zdroju": "Busko-Zdrój",
        "Jaśle": "Jasło",
        "Kole": "Koło",
        "Opolu Lubelskim": "Opole Lubelskie",
        "Grójcu": "Grójec",
        "Końskich": "Końskie",
        "Łańcucie": "Łańcut",
        "Mińsku Mazowieckim": "Mińsk Mazowiecki",
        "Środzie Śląskiej": "Środa Śląska",
        "Środzie Wielkopolskiej": "Środa Wielkopolska",
        "Piotrkowie Trybunalskim": "Piotrków Trybunalski",
        "Gorzowie Wielkopolskim": "Gorzów Wielkopolski",
        "Aleksandrowie Kujawskim": "Aleksandrów Kujawski",
        "Nakle nad Notecią": "Nakło nad Notecią",
        "Wodzisławiu Śląskim": "Wodzisław Śląski",
        "Dąbrowie Górniczej": "Dąbrowa Górnicza",
        "Dąbrowie Tarnowskiej": "Dąbrowa Tarnowska",
        "Inowrocławiu": "Inowrocław",
        "Wrocławiu": "Wrocław",
        "Włocławku": "Włocławek",
        "Kędzierzynie-Koźlu": "Kędzierzyn-Koźle",
        "Zduńskiej Woli": "Zduńska Wola",
        "Kamiennej Górze": "Kamienna Góra",
        "Sosnowcu": "Sosnowiec",
        "Wadowicach": "Wadowice",
        "Mysłowicach": "Mysłowice",
        "Mikołowie": "Mikołów",
        "Bytomiu": "Bytom",
        "Chorzowie": "Chorzów",
        "Tychach": "Tychy",
        "Zabrzu": "Zabrze",
        "Siemianowicach Śląskich": "Siemianowice Śląskie",
        "Piekarach Śląskich": "Piekary Śląskie",
        "Rudzie Śląskiej": "Ruda Śląska",
        "Świętochłowicach": "Świętochłowice",
        "Rudzie Śl.": "Ruda Śląska",
        "Katowicach": "Katowice",
        "Gliwicach": "Gliwice",
        "Rybniku": "Rybnik",
        "Żorach": "Żory",
        "Tarnowskich Górach": "Tarnowskie Góry",
        "Częstochowie": "Częstochowa",
        "Pszczynie": "Pszczyna",
        "Raciborzu": "Racibórz",
        "Cieszynie": "Cieszyn",
        "Żywcu": "Żywiec",
        "Kielcach": "Kielce",
        "Ostrołęce": "Ostrołęka",
        "Łomży": "Łomża",
        "Elblągu": "Elbląg",
        "Gdańsku": "Gdańsk",
        "Słupsku": "Słupsk",
        "Toruniu": "Toruń",
        "Krakowie": "Kraków",
        "Tarnowie": "Tarnów",
        "Lublinie": "Lublin",
        "Radomiu": "Radom",
        "Zamościu": "Zamość",
        "Kaliszu": "Kalisz",
        "Łodzi": "Łódź",
        "Płocku": "Płock",
        "Sieradzu": "Sieradz",
        "Koninie": "Konin",
        "Poznaniu": "Poznań",
        "Krośnie": "Krosno",
        "Przemyślu": "Przemyśl",
        "Rzeszowie": "Rzeszów",
        "Tarnobrzegu": "Tarnobrzeg",
        "Koszalinie": "Koszalin",
        "Szczecinie": "Szczecin",
        "Warszawie": "Warszawa",
        "Opolu": "Opole",
        "Świdnicy": "Świdnica",
        "Legnicy": "Legnica",
        "Suwałkach": "Suwałki",
        "Siedlcach": "Siedlce",
        "Olsztynie": "Olsztyn",
    }

    # Additional cities (all remaining locative→nominative conversions for
    # cities found in regional court names, sorted alphabetically)
    exceptions.update({
        "Biskupcu": "Biskupiec",
        "Biłgoraju": "Biłgoraj",
        "Bochni": "Bochnia",
        "Bolesławcu": "Bolesławiec",
        "Braniewie": "Braniewo",
        "Brodnicy": "Brodnica",
        "Brzegu": "Brzeg",
        "Będzinie": "Będzin",
        "Chełmie": "Chełm",
        "Chełmnie": "Chełmno",
        "Chodzieży": "Chodzież",
        "Choszcznie": "Choszczno",
        "Drawsku Pomorskim": "Drawsko Pomorskie",
        "Dębicy": "Dębica",
        "Ełku": "Ełk",
        "Garwolinie": "Garwolin",
        "Gdyni": "Gdynia",
        "Giżycku": "Giżycko",
        "Gnieźnie": "Gniezno",
        "Golubiu-Dobrzyń": "Golub-Dobrzyń",
        "Gostyninie": "Gostynin",
        "Grajewie": "Grajewo",
        "Grodzisku Mazowieckim": "Grodzisk Mazowiecki",
        "Grodzisku Wielkopolskim": "Grodzisk Wielkopolski",
        "Grudziądzu": "Grudziądz",
        "Gryfinie": "Gryfino",
        "Iławie": "Iława",
        "Janowie Lubelskim": "Janów Lubelski",
        "Jarocinie": "Jarocin",
        "Jarosławiu": "Jarosław",
        "Jaworze": "Jawor",
        "Jaworznie": "Jaworzno",
        "Kamieniu Pomorskim": "Kamień Pomorski",
        "Kartuzach": "Kartuzy",
        "Kluczborku": "Kluczbork",
        "Kolbuszowej": "Kolbuszowa",
        "Kołobrzegu": "Kołobrzeg",
        "Kościanie": "Kościan",
        "Kościerzynie": "Kościerzyna",
        "Krasnymstawie": "Krasnystaw",
        "Kraśniku": "Kraśnik",
        "Krotoszynie": "Krotoszyn",
        "Krośnie Odrzańskim": "Krosno Odrzańskie",
        "Kutnie": "Kutno",
        "Kwidzynie": "Kwidzyn",
        "Kępnie": "Kępno",
        "Kętrzynie": "Kętrzyn",
        "Kłodzku": "Kłodzko",
        "Lesznie": "Leszno",
        "Lidzbarku Warmińskim": "Lidzbark Warmiński",
        "Limanowej": "Limanowa",
        "Lipnie": "Lipno",
        "Lubinie": "Lubin",
        "Lublińcu": "Lubliniec",
        "Lwówku Śląskim": "Lwówek Śląski",
        "Lęborku": "Lębork",
        "Malborku": "Malbork",
        "Miastku": "Miastko",
        "Mielcu": "Mielec",
        "Miliczu": "Milicz",
        "Międzyrzeczu": "Międzyrzecz",
        "Mogilnie": "Mogilno",
        "Mławie": "Mława",
        "Myśliborzu": "Myślibórz",
        "Nidzicy": "Nidzica",
        "Nowej Soli": "Nowa Sól",
        "Nowym Tomyślu": "Nowy Tomyśl",
        "Nysie": "Nysa",
        "Obornikach": "Oborniki",
        "Olecku": "Olecko",
        "Oleśnicy": "Oleśnica",
        "Oleśnie": "Oleśno",
        "Olkuszu": "Olkusz",
        "Opocznie": "Opoczno",
        "Ostrodzie": "Ostróda",
        "Ostrowcu Świętokrzyskim": "Ostrowiec Świętokrzyski",
        "Ostrowi Mazowieckiej": "Ostrów Mazowiecka",
        "Ostrowie Wielkopolskim": "Ostrów Wielkopolski",
        "Otwocku": "Otwock",
        "Oławie": "Oława",
        "Oświęcimiu": "Oświęcim",
        "Piasecznie": "Piaseczno",
        "Pile": "Piła",
        "Piszu": "Pisz",
        "Pleszewie": "Pleszew",
        "Prudniku": "Prudnik",
        "Przasnyszu": "Przasnysz",
        "Przysusze": "Przysucha",
        "Puławach": "Puławy",
        "Radzyniu Podlaskim": "Radzyń Podlaski",
        "Rawiczu": "Rawicz",
        "Rawie Mazowieckiej": "Rawa Mazowiecka",
        "Rykach": "Ryki",
        "Rypinie": "Rypin",
        "Sandomierzu": "Sandomierz",
        "Sanoku": "Sanok",
        "Sierpcu": "Sierpc",
        "Skarżysku-Kamiennej": "Skarżysko-Kamienna",
        "Sochaczewie": "Sochaczew",
        "Sokołowie Podlaskim": "Sokołów Podlaski",
        "Sokółce": "Sokółka",
        "Sopocie": "Sopot",
        "Stalowej Woli": "Stalowa Wola",
        "Stargardzie": "Stargard",
        "Starogardzie Gdańskim": "Starogard Gdański",
        "Strzelcach Krajeńskich": "Strzelce Krajeńskie",
        "Strzelcach Opolskich": "Strzelce Opolskie",
        "Strzelinie": "Strzelin",
        "Suchej Beskidzkiej": "Sucha Beskidzka",
        "Sulęcinie": "Sulęcin",
        "Szamotułach": "Szamotuły",
        "Szczecinku": "Szczecinek",
        "Szczytnie": "Szczytno",
        "Szubinie": "Szubin",
        "Szydłowcu": "Szydłowiec",
        "Sławnie": "Sławno",
        "Słupcy": "Słupca",
        "Śremie": "Śrem",
        "Świdniku": "Świdnik",
        "Świebodzinie": "Świebodzin",
        "Świeciu": "Świecie",
        "Świnoujściu": "Świnoujście",
        "Tczewie": "Tczew",
        "Tomaszowie Lubelskim": "Tomaszów Lubelski",
        "Tomaszowie Mazowieckim": "Tomaszów Mazowiecki",
        "Trzciance": "Trzcianka",
        "Trzebnicy": "Trzebnica",
        "Tucholi": "Tuchola",
        "Turku": "Turek",
        "Wałbrzychu": "Wałbrzych",
        "Wałczu": "Wałcz",
        "Wieliczce": "Wieliczka",
        "Wolsztynie": "Wolsztyn",
        "Wołominie": "Wołomin",
        "Wrześni": "Września",
        "Wąbrzeźnie": "Wąbrzeźno",
        "Wągrowcu": "Wągrowiec",
        "Włodawie": "Włodawa",
        "Wysokiem Mazowieckiem": "Wysokie Mazowieckie",
        "Zakopanem": "Zakopane",
        "Zawierciu": "Zawiercie",
        "Zgorzelcu": "Zgorzelec",
        "Zgierzu": "Zgierz",
        "Złotoryi": "Złotoryja",
        "Ząbkowicach Śląskich": "Ząbkowice Śląskie",
        "Żarach": "Żary",
        "Żninie": "Żnin",
        "Łobzie": "Łobez",
        "Łowiczu": "Łowicz",
        "Łęczycy": "Łęczyca",
    })

    if s in exceptions:
        return exceptions[s]

    # Pattern-based rules (less common cities)
    # -owie → -ów (e.g., Lubartowie → Lubartów)
    m = re.match(r'^(.+)owie$', s)
    if m:
        return m.group(1) + "ów"

    # -niu → -ń (e.g., Starachowicach not, but Koninie → Konin done above)
    # -cach → -ce (e.g., Kielcach → Kielce, Wadowicach → Wadowice)
    m = re.match(r'^(.+)cach$', s)
    if m:
        return m.group(1) + "ce"

    # -nach → -ny/-na (e.g., Brzezinach → Brzeziny)
    m = re.match(r'^(.+)nach$', s)
    if m:
        return m.group(1) + "ny"

    # -sku → -sk (e.g., Gdańsku → Gdańsk)
    m = re.match(r'^(.+)sku$', s)
    if m:
        return m.group(1) + "sk"

    # -niu → -ń (e.g., Lublinie → Lublin)
    m = re.match(r'^(.+)niu$', s)
    if m:
        return m.group(1) + "ń"

    # -nie → -ń/-no/-nia (too ambiguous, skip)

    # -dzie → -d (e.g., Stargardzie → Stargard)
    m = re.match(r'^(.+)dzie$', s)
    if m:
        return m.group(1) + "d"

    # -rze → -ra or -r (ambiguous, skip)

    # -ie → strip -e, various (too many patterns)

    # Fallback: return as-is (locative form)
    return s


def extract_city(name: str) -> str:
    """Extract city name from a court name, converting to nominative case.

    Uses 'z siedzibą w X' if present, otherwise 'w/we X'.
    """
    # "z siedzibą w X" overrides
    m = re.search(r'z siedzibą w[e]?\s+(.+)$', name)
    if m:
        return locative_to_nominative(m.group(1).strip())
    # Standard "w/we X" at end
    m = re.search(r'\s+w[e]?\s+([A-ZŁŚŻŹĆĄ][\wąćęłńóśźżĄĆĘŁŃÓŚŹŻ\s-]+)$', name)
    if m:
        return locative_to_nominative(m.group(1).strip())
    return ""


def normalize_for_matching(name: str) -> str:
    """Normalize court name for fuzzy matching."""
    s = name.strip().lower()
    s = transliterate(s)
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


# Direct mapping: SAOS district court name -> our enum code.
# Polish locative case makes name parsing unreliable, so we hardcode all 47.
SAOS_DISTRICT_NAME_TO_ENUM = {
    "Sąd Okręgowy w Białymstoku": "sad_okregowy_bialystok",
    "Sąd Okręgowy w Łomży": "sad_okregowy_lomza",
    "Sąd Okręgowy w Olsztynie": "sad_okregowy_olsztyn",
    "Sąd Okręgowy w Ostrołęce": "sad_okregowy_ostroleka",
    "Sąd Okręgowy w Suwałkach": "sad_okregowy_suwalki",
    "Sąd Okręgowy w Bydgoszczy": "sad_okregowy_bydgoszcz",
    "Sąd Okręgowy w Elblągu": "sad_okregowy_elblag",
    "Sąd Okręgowy w Gdańsku": "sad_okregowy_gdansk",
    "Sąd Okręgowy w Słupsku": "sad_okregowy_slupsk",
    "Sąd Okręgowy w Toruniu": "sad_okregowy_torun",
    "Sąd Okręgowy we Włocławku": "sad_okregowy_wloclawek",
    "Sąd Okręgowy w Bielsku-Białej": "sad_okregowy_bielsko_biala",
    "Sąd Okręgowy w Częstochowie": "sad_okregowy_czestochowa",
    "Sąd Okręgowy w Gliwicach": "sad_okregowy_gliwice",
    "Sąd Okręgowy w Katowicach": "sad_okregowy_katowice",
    "Sąd Okręgowy w Rybniku": "sad_okregowy_rybnik",
    "Sąd Okręgowy w Sosnowcu": "sad_okregowy_sosnowiec",
    "Sąd Okręgowy w Kielcach": "sad_okregowy_kielce",
    "Sąd Okręgowy w Krakowie": "sad_okregowy_krakow",
    "Sąd Okręgowy w Nowym Sączu": "sad_okregowy_nowy_sacz",
    "Sąd Okręgowy w Tarnowie": "sad_okregowy_tarnow",
    "Sąd Okręgowy w Lublinie": "sad_okregowy_lublin",
    "Sąd Okręgowy w Radomiu": "sad_okregowy_radom",
    "Sąd Okręgowy w Siedlcach": "sad_okregowy_siedlce",
    "Sąd Okręgowy w Zamościu": "sad_okregowy_zamosc",
    "Sąd Okręgowy w Kaliszu": "sad_okregowy_kalisz",
    "Sąd Okręgowy w Łodzi": "sad_okregowy_lodz",
    "Sąd Okręgowy w Piotrkowie Trybunalskim": "sad_okregowy_piotrkow_trybunalski",
    "Sąd Okręgowy w Płocku": "sad_okregowy_plock",
    "Sąd Okręgowy w Sieradzu": "sad_okregowy_sieradz",
    "Sąd Okręgowy w Koninie": "sad_okregowy_konin",
    "Sąd Okręgowy w Poznaniu": "sad_okregowy_poznan",
    "Sąd Okręgowy w Zielonej Górze": "sad_okregowy_zielona_gora",
    "Sąd Okręgowy w Krośnie": "sad_okregowy_krosno",
    "Sąd Okręgowy w Przemyślu": "sad_okregowy_przemysl",
    "Sąd Okręgowy w Rzeszowie": "sad_okregowy_rzeszow",
    "Sąd Okręgowy w Tarnobrzegu": "sad_okregowy_tarnobrzeg",
    "Sąd Okręgowy w Gorzowie Wielkopolskim": "sad_okregowy_gorzow_wielkopolski",
    "Sąd Okręgowy w Koszalinie": "sad_okregowy_koszalin",
    "Sąd Okręgowy w Szczecinie": "sad_okregowy_szczecin",
    "Sąd Okręgowy w Warszawie": "sad_okregowy_warszawa",
    "Sąd Okręgowy Warszawa-Praga w Warszawie": "sad_okregowy_warszawa_praga",
    "Sąd Okręgowy w Jeleniej Górze": "sad_okregowy_jelenia_gora",
    "Sąd Okręgowy w Legnicy": "sad_okregowy_legnica",
    "Sąd Okręgowy w Opolu": "sad_okregowy_opole",
    "Sąd Okręgowy w Świdnicy": "sad_okregowy_swidnica",
    "Sąd Okręgowy we Wrocławiu": "sad_okregowy_wroclaw",
}


def district_name_to_enum(name: str) -> str | None:
    """Convert a SAOS district court name to our enum code."""
    return SAOS_DISTRICT_NAME_TO_ENUM.get(name.strip())


# ---------- SAOS API ----------

def fetch_saos_courts() -> list[dict]:
    """Fetch all courts from SAOS API (paginated)."""
    all_items = []
    for page in range(SAOS_MAX_PAGES):
        url = f"{SAOS_BASE_URL}?pageSize={SAOS_PAGE_SIZE}&pageNumber={page}"
        print(f"  Fetching SAOS page {page}... ", end="", flush=True)
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"ERROR: {e}")
            break
        data = resp.json()
        items = data.get("items", [])
        print(f"{len(items)} courts")
        if not items:
            break
        all_items.extend(items)
    return all_items


def parse_saos_courts(items: list[dict]) -> dict:
    """Parse SAOS court items into structured dictionaries.

    IMPORTANT: SAOS types are inverted:
      - SAOS "REGIONAL" = our District courts (sądy okręgowe)
      - SAOS "DISTRICT" = our Regional courts (sądy rejonowe)
      - SAOS "APPEAL" = our Appeal courts (sądy apelacyjne)
    """
    appeals = {}    # saos_id -> {name, ...}
    districts = {}  # saos_id -> {name, enum_code, parent_saos_id}
    regionals = {}  # saos_id -> {name, code, parent_saos_id, parent_district_enum}

    for item in items:
        saos_id = item.get("id")
        name = item.get("name", "")
        court_type = item.get("type", "")
        parent = item.get("parentCourt")
        parent_id = parent.get("id") if parent else None

        if court_type == "APPEAL":
            appeals[saos_id] = {"name": name}
        elif court_type == "REGIONAL":
            # SAOS "REGIONAL" = our district courts
            enum_code = district_name_to_enum(name)
            districts[saos_id] = {
                "name": name,
                "enum_code": enum_code,
                "parent_saos_id": parent_id,
            }
        elif court_type == "DISTRICT":
            # SAOS "DISTRICT" = our regional courts
            regionals[saos_id] = {
                "name": name,
                "parent_saos_id": parent_id,
            }

    # Resolve parent district enum for each regional court
    for reg in regionals.values():
        parent_saos_id = reg.get("parent_saos_id")
        if parent_saos_id and parent_saos_id in districts:
            reg["parent_district_enum"] = districts[parent_saos_id].get("enum_code")
            reg["parent_district_name"] = districts[parent_saos_id].get("name")
        else:
            reg["parent_district_enum"] = None
            reg["parent_district_name"] = None

    return {
        "appeals": appeals,
        "districts": districts,
        "regionals": regionals,
    }


# ---------- dane.gov.pl ----------

def fetch_dane_gov_courts() -> list[str]:
    """Fetch the authoritative list of court names from dane.gov.pl."""
    print("  Fetching dane.gov.pl court list... ", end="", flush=True)
    try:
        resp = requests.get(DANE_GOV_URL, timeout=30)
        resp.raise_for_status()
        text = resp.text
    except requests.RequestException as e:
        print(f"ERROR: {e}")
        return []

    # Filter for regional courts
    lines = text.strip().split("\n")
    regional = [line.strip() for line in lines if "Sąd Rejonowy" in line]
    # Clean: remove any CSV quoting or extra columns
    cleaned = []
    for line in regional:
        # Take the court name (may be quoted CSV)
        name = line.strip('"').strip()
        if name.startswith("Sąd Rejonowy"):
            cleaned.append(name)
    print(f"{len(cleaned)} regional courts found")
    return cleaned


# Name aliases: dane.gov.pl name -> SAOS name (for courts renamed since SAOS snapshot)
NAME_ALIASES = {
    "Sąd Rejonowy w Stargardzie": "Sąd Rejonowy w Stargardzie Szczecińskim",
}

# Courts not in SAOS at all (manually researched)
MANUAL_COURTS = [
    {
        "name": "Sąd Rejonowy dla miasta stołecznego Warszawy w Warszawie",
        "district_code": "sad_okregowy_warszawa",
        "city": "Warszawa",
        "code": "sad_rejonowy_warszawa_miasto_stoleczne",
        "source": "manual",
    },
    {
        "name": "Sąd Rejonowy w Czeladzi",
        "district_code": "sad_okregowy_sosnowiec",
        "city": "Czeladź",
        "code": "sad_rejonowy_czeladz",
        "source": "manual",
    },
]

# District reassignments: courts that moved to newer districts (Rybnik est. 2020, Sosnowiec est. 2022)
# SAOS still has them under old parents. Keys are slugs generated by name_to_slug().
# We populate these lazily after first run to match actual generated slugs.
DISTRICT_REASSIGNMENTS: dict[str, str] = {}

# Reassignment rules by court name substring -> new district
_REASSIGNMENT_RULES = [
    # From SO Gliwice -> SO Rybnik (est. July 2020)
    ("Jastrzębiu-Zdroju", "sad_okregowy_rybnik"),
    ("Raciborzu", "sad_okregowy_rybnik"),
    ("Rybniku", "sad_okregowy_rybnik"),
    ("Wodzisławiu Śląskim", "sad_okregowy_rybnik"),
    ("Żorach", "sad_okregowy_rybnik"),
    # From SO Katowice -> SO Sosnowiec (est. April 2022)
    ("Będzinie", "sad_okregowy_sosnowiec"),
    ("Dąbrowie Górniczej", "sad_okregowy_sosnowiec"),
    ("Jaworznie", "sad_okregowy_sosnowiec"),
    ("Sosnowcu", "sad_okregowy_sosnowiec"),
    # From SO Częstochowa -> SO Sosnowiec (est. April 2022)
    ("Zawierciu", "sad_okregowy_sosnowiec"),
]


def get_reassignment(name: str) -> str | None:
    """Check if a court should be reassigned to a newer district."""
    for substring, new_district in _REASSIGNMENT_RULES:
        if substring in name:
            return new_district
    return None


# ---------- Matching ----------

def match_courts(dane_gov_names: list[str], saos_regionals: dict) -> tuple[list[dict], list[str]]:
    """Match dane.gov.pl names against SAOS regional courts.

    Returns (matched, unmatched_names).
    """
    # Build normalized lookup from SAOS
    saos_by_norm = {}
    for saos_id, info in saos_regionals.items():
        norm = normalize_for_matching(info["name"])
        saos_by_norm[norm] = info

    matched = []
    unmatched = []

    for name in dane_gov_names:
        # Check if this court has a name alias (renamed since SAOS snapshot)
        saos_name = NAME_ALIASES.get(name, name)
        norm = normalize_for_matching(saos_name)
        if norm in saos_by_norm:
            info = saos_by_norm[norm]
            code = name_to_slug(name)
            reassigned = get_reassignment(name)
            district = reassigned or info.get("parent_district_enum")
            matched.append({
                "name": name,
                "district_code": district,
                "city": extract_city(name),
                "code": code,
                "source": "saos+dane_gov",
            })
        else:
            # Check if it's a manual entry
            manual = next((m for m in MANUAL_COURTS if m["name"] == name), None)
            if manual:
                matched.append(dict(manual))
            else:
                unmatched.append(name)

    return matched, unmatched


# ---------- Main ----------

def main():
    print("=" * 60)
    print("Regional Courts Data Collection")
    print("=" * 60)

    # Step 1: Fetch SAOS
    print("\n[1/4] Fetching SAOS API...")
    saos_items = fetch_saos_courts()
    if not saos_items:
        print("WARNING: No data from SAOS API. Continuing with dane.gov.pl only.")
        saos_parsed = {"appeals": {}, "districts": {}, "regionals": {}}
    else:
        saos_parsed = parse_saos_courts(saos_items)
        print(f"  Parsed: {len(saos_parsed['appeals'])} appeals, "
              f"{len(saos_parsed['districts'])} districts, "
              f"{len(saos_parsed['regionals'])} regionals")

    # Check unmapped districts
    unmapped_districts = [
        d for d in saos_parsed["districts"].values()
        if d["enum_code"] is None
    ]
    if unmapped_districts:
        print(f"\n  WARNING: {len(unmapped_districts)} SAOS district courts could not be mapped:")
        for d in unmapped_districts:
            print(f"    - {d['name']}")

    # Step 2: Fetch dane.gov.pl
    print("\n[2/4] Fetching dane.gov.pl...")
    dane_gov_names = fetch_dane_gov_courts()

    # Step 3: Match
    print("\n[3/4] Matching courts...")
    matched, unmatched = match_courts(dane_gov_names, saos_parsed["regionals"])
    print(f"  Matched: {len(matched)}")
    print(f"  Unmatched: {len(unmatched)}")

    # Step 4: Output
    print(f"\n[4/4] Writing output to {OUTPUT_FILE}...")

    # Check for slug collisions
    slugs = [m["code"] for m in matched]
    slug_dupes = [s for s in set(slugs) if slugs.count(s) > 1]
    if slug_dupes:
        print(f"  WARNING: Slug collisions detected: {slug_dupes}")

    # Check district coverage
    covered_districts = set(m["district_code"] for m in matched if m["district_code"])
    missing_districts = set(DISTRICT_COURT_ENUMS) - covered_districts
    if missing_districts:
        print(f"  WARNING: Districts with no matched regional courts: {missing_districts}")

    output = {
        "metadata": {
            "dane_gov_total": len(dane_gov_names),
            "saos_total": len(saos_parsed["regionals"]),
            "matched": len(matched),
            "unmatched": len(unmatched),
        },
        "courts": sorted(matched, key=lambda c: (c.get("district_code") or "", c["name"])),
        "unmatched_names": sorted(unmatched),
    }

    OUTPUT_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Done. Wrote {len(matched)} matched + {len(unmatched)} unmatched courts.")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  dane.gov.pl regional courts: {len(dane_gov_names)}")
    print(f"  SAOS regional courts:        {len(saos_parsed['regionals'])}")
    print(f"  Matched (with hierarchy):     {len(matched)}")
    print(f"  Unmatched (need research):    {len(unmatched)}")
    if unmatched:
        print("\n  Unmatched courts:")
        for name in sorted(unmatched):
            print(f"    - {name}")

    return 0 if not unmatched else 1


if __name__ == "__main__":
    sys.exit(main())
