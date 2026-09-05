from __future__ import annotations

import hashlib
import hmac


class SignatureError(ValueError):
    pass


def verify_github_signature(body: bytes, signature_header: str, secret: str) -> None:
    if not signature_header.startswith("sha256="):
        raise SignatureError("GitHub signature must use sha256")
    supplied = signature_header.removeprefix("sha256=")
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(supplied, expected):
        raise SignatureError("GitHub webhook signature mismatch")


def tenant_key(installation_id: int) -> str:
    if installation_id <= 0:
        raise ValueError("installation_id must be positive")
    return f"github-installation:{installation_id}"

