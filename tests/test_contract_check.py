"""FR-005 / FR-006: contract validation, semver and breaking-change rules (ADR 0003)."""

import copy
import json
import subprocess

import contract_check as cc
import pytest
import yaml

API = {
    "openapi": "3.1.0",
    "info": {"title": "svc", "version": "1.2.0"},
    "paths": {
        "/v1/items/{id}": {
            "parameters": [
                {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
            ],  # fmt: skip
            "get": {
                "operationId": "getItem",
                "parameters": [{"name": "fields", "in": "query", "schema": {"type": "string"}}],
                "responses": {
                    "200": {
                        "description": "ok",
                        "headers": {"etag": {"schema": {"type": "string"}}},
                        "content": {
                            "application/json": {"schema": {"$ref": "#/components/schemas/Item"}}
                        },  # fmt: skip
                    }
                },
            },
            "put": {
                "operationId": "putItem",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["name"],
                                "properties": {
                                    "name": {"type": "string", "maxLength": 100},
                                    "kind": {"type": "string", "enum": ["a", "b"]},
                                    "tags": {"type": "array", "items": {"type": "string"}},
                                },
                            }
                        }
                    },  # fmt: skip
                },
                "responses": {"204": {"description": "stored"}},
            },
        }
    },
    "components": {
        "schemas": {
            "Item": {
                "type": "object",
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "status": {"type": "string", "enum": ["active", "archived"]},
                },
            }
        }
    },
}
PATH = "/v1/items/{id}"


def check(new: dict, base: dict | None = API, rel: str = "contracts/openapi.yaml") -> list[str]:
    return cc.check_contract(rel, yaml.safe_dump(new), yaml.safe_dump(base) if base else None)


def changed(version: str, mutate) -> dict:
    doc = copy.deepcopy(API)
    mutate(doc)
    doc["info"]["version"] = version
    return doc


# --- FR-005: validity and semver ------------------------------------------------------------


@pytest.mark.spec("FR-005")
def test_new_valid_contract_passes():
    assert check(API, base=None) == []


@pytest.mark.spec("FR-005")
@pytest.mark.parametrize("version", ["1.2", "v1.2.0", "01.2.0", None])
def test_version_must_be_semver(version):
    doc = copy.deepcopy(API)
    doc["info"]["version"] = version
    assert any("MAJOR.MINOR.PATCH" in p or "invalid" in p for p in check(doc, base=None))


@pytest.mark.spec("FR-005")
def test_invalid_openapi_rejected():
    doc = copy.deepcopy(API)
    doc["paths"][PATH]["get"]["responses"] = "not-a-mapping"
    assert any("invalid OpenAPI" in p for p in check(doc, base=None))
    doc = copy.deepcopy(API)
    doc["openapi"] = "3.0.3"
    assert any("3.1" in p for p in check(doc, base=None))


@pytest.mark.spec("FR-005")
def test_mcp_tool_definition_validated():
    tool = {"name": "search", "description": "d", "version": "0.1.0",
            "inputSchema": {"type": "object", "properties": {"q": {"type": "strin"}}}}  # fmt: skip
    problems = cc.check_contract("contracts/mcp/search.json", json.dumps(tool), None)
    assert any("not a valid JSON Schema" in p for p in problems)
    del tool["inputSchema"]
    problems = cc.check_contract("contracts/mcp/search.json", json.dumps(tool), None)
    assert any("lacks 'inputSchema'" in p for p in problems)


@pytest.mark.spec("FR-005")
def test_consumed_copies_are_validated_but_never_diffed():
    doc = changed("1.2.0", lambda d: d["paths"].pop(PATH))  # breaking, same version
    rel = "contracts/consumed/provider/openapi.yaml"
    assert check(doc, rel=rel) == []
    assert cc.kind_of(rel) is cc.OPENAPI


# --- FR-006: compatibility and version bumps ------------------------------------------------


@pytest.mark.spec("FR-006")
def test_unchanged_contract_passes():
    assert check(copy.deepcopy(API)) == []


@pytest.mark.spec("FR-006")
def test_version_bump_without_changes_is_flagged():
    assert any("without changes" in p for p in check(changed("1.2.1", lambda d: None)))


@pytest.mark.spec("FR-006")
def test_additive_change_needs_a_bump():
    def add_field(d):
        d["components"]["schemas"]["Item"]["properties"]["color"] = {"type": "string"}

    assert any("not above" in p for p in check(changed("1.2.0", add_field)))
    assert check(changed("1.3.0", add_field)) == []


