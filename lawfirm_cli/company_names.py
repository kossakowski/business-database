"""Polish company name parsing and legal form extraction.

This module provides utilities for parsing Polish company names to:
- Extract the legal form suffix from a full company name
- Generate a suggested short name (name without the suffix)
- Map legal forms (from KRS formaPrawna or kodFormyPrawnej) to internal legal_kind enum

Polish commercial company naming conventions:
- Full name = Particular name + Legal form suffix
- Example: "PROFINANCE SPÓŁKA AKCYJNA" → short name "PROFINANCE", suffix "S.A."
"""

import re
from dataclasses import dataclass
from typing import Optional, Tuple, List


@dataclass
class LegalFormInfo:
    """Information about a Polish legal form."""
    legal_kind: str           # Internal enum value (e.g., 'SPOLKA_AKCYJNA')
    full_suffix: str          # Full Polish suffix (e.g., 'spółka akcyjna')
    short_suffix: str         # Abbreviated suffix (e.g., 'S.A.')
    krs_form_codes: List[str] # KRS kodFormyPrawnej values


# Define all recognized Polish commercial company forms
# Order matters: more specific forms should come first to avoid partial matches
LEGAL_FORMS: List[LegalFormInfo] = [
    LegalFormInfo(
        legal_kind="SPOLKA_KOMANDYTOWO_AKCYJNA",
        full_suffix="spółka komandytowo-akcyjna",
        short_suffix="S.K.A.",
        krs_form_codes=["116"],
    ),
    LegalFormInfo(
        legal_kind="SPOLKA_Z_OO",
        full_suffix="spółka z ograniczoną odpowiedzialnością",
        short_suffix="sp. z o.o.",
        krs_form_codes=["117"],
    ),
    LegalFormInfo(
        legal_kind="PROSTA_SPOLKA_AKCYJNA",
        full_suffix="prosta spółka akcyjna",
        short_suffix="P.S.A.",
        krs_form_codes=["161"],  # Introduced in 2021
    ),
    LegalFormInfo(
        legal_kind="SPOLKA_AKCYJNA",
        full_suffix="spółka akcyjna",
        short_suffix="S.A.",
        krs_form_codes=["114"],
    ),
    LegalFormInfo(
        legal_kind="SPOLKA_KOMANDYTOWA",
        full_suffix="spółka komandytowa",
        short_suffix="sp. k.",
        krs_form_codes=["113"],
    ),
    LegalFormInfo(
        legal_kind="SPOLKA_PARTNERSKA",
        full_suffix="spółka partnerska",
        short_suffix="sp.p.",
        krs_form_codes=["112"],
    ),
    LegalFormInfo(
        legal_kind="SPOLKA_JAWNA",
        full_suffix="spółka jawna",
        short_suffix="sp. j.",
        krs_form_codes=["111"],
    ),
    # Non-commercial entities (no standard abbreviation)
    LegalFormInfo(
        legal_kind="FUNDACJA",
        full_suffix="fundacja",
        short_suffix="",
        krs_form_codes=["125"],
    ),
    LegalFormInfo(
        legal_kind="STOWARZYSZENIE",
        full_suffix="stowarzyszenie",
        short_suffix="",
        krs_form_codes=["126"],
    ),
    LegalFormInfo(
        legal_kind="FUNDACJA_RODZINNA",
        full_suffix="fundacja rodzinna",
        short_suffix="",
        krs_form_codes=["160"],  # Introduced in 2023
    ),
    LegalFormInfo(
        legal_kind="SPOLDZIELNIA",
        full_suffix="spółdzielnia",
        short_suffix="",
        krs_form_codes=["140", "141", "142", "143", "144", "145"],
    ),
    LegalFormInfo(
        legal_kind="SPOLDZIELNIA_MIESZKANIOWA",
        full_suffix="spółdzielnia mieszkaniowa",
        short_suffix="",
        krs_form_codes=["141"],
    ),
]

# Build lookup dictionaries for faster access
_LEGAL_KIND_BY_KRS_CODE: dict = {}
_LEGAL_FORM_BY_KIND: dict = {}

for form in LEGAL_FORMS:
    _LEGAL_FORM_BY_KIND[form.legal_kind] = form
    for code in form.krs_form_codes:
        _LEGAL_KIND_BY_KRS_CODE[code] = form.legal_kind


