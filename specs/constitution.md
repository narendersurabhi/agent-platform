# Project Constitution

These principles govern every change to `agent-platform`. Its output is what other repos
copy (the template) or follow (conventions, ADRs), so a change here is a change to every
service the next time it updates.

## I. Spec first
Behaviour is defined in `specs/NNN-feature/spec.md` before it is implemented.

## II. Every requirement is testable and tested
`FR-###` / `NFR-###` IDs with Given/When/Then criteria, each cited by a test via
`@pytest.mark.spec(...)`; enforced by `tests/test_spec_traceability.py`.

## III. Requirement IDs are permanent
Never renumbered or reused; withdrawn ones stay, struck through.

## IV. Conventions change by ADR
A change to `docs/conventions.md` comes with an ADR and a version bump of the document.
ADRs are never edited to reverse a decision; a new ADR supersedes the old one.

## V. The template must stay green
The template is tested by rendering it and running the new service's own gates
(tests, lint, coverage, layers, contracts). A template change that breaks a fresh service
does not merge.

## VI. Reproducible, offline
uv-managed interpreter, committed `uv.lock`, tests offline once the uv cache is warm.

## VII. One feature, one branch
`spec/NNN-short-name` branches, PRs into a protected `main`, local git hooks as the only
gate, never `--no-verify`, `scripts/branch_policy.py --ready` before a PR.
