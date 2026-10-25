"""Tests for the non-interactive `entity add` command (offline: the database is mocked)."""

import json
from types import SimpleNamespace

import pytest
from click.testing import CliRunner

from lawfirm_cli import commands
from lawfirm_cli import entity_add as ea
from lawfirm_cli.commands import cli
from lawfirm_cli.entities import DuplicateIdentifierError


@pytest.fixture
def db(monkeypatch):
    """A fake database: rows found by list_entities and entities created."""
    state = SimpleNamespace(rows=[], created=[])

    def list_entities(identifier_type=None, identifier_value=None, search=None, limit=50,
                      **_):
        out = []
        for row in state.rows:
            if identifier_type and (identifier_type, identifier_value) in row["ids"]:
                out.append(row)
            elif search and search.lower() in row["canonical_label"].lower():
                out.append(row)
        return out[:limit]

    def create_entity(**kwargs):
        state.created.append(kwargs)
        return "11111111-2222-3333-4444-555555555555"

    monkeypatch.setattr(commands, "check_entities_available", lambda: (True, "OK"))
    monkeypatch.setattr(commands, "list_entities", list_entities)
    monkeypatch.setattr(commands, "create_entity", create_entity)
    return state


def run(*args):
    result = CliRunner().invoke(cli, ["entity", "add", *args])
    return result.exit_code, json.loads(result.output)


PERSON = {"entity_type": "PHYSICAL_PERSON", "first_name": "Anna", "last_name": "Nowak"}


def test_preview_writes_nothing(db):
    code, out = run("--json", json.dumps(PERSON))
    assert code == 0 and out["kind"] == "preview"
    assert out["data"]["entity"]["entity_data"]["canonical_label"] == "Anna Nowak"
    assert db.created == []


def test_apply_creates_entity(db):
    code, out = run("--json", json.dumps(PERSON), "--apply")
    assert code == 0 and out["kind"] == "created"
    assert out["data"]["entity_id"].startswith("11111111")
    assert db.created[0]["entity_type"] == "PHYSICAL_PERSON"
    assert db.created[0]["address"] is None


def test_missing_address_is_a_warning_not_a_blocker(db):
    _, out = run("--json", json.dumps(PERSON))
    assert [w["code"] for w in out["data"]["warnings"]] == ["NO_ADDRESS"]


def test_duplicate_identifier_is_refused_even_with_apply(db):
    db.rows.append({"id": "e1", "canonical_label": "X sp. z o.o.", "ids": {("NIP", "5222837149")}})
    company = {"entity_type": "LEGAL_PERSON", "registered_name": "Y sp. z o.o.",
               "identifiers": [{"type": "NIP", "value": "522-283-71-49"}]}
    code, out = run("--json", json.dumps(company), "--apply")
    assert code == ea.EXIT_CONFLICT
    assert out["error"]["code"] == "DUPLICATE_IDENTIFIER"
    assert db.created == []


def test_similar_name_is_reported(db):
    db.rows.append({"id": "e2", "canonical_label": "Jan Nowak", "ids": set()})
    _, out = run("--json", json.dumps(PERSON))
    codes = [w["code"] for w in out["data"]["warnings"]]
    assert "SIMILAR_NAME" in codes


@pytest.mark.parametrize("payload, fragment", [
    ({"entity_type": "PHYSICAL_PERSON", "first_name": "Anna"}, "last_name"),
    ({"entity_type": "LEGAL_PERSON"}, "registered_name"),
    ({"entity_type": "ROBOT", "last_name": "X"}, "entity_type"),
    ({**PERSON, "pesel": "1"}, "Unknown field"),
    ({**PERSON, "registered_name": "X"}, "do not belong"),
    ({**PERSON, "identifiers": [{"type": "NIP", "value": "123"}]}, "wrong length"),
    ({**PERSON, "address": {"street": "Prosta"}}, "city"),
    ({**PERSON, "identifiers": [{"type": "NIP", "value": "5222837148"}]}, "checksum"),
    ({**PERSON, "krs": "0000969547"}, "krs fetches a company"),
    ({"entity_type": "LEGAL_PERSON", "ceidg_nip": "5222837149"}, "ceidg_nip fetches"),
    ({"krs": "0000969547", "ceidg_nip": "5222837149"}, "not both"),
])
def test_bad_input(db, payload, fragment):
    code, out = run("--json", json.dumps(payload))
    assert code == ea.EXIT_BAD_INPUT
    assert fragment in out["error"]["message"]


def test_not_json_object(db):
    code, out = run("--json", "[1, 2]")
    assert code == ea.EXIT_BAD_INPUT


def test_database_down(monkeypatch):
    monkeypatch.setattr(commands, "check_entities_available", lambda: (False, "down"))
    code, out = run("--json", json.dumps(PERSON))
    assert code == ea.EXIT_INFRA and out["error"]["code"] == "DB_UNAVAILABLE"


def test_krs_prefill_caller_fields_win(db, monkeypatch):
    address = SimpleNamespace(to_dict=lambda: {"city": "Warszawa", "street": "Prosta"})
    profile = SimpleNamespace(
        official_name="GORDOS SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ", short_name="GORDOS",
        legal_kind="SPOLKA_Z_OO", legal_form_suffix="sp. z o.o.", legal_form=None,
        krs="0000969547", nip="5273000214", regon="521884850", seat_address=address,
        email=None, website=None, phone=None)
    monkeypatch.setattr(commands, "fetch_and_normalize_krs", lambda krs: (profile, None))
    code, out = run("--json", json.dumps({"krs": "969547", "canonical_label": "GORDOS"}))
    assert code == 0
    entity = out["data"]["entity"]
    assert entity["entity_type"] == "LEGAL_PERSON"
    assert entity["entity_data"]["canonical_label"] == "GORDOS"
    assert {i["type"] for i in entity["identifiers"]} == {"KRS", "NIP", "REGON"}
    assert entity["address"]["address_type"] == "MAIN"
    assert out["data"]["source"] == "KRS"


def test_krs_not_found(db, monkeypatch):
    def missing(krs):
        raise commands.KRSNotFoundError("not found")
    monkeypatch.setattr(commands, "fetch_and_normalize_krs", missing)
    code, out = run("--json", json.dumps({"krs": "0000000001"}))
    assert code == ea.EXIT_BAD_INPUT and out["error"]["code"] == "REGISTRY_NOT_FOUND"


def test_race_duplicate_on_write(db, monkeypatch):
    def dup(**kwargs):
        raise DuplicateIdentifierError("NIP", "5222837149")
    monkeypatch.setattr(commands, "create_entity", dup)
    code, out = run("--json", json.dumps(PERSON), "--apply")
    assert code == ea.EXIT_CONFLICT


def test_entity_type_any_case(db):
    code, out = run("--json", json.dumps({**PERSON, "entity_type": "physical_person"}))
    assert code == 0 and out["data"]["entity"]["entity_type"] == "PHYSICAL_PERSON"


def test_normalize_identifier():
    assert ea.normalize_identifier("krs", "969547") == {"type": "KRS", "value": "0000969547"}
    assert ea.normalize_identifier("NIP", "522 283 71 49")["value"] == "5222837149"
    with pytest.raises(ea.BadInput):
        ea.normalize_identifier("IBAN", "1")
