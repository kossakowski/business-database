"""Comprehensive tests for CEIDG integration.

Tests cover:
- API v3 response parsing and normalization
- Field mapping (v3 field names: miasto, kod, dataRozpoczecia, etc.)
- HTTP client with mocked responses (success, errors, edge cases)
- CEIDG proposal generation for entity enrichment
- CLI enrichment workflow with mocked CEIDG data
- Token/auth handling
"""

import json
import os
import pytest
import responses
from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock

from lawfirm_cli.registry.ceidg_client import (
    DEFAULT_CEIDG_API_BASE_URL,
    CEIDGClientError,
    CEIDGConnectionError,
    CEIDGNotConfiguredError,
    CEIDGNotFoundError,
    CEIDGParseError,
    fetch_and_normalize_ceidg_by_nip,
    fetch_and_normalize_ceidg_by_regon,
    fetch_ceidg_by_nip,
    fetch_ceidg_by_regon,
    get_ceidg_config,
    is_ceidg_configured,
    normalize_ceidg_response,
    normalize_nip,
    normalize_regon,
)
from lawfirm_cli.registry.models import (
    NormalizedCEIDGProfile,
    NormalizedAddress,
    ProposalAction,
)
from lawfirm_cli.registry.proposals import generate_ceidg_proposal


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def ceidg_v3_sample():
    """Full CEIDG v3 API response (single firm record)."""
    with open(FIXTURES_DIR / "ceidg_v3_sample.json") as f:
        return json.load(f)


@pytest.fixture
def ceidg_v3_minimal():
    """Minimal CEIDG v3 response — empty address, empty REGON."""
    with open(FIXTURES_DIR / "ceidg_v3_minimal.json") as f:
        return json.load(f)


@pytest.fixture
def ceidg_v3_suspended():
    """CEIDG v3 response for a suspended business."""
    with open(FIXTURES_DIR / "ceidg_v3_suspended.json") as f:
        return json.load(f)


@pytest.fixture
def ceidg_v3_api_wrapper(ceidg_v3_sample):
    """Full API wrapper response as returned by /api/ceidg/v3/firmy."""
    return {
        "firmy": [ceidg_v3_sample],
        "count": 1,
        "links": {
            "self": "https://dane.biznes.gov.pl/api/ceidg/v3/firmy?nip=8991234567",
        },
    }


@pytest.fixture
def empty_physical_entity():
    """Physical person entity with no data."""
    return {
        "id": "person-empty-id",
        "entity_type": "PHYSICAL_PERSON",
        "canonical_label": "",
        "first_name": "",
        "last_name": "",
        "identifiers": [],
        "addresses": [],
        "contacts": [],
    }


@pytest.fixture
def populated_physical_entity():
    """Physical person entity with existing data."""
    return {
        "id": "person-pop-id",
        "entity_type": "PHYSICAL_PERSON",
        "canonical_label": "Anna Kowalska",
        "first_name": "Anna",
        "last_name": "Kowalska",
        "identifiers": [
            {"identifier_type": "NIP", "identifier_value": "8991234567"},
        ],
        "addresses": [
            {
                "id": "addr-existing",
                "address_type": "MAIN",
                "city": "Warszawa",
                "postal_code": "00-001",
                "street": "Marszałkowska",
                "building_no": "1",
            },
        ],
        "contacts": [
            {"contact_type": "EMAIL", "contact_value": "old@email.pl"},
        ],
    }


@pytest.fixture
def _set_ceidg_token():
    """Temporarily set CEIDG_API_TOKEN for tests that need it."""
    old = os.environ.get("CEIDG_API_TOKEN")
    os.environ["CEIDG_API_TOKEN"] = "test-token-for-tests"
    yield
    if old is not None:
        os.environ["CEIDG_API_TOKEN"] = old
    else:
        os.environ.pop("CEIDG_API_TOKEN", None)


@pytest.fixture
def _unset_ceidg_token():
    """Temporarily remove CEIDG_API_TOKEN."""
    old = os.environ.pop("CEIDG_API_TOKEN", None)
    yield
    if old is not None:
        os.environ["CEIDG_API_TOKEN"] = old


# ---------------------------------------------------------------------------
# 1. V3 Response Normalization
# ---------------------------------------------------------------------------

