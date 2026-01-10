"""KRS (Krajowy Rejestr Sądowy) API client.

Official KRS API Documentation:
- Base URL: https://api-krs.ms.gov.pl/api/krs/OdsijkKonsolidowana/{krs}
- The API is public and free to use
- KRS number must be 10 digits (padded with leading zeros)
- Returns JSON with company data including: name, NIP, REGON, address, representatives

Environment Variables:
- KRS_API_BASE_URL: Override default API base URL (optional)
- KRS_REQUEST_TIMEOUT: Request timeout in seconds (default: 30)
"""

import hashlib
import json
import os
from datetime import datetime, date
from typing import Any, Dict, Optional, Tuple

import requests
from requests.exceptions import RequestException, Timeout

from lawfirm_cli.registry.models import (
    NormalizedKRSProfile,
    NormalizedAddress,
    RegistrySnapshot,
)


# Default configuration
DEFAULT_KRS_API_BASE_URL = "https://api-krs.ms.gov.pl/api/krs"
DEFAULT_TIMEOUT = 30


class KRSClientError(Exception):
    """Base exception for KRS client errors."""
    pass


class KRSNotFoundError(KRSClientError):
    """Raised when KRS number is not found."""
    pass


class KRSConnectionError(KRSClientError):
    """Raised on network/connection errors."""
    pass


class KRSParseError(KRSClientError):
    """Raised when response cannot be parsed."""
    pass


def get_krs_config() -> Tuple[str, int]:
    """Get KRS API configuration from environment.
    
    Returns:
        Tuple of (base_url, timeout_seconds).
    """
    base_url = os.environ.get("KRS_API_BASE_URL", DEFAULT_KRS_API_BASE_URL)
    timeout = int(os.environ.get("KRS_REQUEST_TIMEOUT", DEFAULT_TIMEOUT))
    return base_url, timeout


def normalize_krs_number(krs: str) -> str:
    """Normalize KRS number to 10 digits.
    
    Args:
        krs: KRS number (may have fewer than 10 digits).
        
    Returns:
        10-digit KRS number padded with leading zeros.
        
    Raises:
        ValueError: If KRS number is invalid.
    """
    # Remove any whitespace or dashes
    krs = krs.strip().replace("-", "").replace(" ", "")
    
    # Validate it's numeric
    if not krs.isdigit():
        raise ValueError(f"Invalid KRS number: {krs} (must be numeric)")
    
    # Validate length
    if len(krs) > 10:
        raise ValueError(f"Invalid KRS number: {krs} (too long)")
    
    # Pad with leading zeros
    return krs.zfill(10)


def fetch_krs_data(krs_number: str) -> Tuple[Dict[str, Any], str]:
    """Fetch raw data from KRS API.
    
    Args:
        krs_number: KRS number (will be normalized).
        
    Returns:
        Tuple of (response_data_dict, raw_json_string).
        
    Raises:
        KRSNotFoundError: If KRS number not found.
        KRSConnectionError: On network errors.
        KRSParseError: If response cannot be parsed.
    """
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


def _extract_address(addr_data: Any) -> Optional[NormalizedAddress]:
    """Extract address from KRS address structure."""
    if not addr_data:
        return None
    
    # Handle case where addr_data is a list
    if isinstance(addr_data, list):
        if len(addr_data) > 0 and isinstance(addr_data[0], dict):
            addr_data = addr_data[0]
        else:
            return None
    
    if not isinstance(addr_data, dict):
        return None
    
    return NormalizedAddress(
        address_type="MAIN",
        country=_ensure_str(addr_data.get("kraj")) or "PL",
        voivodeship=_ensure_str(addr_data.get("wojewodztwo")),
        county=_ensure_str(addr_data.get("powiat")),
        gmina=_ensure_str(addr_data.get("gmina")),
        city=_ensure_str(addr_data.get("miejscowosc")),
        postal_code=_ensure_str(addr_data.get("kodPocztowy")),
        post_office=_ensure_str(addr_data.get("poczta")),
        street=_ensure_str(addr_data.get("ulica")),
        building_no=_ensure_str(addr_data.get("nrDomu")),
        unit_no=_ensure_str(addr_data.get("nrLokalu")),
    )


def _parse_date(date_str: Optional[str]) -> Optional[date]:
    """Parse date string from KRS format."""
    if not date_str:
        return None
    try:
        # KRS uses YYYY-MM-DD format
        return datetime.strptime(date_str[:10], "%Y-%m-%d").date()
    except (ValueError, IndexError):
        return None


