# ADR 0005: Retrieval is a service, not an in-process tool

- **Status:** Accepted, 2026-11-10
- **Context:** In-process retrieval is the right default for one agent, one shared corpus,
  API embeddings and modest volume. At the target load several triggers apply at once:
  per-user document access must be enforced where the model cannot influence it; retrieval
  load per run varies far more than run count (and in-process connection pools multiply
  with worker count); the query-time embedding model must match the one that built the
  index; and retrieved text is the largest share of input tokens, so its size needs
  central control.
- **Decision:** `retrieval-service` owns the index, the embedding-model version, reranking
  and access filtering. Agents reach it through an MCP `search` tool whose arguments are only
  the query, `k` and an optional collection; the caller's identity comes from
  `x-agent-identity`, never from tool arguments. Results carry chunk IDs and sources for
  citations and are trimmed to a token budget. Ingestion (`docling-pipeline`) writes only
  through the service's ingest API, which replaces a document's chunks atomically per
  document version, so the service can re-embed and swap indexes blue/green.
- **Consequences:** One place for relevance work, evaluation (recall@k on a fixed query set)
  and token-budget control; a network hop per search (tens of milliseconds). Small
  deployments may still run the service with a single replica.