class TestCEIDGV3Normalization:
    """Test normalization of CEIDG API v3 response format."""

    def test_extracts_ceidg_id(self, ceidg_v3_sample):
        profile = normalize_ceidg_response(ceidg_v3_sample)
        assert profile.ceidg_id == "A1B2C3D4-E5F6-7890-ABCD-EF1234567890"

    def test_extracts_nip_from_owner(self, ceidg_v3_sample):
        profile = normalize_ceidg_response(ceidg_v3_sample)
        assert profile.nip == "8991234567"

    def test_extracts_regon_from_owner(self, ceidg_v3_sample):
        profile = normalize_ceidg_response(ceidg_v3_sample)
        assert profile.regon == "380123456"

    def test_extracts_owner_names(self, ceidg_v3_sample):
        profile = normalize_ceidg_response(ceidg_v3_sample)
        assert profile.first_name == "Anna"
        assert profile.last_name == "Kowalska"

    def test_extracts_business_name(self, ceidg_v3_sample):
        profile = normalize_ceidg_response(ceidg_v3_sample)
        assert profile.business_name == "ANNA KOWALSKA PROJEKTOWANIE WNĘTRZ"

    def test_extracts_status(self, ceidg_v3_sample):
        profile = normalize_ceidg_response(ceidg_v3_sample)
        assert profile.status == "AKTYWNY"

    def test_extracts_start_date_v3_field(self, ceidg_v3_sample):
        """v3 uses 'dataRozpoczecia' not 'dataRozpoczeciaDzialalnosci'."""
        profile = normalize_ceidg_response(ceidg_v3_sample)
        assert profile.start_date == date(2021, 6, 15)

    def test_extracts_city_from_miasto(self, ceidg_v3_sample):
        """v3 uses 'miasto' not 'miejscowosc' for city."""
        profile = normalize_ceidg_response(ceidg_v3_sample)
        assert profile.main_address is not None
        assert profile.main_address.city == "Wrocław"

    def test_extracts_postal_code_from_kod(self, ceidg_v3_sample):
        """v3 uses 'kod' not 'kodPocztowy' for postal code."""
        profile = normalize_ceidg_response(ceidg_v3_sample)
        assert profile.main_address.postal_code == "50-123"

    def test_extracts_full_address(self, ceidg_v3_sample):
        profile = normalize_ceidg_response(ceidg_v3_sample)
        addr = profile.main_address
        assert addr.street == "ul. Kwiatowa"
        assert addr.building_no == "15"
        assert addr.unit_no == "3"
        assert addr.voivodeship == "DOLNOŚLĄSKIE"
        assert addr.country == "PL"

    def test_extracts_correspondence_address(self, ceidg_v3_sample):
        profile = normalize_ceidg_response(ceidg_v3_sample)
        corr = profile.correspondence_address
        assert corr is not None
        assert corr.address_type == "CORRESPONDENCE"
        assert corr.city == "Wrocław"
        assert corr.street == "ul. Pocztowa"
        assert corr.postal_code == "50-200"

    def test_extracts_additional_business_addresses(self, ceidg_v3_sample):
        profile = normalize_ceidg_response(ceidg_v3_sample)
        assert len(profile.business_addresses) == 1
        biz = profile.business_addresses[0]
        assert biz.address_type == "BUSINESS"
        assert biz.city == "Oława"
        assert biz.postal_code == "55-200"

    def test_extracts_contacts(self, ceidg_v3_sample):
        profile = normalize_ceidg_response(ceidg_v3_sample)
        assert profile.email == "anna@projektowanie.pl"
        assert profile.website == "https://www.projektowanie-kowalska.pl"
        assert profile.phone == "+48501234567"

    def test_extracts_pkd_codes(self, ceidg_v3_sample):
        profile = normalize_ceidg_response(ceidg_v3_sample)
        assert profile.pkd_main == "74.10.Z"
        assert len(profile.pkd_codes) == 2
        assert "74.10.Z" in profile.pkd_codes
        assert "74.20.Z" in profile.pkd_codes

    def test_stores_raw_payload(self, ceidg_v3_sample):
        profile = normalize_ceidg_response(ceidg_v3_sample)
        assert profile.raw_payload == ceidg_v3_sample


