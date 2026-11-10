# Cross-service conventions

These are the only things the agent services share. Everything else (code, data, release
cadence) belongs to one repo. A service may do more than this document asks, never less.
Changing a convention is an ADR plus a version bump of this file, and every service adopts
it on its own schedule.

**Version:** 1.0.0

## Services and ownership

| Service | Repo | Owns | Provides |
|---|---|---|---|
| Orchestrator | `deepagents-deploy` | runs, threads, checkpoints, the run queue | `POST /v1/runs`, run events |
| LLM gateway | `llm-gateway` | provider credentials, placement, capacity limits, usage ledger | `/anthropic/v1/messages`, `/openai/v1/chat/completions`, `/v1/models` |
| Retrieval | `retrieval-service` | the index, embedding-model version, access filtering | MCP `search`, ingest API |
| Ingestion | `docling-pipeline` | parsing and chunking | nothing: a consumer of the ingest API |

A service never reads or writes another service's data store.

## Contracts

- A provider's contract lives in its own repo: `contracts/openapi.yaml` (OpenAPI 3.1,
  version in `info.version`) and `contracts/mcp/<tool>.json` (MCP tool definitions with a
  top-level `version`).
- Versions are semver. A **breaking** change (a consumer's valid request becomes invalid,
  or something in a response disappears or changes type) bumps MAJOR, and the old major
  stays served (for example `/v1` beside `/v2`) until its consumers have moved. Any other
  change bumps MINOR or PATCH. `scripts/contract_check.py` enforces this in the commit hook.
- A consumer pins a copy under `contracts/consumed/<provider>/` at a released version and
  tests its outbound adapter against that copy. Upgrading the pin is a normal change in
  the consumer's repo.
- **Tolerant reader:** consumers ignore unknown response fields, unknown enum values and
  unknown headers. Providers rely on this to add things without a MAJOR bump.

## Request headers

| Header | Set by | Meaning |
|---|---|---|
| `traceparent`, `tracestate` | every caller | W3C trace context. Every call and every queue message carries it. |
| `x-agent-identity` | API tier, forwarded unchanged | Signed JWT naming the end user and tenant (`sub`, `tenant`, `groups`, `exp`). Services authorize from it, never from request bodies or tool arguments. |
| `Authorization: Bearer` / `x-api-key` | calling service | Service-to-service credential. Says *which service* is calling, not which user. |
| `x-agent-thread` | orchestrator | Conversation ID. Used for sticky routing (cache affinity), never for authorization. |
| `x-agent-route` | orchestrator | `interactive` or `background`: priority and queueing class. |
| `Idempotency-Key` | caller of any side-effecting operation | `<run_id>:<tool_call_id>` or another stable key. A provider returns the original result for a repeated key. |
| `x-agent-deadline` | every caller | RFC 3339 instant after which the caller no longer wants the result. Providers stop work and return `504`. Propagated, shortened by each hop. |

Queue messages carry the same fields as message attributes.

## Errors

Every non-2xx JSON response uses one envelope (gateway dialect endpoints keep their
provider's native error shape, because the SDKs parse it):

```json
{"error": {"type": "invalid_request", "message": "human-readable, no secrets or user content"},
 "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"}
```

`type` is one of `invalid_request` (400/422), `unauthenticated` (401), `forbidden` (403),
`not_found` (404), `conflict` (409), `rate_limited` (429, with `retry-after`),
`upstream_error` (502), `unavailable` (503, with `retry-after`), `timeout` (504),
`internal` (500). Messages never contain exception text, prompts or document content.

## Telemetry

- OpenTelemetry for traces, logs and metrics; exporters `none` / `console` / `otlp` chosen
  by the standard `OTEL_*_EXPORTER` variables; `OTEL_SERVICE_NAME` is the repo name.
- Resource attributes: `service.name`, `service.version`, `deployment.environment.name`.
- Logs are JSON lines carrying `trace_id` and `span_id`, also exported over OTLP.
- Metric names use OpenTelemetry semantic conventions where they exist
  (`http.server.request.duration`, `gen_ai.client.operation.duration`,
  `gen_ai.client.token.usage`), otherwise `<service-area>.<noun>` (`retrieval.search.duration`).
  Units are UCUM (`s`, `By`, `{token}`); histograms use explicit buckets matching the unit.
- Metric attributes come from a per-service allow-list of bounded values: never user IDs,
  thread IDs, paths, queries or document IDs. Those may go on spans.
- No conversation content, document text, queries, tool arguments or exception messages in
  any signal. Exceptions are recorded by type and stack frames.
- Telemetry failures never fail a request.

## Code layout (ADR 0002)

Every service follows ports and adapters:

```
src/<package>/
  domain/          pure Python: entities, value objects, domain errors
  application/     use cases and ports (typing.Protocol)
  adapters/        inbound/<transport>/ and outbound/<dependency>/
  infrastructure/  settings, telemetry setup
  bootstrap.py     the composition root: the only place adapters are chosen
```

`domain` imports nothing outside the standard library. `application` imports `domain` and
the OpenTelemetry *API*. Only `adapters`, `infrastructure` and `bootstrap` import frameworks.
`scripts/check_layers.py` enforces this in the commit hook (it also tells the OpenTelemetry API apart from the SDK, which a package-level linter cannot).

## Process

Each repo follows the spec-driven process stamped from the template: specs in
`specs/NNN-name/`, `spec/NNN-name` branches, requirement IDs cited by tests, local git hooks
as the only gate, a protected `main`.
