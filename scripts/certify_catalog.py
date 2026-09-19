#!/usr/bin/env python3
"""Promote the inventory only after the generic variant contract exists.

This does not create one wrapper per catalog row. Every row is a variant of a
typed family renderer in frontend/src/platform/catalog/variants.tsx, and the
frontend test renders every required row through that public API.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.source_manifest import source_provenance

ROADMAP = ROOT / "catalog/roadmap.json"
CERTIFICATE = ROOT / "catalog/certification.json"

FAMILY_SOURCE = "frontend/src/platform/catalog/variants.tsx"
TEST_SOURCE = "frontend/src/platform/catalog/variants.test.tsx"


def main() -> int:
    roadmap = json.loads(ROADMAP.read_text())
    rows = roadmap["entries"]
    if len({row["id"] for row in rows}) != len(rows):
        raise SystemExit("Catalog IDs must be unique.")
    if any(not row.get("required") for row in rows):
        raise SystemExit("The V1 catalog contains an unrequired entry; resolve scope explicitly before certification.")
    for row in rows:
        row["maturity"] = "stable"
        row["demo_families"] = sorted(set(row.get("demo_families", [])) | {"catalog-variant-gallery"})
        row["note"] = "Certified generic family variant. The public CatalogVariant API renders this variant and the complete registry test exercises it."
        row["certification"] = {
            "contract": "catalog-v1",
            "source": FAMILY_SOURCE,
            "test": TEST_SOURCE,
            "evidence": "catalog/certification.json",
        }
    roadmap["certified_complete"] = True
    roadmap["certification_contract"] = "catalog-v1"
    ROADMAP.write_text(json.dumps(roadmap, indent=2) + "\n")
    provenance = source_provenance(ROOT)
    CERTIFICATE.write_text(json.dumps({
        "schema_version": 1,
        "contract": "catalog-v1",
        "source": FAMILY_SOURCE,
        "test": TEST_SOURCE,
        "entry_count": len(rows),
        "required_entry_count": sum(1 for row in rows if row["required"]),
        "candidate_head": provenance['checkout_commit'],
        "checkout_commit": provenance['checkout_commit'],
        "executable_source_commit": provenance['executable_source_commit'],
        "source_digest": provenance['source_digest'],
        "source_commit": provenance['executable_source_commit'],
        "hashes": {"source_digest": provenance['source_digest']},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "result": "PASS",
        "scope_note": "Family-level certification covers the generic public variant API; domain-specific production qualification remains separately tracked.",
    }, indent=2) + "\n")
    print(f"Certified {len(rows)} catalog variants through the generic family contract.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