class TestCEIDGV3MinimalResponse:
    """Test normalization of minimal v3 response (empty fields)."""

    def test_handles_empty_address(self, ceidg_v3_minimal):
        profile = normalize_ceidg_response(ceidg_v3_minimal)
        # adresDzialalnosci is {} — should yield None or empty address
        assert profile.main_address is None or profile.main_address.city is None

    def test_handles_empty_regon_string(self, ceidg_v3_minimal):
        """v3 returns empty string for REGON instead of null."""
        profile = normalize_ceidg_response(ceidg_v3_minimal)
        assert profile.regon is None

    def test_handles_missing_contacts(self, ceidg_v3_minimal):
        profile = normalize_ceidg_response(ceidg_v3_minimal)
        assert profile.email is None
        assert profile.website is None
        assert profile.phone is None

    def test_handles_missing_pkd(self, ceidg_v3_minimal):
        profile = normalize_ceidg_response(ceidg_v3_minimal)
        assert profile.pkd_main is None
        assert profile.pkd_codes == []

    def test_extracts_owner_from_minimal(self, ceidg_v3_minimal):
        profile = normalize_ceidg_response(ceidg_v3_minimal)
        assert profile.first_name == "Jan"
        assert profile.last_name == "Nowak"
        assert profile.nip == "1234563218"

    def test_handles_no_correspondence_address(self, ceidg_v3_minimal):
        profile = normalize_ceidg_response(ceidg_v3_minimal)
        assert profile.correspondence_address is None

    def test_handles_no_additional_addresses(self, ceidg_v3_minimal):
        profile = normalize_ceidg_response(ceidg_v3_minimal)
        assert profile.business_addresses == []


class TestCEIDGV3SuspendedBusiness:
    """Test normalization of a suspended business entry."""

    def test_suspended_status(self, ceidg_v3_suspended):
        profile = normalize_ceidg_response(ceidg_v3_suspended)
        assert profile.status == "ZAWIESZONY"

    def test_suspension_date(self, ceidg_v3_suspended):
        profile = normalize_ceidg_response(ceidg_v3_suspended)
        assert profile.suspension_date == date(2025, 6, 1)

    def test_start_date(self, ceidg_v3_suspended):
        profile = normalize_ceidg_response(ceidg_v3_suspended)
        assert profile.start_date == date(2015, 1, 10)


class TestCEIDGV3BackwardCompatibility:
    """Ensure v2-style field names still work (fallback)."""

    def test_falls_back_to_miejscowosc(self):
        data = {
            "id": "compat-1",
            "wlasciciel": {"imie": "Test", "nazwisko": "User", "nip": "1111111111"},
            "nazwa": "Test",
            "adresDzialalnosci": {
                "miejscowosc": "Gdańsk",
                "kodPocztowy": "80-001",
            },
            "status": "AKTYWNY",
            "dataRozpoczeciaDzialalnosci": "2020-01-01",
        }
        profile = normalize_ceidg_response(data)
        assert profile.main_address.city == "Gdańsk"
        assert profile.main_address.postal_code == "80-001"
        assert profile.start_date == date(2020, 1, 1)

    def test_v3_field_takes_precedence_over_v2(self):
        """When both v3 and v2 field names present, v3 wins."""
        data = {
            "id": "compat-2",
            "wlasciciel": {"imie": "Test", "nazwisko": "User", "nip": "1111111111"},
            "nazwa": "Test",
            "adresDzialalnosci": {
                "miasto": "Kraków",
                "miejscowosc": "OldCity",
                "kod": "30-100",
                "kodPocztowy": "30-999",
            },
            "status": "AKTYWNY",
            "dataRozpoczecia": "2023-05-01",
            "dataRozpoczeciaDzialalnosci": "2000-01-01",
        }
        profile = normalize_ceidg_response(data)
        assert profile.main_address.city == "Kraków"
        assert profile.main_address.postal_code == "30-100"
        assert profile.start_date == date(2023, 5, 1)


# ---------------------------------------------------------------------------
# 2. HTTP Client — Mocked Requests
# ---------------------------------------------------------------------------

