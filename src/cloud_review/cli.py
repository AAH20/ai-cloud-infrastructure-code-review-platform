from __future__ import annotations

import argparse
import json
from pathlib import Path

from .decision import decide
from .evidence import create_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a normalized cloud infrastructure review bundle")
    parser.add_argument("bundle")
    parser.add_argument("--output", default="evidence-manifest.json")
    parser.add_argument("--tenant", default="local:reference")
    parser.add_argument("--delivery", default="local-run")
    parser.add_argument("--repository", default="local/repository")
    parser.add_argument("--sha", default="local")
    parser.add_argument("--signing-key", default="development-only-key")
    parser.add_argument("--fail-on-block", action="store_true")
    args = parser.parse_args()
    bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    manifest = create_manifest(
        tenant_id=args.tenant,
        delivery_id=args.delivery,
        repository=args.repository,
        head_sha=args.sha,
        result=decide(bundle),
        signing_key=args.signing_key,
    )
    Path(args.output).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"{manifest['result']['decision']} score={manifest['result']['score']} {manifest['signature']}")
    return 2 if args.fail_on_block and manifest["result"]["decision"] == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())

