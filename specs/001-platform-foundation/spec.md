# Spec 001: Platform foundation

| | |
|---|---|
| **Status** | Implemented |
| **Created** | 2026-11-10 |
| **Plan** | [plan.md](plan.md) · **Tasks** [tasks.md](tasks.md) |
| **PR** | _to be filled in when opened_ |

## Summary
What lets the agent services live in separate repos and still fit together: written
cross-service conventions, decision records, the contract checker that makes "contracts
live in the provider's repo" enforceable, the layer checker for ports and adapters, and a
service template that stamps all of it into a new repo.

## Out of scope
Shared AWS infrastructure (VPC, ECS cluster, collector tier): spec 002. The services
themselves: their own repos.

---

## Functional requirements

### FR-001: Cross-service conventions
- `docs/conventions.md` is versioned and covers, in order: services and ownership,
  contracts, request headers (`traceparent`, `x-agent-identity`, `x-agent-thread`,
  `x-agent-route`, `Idempotency-Key`, `x-agent-deadline`), the error envelope and its
  types, telemetry, code layout and process.
- The error types listed there are exactly the template's domain errors and contract enum.

### FR-002: Decision records
- `docs/adr/NNNN-*.md` are numbered without gaps, each has a status, context, decision and
  consequences, and each is listed in `docs/adr/README.md`.

### FR-003: Service template
- **Given** `copier copy` with a project name and description, **when** the service is
  rendered, **then** it has the ADR 0002 layout and its own suite, ruff, spec coverage,
  layer check and contract check all pass offline, with every name derived from the answers.

### FR-004: Layer check
- `scripts/check_layers.py` reports, with file and line: `domain` importing anything but
  the standard library or `domain`; `application` importing frameworks or the OpenTelemetry
  SDK, exporters or instrumentation (the API is allowed); inbound and outbound adapters
  importing each other; adapters or infrastructure importing the composition root;
  infrastructure importing adapters. A service may allow named pure libraries in
  `application` through `[tool.check-layers] application-allow`.

### FR-005: Contract validation
- `scripts/contract_check.py` rejects an OpenAPI contract that is not valid 3.1, an MCP
  tool definition missing `name`, `description`, `inputSchema` or `version` or carrying an
  invalid JSON Schema, and any version that is not `MAJOR.MINOR.PATCH`. Consumed copies
  under `contracts/consumed/` are validated but never compared.

### FR-006: Contract compatibility
- **Given** a provided contract differs from its copy on `origin/main` (else `main`),
  **then** its version must increase, and if any change is breaking the MAJOR must
  increase. Breaking: a removed path, operation, success response, response header, media
  type or response field; a response field no longer required; a type change; a newly
  required request field, parameter or body; a narrowed request enum or length/size/range
  limit; for MCP tools, a rename or the same rules on `inputSchema` (request) and
  `outputSchema` (response). Additions to responses (fields, enum values) are not breaking
  (tolerant reader). A version bump with no change is flagged.

### FR-007: Opt-in template updates
- A rendered service records its answers and template source in `.copier-answers.yml`, so
  `copier update` can bring later template changes into it when its owners choose.

## Non-functional requirements

### NFR-001: Reproducible environment
- uv-managed interpreter and committed `uv.lock` here and in every rendered service.

### NFR-002: Every requirement is tested
- Each ID here is cited by a test; no test cites an unknown ID.

### NFR-003: Offline tests
- The suite, including rendering and testing a service, needs no network once the uv
  cache is warm.