class TestCEIDGFetchByNIP:
    """Test fetch_ceidg_by_nip with mocked HTTP."""

    @responses.activate
    def test_success_unwraps_firmy(self, _set_ceidg_token, ceidg_v3_api_wrapper):
        responses.add(
            responses.GET,
            f"{DEFAULT_CEIDG_API_BASE_URL}/firmy",
            json=ceidg_v3_api_wrapper,
            status=200,
        )
        data, raw = fetch_ceidg_by_nip("8991234567")
        assert data["id"] == "A1B2C3D4-E5F6-7890-ABCD-EF1234567890"
        assert isinstance(raw, str)

    @responses.activate
    def test_204_no_content_raises_not_found(self, _set_ceidg_token):
        """CEIDG v3 returns 204 when NIP is valid but not in CEIDG."""
        responses.add(
            responses.GET,
            f"{DEFAULT_CEIDG_API_BASE_URL}/firmy",
            status=204,
        )
        with pytest.raises(CEIDGClientError):
            fetch_ceidg_by_nip("1234563218")

    @responses.activate
    def test_404_raises_not_found(self, _set_ceidg_token):
        responses.add(
            responses.GET,
            f"{DEFAULT_CEIDG_API_BASE_URL}/firmy",
            status=404,
        )
        with pytest.raises(CEIDGNotFoundError):
            fetch_ceidg_by_nip("1234563218")

    @responses.activate
    def test_401_raises_auth_error(self, _set_ceidg_token):
        responses.add(
            responses.GET,
            f"{DEFAULT_CEIDG_API_BASE_URL}/firmy",
            status=401,
        )
        with pytest.raises(CEIDGClientError, match="authentication"):
            fetch_ceidg_by_nip("1234563218")

    @responses.activate
    def test_timeout_raises_connection_error(self, _set_ceidg_token):
        import requests as req
        responses.add(
            responses.GET,
            f"{DEFAULT_CEIDG_API_BASE_URL}/firmy",
            body=req.exceptions.Timeout("timed out"),
        )
        with pytest.raises(CEIDGConnectionError, match="timed out"):
            fetch_ceidg_by_nip("1234563218")

    @responses.activate
    def test_connection_error(self, _set_ceidg_token):
        import requests as req
        responses.add(
            responses.GET,
            f"{DEFAULT_CEIDG_API_BASE_URL}/firmy",
            body=req.exceptions.ConnectionError("refused"),
        )
        with pytest.raises(CEIDGConnectionError):
            fetch_ceidg_by_nip("1234563218")

    @responses.activate
    def test_malformed_json_raises_error(self, _set_ceidg_token):
        """Malformed JSON raises CEIDGConnectionError (JSONDecodeError is a RequestException subclass)."""
        responses.add(
            responses.GET,
            f"{DEFAULT_CEIDG_API_BASE_URL}/firmy",
            body="not json",
            status=200,
            content_type="text/plain",
        )
        with pytest.raises((CEIDGParseError, CEIDGConnectionError)):
            fetch_ceidg_by_nip("1234563218")

    @responses.activate
    def test_empty_firmy_raises_not_found(self, _set_ceidg_token):
        responses.add(
            responses.GET,
            f"{DEFAULT_CEIDG_API_BASE_URL}/firmy",
            json={"firmy": [], "count": 0},
            status=200,
        )
        with pytest.raises(CEIDGNotFoundError):
            fetch_ceidg_by_nip("1234563218")

    @responses.activate
    def test_sends_bearer_token(self, _set_ceidg_token, ceidg_v3_api_wrapper):
        responses.add(
            responses.GET,
            f"{DEFAULT_CEIDG_API_BASE_URL}/firmy",
            json=ceidg_v3_api_wrapper,
            status=200,
        )
        fetch_ceidg_by_nip("8991234567")
        assert responses.calls[0].request.headers["Authorization"] == "Bearer test-token-for-tests"

    @responses.activate
    def test_sends_nip_as_query_param(self, _set_ceidg_token, ceidg_v3_api_wrapper):
        responses.add(
            responses.GET,
            f"{DEFAULT_CEIDG_API_BASE_URL}/firmy",
            json=ceidg_v3_api_wrapper,
            status=200,
        )
        fetch_ceidg_by_nip("8991234567")
        assert "nip=8991234567" in responses.calls[0].request.url


class TestCEIDGFetchByREGON:
    """Test fetch_ceidg_by_regon with mocked HTTP."""

    @responses.activate
    def test_success(self, _set_ceidg_token, ceidg_v3_sample):
        responses.add(
            responses.GET,
            f"{DEFAULT_CEIDG_API_BASE_URL}/firmy",
            json={"firmy": [ceidg_v3_sample]},
            status=200,
        )
        data, raw = fetch_ceidg_by_regon("380123456")
        assert data["id"] == "A1B2C3D4-E5F6-7890-ABCD-EF1234567890"

    @responses.activate
    def test_sends_regon_as_query_param(self, _set_ceidg_token, ceidg_v3_sample):
        responses.add(
            responses.GET,
            f"{DEFAULT_CEIDG_API_BASE_URL}/firmy",
            json={"firmy": [ceidg_v3_sample]},
            status=200,
        )
        fetch_ceidg_by_regon("380123456")
        assert "regon=380123456" in responses.calls[0].request.url


