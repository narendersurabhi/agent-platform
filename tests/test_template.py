"""FR-003 / FR-004 / FR-007: the service template renders a working hexagonal service.

Renders with copier into a temp dir and runs the new service's own gates there: its test
suite, ruff, the layer check and spec coverage. Everything runs with uv's offline mode from
the local cache (NFR-003); run `uv sync` in a rendered service once online to warm it.
"""

import os
import subprocess
from pathlib import Path

import pytest
import yaml
from copier import run_copy

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def service(tmp_path_factory) -> Path:
    dst = tmp_path_factory.mktemp("render") / "demo-service"
    run_copy(
        str(ROOT),
        dst,
        data={"project_name": "demo-service", "description": "A demo service."},
        defaults=True,
        unsafe=True,
        vcs_ref="HEAD",
        quiet=True,
    )
    return dst


def run(service: Path, *cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("VIRTUAL_ENV", "OTEL_"))}
    env |= {"UV_OFFLINE": "1", "UV_NO_PROGRESS": "1"}
    proc = subprocess.run(["uv", "run", "--offline", *cmd], cwd=service, env=env,
                          capture_output=True, text=True, timeout=600)  # fmt: skip
    if check:
        assert proc.returncode == 0, (
            f"{' '.join(cmd)}\n{proc.stdout[-4000:]}\n{proc.stderr[-4000:]}"
        )
    return proc


@pytest.mark.spec("FR-003", "NFR-003")
def test_rendered_service_passes_its_own_suite(service):
    out = run(service, "pytest", "-q", "-p", "no:cacheprovider").stdout
    assert " passed" in out and "failed" not in out


@pytest.mark.spec("FR-003")
def test_rendered_service_is_lint_clean_and_traced(service):
    run(service, "ruff", "check", ".")
    run(service, "ruff", "format", "--check", ".")
    coverage = run(service, "python", "scripts/spec_coverage.py").stdout
    assert "Uncovered" not in coverage
    run(service, "python", "scripts/contract_check.py")


@pytest.mark.spec("FR-003")
def test_rendered_layout_and_names(service):
    pkg = service / "src" / "demo_service"
    layout = [
        "domain/errors.py", "application/ports.py", "application/health.py",
        "adapters/inbound/http/app.py", "adapters/outbound/system_clock.py",
        "infrastructure/settings.py", "infrastructure/telemetry.py", "bootstrap.py",
    ]  # fmt: skip
    for rel in layout:
        assert (pkg / rel).is_file(), rel
    for script in ("branch_policy.py", "spec_coverage.py", "contract_check.py", "check_layers.py"):
        path = service / "scripts" / script
        assert path.is_file() and not path.is_symlink(), script
    assert 'ENV_PREFIX = "DEMO_SERVICE_"' in (pkg / "__init__.py").read_text()
    assert 'CMD ["demo-service"]' in (service / "Dockerfile").read_text()
    contract = yaml.safe_load((service / "contracts" / "openapi.yaml").read_text())
    assert contract["info"] == {"title": "demo-service", "version": "0.1.0",
                                "description": "A demo service."}  # fmt: skip


@pytest.mark.spec("FR-004")
def test_rendered_layer_check_catches_violations(service):
    run(service, "python", "scripts/check_layers.py")
    bad = service / "src" / "demo_service" / "domain" / "leak.py"
    bad.write_text("import fastapi\n")
    try:
        proc = run(service, "python", "scripts/check_layers.py", check=False)
    finally:
        bad.unlink()
    assert proc.returncode == 1 and "domain may only import the standard library" in proc.stderr


@pytest.mark.spec("FR-007")
def test_answers_are_recorded_for_updates(service):
    answers = yaml.safe_load((service / ".copier-answers.yml").read_text())
    assert answers["project_name"] == "demo-service"
    assert answers["package_name"] == "demo_service"
    assert answers["_src_path"]
