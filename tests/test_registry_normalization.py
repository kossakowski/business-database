"""Tests for registry data normalization."""

import json
import pytest
from pathlib import Path

from lawfirm_cli.registry.krs_client import (
    normalize_krs_response,
    normalize_krs_number,
)
from lawfirm_cli.registry.ceidg_client import (
    normalize_ceidg_response,
    normalize_nip,
    normalize_regon,
)


@pytest.fixture
def krs_sample_data():
    """Load KRS sample data."""
    fixture_path = Path(__file__).parent / "fixtures" / "krs_sample.json"
    with open(fixture_path) as f:
        return json.load(f)


@pytest.fixture
def ceidg_sample_data():
    """Load CEIDG sample data."""
    fixture_path = Path(__file__).parent / "fixtures" / "ceidg_sample.json"
    with open(fixture_path) as f:
        return json.load(f)


class TestKRSNormalization:
    """Tests for KRS response normalization."""
    
    def test_normalize_krs_number_basic(self):
        """Test KRS number normalization with leading zeros."""
        assert normalize_krs_number("12345") == "0000012345"
        assert normalize_krs_number("0000012345") == "0000012345"
        assert normalize_krs_number("123456789") == "0123456789"
    
    def test_normalize_krs_number_with_spaces(self):
        """Test KRS number normalization removes whitespace."""
        assert normalize_krs_number(" 12345 ") == "0000012345"
        assert normalize_krs_number("123 456") == "0000123456"
    
    def test_normalize_krs_number_invalid(self):
        """Test KRS number normalization rejects invalid input."""
        with pytest.raises(ValueError, match="must be numeric"):
            normalize_krs_number("ABC123")
        
        with pytest.raises(ValueError, match="too long"):
            normalize_krs_number("12345678901")
    
    def test_normalize_krs_extracts_identifiers(self, krs_sample_data):
        """Test KRS normalization extracts identifiers correctly."""
        profile = normalize_krs_response(krs_sample_data)
        
        assert profile.krs == "0000012345"
        assert profile.nip == "1234567890"
        assert profile.regon == "123456789"
    
    def test_normalize_krs_extracts_names(self, krs_sample_data):
        """Test KRS normalization extracts company names."""
        profile = normalize_krs_response(krs_sample_data)
        
        assert profile.official_name == "TEST SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ"
        assert profile.short_name == "TEST SP. Z O.O."
        assert profile.legal_form == "SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ"
    
    def test_normalize_krs_extracts_address(self, krs_sample_data):
        """Test KRS normalization extracts address."""
        profile = normalize_krs_response(krs_sample_data)
        
        assert profile.seat_address is not None
        assert profile.seat_address.city == "WARSZAWA"
        assert profile.seat_address.postal_code == "00-001"
        assert profile.seat_address.street == "NOWY ŚWIAT"
        assert profile.seat_address.building_no == "15"
        assert profile.seat_address.unit_no == "3"
        assert profile.seat_address.voivodeship == "MAZOWIECKIE"
    
    def test_normalize_krs_extracts_contacts(self, krs_sample_data):
        """Test KRS normalization extracts contact info."""
        profile = normalize_krs_response(krs_sample_data)
        
        assert profile.email == "kontakt@test-spolka.pl"
        assert profile.website == "https://www.test-spolka.pl"
        assert profile.phone == "+48221234567"
    
    def test_normalize_krs_extracts_pkd(self, krs_sample_data):
        """Test KRS normalization extracts PKD codes."""
        profile = normalize_krs_response(krs_sample_data)
        
        assert profile.pkd_main == "62.01.Z"
        assert len(profile.pkd_codes) == 2
        assert "62.01.Z" in profile.pkd_codes
        assert "62.02.Z" in profile.pkd_codes
    
    def test_normalize_krs_extracts_representatives(self, krs_sample_data):
        """Test KRS normalization extracts representatives."""
        profile = normalize_krs_response(krs_sample_data)
        
        assert len(profile.representatives) == 2
        rep_names = [r["name"] for r in profile.representatives]
        assert "JAN KOWALSKI" in rep_names
        assert "ANNA NOWAK" in rep_names
    
    def test_normalize_krs_stores_raw_payload(self, krs_sample_data):
        """Test KRS normalization stores raw payload."""
        profile = normalize_krs_response(krs_sample_data)
        
        assert profile.raw_payload is not None
        assert profile.raw_payload == krs_sample_data


