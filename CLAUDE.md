# CLAUDE.md

`agent-platform`: conventions, ADRs, the contract and layer checkers, and the copier service
template for the agent services. Read `specs/constitution.md` first.

## Rules

- Same process as every repo: `spec/NNN-name` branches, never commit to `main`, hooks are
  the gate (no `--no-verify`), tests cite requirement IDs, `branch_policy.py --ready` before
  a PR.
- **Conventions change by ADR** (constitution IV): edit `docs/conventions.md` only together
  with a new ADR and a version bump of the document.
- **The template must stay green** (V): `tests/test_template.py` renders it and runs the new
  service's suite, ruff, coverage, layers and contract check. Run the full suite after any
  template change.
- `template/scripts/*.py` are symlinks to `scripts/`: edit the files in `scripts/`.
- Template files ending in `.jinja` are rendered; others are copied verbatim. Use relative
  imports inside the package so most files need no template variables. Ruff skips
  `template/` here; the render test lints the rendered result instead.

## Commands

```bash
uv sync && uv run pre-commit install
uv run pytest
uv run copier copy --trust --vcs-ref HEAD . /tmp/demo   # try the template by hand
```
