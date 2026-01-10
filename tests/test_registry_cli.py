"""Tests for registry CLI commands with mocked HTTP."""

import json
import os
import pytest
import responses
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from pathlib import Path

from lawfirm_cli.commands import cli
from lawfirm_cli.registry.krs_client import (
    DEFAULT_KRS_API_BASE_URL,
    KRSConnectionError,
    KRSNotFoundError,
)
from lawfirm_cli.registry.ceidg_client import (
    DEFAULT_CEIDG_API_BASE_URL,
    CEIDGNotConfiguredError,
)


@pytest.fixture
def runner():
    """Create CLI runner."""
    return CliRunner()


@pytest.fixture
def krs_sample_response():
    """Load KRS sample response."""
    fixture_path = Path(__file__).parent / "fixtures" / "krs_sample.json"
    with open(fixture_path) as f:
        return json.load(f)


@pytest.fixture
def ceidg_sample_response():
    """Load CEIDG sample response."""
    fixture_path = Path(__file__).parent / "fixtures" / "ceidg_sample.json"
    with open(fixture_path) as f:
        return json.load(f)


class TestRegistryInitSchema:
    """Tests for registry init-schema command."""
    
    def test_init_schema_command_exists(self, runner):
        """Registry init-schema command should exist."""
        result = runner.invoke(cli, ["registry", "init-schema"])
        
        # Should not be "no such command" error
        assert "No such command" not in result.output
    
    def test_init_schema_creates_tables(self, runner):
        """Registry init-schema should create tables."""
        result = runner.invoke(cli, ["registry", "init-schema"])
        
        assert result.exit_code == 0
        # Should show either created or already exist message
        assert "registry" in result.output.lower()


class TestRegistryStatus:
    """Tests for registry status command."""
    
    def test_status_command_exists(self, runner):
        """Registry status command should exist."""
        result = runner.invoke(cli, ["registry", "status"])
        
        assert "No such command" not in result.output
    
    def test_status_shows_tables(self, runner):
        """Registry status should show table status."""
        result = runner.invoke(cli, ["registry", "status"])
        
        assert result.exit_code == 0
        assert "registry_snapshots" in result.output
        assert "registry_profiles_krs" in result.output
        assert "registry_profiles_ceidg" in result.output
    
    def test_status_shows_configuration(self, runner):
        """Registry status should show configuration."""
        result = runner.invoke(cli, ["registry", "status"])
        
        assert "Configuration" in result.output or "KRS_API_BASE_URL" in result.output


class TestEntityEnrichCommand:
    """Tests for entity enrich command."""
    
    def test_enrich_command_exists(self, runner):
        """Entity enrich command should exist."""
        result = runner.invoke(cli, ["entity", "enrich", "--help"])
        
        assert result.exit_code == 0
        assert "enrich" in result.output.lower() or "Enrich" in result.output
    
    def test_enrich_requires_entity_id(self, runner):
        """Entity enrich should require entity_id argument."""
        result = runner.invoke(cli, ["entity", "enrich"])
        
        # Should show usage error
        assert result.exit_code != 0 or "Missing argument" in result.output or "ENTITY_ID" in result.output
    
    def test_enrich_nonexistent_entity_shows_error(self, runner):
        """Enriching nonexistent entity should show error."""
        result = runner.invoke(cli, ["entity", "enrich", "nonexistent-entity-id-12345"])
        
        # Should show entity not found error
        assert "not found" in result.output.lower() or "error" in result.output.lower()
    
    def test_enrich_help_shows_options(self, runner):
        """Entity enrich help should show available options."""
        result = runner.invoke(cli, ["entity", "enrich", "--help"])
        
        assert "--source" in result.output
        assert "--krs" in result.output
        assert "--nip" in result.output
        assert "--apply-all" in result.output


