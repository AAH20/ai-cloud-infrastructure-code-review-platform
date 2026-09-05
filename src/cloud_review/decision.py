from __future__ import annotations

from typing import Any


PENALTIES = {"critical": 30, "high": 20, "medium": 8, "low": 2}


def decide(bundle: dict[str, Any]) -> dict[str, Any]:
    findings = list(bundle.get("findings", []))
    rollback = bundle.get("rollback", {}).get("steps", [])
    if not rollback:
        findings.append({"id": "ROLLBACK-REQUIRED", "severity": "high", "source": "platform", "title": "Machine-readable rollback is required", "blocking": True})

    blocking = [item for item in findings if item.get("blocking") or item.get("severity", "").lower() in {"critical", "high"}]
    score = max(0, 100 - sum(PENALTIES.get(item.get("severity", "medium").lower(), 5) for item in findings))
    decision = "BLOCK" if blocking else ("REVIEW_REQUIRED" if findings else "APPROVE")
    return {
        "decision": decision,
        "score": score,
        "evidence_class": bundle.get("evidence_class", "simulated"),
        "findings": findings,
        "metrics": {
            "blocking_findings": len(blocking),
            "monthly_cost_delta_usd": float(bundle.get("monthly_cost_delta_usd", 0)),
            "modeled_revenue_exposure_usd": float(bundle.get("modeled_revenue_exposure_usd", 0)),
        },
    }

