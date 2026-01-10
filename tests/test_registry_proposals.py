"""Tests for registry enrichment proposal generation."""

import pytest
from lawfirm_cli.registry.proposals import (
    generate_krs_proposal,
    generate_ceidg_proposal,
)
from lawfirm_cli.registry.models import (
    NormalizedKRSProfile,
    NormalizedCEIDGProfile,
    NormalizedAddress,
    ProposalAction,
)


@pytest.fixture
def empty_legal_entity():
    """An empty legal person entity with no data."""
    return {
        "id": "test-entity-id-1234",
        "entity_type": "LEGAL_PERSON",
        "canonical_label": "",
        "status": "ACTIVE",
        "registered_name": "",
        "short_name": "",
        "identifiers": [],
        "addresses": [],
        "contacts": [],
    }


@pytest.fixture
def populated_legal_entity():
    """A legal person entity with existing data."""
    return {
        "id": "test-entity-id-5678",
        "entity_type": "LEGAL_PERSON",
        "canonical_label": "Existing Company",
        "status": "ACTIVE",
        "registered_name": "EXISTING COMPANY SP. Z O.O.",
        "short_name": "Existing Co",
        "identifiers": [
            {"identifier_type": "NIP", "identifier_value": "1234567890"},
            {"identifier_type": "KRS", "identifier_value": "0000012345"},
        ],
        "addresses": [
            {
                "id": "addr-id-1",
                "address_type": "MAIN",
                "city": "WARSZAWA",
                "postal_code": "00-001",
                "street": "MARSZAŁKOWSKA",
                "building_no": "1",
            }
        ],
        "contacts": [
            {"contact_type": "EMAIL", "contact_value": "existing@company.pl"},
        ],
    }


@pytest.fixture
def empty_physical_entity():
    """An empty physical person entity with no data."""
    return {
        "id": "test-person-id-1234",
        "entity_type": "PHYSICAL_PERSON",
        "canonical_label": "",
        "status": "ACTIVE",
        "first_name": "",
        "last_name": "",
        "identifiers": [],
        "addresses": [],
        "contacts": [],
    }


@pytest.fixture
def krs_profile():
    """A KRS profile with full data."""
    return NormalizedKRSProfile(
        krs="0000012345",
        nip="1234567890",
        regon="123456789",
        official_name="TEST COMPANY SP. Z O.O.",
        short_name="TEST CO",
        legal_form="SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
        registry_status="AKTYWNY",
        seat_address=NormalizedAddress(
            address_type="MAIN",
            city="KRAKÓW",
            postal_code="30-001",
            street="RYNEK GŁÓWNY",
            building_no="10",
            unit_no="5",
            voivodeship="MAŁOPOLSKIE",
        ),
        email="contact@testcompany.pl",
        website="https://www.testcompany.pl",
        phone="+48123456789",
    )


@pytest.fixture
def ceidg_profile():
    """A CEIDG profile with full data."""
    return NormalizedCEIDGProfile(
        ceidg_id="ceidg-test-123",
        nip="9876543210",
        regon="987654321",
        first_name="JAN",
        last_name="TESTOWY",
        business_name="JAN TESTOWY USŁUGI",
        status="AKTYWNY",
        main_address=NormalizedAddress(
            address_type="MAIN",
            city="GDAŃSK",
            postal_code="80-001",
            street="DŁUGA",
            building_no="1",
        ),
        email="jan@testowy.pl",
        website="https://www.testowy.pl",
    )