class TestCEIDGFetchAndNormalize:
    """Test the combined fetch + normalize pipeline."""

    @responses.activate
    def test_by_nip_returns_profile_and_snapshot(self, _set_ceidg_token, ceidg_v3_sample):
        responses.add(
            responses.GET,
            f"{DEFAULT_CEIDG_API_BASE_URL}/firmy",
            json={"firmy": [ceidg_v3_sample]},
            status=200,
        )
        profile, snapshot = fetch_and_normalize_ceidg_by_nip("8991234567")

        assert isinstance(profile, NormalizedCEIDGProfile)
        assert profile.nip == "8991234567"
        assert profile.first_name == "Anna"
        assert profile.main_address.city == "Wrocław"

        assert snapshot.source_system == "CEIDG"
        assert snapshot.external_id == "NIP:8991234567"
        assert snapshot.payload_hash  # Non-empty hash

    @responses.activate
    def test_by_nip_with_entity_id(self, _set_ceidg_token, ceidg_v3_sample):
        responses.add(
            responses.GET,
            f"{DEFAULT_CEIDG_API_BASE_URL}/firmy",
            json={"firmy": [ceidg_v3_sample]},
            status=200,
        )
        profile, snapshot = fetch_and_normalize_ceidg_by_nip(
            "8991234567", entity_id="my-entity-123"
        )
        assert snapshot.entity_id == "my-entity-123"

    @responses.activate
    def test_by_regon_returns_profile_and_snapshot(self, _set_ceidg_token, ceidg_v3_sample):
        responses.add(
            responses.GET,
            f"{DEFAULT_CEIDG_API_BASE_URL}/firmy",
            json={"firmy": [ceidg_v3_sample]},
            status=200,
        )
        profile, snapshot = fetch_and_normalize_ceidg_by_regon("380123456")

        assert profile.regon == "380123456"
        assert snapshot.source_system == "CEIDG"
        assert snapshot.external_id == "REGON:380123456"


# ---------------------------------------------------------------------------
# 3. Input Validation
# ---------------------------------------------------------------------------

class TestNIPValidation:
    """Test NIP normalization and validation."""

    def test_valid_10_digits(self):
        assert normalize_nip("1234567890") == "1234567890"

    def test_strips_dashes(self):
        assert normalize_nip("123-456-78-90") == "1234567890"

    def test_strips_spaces(self):
        assert normalize_nip(" 123 456 78 90 ") == "1234567890"

    def test_rejects_non_numeric(self):
        with pytest.raises(ValueError, match="must be numeric"):
            normalize_nip("12345ABCDE")

    def test_rejects_too_short(self):
        with pytest.raises(ValueError, match="must be 10 digits"):
            normalize_nip("123456789")

    def test_rejects_too_long(self):
        with pytest.raises(ValueError, match="must be 10 digits"):
            normalize_nip("12345678901")


class TestREGONValidation:
    """Test REGON normalization and validation."""

    def test_valid_9_digits(self):
        assert normalize_regon("123456789") == "123456789"

    def test_valid_14_digits(self):
        assert normalize_regon("12345678901234") == "12345678901234"

    def test_strips_dashes(self):
        assert normalize_regon("123-456-789") == "123456789"

    def test_rejects_wrong_length(self):
        with pytest.raises(ValueError, match="must be 9 or 14 digits"):
            normalize_regon("12345")

    def test_rejects_non_numeric(self):
        with pytest.raises(ValueError, match="must be numeric"):
            normalize_regon("ABCDEFGHI")


# ---------------------------------------------------------------------------
# 4. Token & Configuration
# ---------------------------------------------------------------------------

