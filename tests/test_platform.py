import hashlib
import hmac
import json
import tempfile
import unittest
from pathlib import Path

from cloud_review.decision import decide
from cloud_review.evidence import create_manifest, verify_manifest
from cloud_review.security import SignatureError, verify_github_signature
from cloud_review.service import WebhookService
from cloud_review.store import ReviewStore, TenantBoundaryError


ROOT = Path(__file__).parents[1]


def load(name):
    return json.loads((ROOT / "examples" / name).read_text())


class PlatformTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = ReviewStore(Path(self.temp.name) / "reviews.db")
        self.service = WebhookService(self.store, "webhook-secret", "evidence-key")

    def tearDown(self):
        self.temp.cleanup()

    def signed_delivery(self, delivery="delivery-1", sha="abc123"):
        payload = load("github-pull-request.json")
        payload["pull_request"]["head"]["sha"] = sha
        body = json.dumps(payload, separators=(",", ":")).encode()
        signature = hmac.new(b"webhook-secret", body, hashlib.sha256).hexdigest()
        return self.service.receive(body, {"x-hub-signature-256": f"sha256={signature}", "x-github-delivery": delivery})

    def test_signature_rejects_tampering(self):
        with self.assertRaises(SignatureError):
            verify_github_signature(b"tampered", "sha256=bad", "secret")

    def test_delivery_is_idempotent(self):
        self.assertTrue(self.signed_delivery().accepted)
        self.assertFalse(self.signed_delivery().accepted)

    def test_new_sha_supersedes_older_job(self):
        first = self.signed_delivery()
        second = self.signed_delivery("delivery-2", "def456")
        self.assertEqual(second.superseded, 1)
        self.assertEqual(self.store.status(first.tenant_id, first.delivery_id), "superseded")

    def test_cross_tenant_read_is_rejected(self):
        accepted = self.signed_delivery()
        with self.assertRaises(TenantBoundaryError):
            self.store.status("github-installation:9999", accepted.delivery_id)

    def test_safe_and_risky_decisions(self):
        self.assertEqual(decide(load("safe-change.json"))["decision"], "APPROVE")
        risky = decide(load("risky-change.json"))
        self.assertEqual(risky["decision"], "BLOCK")
        self.assertEqual(risky["score"], 32)

    def test_evidence_is_signed_and_tamper_evident(self):
        manifest = create_manifest(tenant_id="t", delivery_id="d", repository="r", head_sha="s", result=decide(load("safe-change.json")), signing_key="key")
        self.assertTrue(verify_manifest(manifest, "key"))
        manifest["result"]["score"] = 0
        self.assertFalse(verify_manifest(manifest, "key"))

    def test_complete_service_flow(self):
        delivery = self.signed_delivery()
        manifest = self.service.evaluate(delivery.tenant_id, delivery.delivery_id, "example/platform", "abc123", load("safe-change.json"))
        self.assertEqual(manifest["result"]["decision"], "APPROVE")
        self.assertEqual(self.store.status(delivery.tenant_id, delivery.delivery_id), "completed")


if __name__ == "__main__":
    unittest.main()