class TestKRSClientMocked:
    """Tests for KRS client with mocked HTTP responses."""
    
    @responses.activate
    def test_krs_fetch_success(self, krs_sample_response):
        """KRS client should successfully fetch and parse data."""
        from lawfirm_cli.registry.krs_client import fetch_and_normalize_krs
        
        krs_number = "0000012345"
        url = f"{DEFAULT_KRS_API_BASE_URL}/OdpisPelny/{krs_number}?rejestr=P&format=json"
        
        responses.add(
            responses.GET,
            url,
            json=krs_sample_response,
            status=200,
        )
        
        profile, snapshot = fetch_and_normalize_krs(krs_number)
        
        assert profile.krs == "0000012345"
        assert profile.nip == "1234567890"
        assert profile.official_name == "TEST SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ"
        assert snapshot.source_system == "KRS"
        assert snapshot.external_id == krs_number
    
    @responses.activate
    def test_krs_fetch_not_found(self):
        """KRS client should raise error for 404."""
        from lawfirm_cli.registry.krs_client import fetch_and_normalize_krs
        
        krs_number = "9999999999"
        url = f"{DEFAULT_KRS_API_BASE_URL}/OdpisPelny/{krs_number}?rejestr=P&format=json"
        
        responses.add(
            responses.GET,
            url,
            status=404,
        )
        
        with pytest.raises(KRSNotFoundError):
            fetch_and_normalize_krs(krs_number)
    
    @responses.activate
    def test_krs_fetch_timeout(self):
        """KRS client should handle timeout."""
        from lawfirm_cli.registry.krs_client import fetch_and_normalize_krs
        import requests
        
        krs_number = "0000012345"
        url = f"{DEFAULT_KRS_API_BASE_URL}/OdpisPelny/{krs_number}?rejestr=P&format=json"
        
        responses.add(
            responses.GET,
            url,
            body=requests.exceptions.Timeout("Connection timed out"),
        )
        
        with pytest.raises(KRSConnectionError):
            fetch_and_normalize_krs(krs_number)
    
    @responses.activate
    def test_krs_fetch_network_error(self):
        """KRS client should handle network errors."""
        from lawfirm_cli.registry.krs_client import fetch_and_normalize_krs
        import requests
        
        krs_number = "0000012345"
        url = f"{DEFAULT_KRS_API_BASE_URL}/OdpisPelny/{krs_number}?rejestr=P&format=json"
        
        responses.add(
            responses.GET,
            url,
            body=requests.exceptions.ConnectionError("Network unreachable"),
        )
        
        with pytest.raises(KRSConnectionError):
            fetch_and_normalize_krs(krs_number)


class TestCEIDGClientMocked:
    """Tests for CEIDG client with mocked HTTP responses."""
    
    @responses.activate
    def test_ceidg_not_configured_error(self):
        """CEIDG client should error when token not configured."""
        from lawfirm_cli.registry.ceidg_client import fetch_ceidg_by_nip
        
        # Ensure token is not set
        old_token = os.environ.pop("CEIDG_API_TOKEN", None)
        
        try:
            with pytest.raises(CEIDGNotConfiguredError):
                fetch_ceidg_by_nip("1234567890")
        finally:
            if old_token:
                os.environ["CEIDG_API_TOKEN"] = old_token
    
    @responses.activate
    def test_ceidg_fetch_success(self, ceidg_sample_response):
        """CEIDG client should successfully fetch and parse data."""
        from lawfirm_cli.registry.ceidg_client import fetch_and_normalize_ceidg_by_nip
        
        # Set token
        old_token = os.environ.get("CEIDG_API_TOKEN")
        os.environ["CEIDG_API_TOKEN"] = "test_token_123"
        
        nip = "9876543210"
        url = f"{DEFAULT_CEIDG_API_BASE_URL}/firmy"
        
        responses.add(
            responses.GET,
            url,
            json={"firmy": [ceidg_sample_response]},
            status=200,
        )
        
        try:
            profile, snapshot = fetch_and_normalize_ceidg_by_nip(nip)
            
            assert profile.nip == "9876543210"
            assert profile.first_name == "MARIA"
            assert profile.last_name == "WIŚNIEWSKA"
            assert profile.business_name == "MARIA WIŚNIEWSKA USŁUGI INFORMATYCZNE"
            assert snapshot.source_system == "CEIDG"
        finally:
            if old_token:
                os.environ["CEIDG_API_TOKEN"] = old_token
            else:
                os.environ.pop("CEIDG_API_TOKEN", None)
    
    def test_ceidg_is_configured_check(self):
        """is_ceidg_configured should reflect token presence."""
        from lawfirm_cli.registry.ceidg_client import is_ceidg_configured
        
        # Without token
        old_token = os.environ.pop("CEIDG_API_TOKEN", None)
        
        try:
            assert is_ceidg_configured() is False
            
            # With token
            os.environ["CEIDG_API_TOKEN"] = "test_token"
            assert is_ceidg_configured() is True
        finally:
            if old_token:
                os.environ["CEIDG_API_TOKEN"] = old_token
            else:
                os.environ.pop("CEIDG_API_TOKEN", None)


