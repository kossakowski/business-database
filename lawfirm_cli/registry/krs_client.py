"""KRS (Krajowy Rejestr Sądowy) API client.

Official KRS API:
- Base URL: https://api-krs.ms.gov.pl/api/krs
- Endpoint: /OdpisPelny/{krs}?rejestr=P&format=json
- Public API, no authentication required
- KRS number must be 10 digits (zero-padded)

Environment Variables:
- KRS_API_BASE_URL: Override default base URL (optional)
- KRS_REQUEST_TIMEOUT: Request timeout in seconds (default: 30)

The normalizer is robust to two response shapes:
  - the real public API (deeply nested historical lists, separate
    `siedziba` and `adres`, `naglowekP.wpis[]` for registration date,
    `dzial2.reprezentacja[0].sklad[]` for board members, PKD codes
    split into kodDzial/kodKlasa/kodPodklasa under `pozycja[]`); and
  - the legacy fixture shape used in tests (flat dicts with merged
    address fields, `dzial2.reprezentacja.skladOrganu`, PKD with
    `kodDzial` as the full code, `danePodmiotu.dataRejestracjiWKRS`,
    `kapital.wysokoscKapitaluZakladowego` as a single string).

The earlier port targeted only the legacy fixture shape and so silently
dropped registry_status, registration_date, voivodeship, powiat, gmina,
share_capital currency, PKD codes and representatives on real API
responses. This version is dual-shape — real API first, fixture fallback.
"""

import hashlib
import json
import os
from datetime import datetime, date, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.exceptions import RequestException, Timeout

from lawfirm_cli.registry.models import (
    NormalizedKRSProfile,
    NormalizedAddress,
    RegistrySnapshot,
)
from lawfirm_cli.company_names import parse_krs_company_data


DEFAULT_KRS_API_BASE_URL = "https://api-krs.ms.gov.pl/api/krs"
DEFAULT_TIMEOUT = 30


class KRSClientError(Exception):
    pass


class KRSNotFoundError(KRSClientError):
    pass


class KRSConnectionError(KRSClientError):
    pass


class KRSParseError(KRSClientError):
    pass


def get_krs_config() -> Tuple[str, int]:
    base_url = os.environ.get("KRS_API_BASE_URL", DEFAULT_KRS_API_BASE_URL)
    timeout = int(os.environ.get("KRS_REQUEST_TIMEOUT", DEFAULT_TIMEOUT))
    return base_url, timeout


def normalize_krs_number(krs: str) -> str:
    krs = krs.strip().replace("-", "").replace(" ", "")

    if not krs.isdigit():
        raise ValueError(f"Invalid KRS number: {krs} (must be numeric)")

    if len(krs) > 10:
        raise ValueError(f"Invalid KRS number: {krs} (too long)")

    return krs.zfill(10)


def fetch_krs_data(krs_number: str) -> Tuple[Dict[str, Any], str]:
    base_url, timeout = get_krs_config()
    krs = normalize_krs_number(krs_number)

    url = f"{base_url}/OdpisPelny/{krs}?rejestr=P&format=json"

    try:
        response = requests.get(url, timeout=timeout)

        if response.status_code == 404:
            raise KRSNotFoundError(f"KRS number {krs} not found in registry")

        if response.status_code != 200:
            raise KRSClientError(
                f"KRS API returned status {response.status_code}: {response.text[:200]}"
            )

        raw_json = response.text
        data = response.json()

        return data, raw_json

    except Timeout:
        raise KRSConnectionError(
            f"Request to KRS API timed out after {timeout} seconds"
        )
    except RequestException as e:
        raise KRSConnectionError(f"Failed to connect to KRS API: {e}")
    except json.JSONDecodeError as e:
        raise KRSParseError(f"Failed to parse KRS API response: {e}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_date(date_str: Optional[str]) -> Optional[date]:
    """Parse a KRS date string. Handles YYYY-MM-DD and DD.MM.YYYY (real API)."""
    if not date_str:
        return None
    s = date_str.strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s[:10], fmt).date()
        except (ValueError, IndexError):
            continue
    return None


def _ensure_dict(data: Any) -> Dict[str, Any]:
    if data is None:
        return {}
    if isinstance(data, dict):
        return data
    if isinstance(data, list) and len(data) > 0:
        if isinstance(data[-1], dict):
            return data[-1]
    return {}


