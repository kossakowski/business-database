"""Non-interactive entity creation for agents and scripts (`entity add --json`).

The interactive `entity create` asks every field; this module takes the same data as one JSON
object, validates it, checks the database for duplicates and returns a preview. Nothing is
written until the caller passes `--apply`, and the write goes through the same
`create_entity()` transaction as the interactive path.

Every answer is one JSON object `{ok, kind, data, error, exit_code}`. Exit codes follow the
invoice program's agent interface: 0 fine, 2 bad input, 5 conflict (duplicate), 7
infrastructure (database or registry down).
"""

import re
from typing import Any, Dict, List, Optional, Tuple

ENTITY_TYPES = ("PHYSICAL_PERSON", "LEGAL_PERSON")
IDENTIFIER_TYPES = ("NIP", "KRS", "REGON", "PESEL")
CONTACT_TYPES = ("EMAIL", "PHONE", "WEBSITE")
ADDRESS_FIELDS = ("street", "building_no", "unit_no", "postal_code", "city", "country")

PERSON_FIELDS = ("first_name", "middle_names", "last_name", "business_name",
                 "citizenship_country", "date_of_birth")
LEGAL_FIELDS = ("registered_name", "short_name", "legal_kind", "legal_form_suffix", "country")
TOP_FIELDS = ("entity_type", "canonical_label", "notes", "identifiers", "address", "contacts",
              "krs", "ceidg_nip") + PERSON_FIELDS + LEGAL_FIELDS

EXIT_OK = 0
EXIT_BAD_INPUT = 2
EXIT_CONFLICT = 5
EXIT_INFRA = 7

_ID_LENGTHS = {"NIP": (10,), "KRS": (10,), "REGON": (9, 14), "PESEL": (11,)}


class BadInput(Exception):
    """The request cannot be turned into an entity."""


def answer(kind: str, data: Any = None, error: Optional[Dict[str, Any]] = None,
           exit_code: int = EXIT_OK) -> Dict[str, Any]:
    return {"ok": error is None, "kind": kind, "data": data, "error": error,
            "exit_code": exit_code}


def error(code: str, message: str, exit_code: int, **details: Any) -> Dict[str, Any]:
    return answer("error", error={"code": code, "message": message, "details": details},
                  exit_code=exit_code)


def _text(value: Any, field: str) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise BadInput(f"Field '{field}' must be text.")
    value = " ".join(value.split())
    return value or None


def normalize_identifier(kind: str, value: Any) -> Dict[str, str]:
    kind = (kind or "").strip().upper()
    if kind not in IDENTIFIER_TYPES:
        raise BadInput(f"Identifier type '{kind}' is not one of {', '.join(IDENTIFIER_TYPES)}.")
    digits = re.sub(r"[\s-]", "", str(value or ""))
    if kind == "KRS" and digits.isdigit():
        digits = digits.zfill(10)
    if not digits.isdigit() or len(digits) not in _ID_LENGTHS[kind]:
        raise BadInput(f"{kind} '{value}' has the wrong length or is not digits only.")
    if kind == "NIP" and not _nip_ok(digits):
        raise BadInput(f"NIP '{value}' fails the checksum.")
    return {"type": kind, "value": digits}


def _nip_ok(nip: str) -> bool:
    wagi = (6, 5, 7, 2, 3, 4, 5, 6, 7)
    suma = sum(int(c) * w for c, w in zip(nip, wagi)) % 11
    return suma != 10 and suma == int(nip[9])


def prefill_from_krs(profile) -> Tuple[Dict[str, Any], List[Dict], Optional[Dict], List[Dict]]:
    """Entity data, identifiers, address and contacts from a normalized KRS profile."""
    data: Dict[str, Any] = {"country": "PL"}
    if profile.official_name:
        data["canonical_label"] = profile.official_name
        data["registered_name"] = profile.official_name
    if profile.short_name:
        data["short_name"] = profile.short_name
    if profile.legal_kind:
        data["legal_kind"] = profile.legal_kind
    if profile.legal_form_suffix:
        data["legal_form_suffix"] = profile.legal_form_suffix
    elif profile.legal_form:
        data["legal_form_suffix"] = profile.legal_form
    identifiers = [{"type": t, "value": v} for t, v in
                   (("KRS", profile.krs), ("NIP", profile.nip), ("REGON", profile.regon)) if v]
    address = profile.seat_address.to_dict() if profile.seat_address else None
    contacts = _profile_contacts(profile)
    return data, identifiers, address, contacts