def normalize_for_matching(text: str) -> str:
    """Normalize text for case-insensitive, whitespace-tolerant matching.
    
    Args:
        text: Input text to normalize.
        
    Returns:
        Lowercase text with normalized whitespace.
    """
    if not text:
        return ""
    # Normalize whitespace and convert to lowercase
    return " ".join(text.lower().split())


def extract_legal_form_from_name(full_name: str) -> Tuple[Optional[LegalFormInfo], str]:
    """Extract legal form information from a full company name.
    
    This function identifies the legal form suffix in a Polish company name
    and returns both the form information and the particular name (without suffix).
    
    Args:
        full_name: Full company name (e.g., "PROFINANCE SPÓŁKA AKCYJNA").
        
    Returns:
        Tuple of (LegalFormInfo or None, particular_name).
        particular_name is the name with the legal form suffix removed.
        
    Examples:
        >>> extract_legal_form_from_name("PROFINANCE SPÓŁKA AKCYJNA")
        (LegalFormInfo(...SPOLKA_AKCYJNA...), "PROFINANCE")
        
        >>> extract_legal_form_from_name("ABC SP. Z O.O.")
        (LegalFormInfo(...SPOLKA_Z_OO...), "ABC")
    """
    if not full_name:
        return None, ""
    
    normalized = normalize_for_matching(full_name)
    original_parts = full_name.strip()
    
    # Try to match full suffixes first (they're more specific)
    for form in LEGAL_FORMS:
        full_suffix_norm = normalize_for_matching(form.full_suffix)
        if not full_suffix_norm:
            continue
            
        if normalized.endswith(full_suffix_norm):
            # Found a match - extract the particular name
            suffix_len = len(full_suffix_norm)
            # Get the original text without the suffix, preserving case
            particular = original_parts[:-suffix_len].strip() if suffix_len else original_parts
            return form, particular
    
    # Try abbreviated suffixes
    # Build patterns for abbreviated forms (handle variations in spacing/dots)
    abbrev_patterns = [
        # S.A. variations
        (r'\s*s\.?\s*a\.?\s*$', "SPOLKA_AKCYJNA"),
        # sp. z o.o. variations  
        (r'\s*sp\.?\s*z\.?\s*o\.?\s*o\.?\s*$', "SPOLKA_Z_OO"),
        (r'\s*spółka\s+z\s+o\.?\s*o\.?\s*$', "SPOLKA_Z_OO"),
        # sp. k. variations
        (r'\s*sp\.?\s*k\.?\s*$', "SPOLKA_KOMANDYTOWA"),
        # sp. j. variations
        (r'\s*sp\.?\s*j\.?\s*$', "SPOLKA_JAWNA"),
        # sp. p. variations
        (r'\s*sp\.?\s*p\.?\s*$', "SPOLKA_PARTNERSKA"),
        # S.K.A. variations
        (r'\s*s\.?\s*k\.?\s*a\.?\s*$', "SPOLKA_KOMANDYTOWO_AKCYJNA"),
        # P.S.A. variations
        (r'\s*p\.?\s*s\.?\s*a\.?\s*$', "PROSTA_SPOLKA_AKCYJNA"),
    ]
    
    for pattern, legal_kind in abbrev_patterns:
        match = re.search(pattern, normalized, re.IGNORECASE)
        if match:
            # Get the form info
            form = _LEGAL_FORM_BY_KIND.get(legal_kind)
            if form:
                # Extract particular name
                start_pos = match.start()
                # Find corresponding position in original (approximately)
                particular = original_parts[:start_pos].strip()
                return form, particular
    
    # No match found
    return None, full_name.strip()


def get_legal_kind_from_krs_code(krs_code: Optional[str]) -> Optional[str]:
    """Get the internal legal_kind enum value from a KRS form code.
    
    Args:
        krs_code: KRS kodFormyPrawnej value (e.g., "117" for sp. z o.o.).
        
    Returns:
        Internal legal_kind enum value (e.g., "SPOLKA_Z_OO") or None.
    """
    if not krs_code:
        return None
    return _LEGAL_KIND_BY_KRS_CODE.get(str(krs_code).strip())


