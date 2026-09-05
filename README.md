# AI Cloud Infrastructure Code Review Platform

**Multi-tenant AI code review for Terraform, OpenTofu, Azure, Kubernetes, networking, DevOps, FinOps and compliance as code.**

[![CI](https://github.com/AAH20/ai-cloud-infrastructure-code-review-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/AAH20/ai-cloud-infrastructure-code-review-platform/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Evidence](https://img.shields.io/badge/evidence-explicit-green.svg)](#evidence-boundary)

This project is the deployable product and trust layer above:

- [AI Infrastructure Pull Request Reviewer](https://github.com/AAH20/ai-infrastructure-pull-request-reviewer)
- [Agentic Infrastructure ChangeBench](https://github.com/AAH20/agentic-infrastructure-change-benchmark)

It addresses a recurring delivery problem: infrastructure pull requests are reviewed by disconnected security, cost and policy tools, while engineering leaders still lack one traceable decision covering business services, rollback, agent safety and financial impact.

## What v0.1 actually implements

Version 0.1 provides an executable production-oriented trust kernel:

- GitHub HMAC-SHA256 webhook verification;
- GitHub installation-based tenant identity;
- tenant-scoped SQLite reference persistence;
- idempotent delivery processing;
- automatic supersession of older commit evaluations;
- deterministic `APPROVE`, `REVIEW_REQUIRED` and `BLOCK` decisions;
- signed evidence manifests bound to tenant, repository, delivery and commit;
- cross-tenant negative tests;
- safe and deliberately risky review fixtures;
- CLI and composite GitHub Action;
- foundational Azure Container Apps, Log Analytics and Storage Bicep.

The project does **not** claim a live hosted service, registered GitHub App, production PostgreSQL implementation or deployed Azure environment. Those remain explicit roadmap stages.

## Architecture

```text
GitHub infrastructure pull request
                 │
                 ▼
       HMAC-verified webhook
                 │
                 ▼
 Installation tenant + delivery idempotency
                 │
                 ▼
       Durable evaluation lifecycle
                 │
      ┌──────────┼──────────┐
      ▼          ▼          ▼
 Terraform    Kubernetes   Azure/network
      │          │          │
      └──────────┼──────────┘
                 ▼
 Checkov · Infracost · OPA · ChangeBench
                 │
                 ▼
      Deterministic merge decision
                 │
                 ▼
 Signed evidence · GitHub Check · observability
```

Future model providers—Azure AI Foundry, NVIDIA NIM, OpenAI, Anthropic or OpenRouter—may explain evidence and propose remediation. They must not override deterministic blocking decisions.

## Run the trust kernel

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v

cloud-review-platform examples/safe-change.json \
  --output safe-evidence.json \
  --tenant github-installation:4242 \
  --delivery delivery-1 \
  --repository example/platform \
  --sha abc123 \
  --signing-key local-test-key \
  --fail-on-block
```

Expected result:

```text
APPROVE score=100 hmac-sha256:...
```

The risky reference change produces `BLOCK` with score `32/100` because it includes two high-severity findings, one budget violation and no rollback.

## GitHub Action

```yaml
- uses: AAH20/ai-cloud-infrastructure-code-review-platform@v1
  with:
    bundle: evidence/normalized-review.json
    output: evidence-manifest.json
    fail-on-block: "true"
```

The Action is implemented. The `v1` reference becomes valid only after an actual release tag.

## Trust and isolation model

| Boundary | Implemented control |
|---|---|
| Webhook authenticity | Constant-time HMAC-SHA256 comparison |
| Tenant identity | Positive GitHub installation ID mapped to a canonical tenant key |
| Replay/idempotency | Tenant-scoped GitHub delivery primary key |
| Stale evaluations | Older queued/running commits are marked superseded |
| Data isolation | Every delivery and evidence lookup contains tenant identity |
| Decision authority | Deterministic severity and rollback policy |
| Evidence integrity | Manifest signature binds tenant, delivery, repository, commit and result |
| Model authority | No model call exists in v0.1; future explanations cannot override policy |

The HMAC manifest implementation proves shared-key integrity. Enterprise non-repudiation requires asymmetric signing, managed keys, authenticated identities and evidence custody.

## Azure target architecture

The included [Bicep foundation](infra/azure/main.bicep) creates:

- a Container Apps managed environment;
- a Log Analytics workspace;
- private-by-default, TLS-enforced evidence storage.

The cost-conscious hosted architecture will add:

- Container Apps API and evaluation jobs;
- Service Bus queues and dead-letter handling;
- Azure Database for PostgreSQL;
- Key Vault and managed identities;
- Blob evidence retention;
- OpenTelemetry and Application Insights;
- GitHub OIDC deployment;
- optional private networking for enterprise installations.

AKS is intentionally deferred until workload scale or isolation requirements justify its additional operating cost.

## Product KPIs

### Reliability and security

- webhook processing success above 99.5%;
- deterministic rerun agreement above 99%;
- zero cross-tenant reads in the isolation suite;
- zero duplicate reviews per delivery;
- zero silent infrastructure mutations;
- evidence coverage above 95%;
- documented recovery for every failed evaluation.

### Adoption

- installation-to-first-result below 10 minutes;
- 10 external GitHub installations;
- five weekly active repositories;
- 100 external infrastructure pull requests evaluated;
- 30% week-four repository retention;
- three external scenario contributors;
- two publishable, measured design-partner case studies.

### Unit economics

- platform cost below $0.25 per deterministic evaluation;
- optional model explanation below $0.50;
- free-tenant infrastructure cap below $5/month;
- target gross margin above 80%;
- human support below 30 minutes per active repository/month.

These are target hypotheses. They are not achieved metrics until retained production telemetry demonstrates them.

## CISO, SOC and GRC engineering

The platform connects infrastructure delivery to technical control evidence without reducing architecture to compliance paperwork. Review manifests can feed ISO 27001, ISO 42001, SOC 2, NIST, CIS, NIS2 and DORA workflows while certification, risk acceptance and legal conclusions remain with accountable organizations and auditors.

Relevant capabilities include:

- infrastructure and network security architecture;
- agent authorization and mutation boundaries;
- evidence collection and remediation verification;
- approved risk exceptions;
- SOC and incident-change evidence;
- Infrastructure as Code to compliance-as-code traceability;
- managed platform and virtual CISO operating models.

## Evidence boundary

| Capability | Status |
|---|---|
| Webhook verification and tenant derivation | Implemented and tested |
| Idempotency and commit supersession | Implemented and tested |
| Cross-tenant isolation checks | Implemented and tested |
| Deterministic decisions and signed manifests | Implemented and tested |
| SQLite reference persistence | Implemented; local reference |
| Azure foundation IaC | Implemented; not deployed by this repository |
| OCI Dockerfile | Implemented; local daemon validation not claimed |
| Native Terraform/Checkov/Infracost adapters | Contract/roadmap |
| GitHub Checks API and registered App | Roadmap |
| Production PostgreSQL and Service Bus | Roadmap |
| Customer results and achieved ROI | None claimed |

## Distribution

- GitHub Action for zero-friction repository adoption
- GitHub App for centralized installation and checks
- PyPI CLI
- OCI container
- Azure deployment modules
- self-hosted enterprise edition
- Backstage and Azure DevOps integrations
- MCP interface
- ChangeBench public scenario registry and leaderboard

The free execution path should lead to measurable pull-request value before any services conversation.

## Commercial path

Potential offerings include private Azure deployment, custom scenario packs, platform integration, architecture diagnostics, managed change assurance and CISO/SOC evidence integration. Pricing and demand must be validated with real design partners; this repository makes no revenue guarantees.

## Repository structure

```text
src/cloud_review/  webhook, security, storage, decision and evidence kernel
tests/             isolation, idempotency, signature and lifecycle tests
examples/          safe/risky changes and GitHub webhook fixture
infra/azure/       cost-conscious Bicep foundation
docs/              architecture and staged delivery roadmap
action.yml         composite GitHub Action
Dockerfile         non-root OCI runtime
```

## Contact

Need to evaluate infrastructure-agent changes or build a governed cloud delivery platform?

[Request an architecture and change-intelligence review](https://a2zsoc.com/contact?topic=ai-cloud-infrastructure-code-review-platform&utm_source=github&utm_medium=repository) · [A2Z SOC](https://a2zsoc.com)
