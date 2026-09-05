from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .decision import decide
from .evidence import create_manifest
from .security import tenant_key, verify_github_signature
from .store import ReviewStore


@dataclass(frozen=True)
class DeliveryResult:
    accepted: bool
    tenant_id: str
    delivery_id: str
    superseded: int = 0


class WebhookService:
    def __init__(self, store: ReviewStore, webhook_secret: str, evidence_key: str):
        self.store = store
        self.webhook_secret = webhook_secret
        self.evidence_key = evidence_key

    def receive(self, body: bytes, headers: dict[str, str]) -> DeliveryResult:
        verify_github_signature(body, headers.get("x-hub-signature-256", ""), self.webhook_secret)
        delivery_id = headers.get("x-github-delivery", "")
        if not delivery_id:
            raise ValueError("x-github-delivery is required")
        payload = json.loads(body)
        installation_id = int(payload["installation"]["id"])
        tenant_id = tenant_key(installation_id)
        repository = payload["repository"]["full_name"]
        head_sha = payload["pull_request"]["head"]["sha"]
        accepted = self.store.accept_delivery(tenant_id, delivery_id, repository, head_sha, payload)
        superseded = self.store.supersede_older(tenant_id, repository, head_sha) if accepted else 0
        return DeliveryResult(accepted, tenant_id, delivery_id, superseded)

    def evaluate(self, tenant_id: str, delivery_id: str, repository: str, head_sha: str, evidence_bundle: dict[str, Any]) -> dict[str, Any]:
        self.store.set_status(tenant_id, delivery_id, "running")
        result = decide(evidence_bundle)
        manifest = create_manifest(
            tenant_id=tenant_id,
            delivery_id=delivery_id,
            repository=repository,
            head_sha=head_sha,
            result=result,
            signing_key=self.evidence_key,
        )
        self.store.save_evidence(tenant_id, delivery_id, manifest)
        self.store.set_status(tenant_id, delivery_id, "completed")
        return manifest

