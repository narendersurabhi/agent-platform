# ADR 0003: Contracts live in the provider's repo, consumers pin copies

- **Status:** Accepted, 2026-11-10
- **Context:** Independent repos need an explicit, versioned interface between them, or every
  change becomes a coordinated release (a distributed monolith). A central contracts repo was
  considered and rejected: every contract change would go through a shared repo, recreating
  the coupling the split removes.
- **Decision:** Each provider owns `contracts/openapi.yaml` and `contracts/mcp/*.json`,
  versioned with semver. `scripts/contract_check.py` (from the template) validates them and
  blocks breaking changes without a MAJOR bump in the commit hook. Consumers copy a released
  version to `contracts/consumed/<provider>/` and test their outbound adapter against it.
  Consumers are tolerant readers, so additive response changes are not breaking.
- **Consequences:** Providers can ship additive changes at will, and breaking ones only by
  serving the old major alongside the new. Consumers upgrade when they choose. A consumer's
  pinned copy can lag the provider; that is intended.