class TestCEIDGTokenHandling:
    """Test API token configuration."""

    def test_not_configured_without_token(self, _unset_ceidg_token):
        assert is_ceidg_configured() is False

    def test_configured_with_token(self, _set_ceidg_token):
        assert is_ceidg_configured() is True

    def test_get_config_raises_without_token(self, _unset_ceidg_token):
        with pytest.raises(CEIDGNotConfiguredError, match="CEIDG_API_TOKEN"):
            get_ceidg_config()

    def test_get_config_returns_defaults(self, _set_ceidg_token):
        base_url, token, timeout = get_ceidg_config()
        assert "ceidg/v3" in base_url
        assert token == "test-token-for-tests"
        assert timeout == 30

    def test_base_url_override(self, _set_ceidg_token):
        old = os.environ.get("CEIDG_API_BASE_URL")
        os.environ["CEIDG_API_BASE_URL"] = "https://custom.example.com/api"
        try:
            base_url, _, _ = get_ceidg_config()
            assert base_url == "https://custom.example.com/api"
        finally:
            if old:
                os.environ["CEIDG_API_BASE_URL"] = old
            else:
                os.environ.pop("CEIDG_API_BASE_URL", None)

    def test_timeout_override(self, _set_ceidg_token):
        old = os.environ.get("CEIDG_REQUEST_TIMEOUT")
        os.environ["CEIDG_REQUEST_TIMEOUT"] = "120"
        try:
            _, _, timeout = get_ceidg_config()
            assert timeout == 120
        finally:
            if old:
                os.environ["CEIDG_REQUEST_TIMEOUT"] = old
            else:
                os.environ.pop("CEIDG_REQUEST_TIMEOUT", None)

    def test_fetch_raises_without_token(self, _unset_ceidg_token):
        with pytest.raises(CEIDGNotConfiguredError):
            fetch_ceidg_by_nip("1234567890")

    def test_fetch_by_regon_raises_without_token(self, _unset_ceidg_token):
        with pytest.raises(CEIDGNotConfiguredError):
            fetch_ceidg_by_regon("123456789")


# ---------------------------------------------------------------------------
# 5. Proposal Generation
# ---------------------------------------------------------------------------

class TestCEIDGProposalForEmptyEntity:
    """Proposals when enriching an empty physical person entity."""

    def _make_profile(self, sample):
        return normalize_ceidg_response(sample)

    def test_proposes_nip(self, empty_physical_entity, ceidg_v3_sample):
        profile = self._make_profile(ceidg_v3_sample)
        proposal = generate_ceidg_proposal(empty_physical_entity, profile)
        types = [i.identifier_type for i in proposal.identifiers_to_add]
        assert "NIP" in types

    def test_proposes_regon(self, empty_physical_entity, ceidg_v3_sample):
        profile = self._make_profile(ceidg_v3_sample)
        proposal = generate_ceidg_proposal(empty_physical_entity, profile)
        types = [i.identifier_type for i in proposal.identifiers_to_add]
        assert "REGON" in types

    def test_proposes_first_and_last_name(self, empty_physical_entity, ceidg_v3_sample):
        profile = self._make_profile(ceidg_v3_sample)
        proposal = generate_ceidg_proposal(empty_physical_entity, profile)
        assert proposal.type_specific_updates.get("first_name") == "Anna"
        assert proposal.type_specific_updates.get("last_name") == "Kowalska"

    def test_proposes_canonical_label(self, empty_physical_entity, ceidg_v3_sample):
        profile = self._make_profile(ceidg_v3_sample)
        proposal = generate_ceidg_proposal(empty_physical_entity, profile)
        assert "canonical_label" in proposal.core_updates

    def test_proposes_address(self, empty_physical_entity, ceidg_v3_sample):
        profile = self._make_profile(ceidg_v3_sample)
        proposal = generate_ceidg_proposal(empty_physical_entity, profile)
        main = [a for a in proposal.address_proposals if a.address.address_type == "MAIN"]
        assert len(main) == 1
        assert main[0].address.city == "Wrocław"
        assert main[0].action == ProposalAction.ADD

    def test_proposes_email(self, empty_physical_entity, ceidg_v3_sample):
        profile = self._make_profile(ceidg_v3_sample)
        proposal = generate_ceidg_proposal(empty_physical_entity, profile)
        emails = [c for c in proposal.contacts_to_add if c.contact_type == "EMAIL"]
        assert len(emails) == 1
        assert emails[0].contact_value == "anna@projektowanie.pl"

    def test_proposes_website(self, empty_physical_entity, ceidg_v3_sample):
        profile = self._make_profile(ceidg_v3_sample)
        proposal = generate_ceidg_proposal(empty_physical_entity, profile)
        sites = [c for c in proposal.contacts_to_add if c.contact_type == "WEBSITE"]
        assert len(sites) == 1

    def test_proposes_phone(self, empty_physical_entity, ceidg_v3_sample):
        profile = self._make_profile(ceidg_v3_sample)
        proposal = generate_ceidg_proposal(empty_physical_entity, profile)
        phones = [c for c in proposal.contacts_to_add if c.contact_type == "PHONE"]
        assert len(phones) == 1

    def test_has_proposals(self, empty_physical_entity, ceidg_v3_sample):
        profile = self._make_profile(ceidg_v3_sample)
        proposal = generate_ceidg_proposal(empty_physical_entity, profile)
        assert proposal.has_any_proposals() is True
        assert proposal.count_proposals() > 0

    def test_source_metadata(self, empty_physical_entity, ceidg_v3_sample):
        profile = self._make_profile(ceidg_v3_sample)
        proposal = generate_ceidg_proposal(empty_physical_entity, profile)
        assert proposal.source_system == "CEIDG"
        assert proposal.entity_id == "person-empty-id"


