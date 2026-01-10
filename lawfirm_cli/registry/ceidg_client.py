"""CEIDG (Centralna Ewidencja i Informacja o Działalności Gospodarczej) API client.

CEIDG API Documentation:
- REST API Base URL: https://dane.biznes.gov.pl/api/ceidg/v2
- Requires API token obtained from dane.biznes.gov.pl
- Supports lookup by NIP, REGON, or name

Environment Variables:
- CEIDG_API_TOKEN: API token for authentication (required)
- CEIDG_API_BASE_URL: Override default API base URL (optional)
- CEIDG_REQUEST_TIMEOUT: Request timeout in seconds (default: 30)

Note: Without CEIDG_API_TOKEN, the client will not work and will return
a clear error message.
"""

import hashlib
import json
import os
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.exceptions import RequestException, Timeout

from lawfirm_cli.registry.models import (
    NormalizedCEIDGProfile,
    NormalizedAddress,
    RegistrySnapshot,
)


# Default configuration
DEFAULT_CEIDG_API_BASE_URL = "https://dane.biznes.gov.pl/api/ceidg/v2"
DEFAULT_TIMEOUT = 30


class CEIDGClientError(Exception):
    """Base exception for CEIDG client errors."""
    pass


class CEIDGNotConfiguredError(CEIDGClientError):
    """Raised when CEIDG credentials are not configured."""
    pass


class CEIDGNotFoundError(CEIDGClientError):
    """Raised when entry is not found."""
    pass


class CEIDGConnectionError(CEIDGClientError):
    """Raised on network/connection errors."""
    pass


class CEIDGParseError(CEIDGClientError):
    """Raised when response cannot be parsed."""
    pass


def get_ceidg_config() -> Tuple[str, str, int]:
    """Get CEIDG API configuration from environment.
    
    Returns:
        Tuple of (base_url, api_token, timeout_seconds).
        
    Raises:
        CEIDGNotConfiguredError: If API token is not configured.
    """
    base_url = os.environ.get("CEIDG_API_BASE_URL", DEFAULT_CEIDG_API_BASE_URL)
    api_token = os.environ.get("CEIDG_API_TOKEN", "")
    timeout = int(os.environ.get("CEIDG_REQUEST_TIMEOUT", DEFAULT_TIMEOUT))
    
    if not api_token:
        raise CEIDGNotConfiguredError(
            "CEIDG integration not configured.\n"
            "Please set CEIDG_API_TOKEN environment variable.\n"
            "You can obtain a free API token at: https://dane.biznes.gov.pl"
        )
    
    return base_url, api_token, timeout


def is_ceidg_configured() -> bool:
    """Check if CEIDG API is configured.
    
    Returns:
        True if API token is set.
    """
    return bool(os.environ.get("CEIDG_API_TOKEN"))


def normalize_nip(nip: str) -> str:
    """Normalize NIP number (remove dashes and spaces).
    
    Args:
        nip: NIP number.
        
    Returns:
        Normalized 10-digit NIP.
        
    Raises:
        ValueError: If NIP is invalid.
    """
    nip = nip.strip().replace("-", "").replace(" ", "")
    
    if not nip.isdigit():
        raise ValueError(f"Invalid NIP: {nip} (must be numeric)")
    
    if len(nip) != 10:
        raise ValueError(f"Invalid NIP: {nip} (must be 10 digits)")
    
    return nip


def normalize_regon(regon: str) -> str:
    """Normalize REGON number (remove dashes and spaces).
    
    Args:
        regon: REGON number.
        
    Returns:
        Normalized REGON (9 or 14 digits).
        
    Raises:
        ValueError: If REGON is invalid.
    """
    regon = regon.strip().replace("-", "").replace(" ", "")
    
    if not regon.isdigit():
        raise ValueError(f"Invalid REGON: {regon} (must be numeric)")
    
    if len(regon) not in (9, 14):
        raise ValueError(f"Invalid REGON: {regon} (must be 9 or 14 digits)")
    
    return regon


def fetch_ceidg_by_nip(nip: str) -> Tuple[Dict[str, Any], str]:
    """Fetch CEIDG data by NIP.
    
    Args:
        nip: NIP number.
        
    Returns:
        Tuple of (response_data_dict, raw_json_string).
        
    Raises:
        CEIDGNotConfiguredError: If API token not set.
        CEIDGNotFoundError: If NIP not found.
        CEIDGConnectionError: On network errors.
        CEIDGParseError: If response cannot be parsed.
    """
    base_url, api_token, timeout = get_ceidg_config()
    nip = normalize_nip(nip)
    
    url = f"{base_url}/firmy"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/json",
    }
    params = {"nip": nip}
    
    return _fetch_ceidg(url, headers, params, timeout, f"NIP {nip}")


