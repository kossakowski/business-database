"""Proposal generation for registry enrichment.

This module compares current entity data with registry data and generates
proposals for what can be added or updated.
"""

from typing import Any, Dict, List, Optional, Set

from lawfirm_cli.registry.models import (
    EnrichmentProposal,
    IdentifierProposal,
    ContactProposal,
    AddressProposal,
    NormalizedKRSProfile,
    NormalizedCEIDGProfile,
    NormalizedAddress,
    ProposalAction,
)


def _get_existing_identifier_values(
    entity: Dict[str, Any],
    identifier_type: str,
) -> Set[str]:
    """Get set of existing identifier values of given type."""
    values = set()
    for ident in entity.get("identifiers", []):
        if ident.get("identifier_type") == identifier_type:
            val = ident.get("identifier_value")
            if val:
                values.add(val.strip().replace("-", "").replace(" ", ""))
    return values


def _get_existing_contact_values(
    entity: Dict[str, Any],
    contact_type: str,
) -> Set[str]:
    """Get set of existing contact values of given type."""
    values = set()
    for contact in entity.get("contacts", []):
        if contact.get("contact_type") == contact_type:
            val = contact.get("contact_value")
            if val:
                values.add(val.strip().lower())
    return values


def _get_existing_address_by_type(
    entity: Dict[str, Any],
    address_type: str,
) -> Optional[Dict[str, Any]]:
    """Get existing address by type."""
    for addr in entity.get("addresses", []):
        if addr.get("address_type") == address_type:
            return addr
    return None


def _propose_identifier(
    proposal: EnrichmentProposal,
    entity: Dict[str, Any],
    identifier_type: str,
    value: Optional[str],
    all_existing: Optional[Dict[str, str]] = None,
) -> None:
    """Add identifier proposal if value is new."""
    if not value:
        return
    
    normalized = value.strip().replace("-", "").replace(" ", "")
    existing = _get_existing_identifier_values(entity, identifier_type)
    
    if normalized in existing:
        proposal.info_messages.append(
            f"{identifier_type} {normalized} already exists on entity"
        )
        return
    
    # Check collision with other entities
    collision_id = None
    if all_existing and identifier_type in all_existing:
        collision_id = all_existing[identifier_type].get(normalized)
    
    ident_proposal = IdentifierProposal(
        identifier_type=identifier_type,
        identifier_value=normalized,
        action=ProposalAction.ADD if not collision_id else ProposalAction.SKIP,
        reason="From registry" if not collision_id else f"Collision with entity {collision_id}",
        collision_entity_id=collision_id,
    )
    
    if collision_id:
        proposal.warnings.append(
            f"{identifier_type} {normalized} already exists on another entity ({collision_id})"
        )
    
    proposal.identifiers_to_add.append(ident_proposal)


def _propose_contact(
    proposal: EnrichmentProposal,
    entity: Dict[str, Any],
    contact_type: str,
    value: Optional[str],
    label: Optional[str] = None,
) -> None:
    """Add contact proposal if value is new."""
    if not value:
        return
    
    normalized = value.strip()
    existing = _get_existing_contact_values(entity, contact_type)
    
    if normalized.lower() in existing:
        proposal.info_messages.append(
            f"{contact_type} {normalized} already exists on entity"
        )
        return
    
    proposal.contacts_to_add.append(ContactProposal(
        contact_type=contact_type,
        contact_value=normalized,
        label=label or "From registry",
        action=ProposalAction.ADD,
        reason="From registry",
    ))


def _propose_address(
    proposal: EnrichmentProposal,
    entity: Dict[str, Any],
    address: Optional[NormalizedAddress],
) -> None:
    """Add address proposal."""
    if not address:
        return
    
    existing = _get_existing_address_by_type(entity, address.address_type)
    
    if not existing:
        # No existing address of this type - propose adding
        proposal.address_proposals.append(AddressProposal(
            address=address,
            action=ProposalAction.ADD,
            reason=f"No {address.address_type} address exists",
        ))
    else:
        # Existing address - propose update only if there are meaningful differences
        addr_proposal = AddressProposal(
            address=address,
            action=ProposalAction.UPDATE,
            existing_address_id=str(existing.get("id")),
            reason=f"Update {address.address_type} address from registry",
        )
        
        changes = addr_proposal.get_changes_summary(existing)
        if changes and changes != ["New address"]:
            proposal.address_proposals.append(addr_proposal)
        else:
            proposal.info_messages.append(
                f"{address.address_type} address matches registry data"
            )