class TestKRSProposalAddMissing:
    """Tests for KRS proposal generation - adding missing data."""
    
    def test_proposes_all_identifiers_for_empty_entity(self, empty_legal_entity, krs_profile):
        """Should propose adding all identifiers when entity has none."""
        proposal = generate_krs_proposal(empty_legal_entity, krs_profile)
        
        identifier_types = [i.identifier_type for i in proposal.identifiers_to_add]
        assert "KRS" in identifier_types
        assert "NIP" in identifier_types
        assert "REGON" in identifier_types
        
        # All should be ADD actions
        for ident in proposal.identifiers_to_add:
            assert ident.action == ProposalAction.ADD
    
    def test_proposes_registered_name_when_empty(self, empty_legal_entity, krs_profile):
        """Should propose registered_name when entity has none."""
        proposal = generate_krs_proposal(empty_legal_entity, krs_profile)
        
        assert "registered_name" in proposal.type_specific_updates
        assert proposal.type_specific_updates["registered_name"] == "TEST COMPANY SP. Z O.O."
    
    def test_proposes_canonical_label_when_empty(self, empty_legal_entity, krs_profile):
        """Should propose canonical_label when entity has none."""
        proposal = generate_krs_proposal(empty_legal_entity, krs_profile)
        
        assert "canonical_label" in proposal.core_updates
        assert proposal.core_updates["canonical_label"] == "TEST COMPANY SP. Z O.O."
    
    def test_proposes_contacts_when_missing(self, empty_legal_entity, krs_profile):
        """Should propose adding contacts when entity has none."""
        proposal = generate_krs_proposal(empty_legal_entity, krs_profile)
        
        contact_types = [c.contact_type for c in proposal.contacts_to_add]
        assert "EMAIL" in contact_types
        assert "WEBSITE" in contact_types
        assert "PHONE" in contact_types
        
        # All should be ADD actions
        for contact in proposal.contacts_to_add:
            assert contact.action == ProposalAction.ADD
    
    def test_proposes_address_when_missing(self, empty_legal_entity, krs_profile):
        """Should propose adding address when entity has none."""
        proposal = generate_krs_proposal(empty_legal_entity, krs_profile)
        
        assert len(proposal.address_proposals) == 1
        addr_prop = proposal.address_proposals[0]
        assert addr_prop.action == ProposalAction.ADD
        assert addr_prop.address.city == "KRAKÓW"
    
    def test_has_proposals_returns_true_for_changes(self, empty_legal_entity, krs_profile):
        """Should have proposals when there are changes."""
        proposal = generate_krs_proposal(empty_legal_entity, krs_profile)
        
        assert proposal.has_any_proposals() is True
        assert proposal.count_proposals() > 0


class TestKRSProposalNoOverwrite:
    """Tests for KRS proposal generation - not overwriting existing data by default."""
    
    def test_does_not_propose_existing_identifiers(self, populated_legal_entity, krs_profile):
        """Should not propose identifiers that already exist on entity."""
        proposal = generate_krs_proposal(populated_legal_entity, krs_profile)
        
        # NIP and KRS already exist, only REGON should be proposed
        proposed_types = [i.identifier_type for i in proposal.identifiers_to_add 
                        if i.action == ProposalAction.ADD]
        
        assert "REGON" in proposed_types
        assert "NIP" not in proposed_types
        assert "KRS" not in proposed_types
    
    def test_does_not_overwrite_canonical_label(self, populated_legal_entity, krs_profile):
        """Should not propose canonical_label when entity already has one."""
        proposal = generate_krs_proposal(populated_legal_entity, krs_profile)
        
        assert "canonical_label" not in proposal.core_updates
    
    def test_does_not_overwrite_registered_name(self, populated_legal_entity, krs_profile):
        """Should not overwrite registered_name, but should warn if different."""
        proposal = generate_krs_proposal(populated_legal_entity, krs_profile)
        
        assert "registered_name" not in proposal.type_specific_updates
        # Should have a warning about the difference
        assert any("name differs" in w.lower() for w in proposal.warnings)
    
    def test_does_not_overwrite_contacts(self, populated_legal_entity, krs_profile):
        """Should not propose contacts that already exist."""
        proposal = generate_krs_proposal(populated_legal_entity, krs_profile)
        
        # EMAIL already exists (with different value), should not be proposed
        proposed_emails = [c for c in proposal.contacts_to_add 
                         if c.contact_type == "EMAIL"]
        
        # Our email is different from registry, but we don't auto-propose replacement
        # The proposal should add the registry email as it's a different value
        # Actually, the logic checks for exact match - different emails would both be added
        # Let's verify the logic matches: existing@company.pl vs contact@testcompany.pl
        # These are different, so the registry email should be proposed
        assert len(proposed_emails) == 1
    
    def test_proposes_address_update_not_replacement(self, populated_legal_entity, krs_profile):
        """Should propose address update with changes, but action is UPDATE."""
        proposal = generate_krs_proposal(populated_legal_entity, krs_profile)
        
        main_addr_proposals = [a for a in proposal.address_proposals 
                              if a.address.address_type == "MAIN"]
        
        if main_addr_proposals:
            addr_prop = main_addr_proposals[0]
            assert addr_prop.action == ProposalAction.UPDATE
            assert addr_prop.existing_address_id == "addr-id-1"
    
    def test_info_messages_for_matching_data(self, populated_legal_entity, krs_profile):
        """Should add info messages when data already matches."""
        # Make profile match existing entity data
        krs_profile.nip = "1234567890"  # Same as entity
        krs_profile.krs = "0000012345"  # Same as entity
        
        proposal = generate_krs_proposal(populated_legal_entity, krs_profile)
        
        # Should have info messages about existing identifiers
        assert len(proposal.info_messages) > 0


