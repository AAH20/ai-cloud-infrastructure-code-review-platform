from __future__ import annotations

import hashlib
import json
from collections import defaultdict, deque
from typing import Any


DESTRUCTIVE = {"delete", "replace"}


def parse_plan(plan: dict[str, Any]) -> list[dict[str, Any]]:
    changes = []
    for item in plan.get("resource_changes", []):
        actions = item.get("change", {}).get("actions", [])
        action = "replace" if "delete" in actions and "create" in actions else (actions[0] if actions else "no-op")
        if action == "no-op":
            continue
        changes.append({"address": item["address"], "type": item.get("type", "unknown"), "action": action})
    return sorted(changes, key=lambda row: row["address"])


def analyze_impact(plan: dict[str, Any], graph: dict[str, Any]) -> dict[str, Any]:
    changes = parse_plan(plan)
    nodes = {item["id"]: item for item in graph.get("nodes", [])}
    incoming: dict[str, list[str]] = defaultdict(list)
    for edge in graph.get("edges", []):
        incoming[edge["target"]].append(edge["source"])
    mapping = graph.get("terraform_mapping", {})
    impacted: set[str] = set()
    unmapped = []
    for change in changes:
        node_id = mapping.get(change["address"])
        if not node_id or node_id not in nodes:
            unmapped.append(change["address"])
            continue
        queue = deque([node_id])
        while queue:
            current = queue.popleft()
            if current in impacted:
                continue
            impacted.add(current)
            queue.extend(incoming[current])
    owners = sorted({str(nodes[node]["attributes"]["owner"]) for node in impacted if nodes[node].get("attributes", {}).get("owner")})
    services = sorted(node for node in impacted if nodes[node].get("kind") == "business_service")
    exposure = sum(float(nodes[node].get("attributes", {}).get("monthly_revenue_usd", 0)) for node in services)
    destructive = [item for item in changes if item["action"] in DESTRUCTIVE]
    findings = []
    if destructive:
        findings.append({"id": "TF-DESTRUCTIVE-CHANGE", "severity": "high", "source": "terraform-impact", "title": f"{len(destructive)} resource changes delete or replace infrastructure", "blocking": True})
    if unmapped:
        findings.append({"id": "TF-GRAPH-COVERAGE", "severity": "medium", "source": "cloudgraph", "title": f"{len(unmapped)} changed resources are not mapped to the infrastructure graph", "blocking": False})
    result = {
        "changes": changes,
        "impacted_nodes": sorted(impacted),
        "business_services": services,
        "owners": owners,
        "modeled_revenue_exposure_usd": exposure,
        "mapping_coverage_percent": round(100 * (len(changes) - len(unmapped)) / max(len(changes), 1), 2),
        "unmapped_changes": unmapped,
        "findings": findings,
        "claim_boundary": "Graph reachability indicates potential impact and does not prove runtime causality. Financial values are modeled graph attributes.",
    }
    result["receipt"] = "sha256:" + hashlib.sha256(json.dumps(result, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return result


def to_review_bundle(impact: dict[str, Any], rollback_steps: list[str]) -> dict[str, Any]:
    return {
        "evidence_class": "simulated",
        "rollback": {"steps": rollback_steps},
        "findings": impact["findings"],
        "monthly_cost_delta_usd": 0,
        "modeled_revenue_exposure_usd": impact["modeled_revenue_exposure_usd"],
        "impact": impact,
    }


def markdown_report(impact: dict[str, Any], decision: dict[str, Any]) -> str:
    changes = "\n".join(f"- `{row['action']}` `{row['address']}`" for row in impact["changes"]) or "- No material changes"
    services = ", ".join(f"`{item}`" for item in impact["business_services"]) or "None mapped"
    return f"""# Terraform infrastructure impact analysis

**Decision:** {decision['decision']} — score {decision['score']}/100

- Mapping coverage: {impact['mapping_coverage_percent']}%
- Modeled revenue exposure: ${impact['modeled_revenue_exposure_usd']:,.2f}
- Owners: {', '.join(impact['owners']) or 'None mapped'}
- Business services: {services}

## Changes

{changes}

## Evidence boundary

{impact['claim_boundary']}

Receipt: `{impact['receipt']}`
"""


def sarif(impact: dict[str, Any]) -> dict[str, Any]:
    results = [{"ruleId": item["id"], "level": "error" if item["severity"] in {"critical", "high"} else "warning", "message": {"text": item["title"]}} for item in impact["findings"]]
    return {"version": "2.1.0", "$schema": "https://json.schemastore.org/sarif-2.1.0.json", "runs": [{"tool": {"driver": {"name": "CloudGraph Terraform Impact"}}, "results": results}]}