def _safe_get(data: Any, key: str, default: Any = None) -> Any:
    """Safely get a value from a dict, handling lists and None."""
    if data is None:
        return default
    if isinstance(data, list):
        # If it's a list, try to get from first element
        if len(data) > 0 and isinstance(data[0], dict):
            return data[0].get(key, default)
        return default
    if isinstance(data, dict):
        return data.get(key, default)
    return default


def _ensure_dict(data: Any) -> Dict[str, Any]:
    """Ensure data is a dict, extracting from list if needed."""
    if data is None:
        return {}
    if isinstance(data, dict):
        return data
    if isinstance(data, list) and len(data) > 0:
        if isinstance(data[0], dict):
            return data[0]
    return {}


def _ensure_str(value: Any) -> Optional[str]:
    """Ensure a value is a string, handling lists and other types.
    
    - If value is a list, take the first string element or first dict's text value.
    - If value is a dict, try to extract a text representation.
    - If value is None or empty, return None.
    - Otherwise convert to string.
    
    Handles KRS API nested structures like:
        "nazwaSkrocona": [{"nazwaSkrocona": "...", "nrWpisuWprow": "1"}]
    """
    if value is None:
        return None
    
    if isinstance(value, str):
        return value if value.strip() else None
    
    if isinstance(value, (int, float)):
        return str(value)
    
    if isinstance(value, list):
        if len(value) == 0:
            return None
        # Take first element
        first = value[0]
        if isinstance(first, str):
            return first if first.strip() else None
        if isinstance(first, dict):
            # Try common text keys (including Polish KRS field names)
            for key in ['value', 'text', 'nazwa', 'name', 'opis',
                        'nazwaSkrocona', 'formaPrawna', 'status',
                        'kodDzial', 'kod', 'imiona', 'nazwisko']:
                if key in first and first[key]:
                    return str(first[key])
            # Return first non-empty string value from dict
            for v in first.values():
                if isinstance(v, str) and v.strip():
                    return v
        return str(first) if first else None
    
    if isinstance(value, dict):
        # Try common text keys (including Polish KRS field names)
        for key in ['value', 'text', 'nazwa', 'name', 'opis',
                    'nazwaSkrocona', 'formaPrawna', 'status',
                    'kodDzial', 'kod', 'imiona', 'nazwisko']:
            if key in value and value[key]:
                return str(value[key])
        return None
    
    return str(value)


