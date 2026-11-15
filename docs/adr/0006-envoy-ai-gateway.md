# ADR 0006: Build the LLM gateway on Envoy AI Gateway, on Kubernetes

- **Status:** Accepted, 2026-11-14
- **Context:** ADR 0004 set what the gateway must do: pass each provider dialect through
  unchanged, keep model choice with the agent, preserve prompt caching, keep a conversation on
  one placement, count only uncached input against quotas, hold provider credentials, and
  record usage without content. Before writing it ourselves we evaluated off-the-shelf gateways
  against those requirements as 14 black-box acceptance checks, with WireMock standing in for
  the providers (llm-gateway, branch `chore/gateway-framework-spike`, `spikes/README.md`):

  | | Envoy AI Gateway 1.2.0 on Kubernetes | LiteLLM 1.106.6 + Postgres + Redis | Envoy AI Gateway 1.2.0 standalone (`aigw run`) |
  |---|---|---|---|
  | Checks passed | **13 / 14** (all functional) | 9 / 14 | 8 / 12 |
  | Body forwarded byte for byte | ✓ | re-serialized (content intact) | ✓ |
  | Failover keeps the model | ✓ | ✗ a 500 on the first failover | ✓ |
  | Per-request usage record without content | ✓ access log: client, thread, model, tokens, cost | ✗ per-request spend logs incomplete (per-key totals complete) | — |
  | Budgets | per-window, cost-weighted per client | cumulative per key, built in | — |
  | Added latency in-cluster, 1 connection | +1.5 ms p50 | +13.8 ms p50 | — |
  | Throughput, 16 connections, laptop | 563 req/s per pod | 51 req/s per worker (~700 MiB each) | — |

  Standalone mode lacks client API-key auth, header consistent hashing and global rate
  limiting, and sent the first backend's credential to the second backend of a route; these
  were reported upstream (theagentrouter/agent-router#3015, #3016, and a private security
  advisory). None of them reproduce on Kubernetes.
- **Decision:**
  1. `llm-gateway` runs **Envoy AI Gateway on Envoy Gateway, on Kubernetes**, installed from the
     projects' Helm charts at pinned versions. The repo holds configuration (Gateway, routes,
     backends, security and traffic policies), deployment overlays, and the acceptance suite;
     it does not implement forwarding, limits or auth itself.
  2. **Target: Amazon EKS on EC2 (Graviton) nodes**, one cluster for the gateway and, later,
     self-hosted model serving (llm-d needs Kubernetes too). How the nodes are managed is
     evaluated in agent-platform spec 002: **EKS Auto Mode first** (AWS provisions, patches
     and scales the EC2 nodes; a management fee of roughly 12% of the On-Demand price), with
     EKS managed node groups as the fallback. Other services may stay on ECS and reach the
     gateway through an internal load balancer in the same VPC.
  2a. **Considered and rejected for now:**
     - *EKS on Fargate:* no Arm (Graviton), no GPUs, no DaemonSets, no Fargate Spot on EKS;
       GPU serving would need EC2 nodes anyway, so the cluster would mix two compute models.
     - *Envoy AI Gateway directly on EC2 or ECS (`aigw run`, no Kubernetes):* this is the
       standalone mode the spike tested (8/12): no client API-key auth, no header consistent
       hashing, no global rate limiting, and one backend's credential sent to another.
       Revisit when those upstream issues are fixed; `spikes/run_spike.sh envoy` re-tests it.
     - *Hand-built Envoy plus the AI Gateway external processor on ECS, without Envoy
       Gateway:* possible in principle, but we would generate and maintain Envoy's raw
       configuration ourselves and lose the policy APIs (security, traffic, rate limits) that
       the acceptance suite relies on. That is custom integration code the evaluation was
       meant to avoid.
     - *LiteLLM on ECS:* runs without Kubernetes, but scored 9/14 (see Context).
  3. **The acceptance suite is the contract with the framework.** Any gateway, Envoy Gateway or
     AI Gateway upgrade must pass it on a pinned kind cluster before rollout, because the
     guarantees we rely on (byte-exact bodies, `usage` untouched, per-backend credentials,
     no content in traces) come from the framework's behaviour, not our code.
  4. **Configuration is validated before it is applied.** An invalid CEL cost expression was
     accepted by the API server and then failed every request, so the repo's hooks must
     validate CEL and manifests offline.
  5. **Cumulative spend and budgets are ours.** Envoy gives per-request usage in access logs
     and per-window budgets through cost-weighted rate limits; cumulative per-tenant spend and
     budgets are a small usage-ledger service in `llm-gateway` fed by those logs (its spec
     follows the gateway spec).
  6. Supersedes two details of ADR 0004, decision 1: the OpenAI-compatible endpoint is
     Envoy's `/v1/chat/completions` (not `/openai/v1/chat/completions`), and `GET /v1/models`
     lists served model IDs only. Dialect and capabilities move to the agent config, which
     already owns model choice. Everything else in ADR 0004 stands.
- **Consequences:** We operate a Kubernetes cluster (EKS control plane ~$73 a month, small next
  to model spend) plus Redis for limits. We inherit Envoy's performance and the projects'
  maintenance, and we depend on a project that recently moved from `envoyproxy/ai-gateway`
  to `theagentrouter/agent-router`; the pinned versions and acceptance suite bound that
  risk. LiteLLM's built-in keys, budgets and UI are given up; the ledger replaces the parts we
  need. The paused Python gateway code is kept stashed, not merged.
