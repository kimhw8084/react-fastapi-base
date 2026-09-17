#!/usr/bin/env python3
"""Cross-check the final CompanyQualification model, schema and safe template."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))

from app.platform.settings import (  # noqa: E402
    COMPANY_QUALIFICATION_SCHEMA_VERSION,
    MANDATORY_GATE_IDS,
    CompanyQualification,
    VERSION,
)


def main() -> int:
    template_path = ROOT / 'deploy/company-qualification.template.json'
    schema_path = ROOT / 'deploy/company-qualification.schema.json'
    template = json.loads(template_path.read_text(encoding='utf-8'))
    model = CompanyQualification.model_validate(template)
    gate_ids = [gate.id for gate in model.gates]
    if tuple(gate_ids) != MANDATORY_GATE_IDS:
        raise AssertionError('Qualification template gate order/set drifted from the typed mandatory model.')
    if any(gate.status != 'BLOCKED' or gate.evidence or gate.facts is not None for gate in model.gates):
        raise AssertionError('Qualification template must contain only unproven BLOCKED gates.')
    if 'production_ready' in template:
        raise AssertionError('Qualification template must not contain an operator-editable production_ready field.')
    if model.derived_production_ready(
        expected_version=VERSION,
        expected_deployment_id='template-deployment',
        expected_root=Path('/template/root'),
    ):
        raise AssertionError('Qualification template unexpectedly derives production readiness.')
    expected_schema = CompanyQualification.model_json_schema()
    if json.loads(schema_path.read_text(encoding='utf-8')) != expected_schema:
        raise AssertionError('deploy/company-qualification.schema.json drifted from the typed model.')
    if model.schema_version != COMPANY_QUALIFICATION_SCHEMA_VERSION:
        raise AssertionError('Qualification schema version constant drifted.')
    print(f'CompanyQualification contract passed: schema v{model.schema_version}, gates={",".join(MANDATORY_GATE_IDS)}.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (AssertionError, OSError, json.JSONDecodeError, ValueError) as error:
        print(f'CompanyQualification contract check FAILED: {error}')
        raise SystemExit(1) from None