def prefill_from_ceidg(profile) -> Tuple[Dict[str, Any], List[Dict], Optional[Dict], List[Dict]]:
    """Person data, identifiers, address and contacts from a normalized CEIDG profile."""
    data: Dict[str, Any] = {"citizenship_country": "PL", "is_deceased": False}
    if profile.first_name:
        data["first_name"] = profile.first_name
    if profile.last_name:
        data["last_name"] = profile.last_name
    if profile.business_name:
        data["business_name"] = profile.business_name
        data["canonical_label"] = profile.business_name
    elif profile.first_name and profile.last_name:
        data["canonical_label"] = f"{profile.first_name} {profile.last_name}"
    identifiers = [{"type": t, "value": v} for t, v in
                   (("NIP", profile.nip), ("REGON", profile.regon)) if v]
    address = profile.main_address.to_dict() if profile.main_address else None
    contacts = _profile_contacts(profile)
    return data, identifiers, address, contacts


def _profile_contacts(profile) -> List[Dict[str, str]]:
    return [{"type": t, "value": v} for t, v in
            (("EMAIL", profile.email), ("WEBSITE", profile.website), ("PHONE", profile.phone)) if v]


def check_sources(raw: Dict[str, Any]) -> None:
    """A registry lookup must fit the entity type: KRS is for companies, CEIDG for sole traders."""
    kind = str(raw.get("entity_type") or "").upper()
    if raw.get("krs") and raw.get("ceidg_nip"):
        raise BadInput("Give krs (company) or ceidg_nip (sole trader), not both.")
    if raw.get("krs") and kind == "PHYSICAL_PERSON":
        raise BadInput("krs fetches a company; a PHYSICAL_PERSON takes ceidg_nip or manual fields.")
    if raw.get("ceidg_nip") and kind == "LEGAL_PERSON":
        raise BadInput("ceidg_nip fetches a sole trader; a LEGAL_PERSON takes krs or manual fields.")


