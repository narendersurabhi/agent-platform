# ADR 0001: Split the agent system into independently deployed services

- **Status:** Accepted, 2026-11-10
- **Context:** One orchestrator process ran the agent loop, model calls, tools and (soon)
  retrieval. At the target load (~1M runs per hour, 300K users per hour) these parts have
  different resource profiles: the loop is memory-bound and mostly waiting, model calls are
  capped by provider quota, retrieval is QPS-bound, and heavy tools are CPU-bound. They also
  change at different speeds and could be owned by different people.
- **Decision:** Separate repos and deployments for the orchestrator (`deepagents-deploy`),
  the LLM gateway (`llm-gateway`), retrieval (`retrieval-service`) and ingestion
  (`docling-pipeline`). Shared infrastructure, conventions, decisions and the service
  template live in `agent-platform`. Tool services, a sandbox fleet and remote subagent
  fleets are added from the template when a concrete need appears.
- **Consequences:** Each service scales on its own signal and ships on its own schedule.
  The price is network hops (milliseconds, small next to model latency), more deployments,
  and the need for explicit contracts (ADR 0003) and shared conventions
  (`docs/conventions.md`). Fast, pure tools stay in-process: a hop for microseconds of work
  is all cost.
