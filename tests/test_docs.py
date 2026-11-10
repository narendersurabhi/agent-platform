"""FR-001 / FR-002: the conventions document and the decision records."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CONVENTIONS = (ROOT / "docs" / "conventions.md").read_text()
ADR_DIR = ROOT / "docs" / "adr"

REQUIRED_SECTIONS = [
    "Services and ownership",
    "Contracts",
    "Request headers",
    "Errors",
    "Telemetry",
    "Code layout (ADR 0002)",
    "Process",
]
REQUIRED_HEADERS = [
    "traceparent", "x-agent-identity", "x-agent-thread", "x-agent-route",
    "Idempotency-Key", "x-agent-deadline",
]  # fmt: skip
ERROR_TYPES = [
    "invalid_request", "unauthenticated", "forbidden", "not_found", "conflict",
    "rate_limited", "upstream_error", "unavailable", "timeout", "internal",
]  # fmt: skip


@pytest.mark.spec("FR-001")
def test_conventions_cover_every_shared_concern():
    headings = re.findall(r"(?m)^## (.+)$", CONVENTIONS)
    assert headings[: len(REQUIRED_SECTIONS)] == REQUIRED_SECTIONS
    assert re.search(r"\*\*Version:\*\* \d+\.\d+\.\d+", CONVENTIONS)
    for header in REQUIRED_HEADERS:
        assert f"`{header}" in CONVENTIONS, header


@pytest.mark.spec("FR-001")
def test_error_types_match_the_template():
    """The template's envelope and the conventions must list the same error types."""
    for error_type in ERROR_TYPES:
        assert f"`{error_type}`" in CONVENTIONS, error_type
    errors = (ROOT / "template/src/{{package_name}}/domain/errors.py").read_text()
    assert sorted(re.findall(r'type = "(\w+)"', errors)) == sorted(ERROR_TYPES)
    contract = (ROOT / "template/contracts/openapi.yaml.jinja").read_text()
    for error_type in ERROR_TYPES:
        assert error_type in contract, error_type


@pytest.mark.spec("FR-002")
def test_every_adr_is_indexed_and_well_formed():
    files = sorted(p.name for p in ADR_DIR.glob("[0-9][0-9][0-9][0-9]-*.md"))
    index = (ADR_DIR / "README.md").read_text()
    assert files, "no ADRs"
    numbers = [name[:4] for name in files]
    assert numbers == [f"{i:04d}" for i in range(1, len(files) + 1)], "ADR numbers have gaps"
    for name in files:
        assert f"]({name})" in index, f"{name} missing from docs/adr/README.md"
        text = (ADR_DIR / name).read_text()
        assert text.startswith(f"# ADR {name[:4]}: ")
        assert re.search(r"\*\*Status:\*\* (Accepted|Proposed|Superseded by \d{4})", text)
        for part in ("**Context:**", "**Decision:**", "**Consequences:**"):
            assert part in text, (name, part)