BREAKING = {
    "path removed": lambda d: d["paths"].pop(PATH),
    "operation removed": lambda d: d["paths"][PATH].pop("put"),
    "response field removed (via $ref)": lambda d: (
        d["components"]["schemas"]["Item"]["properties"].pop("status")),
    "response field no longer guaranteed": lambda d: (
        d["components"]["schemas"]["Item"]["required"].remove("name")),
    "response type changed": lambda d: d["components"]["schemas"]["Item"]["properties"][
        "id"].update(type="integer"),
    "response header removed": lambda d: d["paths"][PATH]["get"]["responses"]["200"].pop("headers"),
    "success response removed": lambda d: d["paths"][PATH]["put"]["responses"].update(
        {"200": {"description": "ok"}}) or d["paths"][PATH]["put"]["responses"].pop("204"),
    "request field newly required": lambda d: d["paths"][PATH]["put"]["requestBody"]["content"][
        "application/json"]["schema"]["required"].append("kind"),
    "request enum narrowed": lambda d: d["paths"][PATH]["put"]["requestBody"]["content"][
        "application/json"]["schema"]["properties"]["kind"].update(enum=["a"]),
    "request maxLength narrowed": lambda d: d["paths"][PATH]["put"]["requestBody"]["content"][
        "application/json"]["schema"]["properties"]["name"].update(maxLength=10),
    "request array items type changed": lambda d: d["paths"][PATH]["put"]["requestBody"][
        "content"]["application/json"]["schema"]["properties"]["tags"]["items"].update(
        type="integer"),
    "query parameter newly required": lambda d: d["paths"][PATH]["get"]["parameters"][0].update(
        required=True),
    "media type removed": lambda d: d["paths"][PATH]["put"]["requestBody"].update(
        content={"text/plain": {"schema": {"type": "string"}}}),
}  # fmt: skip


@pytest.mark.spec("FR-006")
@pytest.mark.parametrize("mutate", BREAKING.values(), ids=BREAKING.keys())
def test_breaking_changes_need_a_major_bump(mutate):
    minor = check(changed("1.3.0", mutate))
    assert any("MAJOR" in p for p in minor), minor
    assert any(p.startswith("contracts/openapi.yaml: breaking:") for p in minor)
    assert check(changed("2.0.0", mutate)) == []


NON_BREAKING = {
    "new path": lambda d: d["paths"].update({"/v1/other": {"get": {
        "operationId": "other", "responses": {"200": {"description": "ok"}}}}}),
    "new optional request field": lambda d: d["paths"][PATH]["put"]["requestBody"]["content"][
        "application/json"]["schema"]["properties"].update(note={"type": "string"}),
    "new response enum value (tolerant reader)": lambda d: d["components"]["schemas"]["Item"][
        "properties"]["status"].update(enum=["active", "archived", "deleted"]),
    "request enum widened": lambda d: d["paths"][PATH]["put"]["requestBody"]["content"][
        "application/json"]["schema"]["properties"]["kind"].update(enum=["a", "b", "c"]),
    "request maxLength relaxed": lambda d: d["paths"][PATH]["put"]["requestBody"]["content"][
        "application/json"]["schema"]["properties"]["name"].update(maxLength=500),
    "new error response": lambda d: d["paths"][PATH]["get"]["responses"].update(
        {"404": {"description": "missing"}}),
}  # fmt: skip


@pytest.mark.spec("FR-006")
@pytest.mark.parametrize("mutate", NON_BREAKING.values(), ids=NON_BREAKING.keys())
def test_additive_changes_are_not_breaking(mutate):
    assert check(changed("1.3.0", mutate)) == []


@pytest.mark.spec("FR-006")
def test_mcp_tool_compatibility():
    tool = {"name": "search", "description": "Search", "version": "1.0.0",
            "inputSchema": {"type": "object", "required": ["query"],
                            "properties": {"query": {"type": "string"},
                                           "k": {"type": "integer", "maximum": 50}}},
            "outputSchema": {"type": "object", "required": ["results"],
                             "properties": {"results": {"type": "array"},
                                            "truncated": {"type": "boolean"}}}}  # fmt: skip
    base = json.dumps(tool)
    rel = "contracts/mcp/search.json"

    def variant(version, mutate):
        doc = copy.deepcopy(tool)
        mutate(doc)
        doc["version"] = version
        return json.dumps(doc)

    narrowed = variant("1.1.0", lambda d: d["inputSchema"]["properties"]["k"].update(maximum=10))
    assert any("MAJOR" in p for p in cc.check_contract(rel, narrowed, base))
    dropped = variant("1.1.0", lambda d: d["outputSchema"]["properties"].pop("truncated"))
    assert any("MAJOR" in p for p in cc.check_contract(rel, dropped, base))
    renamed = variant("2.0.0", lambda d: d.update(name="find"))
    assert cc.check_contract(rel, renamed, base) == []
    added = variant("1.1.0", lambda d: d["inputSchema"]["properties"].update(
        collection={"type": "string"}))  # fmt: skip
    assert cc.check_contract(rel, added, base) == []


@pytest.mark.spec("FR-006")
def test_main_compares_against_main_branch(tmp_path):
    repo = tmp_path / "svc"
    (repo / "contracts").mkdir(parents=True)
    contract = repo / "contracts" / "openapi.yaml"
    contract.write_text(yaml.safe_dump(API))
    git = ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t",
           "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null"]  # fmt: skip
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    subprocess.run([*git, "add", "."], check=True)
    subprocess.run([*git, "commit", "-q", "-m", "v1"], check=True)
    subprocess.run([*git, "switch", "-q", "-c", "spec/002-x"], check=True)

    assert cc.main(["--root", str(repo)]) == 0
    contract.write_text(yaml.safe_dump(changed("1.3.0", BREAKING["path removed"])))
    assert cc.main(["--root", str(repo)]) == 1
    contract.write_text(yaml.safe_dump(changed("2.0.0", BREAKING["path removed"])))
    assert cc.main(["--root", str(repo)]) == 0