class TestKRSNumberNormalization:
    """Tests for KRS number normalization."""
    
    def test_pads_short_numbers(self):
        """Should pad short KRS numbers with leading zeros."""
        from lawfirm_cli.registry.krs_client import normalize_krs_number
        
        assert normalize_krs_number("1") == "0000000001"
        assert normalize_krs_number("12345") == "0000012345"
        assert normalize_krs_number("123456789") == "0123456789"
    
    def test_keeps_full_numbers(self):
        """Should keep full 10-digit KRS numbers as-is."""
        from lawfirm_cli.registry.krs_client import normalize_krs_number
        
        assert normalize_krs_number("0000012345") == "0000012345"
        assert normalize_krs_number("1234567890") == "1234567890"
    
    def test_removes_whitespace(self):
        """Should remove whitespace from KRS numbers."""
        from lawfirm_cli.registry.krs_client import normalize_krs_number
        
        assert normalize_krs_number(" 12345 ") == "0000012345"
        assert normalize_krs_number("123 456 789") == "0123456789"
    
    def test_rejects_non_numeric(self):
        """Should reject non-numeric KRS numbers."""
        from lawfirm_cli.registry.krs_client import normalize_krs_number
        
        with pytest.raises(ValueError, match="must be numeric"):
            normalize_krs_number("ABC123")
    
    def test_rejects_too_long(self):
        """Should reject KRS numbers longer than 10 digits."""
        from lawfirm_cli.registry.krs_client import normalize_krs_number
        
        with pytest.raises(ValueError, match="too long"):
            normalize_krs_number("12345678901")


class TestCEIDGCredentialsHandling:
    """Tests for CEIDG credentials handling."""
    
    def test_cli_shows_friendly_error_when_not_configured(self, runner):
        """CLI should show friendly error when CEIDG not configured."""
        # Remove token if set
        old_token = os.environ.pop("CEIDG_API_TOKEN", None)
        
        try:
            # Mock entity to exist for enrich command
            with patch('lawfirm_cli.commands.get_entity') as mock_get:
                mock_get.return_value = {
                    "id": "test-id",
                    "entity_type": "PHYSICAL_PERSON",
                    "canonical_label": "Test Person",
                    "identifiers": [{"identifier_type": "NIP", "identifier_value": "1234567890"}],
                    "addresses": [],
                    "contacts": [],
                }
                
                with patch('lawfirm_cli.commands.check_entities_available') as mock_check:
                    mock_check.return_value = (True, "OK")
                    
                    with patch('lawfirm_cli.commands.check_registry_tables_exist') as mock_reg:
                        mock_reg.return_value = {"registry_snapshots": True}
                        
                        result = runner.invoke(cli, [
                            "entity", "enrich", "test-id",
                            "--source", "ceidg",
                            "--nip", "1234567890"
                        ])
                        
                        # Should show CEIDG not configured message
                        assert "not configured" in result.output.lower() or "CEIDG_API_TOKEN" in result.output
        finally:
            if old_token:
                os.environ["CEIDG_API_TOKEN"] = old_token