class TestCEIDGNormalization:
    """Tests for CEIDG response normalization."""
    
    def test_normalize_nip_basic(self):
        """Test NIP normalization."""
        assert normalize_nip("1234567890") == "1234567890"
        assert normalize_nip("123-456-78-90") == "1234567890"
        assert normalize_nip(" 123 456 78 90 ") == "1234567890"
    
    def test_normalize_nip_invalid(self):
        """Test NIP normalization rejects invalid input."""
        with pytest.raises(ValueError, match="must be numeric"):
            normalize_nip("ABC1234567")
        
        with pytest.raises(ValueError, match="must be 10 digits"):
            normalize_nip("123456789")  # 9 digits
        
        with pytest.raises(ValueError, match="must be 10 digits"):
            normalize_nip("12345678901")  # 11 digits
    
    def test_normalize_regon_basic(self):
        """Test REGON normalization."""
        assert normalize_regon("123456789") == "123456789"
        assert normalize_regon("12345678901234") == "12345678901234"
        assert normalize_regon("123-456-789") == "123456789"
    
    def test_normalize_regon_invalid(self):
        """Test REGON normalization rejects invalid input."""
        with pytest.raises(ValueError, match="must be numeric"):
            normalize_regon("ABC123456")
        
        with pytest.raises(ValueError, match="must be 9 or 14 digits"):
            normalize_regon("12345")  # Too short
        
        with pytest.raises(ValueError, match="must be 9 or 14 digits"):
            normalize_regon("1234567890123456")  # Too long
    
    def test_normalize_ceidg_extracts_identifiers(self, ceidg_sample_data):
        """Test CEIDG normalization extracts identifiers."""
        profile = normalize_ceidg_response(ceidg_sample_data)
        
        assert profile.nip == "9876543210"
        assert profile.regon == "987654321"
        assert profile.ceidg_id == "ceidg-unique-id-12345"
    
    def test_normalize_ceidg_extracts_person_data(self, ceidg_sample_data):
        """Test CEIDG normalization extracts person data."""
        profile = normalize_ceidg_response(ceidg_sample_data)
        
        assert profile.first_name == "MARIA"
        assert profile.last_name == "WIŚNIEWSKA"
        assert profile.business_name == "MARIA WIŚNIEWSKA USŁUGI INFORMATYCZNE"
    
    def test_normalize_ceidg_extracts_status(self, ceidg_sample_data):
        """Test CEIDG normalization extracts status."""
        profile = normalize_ceidg_response(ceidg_sample_data)
        
        assert profile.status == "AKTYWNY"
        assert profile.start_date is not None
        assert profile.start_date.year == 2019
        assert profile.start_date.month == 3
    
    def test_normalize_ceidg_extracts_main_address(self, ceidg_sample_data):
        """Test CEIDG normalization extracts main address."""
        profile = normalize_ceidg_response(ceidg_sample_data)
        
        assert profile.main_address is not None
        assert profile.main_address.city == "POZNAŃ"
        assert profile.main_address.postal_code == "60-001"
        assert profile.main_address.street == "ŚWIĘTY MARCIN"
        assert profile.main_address.building_no == "42"
        assert profile.main_address.unit_no == "5"
    
    def test_normalize_ceidg_extracts_correspondence_address(self, ceidg_sample_data):
        """Test CEIDG normalization extracts correspondence address."""
        profile = normalize_ceidg_response(ceidg_sample_data)
        
        assert profile.correspondence_address is not None
        assert profile.correspondence_address.city == "POZNAŃ"
        assert profile.correspondence_address.street == "PÓŁWIEJSKA"
        assert profile.correspondence_address.address_type == "CORRESPONDENCE"
    
    def test_normalize_ceidg_extracts_contacts(self, ceidg_sample_data):
        """Test CEIDG normalization extracts contacts."""
        profile = normalize_ceidg_response(ceidg_sample_data)
        
        assert profile.email == "maria@uslugi-it.pl"
        assert profile.website == "https://www.uslugi-it.pl"
        assert profile.phone == "+48601234567"
    
    def test_normalize_ceidg_extracts_pkd(self, ceidg_sample_data):
        """Test CEIDG normalization extracts PKD codes."""
        profile = normalize_ceidg_response(ceidg_sample_data)
        
        assert profile.pkd_main == "62.01.Z"
        assert len(profile.pkd_codes) == 2
    
    def test_normalize_ceidg_extracts_business_addresses(self, ceidg_sample_data):
        """Test CEIDG normalization extracts additional business addresses."""
        profile = normalize_ceidg_response(ceidg_sample_data)
        
        assert len(profile.business_addresses) == 1
        biz_addr = profile.business_addresses[0]
        assert biz_addr.city == "WROCŁAW"
        assert biz_addr.address_type == "BUSINESS"
    
    def test_normalize_ceidg_stores_raw_payload(self, ceidg_sample_data):
        """Test CEIDG normalization stores raw payload."""
        profile = normalize_ceidg_response(ceidg_sample_data)
        
        assert profile.raw_payload is not None
        assert profile.raw_payload == ceidg_sample_data