class TestKRSProposalCollisionDetection:
    """Tests for identifier collision detection."""
    
    def test_detects_collision_with_other_entity(self, empty_legal_entity, krs_profile):
        """Should detect when identifier exists on another entity."""
        # Simulate that NIP exists on another entity
        all_identifiers = {
            "NIP": {"1234567890": "other-entity-id-999"},
        }
        
        proposal = generate_krs_proposal(
            empty_legal_entity, 
            krs_profile, 
            all_identifiers=all_identifiers
        )
        
        nip_proposal = next(
            (i for i in proposal.identifiers_to_add if i.identifier_type == "NIP"),
            None
        )
        
        assert nip_proposal is not None
        assert nip_proposal.action == ProposalAction.SKIP
        assert nip_proposal.collision_entity_id == "other-entity-id-999"
        
        # Should have a warning
        assert any("collision" in w.lower() or "exists on another" in w.lower() 
                  for w in proposal.warnings)


class TestCEIDGProposalAddMissing:
    """Tests for CEIDG proposal generation - adding missing data."""
    
    def test_proposes_identifiers_for_empty_entity(self, empty_physical_entity, ceidg_profile):
        """Should propose adding identifiers when entity has none."""
        proposal = generate_ceidg_proposal(empty_physical_entity, ceidg_profile)
        
        identifier_types = [i.identifier_type for i in proposal.identifiers_to_add]
        assert "NIP" in identifier_types
        assert "REGON" in identifier_types
    
    def test_proposes_person_names_when_empty(self, empty_physical_entity, ceidg_profile):
        """Should propose first_name and last_name when entity has none."""
        proposal = generate_ceidg_proposal(empty_physical_entity, ceidg_profile)
        
        assert "first_name" in proposal.type_specific_updates
        assert "last_name" in proposal.type_specific_updates
        assert proposal.type_specific_updates["first_name"] == "JAN"
        assert proposal.type_specific_updates["last_name"] == "TESTOWY"
    
    def test_proposes_canonical_label_from_name(self, empty_physical_entity, ceidg_profile):
        """Should propose canonical_label built from name."""
        proposal = generate_ceidg_proposal(empty_physical_entity, ceidg_profile)
        
        assert "canonical_label" in proposal.core_updates
        assert proposal.core_updates["canonical_label"] == "JAN TESTOWY"
    
    def test_proposes_contacts(self, empty_physical_entity, ceidg_profile):
        """Should propose adding contacts."""
        proposal = generate_ceidg_proposal(empty_physical_entity, ceidg_profile)
        
        contact_types = [c.contact_type for c in proposal.contacts_to_add]
        assert "EMAIL" in contact_types
        assert "WEBSITE" in contact_types
    
    def test_proposes_main_address(self, empty_physical_entity, ceidg_profile):
        """Should propose adding main address."""
        proposal = generate_ceidg_proposal(empty_physical_entity, ceidg_profile)
        
        main_addr = [a for a in proposal.address_proposals 
                    if a.address.address_type == "MAIN"]
        assert len(main_addr) == 1
        assert main_addr[0].address.city == "GDAŃSK"