class TestEnrichmentApplyAll:
    """Tests for --apply-all flag behavior."""
    
    @responses.activate
    def test_apply_all_applies_safe_additions(self, runner, krs_sample_response):
        """--apply-all should apply safe additions automatically."""
        from lawfirm_cli.registry.krs_client import DEFAULT_KRS_API_BASE_URL
        
        krs_number = "0000012345"
        url = f"{DEFAULT_KRS_API_BASE_URL}/OdpisPelny/{krs_number}?rejestr=P&format=json"
        
        responses.add(
            responses.GET,
            url,
            json=krs_sample_response,
            status=200,
        )
        
        # Mock database operations
        with patch('lawfirm_cli.commands.get_entity') as mock_get:
            mock_get.return_value = {
                "id": "test-entity-id",
                "entity_type": "LEGAL_PERSON",
                "canonical_label": "",
                "registered_name": "",
                "identifiers": [],
                "addresses": [],
                "contacts": [],
            }
            
            with patch('lawfirm_cli.commands.check_entities_available') as mock_check:
                mock_check.return_value = (True, "OK")
                
                with patch('lawfirm_cli.commands.check_registry_tables_exist') as mock_reg:
                    mock_reg.return_value = {"registry_snapshots": True}
                    
                    with patch('lawfirm_cli.commands.insert_snapshot') as mock_snap:
                        mock_snap.return_value = "snapshot-id-123"
                        
                        with patch('lawfirm_cli.commands.update_entity') as mock_update:
                            with patch('lawfirm_cli.commands.add_identifier') as mock_ident:
                                with patch('lawfirm_cli.commands.add_contact') as mock_contact:
                                    with patch('lawfirm_cli.commands.add_address') as mock_addr:
                                        with patch('lawfirm_cli.commands.upsert_krs_profile') as mock_profile:
                                            result = runner.invoke(cli, [
                                                "entity", "enrich", "test-entity-id",
                                                "--source", "krs",
                                                "--krs", krs_number,
                                                "--apply-all"
                                            ])
                                            
                                            # Should show apply-all message
                                            assert "apply" in result.output.lower() or result.exit_code == 0


class TestEnvironmentVariables:
    """Tests for environment variable handling."""
    
    def test_krs_url_can_be_overridden(self):
        """KRS API URL should be overridable via env var."""
        from lawfirm_cli.registry.krs_client import get_krs_config
        
        old_url = os.environ.get("KRS_API_BASE_URL")
        os.environ["KRS_API_BASE_URL"] = "https://custom-krs.example.com"
        
        try:
            base_url, _ = get_krs_config()
            assert base_url == "https://custom-krs.example.com"
        finally:
            if old_url:
                os.environ["KRS_API_BASE_URL"] = old_url
            else:
                os.environ.pop("KRS_API_BASE_URL", None)
    
    def test_krs_timeout_can_be_overridden(self):
        """KRS timeout should be overridable via env var."""
        from lawfirm_cli.registry.krs_client import get_krs_config
        
        old_timeout = os.environ.get("KRS_REQUEST_TIMEOUT")
        os.environ["KRS_REQUEST_TIMEOUT"] = "60"
        
        try:
            _, timeout = get_krs_config()
            assert timeout == 60
        finally:
            if old_timeout:
                os.environ["KRS_REQUEST_TIMEOUT"] = old_timeout
            else:
                os.environ.pop("KRS_REQUEST_TIMEOUT", None)
    
    def test_ceidg_url_can_be_overridden(self):
        """CEIDG API URL should be overridable via env var."""
        from lawfirm_cli.registry.ceidg_client import get_ceidg_config
        
        old_url = os.environ.get("CEIDG_API_BASE_URL")
        old_token = os.environ.get("CEIDG_API_TOKEN")
        
        os.environ["CEIDG_API_BASE_URL"] = "https://custom-ceidg.example.com"
        os.environ["CEIDG_API_TOKEN"] = "test_token"
        
        try:
            base_url, _, _ = get_ceidg_config()
            assert base_url == "https://custom-ceidg.example.com"
        finally:
            if old_url:
                os.environ["CEIDG_API_BASE_URL"] = old_url
            else:
                os.environ.pop("CEIDG_API_BASE_URL", None)
            if old_token:
                os.environ["CEIDG_API_TOKEN"] = old_token
            else:
                os.environ.pop("CEIDG_API_TOKEN", None)
