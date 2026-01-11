"""Tests for Polish company name parsing utilities."""

import pytest
from lawfirm_cli.company_names import (
    extract_legal_form_from_name,
    get_legal_kind_from_krs_code,
    get_legal_kind_from_krs_form_name,
    suggest_short_name,
    get_legal_form_suffix,
    parse_krs_company_data,
    normalize_for_matching,
)


class TestNormalizeForMatching:
    """Tests for text normalization."""
    
    def test_empty_string(self):
        assert normalize_for_matching("") == ""
    
    def test_none_input(self):
        assert normalize_for_matching(None) == ""
    
    def test_whitespace_normalization(self):
        assert normalize_for_matching("  hello   world  ") == "hello world"
    
    def test_lowercase_conversion(self):
        assert normalize_for_matching("HELLO WORLD") == "hello world"


class TestExtractLegalFormFromName:
    """Tests for extracting legal form from company names."""
    
    def test_spolka_akcyjna_full(self):
        form, particular = extract_legal_form_from_name("PROFINANCE SPÓŁKA AKCYJNA")
        assert form is not None
        assert form.legal_kind == "SPOLKA_AKCYJNA"
        assert particular == "PROFINANCE"
    
    def test_spolka_akcyjna_lowercase(self):
        form, particular = extract_legal_form_from_name("Profinance spółka akcyjna")
        assert form is not None
        assert form.legal_kind == "SPOLKA_AKCYJNA"
        assert particular == "Profinance"
    
    def test_spolka_z_oo_full(self):
        form, particular = extract_legal_form_from_name(
            "ABC SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ"
        )
        assert form is not None
        assert form.legal_kind == "SPOLKA_Z_OO"
        assert particular == "ABC"
    
    def test_spolka_jawna(self):
        form, particular = extract_legal_form_from_name("XYZ SPÓŁKA JAWNA")
        assert form is not None
        assert form.legal_kind == "SPOLKA_JAWNA"
        assert particular == "XYZ"
    
    def test_spolka_komandytowa(self):
        form, particular = extract_legal_form_from_name("FIRMA SPÓŁKA KOMANDYTOWA")
        assert form is not None
        assert form.legal_kind == "SPOLKA_KOMANDYTOWA"
        assert particular == "FIRMA"
    
    def test_spolka_komandytowo_akcyjna(self):
        form, particular = extract_legal_form_from_name(
            "HOLDING SPÓŁKA KOMANDYTOWO-AKCYJNA"
        )
        assert form is not None
        assert form.legal_kind == "SPOLKA_KOMANDYTOWO_AKCYJNA"
        assert particular == "HOLDING"
    
    def test_spolka_partnerska(self):
        form, particular = extract_legal_form_from_name("KANCELARIA SPÓŁKA PARTNERSKA")
        assert form is not None
        assert form.legal_kind == "SPOLKA_PARTNERSKA"
        assert particular == "KANCELARIA"
    
    def test_prosta_spolka_akcyjna(self):
        form, particular = extract_legal_form_from_name("STARTUP PROSTA SPÓŁKA AKCYJNA")
        assert form is not None
        assert form.legal_kind == "PROSTA_SPOLKA_AKCYJNA"
        assert particular == "STARTUP"
    
    def test_fundacja(self):
        form, particular = extract_legal_form_from_name("OCHRONY ŚRODOWISKA FUNDACJA")
        # Fundacja at the end
        assert form is not None
        assert form.legal_kind == "FUNDACJA"
    
    def test_no_legal_form(self):
        form, particular = extract_legal_form_from_name("RANDOM COMPANY NAME")
        assert form is None
        assert particular == "RANDOM COMPANY NAME"
    
    def test_empty_string(self):
        form, particular = extract_legal_form_from_name("")
        assert form is None
        assert particular == ""
    
    def test_multiword_particular_name(self):
        form, particular = extract_legal_form_from_name(
            "ABC DEVELOPMENT GROUP SPÓŁKA AKCYJNA"
        )
        assert form is not None
        assert form.legal_kind == "SPOLKA_AKCYJNA"
        assert particular == "ABC DEVELOPMENT GROUP"