def _last_dict(value: Any) -> Dict[str, Any]:
    """Return the last dict from a list-of-dicts, or value if it is a dict."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        for item in reversed(value):
            if isinstance(item, dict):
                return item
    return {}


def _active_entries(value: Any) -> list:
    """Return entries from a historical list that are still active.

    KRS marks superseded entries with `nrWpisuWykr`. Active entries lack
    that field. Falls back to all entries if none are flagged active so
    that callers always get something to work with.
    """
    if not isinstance(value, list):
        return [value] if value else []
    active = [v for v in value if isinstance(v, dict) and not v.get("nrWpisuWykr")]
    return active if active else value


def _last_active_dict(value: Any) -> Dict[str, Any]:
    return _last_dict(_active_entries(value))


def _build_pkd_code(pozycja: Dict[str, Any]) -> Optional[str]:
    """Build a PKD code from a `pozycja` dict.

    Real API: separate kodDzial / kodKlasa / kodPodklasa fields; we
    concatenate. Legacy fixture: single kodDzial that already contains
    the full dotted code; we just return it.
    """
    if not isinstance(pozycja, dict):
        return None
    parts = []
    for key in ("kodDzial", "kodKlasa", "kodPodklasa"):
        v = pozycja.get(key)
        if v is not None:
            parts.append(str(v))
    if len(parts) > 1:
        return ".".join(parts)
    if len(parts) == 1:
        return parts[0]
    # Some shapes use just `kod`
    kod = pozycja.get("kod")
    return str(kod) if kod else None


def _extract_first_inner(member: Dict[str, Any], outer_key: str, *inner_keys: str) -> Optional[str]:
    """Walk member[outer_key] (list-of-dicts or flat string) and extract a value.

    Real API shape: member["nazwisko"] == [{"nazwisko": {"nazwiskoICzlon": "..."}}]
    Legacy shape:   member["nazwisko"] == "KOWALSKI"
    """
    container = member.get(outer_key)
    if container is None:
        return None
    entries = _active_entries(container)
    for entry in reversed(entries):
        # Legacy: the entry itself is the value
        if isinstance(entry, str) and entry.strip():
            return entry
        if not isinstance(entry, dict):
            continue
        # Real API: walk inner keys
        cur: Any = entry
        for k in inner_keys:
            if isinstance(cur, dict):
                cur = cur.get(k)
            else:
                cur = None
                break
        if cur is None:
            cur = entry.get(outer_key)
        if isinstance(cur, str) and cur.strip():
            return cur
        if cur is not None and not isinstance(cur, (dict, list)):
            return str(cur)
    return None


def _member_is_active(member: Dict[str, Any]) -> bool:
    """A sklad member is active if their funkcjaWOrganie list has at least
    one entry with no nrWpisuWykr (the role has not been superseded).

    For legacy-shape fixtures funkcjaWOrganie is a flat string — those
    are always treated as active.
    """
    if not isinstance(member, dict):
        return False
    funkcje = member.get("funkcjaWOrganie")
    if funkcje is None:
        return False
    if not isinstance(funkcje, list):
        return bool(funkcje)
    for entry in funkcje:
        if isinstance(entry, dict) and not entry.get("nrWpisuWykr"):
            return True
        if isinstance(entry, str) and entry.strip():
            return True
    return False


def _build_address(adres: Dict[str, Any], siedziba: Dict[str, Any]) -> Optional[NormalizedAddress]:
    """Merge `adres` (street-level) and `siedziba` (admin-level).

    Real API splits address fields between two siblings; the legacy
    fixture inlines everything into `adres`. Pulling each field from
    whichever source has it works for both shapes.
    """
    if not adres and not siedziba:
        return None
    return NormalizedAddress(
        address_type="MAIN",
        country=(adres.get("kraj") or siedziba.get("kraj") or "PL"),
        voivodeship=(siedziba.get("wojewodztwo") or adres.get("wojewodztwo")),
        county=(siedziba.get("powiat") or adres.get("powiat")),
        gmina=(siedziba.get("gmina") or adres.get("gmina")),
        city=(adres.get("miejscowosc") or siedziba.get("miejscowosc")),
        postal_code=adres.get("kodPocztowy"),
        post_office=adres.get("poczta"),
        street=adres.get("ulica"),
        building_no=adres.get("nrDomu"),
        unit_no=adres.get("nrLokalu"),
    )


def _coerce_string(value: Any) -> Optional[str]:
    """Best-effort string extraction from real-or-legacy shapes."""
    if value is None:
        return None
    if isinstance(value, str):
        return value if value.strip() else None
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list) and value:
        # take last non-empty active entry
        for item in reversed(_active_entries(value)):
            s = _coerce_string(item)
            if s:
                return s
        return None
    if isinstance(value, dict):
        # try common text keys (Polish KRS field names)
        for key in (
            "value", "text", "nazwa", "name", "opis",
            "nazwaSkrocona", "formaPrawna", "status",
            "kodDzial", "kod", "imiona", "nazwisko",
            "wartosc",
        ):
            if key in value and value[key]:
                v = value[key]
                if isinstance(v, str) and v.strip():
                    return v
                if isinstance(v, (int, float)):
                    return str(v)
        # otherwise return first non-empty string value
        for v in value.values():
            if isinstance(v, str) and v.strip():
                return v
    return None


# Kept as `_ensure_str` for callsites elsewhere in the package.
def _ensure_str(value: Any) -> Optional[str]:
    return _coerce_string(value)


def _safe_get(data: Any, key: str, default: Any = None) -> Any:
    if data is None:
        return default
    if isinstance(data, list):
        if len(data) > 0 and isinstance(data[-1], dict):
            return data[-1].get(key, default)
        return default
    if isinstance(data, dict):
        return data.get(key, default)
    return default


def _extract_address(addr_data: Any) -> Optional[NormalizedAddress]:
    """Legacy single-source address extractor — kept for any external callers.

    For new code prefer `_build_address(adres, siedziba)` which captures the
    real-API split. This function still works on the legacy fixture shape
    (flat dict with everything inlined).
    """
    if not addr_data:
        return None

    if isinstance(addr_data, list):
        if len(addr_data) > 0 and isinstance(addr_data[-1], dict):
            addr_data = addr_data[-1]
        else:
            return None

    if not isinstance(addr_data, dict):
        return None

    return NormalizedAddress(
        address_type="MAIN",
        country=_coerce_string(addr_data.get("kraj")) or "PL",
        voivodeship=_coerce_string(addr_data.get("wojewodztwo")),
        county=_coerce_string(addr_data.get("powiat")),
        gmina=_coerce_string(addr_data.get("gmina")),
        city=_coerce_string(addr_data.get("miejscowosc")),
        postal_code=_coerce_string(addr_data.get("kodPocztowy")),
        post_office=_coerce_string(addr_data.get("poczta")),
        street=_coerce_string(addr_data.get("ulica")),
        building_no=_coerce_string(addr_data.get("nrDomu")),
        unit_no=_coerce_string(addr_data.get("nrLokalu")),
    )


# ---------------------------------------------------------------------------
# Main normalizer
# ---------------------------------------------------------------------------


def normalize_krs_response(data: Dict[str, Any]) -> NormalizedKRSProfile:
    odpis = _ensure_dict(data.get("odpis", data))
    dane = _ensure_dict(odpis.get("dane", odpis))

    naglowek = _ensure_dict(odpis.get("naglowekP") or odpis.get("naglowekA") or {})
    krs_number = _coerce_string(naglowek.get("numerKRS"))

    dzial1 = _ensure_dict(dane.get("dzial1", {}))
    dane_podmiotu = _ensure_dict(dzial1.get("danePodmiotu", {}))

    # --- Registration date: real API stores it in naglowek.wpis[]; legacy
    # fixture puts it in danePodmiotu.dataRejestracjiWKRS. Try both.
    registration_date = None
    wpis_list = naglowek.get("wpis")
    if isinstance(wpis_list, list) and wpis_list:
        registration_entry = None
        for entry in wpis_list:
            if isinstance(entry, dict) and "REJESTRACJA" in (entry.get("opis") or "").upper():
                registration_entry = entry
                break
        if registration_entry is None and isinstance(wpis_list[0], dict):
            registration_entry = wpis_list[0]
        if registration_entry:
            registration_date = _parse_date(registration_entry.get("dataWpisu"))
    if registration_date is None:
        registration_date = _parse_date(_coerce_string(dane_podmiotu.get("dataRejestracjiWKRS")))

    # --- Registry status: real API has stanPozycji=1 (active); legacy fixture
    # has danePodmiotu.status. Prefer the explicit status string when present.
    legacy_status = _coerce_string(dane_podmiotu.get("status"))
    if legacy_status:
        registry_status: Optional[str] = legacy_status
    else:
        stan_pozycji = naglowek.get("stanPozycji")
        if stan_pozycji == 1:
            registry_status = "AKTYWNY"
        elif stan_pozycji is not None:
            registry_status = str(stan_pozycji)
        else:
            registry_status = None

    # --- NIP / REGON: walk historical identifiers, take latest non-null ---
    nip = None
    regon = None
    identyfikatory_list = dane_podmiotu.get("identyfikatory", [])
    if isinstance(identyfikatory_list, list):
        for item in reversed(identyfikatory_list):
            item_dict = _ensure_dict(item)
            inner_ident = _ensure_dict(item_dict.get("identyfikatory", {}))
            if not nip:
                nip = _coerce_string(inner_ident.get("nip"))
            if not regon:
                regon = _coerce_string(inner_ident.get("regon"))
            if nip and regon:
                break
    elif isinstance(identyfikatory_list, dict):
        inner_ident = _ensure_dict(identyfikatory_list.get("identyfikatory", identyfikatory_list))
        nip = _coerce_string(inner_ident.get("nip"))
        regon = _coerce_string(inner_ident.get("regon"))

    # --- Address: merge `adres` (street) with `siedziba` (admin) ---
    siedziba_iadres = _ensure_dict(dzial1.get("siedzibaIAdres", {}))
    adres_dict = _last_active_dict(siedziba_iadres.get("adres"))
    siedziba_dict = _last_active_dict(siedziba_iadres.get("siedziba"))
    seat_address = _build_address(adres_dict, siedziba_dict)

    # --- Contacts: real API uses lists of dicts; legacy uses flat strings ---
    email = (
        _extract_first_inner(siedziba_iadres, "adresPocztyElektronicznej", "adresPocztyElektronicznej")
        or _coerce_string(siedziba_iadres.get("adresEmail"))
        or _coerce_string(siedziba_iadres.get("email"))
    )
    website = (
        _extract_first_inner(siedziba_iadres, "adresStronyInternetowej", "adresStronyInternetowej")
        or _coerce_string(siedziba_iadres.get("adresStronyInternetowej"))
        or _coerce_string(siedziba_iadres.get("www"))
    )
    phone = (
        _extract_first_inner(siedziba_iadres, "telefon", "telefon")
        or _coerce_string(siedziba_iadres.get("telefon"))
    )

    # --- Share capital: real API has list of {wartosc, waluta}; legacy has
    # a single string like "50000.00 PLN". Try real-shape first.
    kapital = _ensure_dict(dzial1.get("kapital", {}))
    cap_raw = kapital.get("wysokoscKapitaluZakladowego")
    share_capital: Optional[str] = None
    share_capital_currency: Optional[str] = None
    cap_entry = _last_active_dict(cap_raw)
    if cap_entry and (cap_entry.get("wartosc") or cap_entry.get("waluta")):
        wartosc = cap_entry.get("wartosc")
        waluta = cap_entry.get("waluta")
        if wartosc and waluta:
            share_capital = f"{wartosc} {waluta}"
        elif wartosc:
            share_capital = str(wartosc)
        share_capital_currency = waluta
    else:
        share_capital = _coerce_string(cap_raw)
        # Legacy shape stores currency inline in the string

    # --- PKD codes: real API nests under pozycja[]; legacy uses flat dicts ---
    dzial3 = _ensure_dict(dane.get("dzial3", {}))
    przedmiot = _ensure_dict(dzial3.get("przedmiotDzialalnosci", {}))

    pkd_codes: List[str] = []
    pkd_main: Optional[str] = None

    def _gather_pkd(group_iterable: Any, is_main: bool) -> None:
        nonlocal pkd_main
        if not isinstance(group_iterable, list):
            if isinstance(group_iterable, dict):
                group_iterable = [group_iterable]
            else:
                return
        for group in group_iterable:
            group_dict = _ensure_dict(group)
            pozycja_entries = _active_entries(group_dict.get("pozycja"))
            if not pozycja_entries:
                pozycja_entries = [group_dict]
            for pozycja in pozycja_entries:
                pos_dict = _ensure_dict(pozycja)
                code = _build_pkd_code(pos_dict)
                if code:
                    if is_main and pkd_main is None:
                        pkd_main = code
                    if code not in pkd_codes:
                        pkd_codes.append(code)

    _gather_pkd(przedmiot.get("przedmiotPrzewazajacejDzialalnosci"), is_main=True)
    _gather_pkd(przedmiot.get("przedmiotPozostalejDzialalnosci"), is_main=False)

    # --- Representatives: real API has dzial2.reprezentacja[0].sklad[];
    # legacy fixture has dzial2.reprezentacja.skladOrganu[]. Try both.
    dzial2 = _ensure_dict(dane.get("dzial2", {}))
    reprezentacja = dzial2.get("reprezentacja")

    sklad_list: List[Any] = []
    if isinstance(reprezentacja, list) and reprezentacja:
        rep_org = _ensure_dict(reprezentacja[0])
        s = rep_org.get("sklad")
        if isinstance(s, list):
            sklad_list = s
    elif isinstance(reprezentacja, dict):
        # Legacy fixture: reprezentacja.skladOrganu[]
        s = reprezentacja.get("skladOrganu") or reprezentacja.get("sklad")
        if isinstance(s, dict):
            sklad_list = [s]
        elif isinstance(s, list):
            sklad_list = s

    representatives: List[Dict[str, Any]] = []
    for member in sklad_list:
        member_dict = _ensure_dict(member)
        if not member_dict:
            continue
        # In real API we filter out historical members; in legacy the field
        # is a flat string and `_member_is_active` returns True for that.
        if not _member_is_active(member_dict):
            # Legacy fallback fires only when funkcjaWOrganie is completely
            # absent (legacy fixture shape). For real-API responses the field
            # is present but all entries are superseded — those are former
            # board members and we want to skip them.
            if "funkcjaWOrganie" in member_dict:
                continue
            if not (member_dict.get("imiona") or member_dict.get("nazwisko")):
                continue
        imie1 = _extract_first_inner(member_dict, "imiona", "imiona", "imie") or ""
        imie2 = _extract_first_inner(member_dict, "imiona", "imiona", "imieDrugie") or ""
        nazw = _extract_first_inner(member_dict, "nazwisko", "nazwisko", "nazwiskoICzlon") or ""

        # Legacy fallback: if the nested-list walker returned nothing, the
        # field is probably a flat string — read it directly.
        if not imie1 and isinstance(member_dict.get("imiona"), str):
            imie1 = member_dict["imiona"]
        if not nazw and isinstance(member_dict.get("nazwisko"), str):
            nazw = member_dict["nazwisko"]

        # PESEL: nested {pesel: ...} or flat string
        pesel = _extract_first_inner(member_dict, "identyfikator", "pesel")
        if pesel is None:
            ident = member_dict.get("identyfikator")
            if isinstance(ident, dict):
                pesel = _coerce_string(ident.get("pesel"))
        funkcja = _extract_first_inner(member_dict, "funkcjaWOrganie", "funkcjaWOrganie")

        # In the legacy shape `imiona` is a flat string; both imie1 and imie2
        # then resolve to the same value via the flat-string fallback in
        # _extract_first_inner. Dedupe so we don't get "JAN JAN KOWALSKI".
        given_parts: List[str] = []
        for part in (imie1, imie2):
            if part and part not in given_parts:
                given_parts.append(part)
        given = " ".join(given_parts).strip()
        full_name = f"{given} {nazw}".strip()
        if full_name:
            representatives.append({
                "name": full_name,
                "function": funkcja,
                "pesel": pesel,
            })

    # --- Names & legal form ---
    official_name = _coerce_string(dane_podmiotu.get("nazwa"))
    krs_short_name = _coerce_string(dane_podmiotu.get("nazwaSkrocona"))
    legal_form_name = _coerce_string(dane_podmiotu.get("formaPrawna"))
    legal_form_code = _coerce_string(dane_podmiotu.get("kodFormyPrawnej"))

    parsed_company = parse_krs_company_data(
        official_name=official_name,
        legal_form_name=legal_form_name,
        legal_form_code=legal_form_code,
    )

    short_name = krs_short_name or parsed_company.get("short_name")

    return NormalizedKRSProfile(
        krs=krs_number,
        nip=nip,
        regon=regon,
        official_name=official_name,
        short_name=short_name,
        legal_form=legal_form_name,
        legal_form_code=legal_form_code,
        legal_kind=parsed_company.get("legal_kind"),
        legal_form_suffix=parsed_company.get("legal_form_suffix"),
        particular_name=parsed_company.get("particular_name"),
        registry_status=registry_status,
        registration_date=registration_date,
        seat_address=seat_address,
        correspondence_address=None,
        email=email,
        website=website,
        phone=phone,
        share_capital=share_capital,
        share_capital_currency=share_capital_currency or "PLN",
        pkd_main=pkd_main,
        pkd_codes=pkd_codes,
        representatives=representatives,
        raw_payload=data,
    )


def fetch_and_normalize_krs(
    krs_number: str,
    entity_id: Optional[str] = None,
) -> Tuple[NormalizedKRSProfile, RegistrySnapshot]:
    krs = normalize_krs_number(krs_number)

    data, raw_json = fetch_krs_data(krs)

    snapshot = RegistrySnapshot(
        entity_id=entity_id,
        source_system="KRS",
        external_id=krs,
        fetched_at=datetime.now(timezone.utc),
        payload_format="json",
        payload_raw=raw_json,
        payload_hash=hashlib.sha256(raw_json.encode()).hexdigest(),
    )

    profile = normalize_krs_response(data)

    return profile, snapshot
