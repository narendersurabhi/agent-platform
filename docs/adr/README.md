# Architecture decision records

| ADR | Decision |
|---|---|
| [0001](0001-service-split.md) | Split into independently deployed services |
| [0002](0002-hexagonal-layout.md) | Ports and adapters inside every service |
| [0003](0003-contracts-in-provider-repos.md) | Contracts live in the provider's repo; consumers pin copies |
| [0004](0004-llm-gateway-dialects-and-model-ownership.md) | Gateway passes dialects through; agents own model choice |
| [0005](0005-retrieval-as-a-service.md) | Retrieval is a service, not an in-process tool |

New ADRs take the next number. An ADR is never edited to reverse it: write a new one that
supersedes it and set the old one's status to `Superseded by NNNN`.
