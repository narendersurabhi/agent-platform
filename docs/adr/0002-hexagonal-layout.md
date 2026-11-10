# ADR 0002: Ports and adapters inside every service

- **Status:** Accepted, 2026-11-10
- **Context:** The first orchestrator was layered by technology. Its use case called LangGraph
  directly, persistence was fixed inside the engine factory, input policy and authentication
  lived only in the HTTP layer, and wiring was spread over three modules. A second inbound
  transport (a queue worker) or a new store (Postgres checkpoints) would have meant editing
  the core.
- **Decision:** Every service uses `domain/`, `application/` (use cases and `Protocol` ports),
  `adapters/inbound|outbound/`, `infrastructure/` and a single `bootstrap.py` composition
  root. `scripts/check_layers.py` (an AST check, in the commit hook) keeps frameworks out of `domain` and
  `application`. Frameworks that already define fine-grained ports (LangChain's chat model and
  tool interfaces, deepagents' backend, LangGraph's checkpointer) are used inside an adapter
  as they are, not wrapped again: the orchestrator has one coarse `AgentEngine` port, and the
  LLM gateway, retrieval tool, sandbox and Postgres plug into the framework's own ports at the
  composition root. The OpenTelemetry API is allowed in `application` (it is already a
  no-op-by-default facade); SDK and exporter setup is infrastructure.
- **Consequences:** Use cases are tested with in-memory fakes, adapters with contract tests,
  and only a thin end-to-end layer needs the whole stack. New transports and stores are new
  adapters. The cost is a few more modules per service.