class TestCEIDGProposalExistingData:
    """Proposals should not overwrite existing entity data."""

    def _make_profile(self, sample):
        return normalize_ceidg_response(sample)

    def test_skips_existing_nip(self, populated_physical_entity, ceidg_v3_sample):
        profile = self._make_profile(ceidg_v3_sample)
        proposal = generate_ceidg_proposal(populated_physical_entity, profile)
        nip_props = [i for i in proposal.identifiers_to_add
                     if i.identifier_type == "NIP" and i.action == ProposalAction.ADD]
        assert len(nip_props) == 0

    def test_still_proposes_missing_regon(self, populated_physical_entity, ceidg_v3_sample):
        profile = self._make_profile(ceidg_v3_sample)
        proposal = generate_ceidg_proposal(populated_physical_entity, profile)
        regon_props = [i for i in proposal.identifiers_to_add
                       if i.identifier_type == "REGON" and i.action == ProposalAction.ADD]
        assert len(regon_props) == 1

    def test_updates_canonical_label_to_business_name(self, populated_physical_entity, ceidg_v3_sample):
        """canonical_label should be updated to business_name from CEIDG for invoicing."""
        profile = self._make_profile(ceidg_v3_sample)
        proposal = generate_ceidg_proposal(populated_physical_entity, profile)
        assert "canonical_label" in proposal.core_updates
        assert proposal.core_updates["canonical_label"] == profile.business_name

    def test_address_update_not_add(self, populated_physical_entity, ceidg_v3_sample):
        profile = self._make_profile(ceidg_v3_sample)
        proposal = generate_ceidg_proposal(populated_physical_entity, profile)
        main_addrs = [a for a in proposal.address_proposals
                      if a.address.address_type == "MAIN"]
        if main_addrs:
            assert main_addrs[0].action == ProposalAction.UPDATE


class TestCEIDGProposalMinimalProfile:
    """Proposals from a minimal profile (no address, no contacts)."""

    def _make_profile(self, sample):
        return normalize_ceidg_response(sample)

    def test_no_address_proposal_when_profile_has_none(self, empty_physical_entity, ceidg_v3_minimal):
        profile = self._make_profile(ceidg_v3_minimal)
        proposal = generate_ceidg_proposal(empty_physical_entity, profile)
        # Address is empty dict → no address to propose
        assert len(proposal.address_proposals) == 0

    def test_no_contact_proposals(self, empty_physical_entity, ceidg_v3_minimal):
        profile = self._make_profile(ceidg_v3_minimal)
        proposal = generate_ceidg_proposal(empty_physical_entity, profile)
        assert len(proposal.contacts_to_add) == 0

    def test_no_regon_when_empty_string(self, empty_physical_entity, ceidg_v3_minimal):
        """Empty REGON string should not generate a proposal."""
        profile = self._make_profile(ceidg_v3_minimal)
        proposal = generate_ceidg_proposal(empty_physical_entity, profile)
        regon_props = [i for i in proposal.identifiers_to_add
                       if i.identifier_type == "REGON"]
        assert len(regon_props) == 0