def generate_krs_proposal(
    entity: Dict[str, Any],
    profile: NormalizedKRSProfile,
    all_identifiers: Optional[Dict[str, Dict[str, str]]] = None,
) -> EnrichmentProposal:
    """Generate enrichment proposal from KRS profile.
    
    Args:
        entity: Current entity data from database.
        profile: Normalized KRS profile.
        all_identifiers: Optional map of {type: {value: entity_id}} for collision detection.
        
    Returns:
        EnrichmentProposal with suggested changes.
    """
    entity_id = str(entity.get("id", ""))
    
    proposal = EnrichmentProposal(
        entity_id=entity_id,
        source_system="KRS",
        external_id=profile.krs or "",
    )
    
    # Identifiers
    _propose_identifier(proposal, entity, "KRS", profile.krs, all_identifiers)
    _propose_identifier(proposal, entity, "NIP", profile.nip, all_identifiers)
    _propose_identifier(proposal, entity, "REGON", profile.regon, all_identifiers)
    
    # Type-specific updates (for LEGAL_PERSON)
    if entity.get("entity_type") == "LEGAL_PERSON":
        # Registered name
        current_name = entity.get("registered_name", "")
        if profile.official_name and not current_name:
            proposal.type_specific_updates["registered_name"] = profile.official_name
        elif profile.official_name and current_name != profile.official_name:
            proposal.warnings.append(
                f"Registry name differs: '{profile.official_name}' vs current '{current_name}'"
            )
        
        # Short name
        if profile.short_name and not entity.get("short_name"):
            proposal.type_specific_updates["short_name"] = profile.short_name
        
        # Legal form suffix
        if profile.legal_form and not entity.get("legal_form_suffix"):
            proposal.type_specific_updates["legal_form_suffix"] = profile.legal_form
    
    # Core updates (canonical_label)
    current_label = entity.get("canonical_label", "")
    if profile.official_name and not current_label:
        proposal.core_updates["canonical_label"] = profile.official_name
    
    # Contacts
    _propose_contact(proposal, entity, "EMAIL", profile.email, "KRS")
    _propose_contact(proposal, entity, "WEBSITE", profile.website, "KRS")
    _propose_contact(proposal, entity, "PHONE", profile.phone, "KRS")
    
    # Address
    if profile.seat_address:
        profile.seat_address.address_type = "MAIN"
        _propose_address(proposal, entity, profile.seat_address)
    
    if profile.correspondence_address:
        profile.correspondence_address.address_type = "CORRESPONDENCE"
        _propose_address(proposal, entity, profile.correspondence_address)
    
    return proposal


def generate_ceidg_proposal(
    entity: Dict[str, Any],
    profile: NormalizedCEIDGProfile,
    all_identifiers: Optional[Dict[str, Dict[str, str]]] = None,
) -> EnrichmentProposal:
    """Generate enrichment proposal from CEIDG profile.
    
    Args:
        entity: Current entity data from database.
        profile: Normalized CEIDG profile.
        all_identifiers: Optional map of {type: {value: entity_id}} for collision detection.
        
    Returns:
        EnrichmentProposal with suggested changes.
    """
    entity_id = str(entity.get("id", ""))
    
    proposal = EnrichmentProposal(
        entity_id=entity_id,
        source_system="CEIDG",
        external_id=profile.nip or profile.regon or "",
    )
    
    # Identifiers
    _propose_identifier(proposal, entity, "NIP", profile.nip, all_identifiers)
    _propose_identifier(proposal, entity, "REGON", profile.regon, all_identifiers)
    
    entity_type = entity.get("entity_type")
    
    # Type-specific updates
    if entity_type == "PHYSICAL_PERSON":
        # Person name updates
        if profile.first_name and not entity.get("first_name"):
            proposal.type_specific_updates["first_name"] = profile.first_name
        if profile.last_name and not entity.get("last_name"):
            proposal.type_specific_updates["last_name"] = profile.last_name
        
        # Warn if names differ
        if profile.first_name and entity.get("first_name"):
            if profile.first_name.upper() != entity.get("first_name", "").upper():
                proposal.warnings.append(
                    f"First name differs: '{profile.first_name}' vs '{entity.get('first_name')}'"
                )
        if profile.last_name and entity.get("last_name"):
            if profile.last_name.upper() != entity.get("last_name", "").upper():
                proposal.warnings.append(
                    f"Last name differs: '{profile.last_name}' vs '{entity.get('last_name')}'"
                )
    
    elif entity_type == "LEGAL_PERSON":
        # Business name as registered name
        if profile.business_name and not entity.get("registered_name"):
            proposal.type_specific_updates["registered_name"] = profile.business_name
    
    # Core updates
    current_label = entity.get("canonical_label", "")
    if not current_label:
        # Build label from CEIDG data
        if entity_type == "PHYSICAL_PERSON" and profile.first_name and profile.last_name:
            proposal.core_updates["canonical_label"] = f"{profile.first_name} {profile.last_name}"
        elif profile.business_name:
            proposal.core_updates["canonical_label"] = profile.business_name
    
    # Contacts
    _propose_contact(proposal, entity, "EMAIL", profile.email, "CEIDG")
    _propose_contact(proposal, entity, "WEBSITE", profile.website, "CEIDG")
    _propose_contact(proposal, entity, "PHONE", profile.phone, "CEIDG")
    
    # Addresses
    if profile.main_address:
        profile.main_address.address_type = "MAIN"
        _propose_address(proposal, entity, profile.main_address)
    
    if profile.correspondence_address:
        _propose_address(proposal, entity, profile.correspondence_address)
    
    for biz_addr in profile.business_addresses:
        _propose_address(proposal, entity, biz_addr)
    
    return proposal