def fetch_ceidg_by_regon(regon: str) -> Tuple[Dict[str, Any], str]:
    """Fetch CEIDG data by REGON.
    
    Args:
        regon: REGON number.
        
    Returns:
        Tuple of (response_data_dict, raw_json_string).
        
    Raises:
        CEIDGNotConfiguredError: If API token not set.
        CEIDGNotFoundError: If REGON not found.
        CEIDGConnectionError: On network errors.
        CEIDGParseError: If response cannot be parsed.
    """
    base_url, api_token, timeout = get_ceidg_config()
    regon = normalize_regon(regon)
    
    url = f"{base_url}/firmy"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/json",
    }
    params = {"regon": regon}
    
    return _fetch_ceidg(url, headers, params, timeout, f"REGON {regon}")


def _fetch_ceidg(
    url: str,
    headers: Dict[str, str],
    params: Dict[str, str],
    timeout: int,
    lookup_desc: str,
) -> Tuple[Dict[str, Any], str]:
    """Internal fetch function for CEIDG API.
    
    Args:
        url: API endpoint URL.
        headers: HTTP headers.
        params: Query parameters.
        timeout: Request timeout.
        lookup_desc: Description of lookup for error messages.
        
    Returns:
        Tuple of (response_data_dict, raw_json_string).
    """
    try:
        response = requests.get(url, headers=headers, params=params, timeout=timeout)
        
        if response.status_code == 401:
            raise CEIDGClientError("CEIDG API authentication failed. Check your API token.")
        
        if response.status_code == 404:
            raise CEIDGNotFoundError(f"{lookup_desc} not found in CEIDG")
        
        if response.status_code != 200:
            raise CEIDGClientError(
                f"CEIDG API returned status {response.status_code}: {response.text[:200]}"
            )
        
        raw_json = response.text
        data = response.json()
        
        # CEIDG returns array of results
        if isinstance(data, dict) and "firmy" in data:
            firms = data.get("firmy", [])
        elif isinstance(data, list):
            firms = data
        else:
            firms = [data] if data else []
        
        if not firms:
            raise CEIDGNotFoundError(f"{lookup_desc} not found in CEIDG")
        
        # Return first match
        return firms[0], raw_json
        
    except Timeout:
        raise CEIDGConnectionError(
            f"Request to CEIDG API timed out after {timeout} seconds"
        )
    except RequestException as e:
        raise CEIDGConnectionError(f"Failed to connect to CEIDG API: {e}")
    except json.JSONDecodeError as e:
        raise CEIDGParseError(f"Failed to parse CEIDG API response: {e}")


def _extract_ceidg_address(addr_data: Optional[Dict]) -> Optional[NormalizedAddress]:
    """Extract address from CEIDG address structure."""
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
        building_no=addr_data.get("budynek") or addr_data.get("nrNieruchomosci"),
        unit_no=addr_data.get("lokal") or addr_data.get("nrLokalu"),
    )


def _parse_date(date_str: Optional[str]) -> Optional[date]:
    """Parse date string from CEIDG format."""
    if not date_str:
        return None
    try:
        # CEIDG uses YYYY-MM-DD format
        return datetime.strptime(date_str[:10], "%Y-%m-%d").date()
    except (ValueError, IndexError):
        return None


