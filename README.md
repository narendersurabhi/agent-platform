# agent-platform

Shared ground for the agent services, which otherwise live and ship independently:

- **[docs/conventions.md](docs/conventions.md):** the only rules services share: ownership,
  contracts, request headers (trace context, identity, idempotency, deadlines), the error
  envelope, telemetry and code layout.
- **[docs/adr/](docs/adr/README.md):** the decisions behind the split, the ports-and-adapters
  layout, contracts, the LLM gateway and retrieval.
- **[docs/roadmap.md](docs/roadmap.md):** which spec each repo takes next.
- **The service template** (`copier.yml`, `template/`): a hexagonal FastAPI service with
  OpenTelemetry, the error envelope, a versioned OpenAPI contract, Docker, compose with
  Grafana LGTM, the spec-driven process and local git hooks.
- **[scripts/contract_check.py](scripts/contract_check.py)** and
  **[scripts/check_layers.py](scripts/check_layers.py):** the checks every service runs in
  its commit hook (copied in by the template).

| Service | Repo |
|---|---|
| Orchestrator (deepagents) | [deepagents-deploy](https://github.com/narendersurabhi/deepagents-deploy) |
| LLM gateway | [llm-gateway](https://github.com/narendersurabhi/llm-gateway) |
| Retrieval | [retrieval-service](https://github.com/narendersurabhi/retrieval-service) |
| Ingestion | [docling-pipeline](https://github.com/narendersurabhi/docling-pipeline) |

## Create a service

```bash
uvx copier copy --trust gh:narendersurabhi/agent-platform my-service
cd my-service && git init -b main && uv sync && uv run pre-commit install
uv run pytest
```

Later template changes reach a service only when its owners run `uvx copier update --trust`.

## Develop this repo

```bash
uv sync && uv run pre-commit install
uv run pytest        # includes rendering the template and running the new service's gates
```

Spec-driven like every repo here: [specs/constitution.md](specs/constitution.md),
[specs/README.md](specs/README.md).
