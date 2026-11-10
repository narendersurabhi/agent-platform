# Roadmap

What each repo takes next. Each line becomes a spec in that repo. Order matters where noted.

| Repo | Next | Summary |
|---|---|---|
| agent-platform | 002-shared-infra | VPC, ECS cluster, ALB, OTel collector tier with tail sampling (all errors and slow traces, a few % of the rest); outputs published to SSM `/agents/<env>/…` |
| llm-gateway | 001-service-skeleton | Template skeleton plus contract v0.1.0 (ADR 0004 endpoints and headers) |
| llm-gateway | 002-dialect-passthrough | Native `/anthropic/v1/messages` and `/openai/v1/chat/completions` forwarding, byte-faithful for `cache_control`, system blocks, tool order and history; `/v1/models` discovery; placement table with thread affinity; token-bucket limiter counting only uncached input and cache writes (estimate, then correct from `usage`); concurrency limiter for self-hosted replicas; `usage` passed through; cache hit-rate and per-provider metrics; provider credentials held here only |
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