def normalize_ceidg_response(data: Dict[str, Any]) -> NormalizedCEIDGProfile:
    """Normalize CEIDG API response to standard profile structure.
    
    Args:
        data: Raw response from CEIDG API (single firm entry).
        
    Returns:
        NormalizedCEIDGProfile with extracted data.
    """
    # Owner data
    wlasciciel = data.get("wlasciciel", {})
    
    # Business data
    firma = data.get("firma", data.get("nazwa", ""))
    
    # Addresses
    adres_glowny = data.get("adresDzialalnosci") or data.get("adresGlownegoMiejscaWykonywaniaDzialalnosci", {})
    adres_koresp = data.get("adresDoKorespondencji", {})
    
    # Additional business addresses
    business_addresses = []
    dodatkowe_adresy = data.get("dodatkoweMiejscaWykonywaniaDzialalnosci", [])
    if isinstance(dodatkowe_adresy, list):
        for addr in dodatkowe_adresy:
            if addr:
                norm_addr = _extract_ceidg_address(addr)
                if norm_addr:
                    norm_addr.address_type = "BUSINESS"
                    business_addresses.append(norm_addr)
    
    # PKD codes
    pkd_data = data.get("pkd", [])
    if isinstance(pkd_data, dict):
        pkd_data = [pkd_data]
    
    pkd_codes = []
    pkd_main = None
    for pkd in pkd_data:
        if isinstance(pkd, dict):
            code = pkd.get("kod")
            if code:
                pkd_codes.append(code)
                if pkd.get("przewazajace") or not pkd_main:
                    pkd_main = code
        elif isinstance(pkd, str):
            pkd_codes.append(pkd)
            if not pkd_main:
                pkd_main = pkd
    
    # Contact info
    kontakt = data.get("kontakt", {})
    email = kontakt.get("email") or data.get("email")
    website = kontakt.get("stronaWww") or data.get("www") or data.get("stronaInternetowa")
    phone = kontakt.get("telefon") or data.get("telefon")
    
    # Status mapping
    status_raw = data.get("status", "")
    status = status_raw.upper() if status_raw else None
    
    # Build correspondence address
    corr_addr = None
    if adres_koresp:
        corr_addr = _extract_ceidg_address(adres_koresp)
        if corr_addr:
            corr_addr.address_type = "CORRESPONDENCE"
    
    return NormalizedCEIDGProfile(
        ceidg_id=data.get("id") or data.get("identyfikatorWpisu"),
        nip=data.get("nip") or wlasciciel.get("nip"),
        regon=data.get("regon"),
        first_name=wlasciciel.get("imie") or data.get("imie"),
        last_name=wlasciciel.get("nazwisko") or data.get("nazwisko"),
        business_name=firma,
        status=status,
        start_date=_parse_date(data.get("dataRozpoczeciaDzialalnosci")),
        end_date=_parse_date(data.get("dataZakonczeniaDzialalnosci")),
        suspension_date=_parse_date(data.get("dataZawieszeniaDzialalnosci")),
        resume_date=_parse_date(data.get("dataWznowieniaDzialalnosci")),
        main_address=_extract_ceidg_address(adres_glowny),
        correspondence_address=corr_addr,
        business_addresses=business_addresses,
        email=email,
        website=website,
        phone=phone,
        pkd_main=pkd_main,
        pkd_codes=pkd_codes,
        raw_payload=data,
    )


def fetch_and_normalize_ceidg_by_nip(
    nip: str,
    entity_id: Optional[str] = None,
) -> Tuple[NormalizedCEIDGProfile, RegistrySnapshot]:
    """Fetch CEIDG data by NIP and return normalized profile with snapshot.
    
    Args:
        nip: NIP number to lookup.
        entity_id: Optional entity ID to associate with snapshot.
        
    Returns:
        Tuple of (NormalizedCEIDGProfile, RegistrySnapshot).
        
    Raises:
        CEIDGClientError: On any error.
    """
    nip = normalize_nip(nip)
    
    # Fetch raw data
    data, raw_json = fetch_ceidg_by_nip(nip)
    
    # Create snapshot
    snapshot = RegistrySnapshot(
        entity_id=entity_id,
        source_system="CEIDG",
        external_id=f"NIP:{nip}",
        fetched_at=datetime.utcnow(),
        payload_format="json",
        payload_raw=raw_json,
        payload_hash=hashlib.sha256(raw_json.encode()).hexdigest(),
    )
    
    # Normalize
    profile = normalize_ceidg_response(data)
    
    return profile, snapshot


def fetch_and_normalize_ceidg_by_regon(
    regon: str,
    entity_id: Optional[str] = None,
) -> Tuple[NormalizedCEIDGProfile, RegistrySnapshot]:
    """Fetch CEIDG data by REGON and return normalized profile with snapshot.
    
    Args:
        regon: REGON number to lookup.
        entity_id: Optional entity ID to associate with snapshot.
        
    Returns:
        Tuple of (NormalizedCEIDGProfile, RegistrySnapshot).
        
    Raises:
        CEIDGClientError: On any error.
    """
    regon = normalize_regon(regon)
    
    # Fetch raw data
    data, raw_json = fetch_ceidg_by_regon(regon)
    
    # Create snapshot
    snapshot = RegistrySnapshot(
        entity_id=entity_id,
        source_system="CEIDG",
        external_id=f"REGON:{regon}",
        fetched_at=datetime.utcnow(),
        payload_format="json",
        payload_raw=raw_json,
        payload_hash=hashlib.sha256(raw_json.encode()).hexdigest(),
    )
    
    # Normalize
    profile = normalize_ceidg_response(data)
    
    return profile, snapshot
