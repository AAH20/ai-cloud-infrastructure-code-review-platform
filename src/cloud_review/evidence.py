from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any


def create_manifest(*, tenant_id: str, delivery_id: str, repository: str, head_sha: str, result: dict[str, Any], signing_key: str) -> dict[str, Any]:
    manifest = {
        "schema_version": "1.0",
        "tenant_id": tenant_id,
        "delivery_id": delivery_id,
        "repository": repository,
        "head_sha": head_sha,
        "evidence_class": result.get("evidence_class", "simulated"),
        "result": result,
    }
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    manifest["signature"] = "hmac-sha256:" + hmac.new(signing_key.encode(), canonical.encode(), hashlib.sha256).hexdigest()
    return manifest


def verify_manifest(manifest: dict[str, Any], signing_key: str) -> bool:
    unsigned = dict(manifest)
    signature = unsigned.pop("signature", "").removeprefix("hmac-sha256:")
    canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    expected = hmac.new(signing_key.encode(), canonical.encode(), hashlib.sha256).hexdigest()
    return bool(signature) and hmac.compare_digest(signature, expected)