class TestGetLegalKindFromKrsCode:
    """Tests for KRS form code mapping."""
    
    def test_spolka_z_oo(self):
        assert get_legal_kind_from_krs_code("117") == "SPOLKA_Z_OO"
    
    def test_spolka_akcyjna(self):
        assert get_legal_kind_from_krs_code("114") == "SPOLKA_AKCYJNA"
    
    def test_spolka_jawna(self):
        assert get_legal_kind_from_krs_code("111") == "SPOLKA_JAWNA"
    
    def test_spolka_partnerska(self):
        assert get_legal_kind_from_krs_code("112") == "SPOLKA_PARTNERSKA"
    
    def test_spolka_komandytowa(self):
        assert get_legal_kind_from_krs_code("113") == "SPOLKA_KOMANDYTOWA"
    
    def test_spolka_komandytowo_akcyjna(self):
        assert get_legal_kind_from_krs_code("116") == "SPOLKA_KOMANDYTOWO_AKCYJNA"
    
    def test_prosta_spolka_akcyjna(self):
        assert get_legal_kind_from_krs_code("161") == "PROSTA_SPOLKA_AKCYJNA"
    
    def test_fundacja(self):
        assert get_legal_kind_from_krs_code("125") == "FUNDACJA"
    
    def test_unknown_code(self):
        assert get_legal_kind_from_krs_code("999") is None
    
    def test_none_input(self):
        assert get_legal_kind_from_krs_code(None) is None
    
    def test_empty_string(self):
        assert get_legal_kind_from_krs_code("") is None


class TestGetLegalKindFromKrsFormName:
    """Tests for KRS form name mapping."""
    
    def test_spolka_z_oo(self):
        result = get_legal_kind_from_krs_form_name(
            "spółka z ograniczoną odpowiedzialnością"
        )
        assert result == "SPOLKA_Z_OO"
    
    def test_spolka_z_oo_uppercase(self):
        result = get_legal_kind_from_krs_form_name(
            "SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ"
        )
        assert result == "SPOLKA_Z_OO"
    
    def test_spolka_akcyjna(self):
        result = get_legal_kind_from_krs_form_name("spółka akcyjna")
        assert result == "SPOLKA_AKCYJNA"
    
    def test_unknown_form(self):
        result = get_legal_kind_from_krs_form_name("unknown form")
        assert result is None
    
    def test_none_input(self):
        result = get_legal_kind_from_krs_form_name(None)
        assert result is None


class TestSuggestShortName:
    """Tests for short name suggestion."""
    
    def test_spolka_akcyjna(self):
        result = suggest_short_name("PROFINANCE SPÓŁKA AKCYJNA")
        assert result == "PROFINANCE S.A."
    
    def test_spolka_z_oo(self):
        result = suggest_short_name("ABC SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ")
        assert result == "ABC sp. z o.o."
    
    def test_spolka_jawna(self):
        result = suggest_short_name("XYZ SPÓŁKA JAWNA")
        assert result == "XYZ sp. j."
    
    def test_spolka_komandytowa(self):
        result = suggest_short_name("FIRMA SPÓŁKA KOMANDYTOWA")
        assert result == "FIRMA sp. k."
    
    def test_spolka_partnerska(self):
        result = suggest_short_name("KANCELARIA SPÓŁKA PARTNERSKA")
        assert result == "KANCELARIA sp.p."
    
    def test_prosta_spolka_akcyjna(self):
        result = suggest_short_name("STARTUP PROSTA SPÓŁKA AKCYJNA")
        assert result == "STARTUP P.S.A."
    
    def test_spolka_komandytowo_akcyjna(self):
        result = suggest_short_name("HOLDING SPÓŁKA KOMANDYTOWO-AKCYJNA")
        assert result == "HOLDING S.K.A."
    
    def test_fundacja_no_suffix(self):
        # Fundacje don't have standard abbreviations
        result = suggest_short_name("OCHRONY ŚRODOWISKA FUNDACJA")
        assert "fundacja" not in result.lower() or result == "OCHRONY ŚRODOWISKA"
    
    def test_no_legal_form(self):
        result = suggest_short_name("RANDOM COMPANY")
        assert result == "RANDOM COMPANY"
    
    def test_empty_string(self):
        result = suggest_short_name("")
        assert result == ""
    
    def test_multiword_name(self):
        result = suggest_short_name("ABC DEVELOPMENT GROUP SPÓŁKA AKCYJNA")
        assert result == "ABC DEVELOPMENT GROUP S.A."


class TestGetLegalFormSuffix:
    """Tests for getting legal form suffix from legal_kind."""
    
    def test_spolka_akcyjna(self):
        assert get_legal_form_suffix("SPOLKA_AKCYJNA") == "S.A."
    
    def test_spolka_z_oo(self):
        assert get_legal_form_suffix("SPOLKA_Z_OO") == "sp. z o.o."
    
    def test_spolka_jawna(self):
        assert get_legal_form_suffix("SPOLKA_JAWNA") == "sp. j."
    
    def test_fundacja_no_suffix(self):
        # Fundacje don't have standard abbreviations
        suffix = get_legal_form_suffix("FUNDACJA")
        assert suffix == "" or suffix is None
    
    def test_unknown_kind(self):
        assert get_legal_form_suffix("UNKNOWN") is None


