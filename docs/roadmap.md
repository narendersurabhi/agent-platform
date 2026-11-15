# Roadmap

What each repo takes next. Each line becomes a spec in that repo. Order matters where noted.

| Repo | Next | Summary |
|---|---|---|
| agent-platform | 002-shared-infra | VPC, ECS cluster, **EKS cluster for the gateway on Graviton EC2 nodes: evaluate EKS Auto Mode first, managed node groups as the fallback** (ADR 0006), Redis for gateway limits, internal load balancer between ECS and EKS, OTel collector tier with tail sampling (all errors and slow traces, a few % of the rest); outputs published to SSM `/agents/<env>/…` |
| llm-gateway | 001-service-skeleton | Template skeleton plus contract v0.1.0 (ADR 0004 endpoints and headers) |
| llm-gateway | 002-envoy-gateway | Envoy AI Gateway (ADR 0006): pinned Helm installs, Gateway/route/backend/policy config with kind and EKS overlays, offline validation of manifests and CEL costs in the hooks, the spike's acceptance suite promoted to `tests/acceptance/` and required before any upgrade, contract v1.0.0 (Envoy paths, `/v1/models` IDs only) |
| llm-gateway | 003-usage-ledger | Cumulative per-tenant spend and budgets from Envoy's per-request access logs (Python, ports and adapters) |
| retrieval-service | 001-service-skeleton | Template skeleton plus contracts: MCP `search` v0.1.0 and ingest API v0.1.0 (ADR 0005) |
| retrieval-service | 002-search-and-ingest | Embedder, vector index and reranker ports with adapters; access filtering from `x-agent-identity`; token-budgeted results; atomic per-document-version ingest; recall@k evaluation set |
| docling-pipeline | 005-retrieval-ingest | `ChunkSink` port; an adapter that sends chunks to retrieval's ingest API (pinned contract), idempotent per document version |
| deepagents-deploy | after PR #1 merges: `chore/hexagonal-layout` | ADR 0002 refactor, behaviour unchanged: `AgentEngine` port, `RunAgent` use case owning input and auth policy, single composition root, telemetry split API/SDK |
| deepagents-deploy | 002-gateway-and-model-roles | Agent config binding each role and subagent to a real model ID; `ChatAnthropic` / `ChatOpenAI(use_responses_api=False)` pointed at the gateway with a gateway client key; startup validation against `/v1/models`; cache read/write token metrics; deterministic tool order; model name taken per call in the callback handler; a regression test that captures the outgoing request and asserts deepagents' three cache markers |
| deepagents-deploy | 003-durable-state-and-identity | Postgres checkpointer; JWT end-user identity from `x-agent-identity`; threads owned by a user |
| deepagents-deploy | 004-async-runs | Run queue (SQS FIFO by thread), worker inbound adapter, SSE progress, per-user quotas, suspend/resume for slow tools |
| deepagents-deploy | 005-retrieval-tool | MCP client for retrieval `search` against the pinned contract |
| new: model-serving | when a self-hosted model is chosen | vLLM/SGLang on GPU nodes, prefix caching, autoscaling on queue depth and KV-cache headroom |
| new: sandbox-service | when `execute` is needed | isolated code execution behind a deepagents sandbox backend |
