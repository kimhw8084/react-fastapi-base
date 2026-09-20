#!/usr/bin/env python3
"""Check the canonical operational-reliability contract and typed evidence template."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.operational_reliability_contract import EXTERNAL_DRILL_IDS, REPOSITORY_SCENARIO_IDS, load_contract


def main() -> int:
    contract = load_contract()
    if tuple(row['id'] for row in contract['repository_scenarios']) != REPOSITORY_SCENARIO_IDS:
        raise AssertionError('Repository operational scenario order drifted.')
    if tuple(row['id'] for row in contract['external_drill_categories']) != EXTERNAL_DRILL_IDS:
        raise AssertionError('External operations drill order drifted.')
    template_path = ROOT / 'deploy/company-operations-evidence.template.json'
    schema_path = ROOT / 'deploy/company-operations-evidence.schema.json'
    template = json.loads(template_path.read_text(encoding='utf-8'))
    if 'production_ready' in template or 'production_ready' in json.dumps(template):
        raise AssertionError('External operations evidence template contains a production_ready shortcut.')
    sys.path.insert(0, str(ROOT / 'backend'))
    from app.platform.settings import CompanyOperationsEvidence

    model = CompanyOperationsEvidence.model_validate(template)
    if any(drill.status != 'BLOCKED_EXTERNAL' for drill in model.drills):
        raise AssertionError('External operations evidence template must remain unproven.')
    if json.loads(schema_path.read_text(encoding='utf-8')) != CompanyOperationsEvidence.model_json_schema():
        raise AssertionError('Typed company operations evidence schema drifted from the model.')
    print('Operational-reliability contract passed: repository scenarios=%d, external drills=%d.' % (len(REPOSITORY_SCENARIO_IDS), len(EXTERNAL_DRILL_IDS)))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (AssertionError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f'Operational-reliability contract FAILED: {error}')
        raise SystemExit(1) from None
