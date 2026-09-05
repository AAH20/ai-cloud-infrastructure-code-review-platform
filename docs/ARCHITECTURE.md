# Architecture

The current release implements the domain and trust kernel locally. It does not claim a hosted production service.

## Trust boundaries

- GitHub webhook bodies are accepted only after HMAC-SHA256 verification.
- The GitHub installation ID is the tenant key.
- Delivery IDs are idempotency keys scoped to a tenant.
- New commits supersede queued or running evaluations for older SHAs.
- Every storage lookup includes tenant identity and negative isolation tests.
- Decisions are deterministic; future LLM explanations cannot override blocking results.
- Evidence manifests bind tenant, delivery, repository, commit and result.

The reference store uses SQLite for zero-cost reproducibility. A production adapter should use PostgreSQL with row-level tenant policies, connection pooling, backups and point-in-time recovery.

## Azure target

The included Bicep provisions a low-cost foundational Container Apps environment, Log Analytics workspace and private-by-default evidence storage. The webhook application, workers, Service Bus, PostgreSQL, Key Vault, managed identities and private endpoints remain roadmap components until implemented and validated in an authorized subscription.