def build_request(raw: Dict[str, Any], prefill: Optional[Tuple] = None) -> Dict[str, Any]:
    """Validate the caller's object, merged over registry data; the caller's fields win.

    Returns {entity_type, entity_data, identifiers, address, contacts}.
    """
    if not isinstance(raw, dict):
        raise BadInput("The --json value must be one JSON object.")
    unknown = sorted(set(raw) - set(TOP_FIELDS))
    if unknown:
        raise BadInput(f"Unknown field(s): {', '.join(unknown)}.")

    base_data, base_ids, base_addr, base_contacts = prefill or ({}, [], None, [])
    entity_type = _text(raw.get("entity_type"), "entity_type")
    entity_type = entity_type.upper() if entity_type else None
    check_sources(raw)
    if entity_type is None:
        entity_type = "LEGAL_PERSON" if raw.get("krs") else (
            "PHYSICAL_PERSON" if raw.get("ceidg_nip") else None)
    if entity_type not in ENTITY_TYPES:
        raise BadInput(f"entity_type must be one of {', '.join(ENTITY_TYPES)}.")

    own = PERSON_FIELDS if entity_type == "PHYSICAL_PERSON" else LEGAL_FIELDS
    foreign = [f for f in (LEGAL_FIELDS if entity_type == "PHYSICAL_PERSON" else PERSON_FIELDS)
               if raw.get(f) is not None and f != "country"]
    if foreign:
        raise BadInput(f"Field(s) {', '.join(foreign)} do not belong to {entity_type}.")

    data = dict(base_data)
    for field in own + ("canonical_label", "notes"):
        value = _text(raw.get(field), field)
        if value is not None:
            data[field] = value

    if entity_type == "PHYSICAL_PERSON":
        if not data.get("last_name"):
            raise BadInput("A person needs last_name (and usually first_name).")
        data.setdefault("canonical_label", " ".join(
            p for p in (data.get("first_name"), data.get("last_name")) if p))
        data.setdefault("is_deceased", False)
    else:
        if not data.get("registered_name"):
            raise BadInput("A company needs registered_name, or krs to fetch it from KRS.")
        data.setdefault("canonical_label", data["registered_name"])
        data.setdefault("country", "PL")

    identifiers: Dict[str, Dict[str, str]] = {}
    for ident in base_ids:
        norm = normalize_identifier(ident["type"], ident["value"])
        identifiers[norm["type"]] = norm
    for ident in raw.get("identifiers") or []:
        if not isinstance(ident, dict):
            raise BadInput("Each identifier must be an object {type, value}.")
        norm = normalize_identifier(ident.get("type"), ident.get("value"))
        identifiers[norm["type"]] = norm
    if entity_type == "LEGAL_PERSON" and "PESEL" in identifiers:
        raise BadInput("A company cannot have a PESEL.")

    address = dict(base_addr) if base_addr else None
    if raw.get("address") is not None:
        addr = raw["address"]
        if not isinstance(addr, dict):
            raise BadInput("address must be an object.")
        extra = sorted(set(addr) - set(ADDRESS_FIELDS))
        if extra:
            raise BadInput(f"Unknown address field(s): {', '.join(extra)}.")
        address = {k: _text(addr.get(k), f"address.{k}") for k in ADDRESS_FIELDS}
        address["country"] = address["country"] or "PL"
        if not address["city"]:
            raise BadInput("address needs at least a city.")
    if address is not None:
        address["address_type"] = "MAIN"

    contacts = list(base_contacts)
    for contact in raw.get("contacts") or []:
        if not isinstance(contact, dict):
            raise BadInput("Each contact must be an object {type, value}.")
        kind = (contact.get("type") or "").strip().upper()
        value = _text(contact.get("value"), "contacts.value")
        if kind not in CONTACT_TYPES or not value:
            raise BadInput(f"Contact needs type in {', '.join(CONTACT_TYPES)} and a value.")
        if value.lower() not in {c["value"].lower() for c in contacts}:
            contacts.append({"type": kind, "value": value})

    return {"entity_type": entity_type, "entity_data": data,
            "identifiers": list(identifiers.values()), "address": address,
            "contacts": contacts}


def find_conflicts(request: Dict[str, Any], list_entities) -> Tuple[List[Dict], List[Dict]]:
    """(duplicates, similar): same identifier = duplicate; same name words = similar.

    `list_entities` is passed in so tests run without a database.
    """
    duplicates: List[Dict] = []
    for ident in request["identifiers"]:
        for row in list_entities(identifier_type=ident["type"],
                                 identifier_value=ident["value"], limit=5):
            duplicates.append({"identifier": ident, "entity_id": str(row["id"]),
                               "label": row["canonical_label"]})
    data = request["entity_data"]
    probe = data.get("last_name") or data.get("short_name") or data.get("canonical_label")
    similar: List[Dict] = []
    seen = {d["entity_id"] for d in duplicates}
    if probe:
        for row in list_entities(search=probe, limit=10):
            if str(row["id"]) not in seen:
                similar.append({"entity_id": str(row["id"]), "label": row["canonical_label"]})
    return duplicates, similar


def preview(request: Dict[str, Any], duplicates: List[Dict], similar: List[Dict],
            source: Optional[str]) -> Dict[str, Any]:
    warnings = []
    if similar:
        warnings.append({"code": "SIMILAR_NAME",
                         "message": "Entities with a similar name already exist; check they "
                                    "are not the same client.", "details": {"similar": similar}})
    if request["address"] is None:
        warnings.append({"code": "NO_ADDRESS",
                         "message": "No address: costs can be recorded, but an invoice needs "
                                    "the buyer's address."})
    return {"entity": request, "source": source or "manual", "duplicates": duplicates,
            "warnings": warnings}