def get_legal_kind_from_krs_form_name(form_name: Optional[str]) -> Optional[str]:
    """Get the internal legal_kind enum value from a KRS form name.
    
    Args:
        form_name: KRS formaPrawna value (e.g., "SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ").
        
    Returns:
        Internal legal_kind enum value (e.g., "SPOLKA_Z_OO") or None.
    """
    if not form_name:
        return None
    
    normalized = normalize_for_matching(form_name)
    
    for form in LEGAL_FORMS:
        if normalize_for_matching(form.full_suffix) == normalized:
            return form.legal_kind
    
    return None


def suggest_short_name(full_name: str, legal_form: Optional[LegalFormInfo] = None) -> str:
    """Suggest a short name for a company based on its full name.
    
    The short name is the particular name plus the abbreviated suffix.
    For example: "PROFINANCE SPÓŁKA AKCYJNA" → "PROFINANCE S.A."
    
    Args:
        full_name: Full company name.
        legal_form: Optional pre-computed legal form info.
        
    Returns:
        Suggested short name with abbreviated suffix.
    """
    if not full_name:
        return ""
    
    if legal_form is None:
        legal_form, particular = extract_legal_form_from_name(full_name)
    else:
        _, particular = extract_legal_form_from_name(full_name)
    
    if not particular:
        return full_name.strip()
    
    if legal_form and legal_form.short_suffix:
        return f"{particular} {legal_form.short_suffix}"
    
    return particular


def get_legal_form_suffix(legal_kind: str) -> Optional[str]:
    """Get the standard abbreviated suffix for a legal_kind.
    
    Args:
        legal_kind: Internal enum value (e.g., "SPOLKA_AKCYJNA").
        
    Returns:
        Abbreviated suffix (e.g., "S.A.") or None if not applicable.
    """
    form = _LEGAL_FORM_BY_KIND.get(legal_kind)
    return form.short_suffix if form else None


def parse_krs_company_data(
    official_name: Optional[str],
    legal_form_name: Optional[str] = None,
    legal_form_code: Optional[str] = None,
) -> dict:
    """Parse KRS company data and suggest legal_kind and short_name.
    
    This is the main entry point for processing KRS data. It uses all available
    information to determine the legal form and suggest a short name.
    
    Args:
        official_name: Full company name from KRS (nazwa field).
        legal_form_name: Legal form name from KRS (formaPrawna field).
        legal_form_code: Legal form code from KRS (kodFormyPrawnej field).
        
    Returns:
        Dict with keys:
        - legal_kind: Suggested internal enum value or None
        - short_name: Suggested short name or None
        - legal_form_suffix: Standard suffix (e.g., "sp. z o.o.") or None
        - particular_name: Company name without legal form suffix
        - confidence: 'high' if code-based, 'medium' if name-based, 'low' if guessed
    """
    result = {
        "legal_kind": None,
        "short_name": None,
        "legal_form_suffix": None,
        "particular_name": None,
        "confidence": "low",
    }
    
    # Strategy 1: Use KRS form code (most reliable)
    legal_kind = get_legal_kind_from_krs_code(legal_form_code)
    if legal_kind:
        result["legal_kind"] = legal_kind
        result["confidence"] = "high"
    
    # Strategy 2: Use KRS form name
    if not result["legal_kind"] and legal_form_name:
        legal_kind = get_legal_kind_from_krs_form_name(legal_form_name)
        if legal_kind:
            result["legal_kind"] = legal_kind
            result["confidence"] = "medium"
    
    # Strategy 3: Parse from company name
    if official_name:
        form_info, particular = extract_legal_form_from_name(official_name)
        result["particular_name"] = particular
        
        if form_info:
            if not result["legal_kind"]:
                result["legal_kind"] = form_info.legal_kind
                result["confidence"] = "medium"
            
            result["legal_form_suffix"] = form_info.short_suffix or form_info.full_suffix
            result["short_name"] = suggest_short_name(official_name, form_info)
    
    # If we have legal_kind but no suffix, get it from the form
    if result["legal_kind"] and not result["legal_form_suffix"]:
        result["legal_form_suffix"] = get_legal_form_suffix(result["legal_kind"])
    
    return result