class TestCEIDGProposalForLegalPerson:
    """CEIDG proposals when target entity is a legal person."""

    def test_business_name_as_registered_name(self, ceidg_v3_sample):
        entity = {
            "id": "legal-id",
            "entity_type": "LEGAL_PERSON",
            "canonical_label": "",
            "registered_name": "",
            "identifiers": [],
            "addresses": [],
            "contacts": [],
        }
        profile = normalize_ceidg_response(ceidg_v3_sample)
        proposal = generate_ceidg_proposal(entity, profile)
        assert "registered_name" in proposal.type_specific_updates
        assert proposal.type_specific_updates["registered_name"] == "ANNA KOWALSKA PROJEKTOWANIE WNĘTRZ"


class TestCEIDGProposalCollision:
    """Test identifier collision detection."""

    def test_collision_skips_identifier(self, empty_physical_entity, ceidg_v3_sample):
        profile = normalize_ceidg_response(ceidg_v3_sample)
        all_identifiers = {
            "NIP": {"8991234567": "other-entity-id"},
        }
        proposal = generate_ceidg_proposal(
            empty_physical_entity, profile, all_identifiers=all_identifiers
        )
        nip_prop = next(
            (i for i in proposal.identifiers_to_add if i.identifier_type == "NIP"),
            None,
        )
        assert nip_prop is not None
        assert nip_prop.action == ProposalAction.SKIP
        assert nip_prop.collision_entity_id == "other-entity-id"


# ---------------------------------------------------------------------------
# 6. CLI Integration (mocked DB + HTTP)
# ---------------------------------------------------------------------------

class TestCEIDGCLIEnrich:
    """Test CLI entity enrich --source ceidg with mocked dependencies."""

    @pytest.fixture
    def runner(self):
        from click.testing import CliRunner
        return CliRunner()

    @pytest.fixture
    def cli(self):
        from lawfirm_cli.commands import cli
        return cli

    def test_enrich_ceidg_not_configured_message(self, runner, cli, _unset_ceidg_token):
        """Should show error when CEIDG token not configured."""
        with patch("lawfirm_cli.commands.get_entity") as mock_get:
            mock_get.return_value = {
                "id": "ent-1",
                "entity_type": "PHYSICAL_PERSON",
                "canonical_label": "Test",
                "identifiers": [{"identifier_type": "NIP", "identifier_value": "1234567890"}],
                "addresses": [],
                "contacts": [],
            }
            with patch("lawfirm_cli.commands.check_entities_available", return_value=(True, "OK")):
                with patch("lawfirm_cli.commands.check_registry_tables_exist",
                           return_value={"registry_snapshots": True}):
                    result = runner.invoke(cli, [
                        "entity", "enrich", "ent-1",
                        "--source", "ceidg",
                        "--nip", "1234567890",
                    ])
                    assert (
                        "not configured" in result.output.lower()
                        or "CEIDG_API_TOKEN" in result.output
                        or result.exit_code != 0
                    )

    @responses.activate
    def test_enrich_ceidg_success_flow(self, runner, cli, _set_ceidg_token, ceidg_v3_sample):
        """Should fetch, normalize, and present proposals."""
        responses.add(
            responses.GET,
            f"{DEFAULT_CEIDG_API_BASE_URL}/firmy",
            json={"firmy": [ceidg_v3_sample]},
            status=200,
        )

        with patch("lawfirm_cli.commands.get_entity") as mock_get:
            mock_get.return_value = {
                "id": "ent-ceidg",
                "entity_type": "PHYSICAL_PERSON",
                "canonical_label": "",
                "first_name": "",
                "last_name": "",
                "identifiers": [],
                "addresses": [],
                "contacts": [],
            }
            with patch("lawfirm_cli.commands.check_entities_available", return_value=(True, "OK")):
                with patch("lawfirm_cli.commands.check_registry_tables_exist",
                           return_value={"registry_snapshots": True}):
                    with patch("lawfirm_cli.commands.insert_snapshot", return_value="snap-1"):
                        with patch("lawfirm_cli.commands.update_entity"):
                            with patch("lawfirm_cli.commands.add_identifier"):
                                with patch("lawfirm_cli.commands.add_contact"):
                                    with patch("lawfirm_cli.commands.add_address"):
                                        with patch("lawfirm_cli.commands.upsert_ceidg_profile"):
                                            result = runner.invoke(cli, [
                                                "entity", "enrich", "ent-ceidg",
                                                "--source", "ceidg",
                                                "--nip", "8991234567",
                                                "--apply-all",
                                            ])
                                            # Should not crash
                                            assert result.exit_code == 0 or "apply" in result.output.lower()