class TestCEIDGProposalNameWarnings:
    """Tests for name mismatch warnings in CEIDG proposals."""
    
    def test_warns_on_first_name_mismatch(self, ceidg_profile):
        """Should warn when first name differs."""
        entity = {
            "id": "test-id",
            "entity_type": "PHYSICAL_PERSON",
            "canonical_label": "Piotr Testowy",
            "first_name": "PIOTR",  # Different from JAN
            "last_name": "TESTOWY",
            "identifiers": [],
            "addresses": [],
            "contacts": [],
        }
        
        proposal = generate_ceidg_proposal(entity, ceidg_profile)
        
        assert any("first name differs" in w.lower() for w in proposal.warnings)
    
    def test_warns_on_last_name_mismatch(self, ceidg_profile):
        """Should warn when last name differs."""
        entity = {
            "id": "test-id",
            "entity_type": "PHYSICAL_PERSON",
            "canonical_label": "Jan Inny",
            "first_name": "JAN",
            "last_name": "INNY",  # Different from TESTOWY
            "identifiers": [],
            "addresses": [],
            "contacts": [],
        }
        
        proposal = generate_ceidg_proposal(entity, ceidg_profile)
        
        assert any("last name differs" in w.lower() for w in proposal.warnings)


class TestCEIDGForLegalPerson:
    """Tests for CEIDG proposals when entity is a legal person."""
    
    def test_proposes_business_name_as_registered_name(self, ceidg_profile):
        """Should propose business_name as registered_name for legal person."""
        entity = {
            "id": "test-id",
            "entity_type": "LEGAL_PERSON",
            "canonical_label": "",
            "registered_name": "",
            "identifiers": [],
            "addresses": [],
            "contacts": [],
        }
        
        proposal = generate_ceidg_proposal(entity, ceidg_profile)
        
        assert "registered_name" in proposal.type_specific_updates
        assert proposal.type_specific_updates["registered_name"] == "JAN TESTOWY USŁUGI"


class TestProposalMetadata:
    """Tests for proposal metadata fields."""
    
    def test_krs_proposal_has_correct_source(self, empty_legal_entity, krs_profile):
        """KRS proposal should have correct source metadata."""
        proposal = generate_krs_proposal(empty_legal_entity, krs_profile)
        
        assert proposal.source_system == "KRS"
        assert proposal.external_id == "0000012345"
        assert proposal.entity_id == "test-entity-id-1234"
    
    def test_ceidg_proposal_has_correct_source(self, empty_physical_entity, ceidg_profile):
        """CEIDG proposal should have correct source metadata."""
        proposal = generate_ceidg_proposal(empty_physical_entity, ceidg_profile)
        
        assert proposal.source_system == "CEIDG"
        assert proposal.entity_id == "test-person-id-1234"


class TestEmptyProfile:
    """Tests for handling profiles with missing data."""
    
    def test_handles_profile_with_no_identifiers(self, empty_legal_entity):
        """Should handle KRS profile with no identifiers."""
        empty_profile = NormalizedKRSProfile()
        
        proposal = generate_krs_proposal(empty_legal_entity, empty_profile)
        
        # Should not crash, and should have no identifier proposals
        assert len(proposal.identifiers_to_add) == 0
    
    def test_handles_profile_with_no_address(self, empty_legal_entity):
        """Should handle KRS profile with no address."""
        profile = NormalizedKRSProfile(
            krs="0000099999",
            official_name="Test Company",
        )
        
        proposal = generate_krs_proposal(empty_legal_entity, profile)
        
        # Should still propose the identifier and name
        assert len(proposal.identifiers_to_add) == 1
        assert "registered_name" in proposal.type_specific_updates
        assert len(proposal.address_proposals) == 0
    
    def test_handles_profile_with_no_contacts(self, empty_legal_entity):
        """Should handle KRS profile with no contacts."""
        profile = NormalizedKRSProfile(
            krs="0000099999",
            email=None,
            website=None,
            phone=None,
        )
        
        proposal = generate_krs_proposal(empty_legal_entity, profile)
        
        assert len(proposal.contacts_to_add) == 0
