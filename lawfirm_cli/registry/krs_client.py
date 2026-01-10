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


def _extract_address(addr_data: Optional[Dict]) -> Optional[NormalizedAddress]:
    """Extract address from KRS address structure."""
    if not addr_data:
        return None
    
    return NormalizedAddress(
        address_type="MAIN",
        country=addr_data.get("kraj", "PL") or "PL",
        voivodeship=addr_data.get("wojewodztwo"),
        county=addr_data.get("powiat"),
        gmina=addr_data.get("gmina"),
        city=addr_data.get("miejscowosc"),
        postal_code=addr_data.get("kodPocztowy"),
        post_office=addr_data.get("poczta"),
        street=addr_data.get("ulica"),
        building_no=addr_data.get("nrDomu"),
        unit_no=addr_data.get("nrLokalu"),
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


def normalize_krs_response(data: Dict[str, Any]) -> NormalizedKRSProfile:
    """Normalize KRS API response to standard profile structure.
    
    Args:
        data: Raw response from KRS API.
        
    Returns:
        NormalizedKRSProfile with extracted data.
    """
    # KRS response structure varies, handle nested data
    odpis = data.get("odpis", data)
    dane = odpis.get("dane", odpis)
    
    # Get podstawowe dane (basic data)
    dzial1 = dane.get("dzial1", {})
    dane_podmiotu = dzial1.get("danePodmiotu", {})
    identyfikatory = dane_podmiotu.get("identyfikatory", {})
    
    # Get siedziba (seat/address)
    siedziba = dzial1.get("siedzibaIAdres", {})
    adres_siedziby = siedziba.get("adres", {})
    
    # Get PKD codes
    dzial3 = dane.get("dzial3", {})
    przedmiot_dzialalnosci = dzial3.get("przedmiotDzialalnosci", {})
    pkd_list = przedmiot_dzialalnosci.get("przedmiotPrzewazajacejDzialalnosci", [])
    if isinstance(pkd_list, dict):
        pkd_list = [pkd_list]
    
    pkd_codes = []
    pkd_main = None
    for pkd in pkd_list:
        if isinstance(pkd, dict):
            code = pkd.get("kodDzial")
            if code:
                pkd_codes.append(code)
                if not pkd_main:
                    pkd_main = code
    
    # Get representatives (zarząd)
    dzial2 = dane.get("dzial2", {})
    reprezentacja = dzial2.get("reprezentacja", {})
    sklad_organu = reprezentacja.get("skladOrganu", [])
    if isinstance(sklad_organu, dict):
        sklad_organu = [sklad_organu]
    
    representatives = []
    for osoba in sklad_organu:
        if isinstance(osoba, dict):
            rep = {
                "name": f"{osoba.get('imiona', '')} {osoba.get('nazwisko', '')}".strip(),
                "function": osoba.get("funkcjaWOrganie"),
                "pesel": osoba.get("identyfikator", {}).get("pesel") if isinstance(osoba.get("identyfikator"), dict) else None,
            }
            if rep["name"]:
                representatives.append(rep)
    
    # Extract contact info from dzial1 if available
    email = None
    website = None
    phone = None
    
    # Some KRS entries have contact info in siedziba
    if siedziba:
        email = siedziba.get("adresEmail") or siedziba.get("email")
        website = siedziba.get("adresStronyInternetowej") or siedziba.get("www")
        phone = siedziba.get("telefon")
    
    return NormalizedKRSProfile(
        krs=identyfikatory.get("krs") or identyfikatory.get("nrKRS"),
        nip=identyfikatory.get("nip"),
        regon=identyfikatory.get("regon"),
        official_name=dane_podmiotu.get("nazwa"),
        short_name=dane_podmiotu.get("nazwaSkrocona"),
        legal_form=dane_podmiotu.get("formaPrawna"),
        legal_form_code=dane_podmiotu.get("kodFormyPrawnej"),
        registry_status=dane_podmiotu.get("status"),
        registration_date=_parse_date(dane_podmiotu.get("dataRejestracjiWKRS")),
        seat_address=_extract_address(adres_siedziby),
        correspondence_address=None,  # May be in different section
        email=email,
        website=website,
        phone=phone,
        share_capital=dzial1.get("kapital", {}).get("wysokoscKapitaluZakladowego"),
        pkd_main=pkd_main,
        pkd_codes=pkd_codes,
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
