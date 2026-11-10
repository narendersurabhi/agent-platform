# ADR 0004: LLM gateway passes provider dialects through; agents own model choice

- **Status:** Accepted, 2026-11-10
- **Context:** Agents call Claude (Claude API, Claude Platform on AWS, Bedrock) and, later,
  self-hosted open models (Gemma, Qwen) served by vLLM or SGLang with an OpenAI-compatible
  API. A gateway centralizes credentials, placement, capacity limits and cost accounting.
  Converting between the Anthropic and OpenAI formats loses information (thinking blocks,
  `cache_control`, tool-result shapes, citations, refusal details). deepagents enables
  Anthropic prompt caching only when the model object is a `ChatAnthropic`, and selects
  per-model harness profiles by matching `provider:model`.
- **Decision:**
  1. The gateway serves each dialect natively, without conversion:
     `/anthropic/v1/messages` and `/openai/v1/chat/completions`, plus `GET /v1/models`
     listing each served model with its dialect and capabilities.
  2. The request's `model` field carries the **real model ID**, never a role alias, so
     deepagents' profiles and prompt tuning stay correct.
  3. **Model identity belongs to the agent; placement belongs to the gateway.** The agent
     config (in the orchestrator repo, versioned with prompts and evals) binds each role and
     subagent to a model. The gateway decides where that model runs: provider pool,
     workspace, region or replica, and failover between hosts of the same model. It never
     swaps a request onto a different model; that is an agent-config change gated by evals.
  4. The orchestrator uses `ChatAnthropic(base_url=<gateway>/anthropic)` for Claude and
     `ChatOpenAI(base_url=<gateway>/openai/v1, use_responses_api=False)` for OpenAI-dialect
     models. It holds only a gateway client key; the gateway holds provider credentials.
     At startup it validates its agent config against `/v1/models` and refuses to start if
     a role's model is not served.
  5. Prompt caching stays a client decision. The gateway forwards `cache_control`, system
     blocks, tool order and history byte-faithfully, never injects per-request content into
     the cached prefix, routes a conversation to the same workspace and model (hashing
     `x-agent-thread`), passes `usage` through unchanged and reports cache hit rate. It does
     not add cache markers itself.
  6. Capacity limiting has two adapters: a token bucket for provider quotas that counts only
     uncached input and cache-write tokens (cache reads do not count against Anthropic's
     input limit), estimated before the call and corrected from `usage`; and a concurrency
     limiter for self-hosted replicas (in-flight sequences, KV-cache headroom). Both answer
     `429` with `retry-after`.
  7. Self-hosted model serving is its own deployment (a future `model-serving` repo). The
     gateway only routes to it, with thread affinity because vLLM's prefix cache lives on
     each replica.
- **Consequences:** No lossy conversion layer to maintain; caching and harness profiles keep
  working; a model change is always visible in the agent repo's history. Cost-based model
  downgrades are agent decisions (roles and subagents), not hidden gateway logic. Failover to
  another host lands on a cold cache, so it is a deliberate, metered event.