def normalize_krs_response(data: Dict[str, Any]) -> NormalizedKRSProfile:
    """Normalize KRS API response to standard profile structure.
    
    Args:
        data: Raw response from KRS API.
        
    Returns:
        NormalizedKRSProfile with extracted data.
    """
    # KRS response structure varies, handle nested data
    odpis = _ensure_dict(data.get("odpis", data))
    dane = _ensure_dict(odpis.get("dane", odpis))
    
    # Get KRS number from header (naglowekP or naglowekA)
    naglowek = _ensure_dict(odpis.get("naglowekP") or odpis.get("naglowekA") or {})
    krs_number = _ensure_str(naglowek.get("numerKRS"))
    
    # Get podstawowe dane (basic data) - can be dict or list
    dzial1 = _ensure_dict(dane.get("dzial1", {}))
    dane_podmiotu = _ensure_dict(dzial1.get("danePodmiotu", {}))
    
    # Extract NIP and REGON from identyfikatory list
    # Structure: identyfikatory: [{identyfikatory: {nip: ..., regon: ...}}, ...]
    # The latest entry (last in list) has the most current data
    nip = None
    regon = None
    identyfikatory_list = dane_podmiotu.get("identyfikatory", [])
    if isinstance(identyfikatory_list, list):
        for item in reversed(identyfikatory_list):  # Start from latest
            item_dict = _ensure_dict(item)
            inner_ident = _ensure_dict(item_dict.get("identyfikatory", {}))
            if not nip:
                nip = _ensure_str(inner_ident.get("nip"))
            if not regon:
                regon = _ensure_str(inner_ident.get("regon"))
            if nip and regon:
                break
    elif isinstance(identyfikatory_list, dict):
        # Handle case where it's a single dict
        inner_ident = _ensure_dict(identyfikatory_list.get("identyfikatory", identyfikatory_list))
        nip = _ensure_str(inner_ident.get("nip"))
        regon = _ensure_str(inner_ident.get("regon"))
    
    # Get siedziba (seat/address)
    siedziba = _ensure_dict(dzial1.get("siedzibaIAdres", {}))
    adres_siedziby = _ensure_dict(siedziba.get("adres", {}))
    
    # Get PKD codes - dzial3 can be dict or list
    dzial3 = _ensure_dict(dane.get("dzial3", {}))
    przedmiot_dzialalnosci = _ensure_dict(dzial3.get("przedmiotDzialalnosci", {}))
    pkd_list = przedmiot_dzialalnosci.get("przedmiotPrzewazajacejDzialalnosci", [])
    if isinstance(pkd_list, dict):
        pkd_list = [pkd_list]
    elif not isinstance(pkd_list, list):
        pkd_list = []
    
    pkd_codes = []
    pkd_main = None
    for pkd in pkd_list:
        pkd = _ensure_dict(pkd)
        code = pkd.get("kodDzial") or pkd.get("kod")
        if code:
            pkd_codes.append(code)
            if not pkd_main:
                pkd_main = code
    
    # Get representatives (zarząd) - dzial2 can be dict or list
    dzial2 = _ensure_dict(dane.get("dzial2", {}))
    reprezentacja = _ensure_dict(dzial2.get("reprezentacja", {}))
    sklad_organu = reprezentacja.get("skladOrganu", [])
    if isinstance(sklad_organu, dict):
        sklad_organu = [sklad_organu]
    elif not isinstance(sklad_organu, list):
        sklad_organu = []
    
    representatives = []
    for osoba in sklad_organu:
        osoba = _ensure_dict(osoba)
        if osoba:
            ident = _ensure_dict(osoba.get("identyfikator", {}))
            imiona = _ensure_str(osoba.get('imiona')) or ''
            nazwisko = _ensure_str(osoba.get('nazwisko')) or ''
            rep = {
                "name": f"{imiona} {nazwisko}".strip(),
                "function": _ensure_str(osoba.get("funkcjaWOrganie")),
                "pesel": _ensure_str(ident.get("pesel")) if ident else None,
            }
            if rep["name"]:
                representatives.append(rep)
    
    # Extract contact info from dzial1 if available
    email = None
    website = None
    phone = None
    
    # Some KRS entries have contact info in siedziba
    if siedziba:
        email = _ensure_str(siedziba.get("adresEmail") or siedziba.get("email"))
        website = _ensure_str(siedziba.get("adresStronyInternetowej") or siedziba.get("www"))
        phone = _ensure_str(siedziba.get("telefon"))
    
    # Handle kapital which may also be a list
    kapital = _ensure_dict(dzial1.get("kapital", {}))
    share_capital = _ensure_str(kapital.get("wysokoscKapitaluZakladowego"))
    
    return NormalizedKRSProfile(
        krs=krs_number,
        nip=nip,
        regon=regon,
        official_name=_ensure_str(dane_podmiotu.get("nazwa")),
        short_name=_ensure_str(dane_podmiotu.get("nazwaSkrocona")),
        legal_form=_ensure_str(dane_podmiotu.get("formaPrawna")),
        legal_form_code=_ensure_str(dane_podmiotu.get("kodFormyPrawnej")),
        registry_status=_ensure_str(dane_podmiotu.get("status")),
        registration_date=_parse_date(_ensure_str(dane_podmiotu.get("dataRejestracjiWKRS"))),
        seat_address=_extract_address(adres_siedziby),
        correspondence_address=None,  # May be in different section
        email=email,
        website=website,
        phone=phone,
        share_capital=share_capital,
        pkd_main=_ensure_str(pkd_main),
        pkd_codes=[_ensure_str(c) for c in pkd_codes if _ensure_str(c)],
        representatives=representatives,
        raw_payload=data,
    )


def fetch_and_normalize_krs(
    krs_number: str,
    entity_id: Optional[str] = None,
) -> Tuple[NormalizedKRSProfile, RegistrySnapshot]:
    """Fetch KRS data and return normalized profile with snapshot.
    
    Args:
        krs_number: KRS number to lookup.
        entity_id: Optional entity ID to associate with snapshot.
        
    Returns:
        Tuple of (NormalizedKRSProfile, RegistrySnapshot).
        
    Raises:
        KRSClientError: On any error.
    """
    krs = normalize_krs_number(krs_number)
    
    # Fetch raw data
    data, raw_json = fetch_krs_data(krs)
    
    # Create snapshot
    snapshot = RegistrySnapshot(
        entity_id=entity_id,
        source_system="KRS",
        external_id=krs,
        fetched_at=datetime.utcnow(),
        payload_format="json",
        payload_raw=raw_json,
        payload_hash=hashlib.sha256(raw_json.encode()).hexdigest(),
    )
    
    # Normalize
    profile = normalize_krs_response(data)
    
    return profile, snapshot
