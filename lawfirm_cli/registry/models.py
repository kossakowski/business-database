"""Data models for registry integration."""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from enum import Enum


class ProposalAction(Enum):
    """Action type for a proposal."""
    ADD = "add"
    UPDATE = "update"
    SKIP = "skip"


@dataclass
class NormalizedAddress:
    """Normalized address structure from registry data."""
    address_type: str = "MAIN"
    country: str = "PL"
    voivodeship: Optional[str] = None
    county: Optional[str] = None
    gmina: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    post_office: Optional[str] = None
    street: Optional[str] = None
    building_no: Optional[str] = None
    unit_no: Optional[str] = None
    additional_line: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for DB insertion."""
        return {
            "address_type": self.address_type,
            "country": self.country,
            "voivodeship": self.voivodeship,
            "county": self.county,
            "gmina": self.gmina,
            "city": self.city,
            "postal_code": self.postal_code,
            "post_office": self.post_office,
            "street": self.street,
            "building_no": self.building_no,
            "unit_no": self.unit_no,
            "additional_line": self.additional_line,
        }
    
    def format_oneline(self) -> str:
        """Format address as single line for display."""
        parts = []
        if self.street:
            s = self.street
            if self.building_no:
                s += f" {self.building_no}"
                if self.unit_no:
                    s += f"/{self.unit_no}"
            parts.append(s)
        if self.postal_code or self.city:
            parts.append(f"{self.postal_code or ''} {self.city or ''}".strip())
        return ", ".join(parts) if parts else "(no address)"


@dataclass
class RegistrySnapshot:
    """Immutable snapshot of registry data."""
    id: Optional[str] = None
    entity_id: Optional[str] = None
    source_system: str = ""  # KRS or CEIDG
    external_id: str = ""    # KRS number or CEIDG unique ID
    fetched_at: Optional[datetime] = None
    effective_date: Optional[date] = None
    payload_format: str = "json"
    payload_raw: str = ""
    payload_hash: str = ""
    fetched_by: Optional[str] = None
    purpose_ref: Optional[str] = None


@dataclass
class NormalizedKRSProfile:
    """Normalized data extracted from KRS registry."""
    # Core identifiers
    krs: Optional[str] = None
    nip: Optional[str] = None
    regon: Optional[str] = None
    
    # Names
    official_name: Optional[str] = None
    short_name: Optional[str] = None
    
    # Legal form
    legal_form: Optional[str] = None
    legal_form_code: Optional[str] = None
    
    # Status
    registry_status: Optional[str] = None
    registration_date: Optional[date] = None
    
    # Addresses
    seat_address: Optional[NormalizedAddress] = None
    correspondence_address: Optional[NormalizedAddress] = None
    
    # Contacts
    email: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    
    # Capital
    share_capital: Optional[str] = None
    share_capital_currency: str = "PLN"
    
    # PKD codes
    pkd_main: Optional[str] = None
    pkd_codes: List[str] = field(default_factory=list)
    
    # Representatives
    representatives: List[Dict[str, Any]] = field(default_factory=list)
    
    # Raw data reference
    raw_payload: Optional[Dict[str, Any]] = None


@dataclass 
class NormalizedCEIDGProfile:
    """Normalized data extracted from CEIDG registry."""
    # Identifiers
    ceidg_id: Optional[str] = None
    nip: Optional[str] = None
    regon: Optional[str] = None
    
    # Person data
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    # Business data
    business_name: Optional[str] = None  # "Firma" field
    
    # Status
    status: Optional[str] = None  # AKTYWNY, ZAWIESZONY, WYKRESLONY
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    suspension_date: Optional[date] = None
    resume_date: Optional[date] = None
    
    # Addresses
    main_address: Optional[NormalizedAddress] = None
    correspondence_address: Optional[NormalizedAddress] = None
    business_addresses: List[NormalizedAddress] = field(default_factory=list)
    
    # Contacts
    email: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    
    # PKD codes
    pkd_main: Optional[str] = None
    pkd_codes: List[str] = field(default_factory=list)
    
    # Raw data reference
    raw_payload: Optional[Dict[str, Any]] = None


@dataclass
class IdentifierProposal:
    """Proposal to add an identifier."""
    identifier_type: str
    identifier_value: str
    registry_name: Optional[str] = None
    action: ProposalAction = ProposalAction.ADD
    reason: str = ""
    collision_entity_id: Optional[str] = None  # If exists on another entity


@dataclass
class ContactProposal:
    """Proposal to add a contact."""
    contact_type: str  # EMAIL, PHONE, WEBSITE
    contact_value: str
    label: Optional[str] = None
    action: ProposalAction = ProposalAction.ADD
    reason: str = ""


@dataclass
class AddressProposal:
    """Proposal to add or update an address."""
    address: NormalizedAddress
    action: ProposalAction = ProposalAction.ADD
    existing_address_id: Optional[str] = None  # If updating
    reason: str = ""
    
    def get_changes_summary(self, existing: Optional[Dict[str, Any]] = None) -> List[str]:
        """Get list of changes compared to existing address."""
        if not existing:
            return ["New address"]
        
        changes = []
        addr_dict = self.address.to_dict()
        for key, new_val in addr_dict.items():
            old_val = existing.get(key)
            if new_val and new_val != old_val:
                changes.append(f"{key}: {old_val or '(empty)'} → {new_val}")
        return changes


@dataclass
class EnrichmentProposal:
    """Complete enrichment proposal for an entity."""
    entity_id: str
    source_system: str  # KRS or CEIDG
    external_id: str    # Lookup key used
    
    # Core entity updates (canonical_label, status, notes)
    core_updates: Dict[str, Any] = field(default_factory=dict)
    
    # Type-specific updates
    # For LEGAL_PERSON: registered_name, short_name, legal_kind, etc.
    # For PHYSICAL_PERSON: first_name, last_name, etc.
    type_specific_updates: Dict[str, Any] = field(default_factory=dict)
    
    # Related data proposals
    identifiers_to_add: List[IdentifierProposal] = field(default_factory=list)
    contacts_to_add: List[ContactProposal] = field(default_factory=list)
    address_proposals: List[AddressProposal] = field(default_factory=list)
    
    # Warnings and notes
    warnings: List[str] = field(default_factory=list)
    info_messages: List[str] = field(default_factory=list)
    
    # Snapshot reference
    snapshot_id: Optional[str] = None
    
    def has_any_proposals(self) -> bool:
        """Check if there are any actual proposals."""
        return bool(
            self.core_updates or
            self.type_specific_updates or
            self.identifiers_to_add or
            self.contacts_to_add or
            self.address_proposals
        )
    
    def count_proposals(self) -> int:
        """Count total number of proposals."""
        count = 0
        count += len(self.core_updates)
        count += len(self.type_specific_updates)
        count += len(self.identifiers_to_add)
        count += len(self.contacts_to_add)
        count += len(self.address_proposals)
        return count
