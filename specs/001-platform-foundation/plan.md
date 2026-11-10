# Plan 001: Platform foundation

Implements [spec.md](spec.md). Checked against [constitution](../constitution.md).

## Modules
| Path | Responsibility | Requirements |
|---|---|---|
| `docs/conventions.md` | the only shared rules between services | FR-001 |
| `docs/adr/` | decisions 0001–0005 from the design discussion | FR-002 |
| `docs/roadmap.md` | which spec each repo takes next | — |
| `scripts/check_layers.py` | AST import check for ADR 0002 | FR-004 |
| `scripts/contract_check.py` | OpenAPI / MCP validation, semver, breaking-change diff | FR-005, FR-006 |
| `copier.yml`, `template/` | the service template; `template/scripts/*` are symlinks to `scripts/` so there is one copy | FR-003, FR-007 |

## Key decisions
- **A template, not a shared library.** Conventions are stamped into each repo and updated
  with `copier update` when a repo chooses; no package forces every service to upgrade
  together.
- **Own layer checker instead of import-linter.** import-linter treats `opentelemetry` as one
  package, so it can't allow the API while forbidding the SDK, and can't express "standard
  library only" for `domain`. The AST checker is ~150 lines and tested.
- **Own breaking-change diff instead of oasdiff.** oasdiff is a Go binary outside the uv
  toolchain. The checker covers the rules in FR-006 over local `$ref`s; providers with
  exotic schemas (`oneOf` unions, external refs) should add cases before relying on it.
- **Stable HTTP semantic conventions in the template.** The FastAPI instrumentation's legacy
  default records `http.host` and `http.server_name` from the client's Host header, which is
  unbounded. The template opts into the stable conventions (`http.server.request.duration`);
  the test that found this asserts the legacy metric is absent.

## Constitution check
- [x] I–III spec first, tested, permanent IDs
- [x] IV no secrets; the template's error envelope never echoes input or exception text
- [x] V locked environments
- [x] VI template asserts spans, logs and metrics
- [x] VII offline tests

## Risks
- The breaking-change rules are a deliberate subset; a change they miss reaches consumers
  as a runtime failure. Consumers' pinned-contract tests are the second line of defence.
- Rendering in the test suite depends on a warm uv cache.