class TestParseKrsCompanyData:
    """Integration tests for parse_krs_company_data."""
    
    def test_full_data_with_code(self):
        """Test with all data available, form code takes priority."""
        result = parse_krs_company_data(
            official_name="ABC SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
            legal_form_name="SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
            legal_form_code="117",
        )
        
        assert result["legal_kind"] == "SPOLKA_Z_OO"
        assert result["short_name"] == "ABC sp. z o.o."
        assert result["legal_form_suffix"] == "sp. z o.o."
        assert result["particular_name"] == "ABC"
        assert result["confidence"] == "high"
    
    def test_only_form_name(self):
        """Test with only form name available."""
        result = parse_krs_company_data(
            official_name="PROFINANCE SPÓŁKA AKCYJNA",
            legal_form_name="SPÓŁKA AKCYJNA",
            legal_form_code=None,
        )
        
        assert result["legal_kind"] == "SPOLKA_AKCYJNA"
        assert result["short_name"] == "PROFINANCE S.A."
        assert result["confidence"] == "medium"
    
    def test_only_name(self):
        """Test with only company name available."""
        result = parse_krs_company_data(
            official_name="XYZ SPÓŁKA JAWNA",
            legal_form_name=None,
            legal_form_code=None,
        )
        
        assert result["legal_kind"] == "SPOLKA_JAWNA"
        assert result["short_name"] == "XYZ sp. j."
        assert result["confidence"] == "medium"
    
    def test_no_legal_form_detectable(self):
        """Test when no legal form can be detected."""
        result = parse_krs_company_data(
            official_name="RANDOM COMPANY NAME",
            legal_form_name=None,
            legal_form_code=None,
        )
        
        assert result["legal_kind"] is None
        assert result["short_name"] is None
        assert result["particular_name"] == "RANDOM COMPANY NAME"
        assert result["confidence"] == "low"
    
    def test_empty_inputs(self):
        """Test with empty inputs."""
        result = parse_krs_company_data(
            official_name=None,
            legal_form_name=None,
            legal_form_code=None,
        )
        
        assert result["legal_kind"] is None
        assert result["short_name"] is None
    
    def test_real_world_example_kghm(self):
        """Test with a real-world-like example."""
        result = parse_krs_company_data(
            official_name="KGHM POLSKA MIEDŹ SPÓŁKA AKCYJNA",
            legal_form_name="SPÓŁKA AKCYJNA",
            legal_form_code="114",
        )
        
        assert result["legal_kind"] == "SPOLKA_AKCYJNA"
        assert result["short_name"] == "KGHM POLSKA MIEDŹ S.A."
        assert result["legal_form_suffix"] == "S.A."
        assert result["particular_name"] == "KGHM POLSKA MIEDŹ"
        assert result["confidence"] == "high"
    
    def test_real_world_example_allegro(self):
        """Test with another real-world-like example."""
        result = parse_krs_company_data(
            official_name="ALLEGRO.EU SPÓŁKA AKCYJNA",
            legal_form_name="SPÓŁKA AKCYJNA",
            legal_form_code="114",
        )
        
        assert result["legal_kind"] == "SPOLKA_AKCYJNA"
        assert result["short_name"] == "ALLEGRO.EU S.A."
        assert result["particular_name"] == "ALLEGRO.EU"


class TestEdgeCases:
    """Tests for edge cases and unusual inputs."""
    
    def test_extra_whitespace(self):
        form, particular = extract_legal_form_from_name(
            "  ABC   SPÓŁKA   AKCYJNA  "
        )
        assert form is not None
        assert form.legal_kind == "SPOLKA_AKCYJNA"
    
    def test_mixed_case(self):
        form, particular = extract_legal_form_from_name(
            "Abc Spółka Akcyjna"
        )
        assert form is not None
        assert form.legal_kind == "SPOLKA_AKCYJNA"
    
    def test_name_with_numbers(self):
        result = parse_krs_company_data(
            official_name="TECH 2000 SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
            legal_form_name="SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ",
            legal_form_code="117",
        )
        
        assert result["legal_kind"] == "SPOLKA_Z_OO"
        assert result["particular_name"] == "TECH 2000"
        assert result["short_name"] == "TECH 2000 sp. z o.o."
    
    def test_name_with_special_chars(self):
        result = parse_krs_company_data(
            official_name="ABC-XYZ SPÓŁKA AKCYJNA",
            legal_form_name="SPÓŁKA AKCYJNA",
            legal_form_code="114",
        )
        
        assert result["legal_kind"] == "SPOLKA_AKCYJNA"
        assert result["particular_name"] == "ABC-XYZ"
        assert result["short_name"] == "ABC-XYZ S.A."
