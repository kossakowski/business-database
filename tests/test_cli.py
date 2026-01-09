"""Integration tests for CLI commands."""

import pytest
from click.testing import CliRunner

from lawfirm_cli.commands import cli


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


class TestCLIBasics:
    """Basic CLI functionality tests."""
    
    def test_cli_help(self, runner):
        """Test that --help works."""
        result = runner.invoke(cli, ["--help"])
        
        assert result.exit_code == 0
        assert "Law Firm CLI" in result.output
    
    def test_cli_version(self, runner):
        """Test that --version works."""
        result = runner.invoke(cli, ["--version"])
        
        assert result.exit_code == 0
        assert "0.1.0" in result.output
    
    def test_entity_group_help(self, runner):
        """Test entity command group help."""
        result = runner.invoke(cli, ["entity", "--help"])
        
        assert result.exit_code == 0
        assert "create" in result.output
        assert "list" in result.output
        assert "view" in result.output
        assert "update" in result.output
        assert "delete" in result.output
    
    def test_meta_group_help(self, runner):
        """Test meta command group help."""
        result = runner.invoke(cli, ["meta", "--help"])
        
        assert result.exit_code == 0
        assert "fields" in result.output
        assert "enums" in result.output


class TestStatusCommand:
    """Tests for status command."""
    
    def test_status_command(self, runner, meta_tables_exist):
        """Test status command shows schema info."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        result = runner.invoke(cli, ["status"])
        
        assert result.exit_code == 0
        assert "Schema Status" in result.output or "meta" in result.output.lower()


class TestMetaCommands:
    """Tests for metadata exploration commands."""
    
    def test_meta_fields(self, runner, meta_tables_exist):
        """Test listing field metadata."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        result = runner.invoke(cli, ["meta", "fields"])
        
        assert result.exit_code == 0
        # Should contain field information
        assert "entity" in result.output.lower() or "field" in result.output.lower()
    
    def test_meta_fields_with_prefix(self, runner, meta_tables_exist):
        """Test filtering fields by prefix."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        result = runner.invoke(cli, ["meta", "fields", "--prefix", "id."])
        
        assert result.exit_code == 0
    
    def test_meta_enums_list_all(self, runner, meta_tables_exist):
        """Test listing all enum keys."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        result = runner.invoke(cli, ["meta", "enums"])
        
        assert result.exit_code == 0
        assert "entity_type" in result.output
    
    def test_meta_enums_specific(self, runner, meta_tables_exist):
        """Test listing specific enum options."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        result = runner.invoke(cli, ["meta", "enums", "entity_type"])
        
        assert result.exit_code == 0
        assert "PHYSICAL_PERSON" in result.output or "Osoba fizyczna" in result.output
    
    def test_meta_field_detail(self, runner, meta_tables_exist):
        """Test viewing single field details."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        result = runner.invoke(cli, ["meta", "field", "entity.entity_type"])
        
        assert result.exit_code == 0
        assert "entity.entity_type" in result.output


class TestEntityCommands:
    """Tests for entity commands when tables don't exist."""
    
    def test_entity_list_without_tables(self, runner, entity_tables_exist):
        """Test entity list shows helpful message when tables missing."""
        if entity_tables_exist:
            pytest.skip("Entity tables exist")
        
        result = runner.invoke(cli, ["entity", "list"])
        
        # Should show error about missing tables
        assert "not yet created" in result.output.lower() or "missing" in result.output.lower()
    
    def test_entity_view_without_tables(self, runner, entity_tables_exist):
        """Test entity view shows helpful message when tables missing."""
        if entity_tables_exist:
            pytest.skip("Entity tables exist")
        
        result = runner.invoke(cli, ["entity", "view", "some-id"])
        
        assert "not yet created" in result.output.lower() or "missing" in result.output.lower()


class TestCLIOutputFormatting:
    """Tests for CLI output formatting."""
    
    def test_meta_fields_table_format(self, runner, meta_tables_exist):
        """Test that meta fields output is formatted as table."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        result = runner.invoke(cli, ["meta", "fields", "--prefix", "entity."])
        
        assert result.exit_code == 0
        # Rich tables use box-drawing characters
        # Just verify we got structured output
        assert len(result.output.strip().split("\n")) > 1
    
    def test_meta_enums_table_format(self, runner, meta_tables_exist):
        """Test that meta enums output is formatted as table."""
        if not meta_tables_exist:
            pytest.skip("Meta tables not available")
        
        result = runner.invoke(cli, ["meta", "enums", "legal_kind"])
        
        assert result.exit_code == 0
        assert len(result.output.strip().split("\n")) > 1
