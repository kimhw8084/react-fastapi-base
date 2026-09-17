from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('release_evidence', ROOT / 'scripts/release_evidence.py')
assert SPEC.loader is not None
RELEASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RELEASE)


def test_readiness_matrix_is_deterministic_and_exactly_enumerates_gates():
    results = [
        {'name': 'backend-tests', 'status': 'PASS'},
        {'name': 'company-identity', 'status': 'BLOCKED', 'required_for': 'deployment'},
    ]
    first = RELEASE.build_readiness_matrix(source_commit='a' * 40, source_digest='b' * 64, version='1.0.0-rc.11', results=results)
    second = RELEASE.build_readiness_matrix(source_commit='a' * 40, source_digest='b' * 64, version='1.0.0-rc.11', results=results)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert first['mandatory_gate_ids'] == [
        'technical_release', 'identity', 'storage', 'deployment',
        'ui_accessibility', 'performance', 'operations', 'release_evidence',
    ]
    assert first['production_ready'] is False
    assert all(row['reason'] for row in first['gates'] if row['status'] in {'BLOCKED', 'FAIL'})
    assert first['gates'][1]['status'] == 'BLOCKED'


def test_local_matrix_keeps_company_gates_unproven_even_when_local_checks_pass():
    results = [{'name': 'all-code-checks', 'status': 'PASS'}]
    matrix = RELEASE.build_readiness_matrix(source_commit='a' * 40, source_digest='b' * 64, version='1.0.0-rc.11', results=results)
    statuses = {row['id']: row['status'] for row in matrix['gates']}
    assert statuses['technical_release'] == 'PASS'
    assert statuses['release_evidence'] == 'PASS'
    assert all(statuses[gate] == 'BLOCKED' for gate in ('identity', 'storage', 'deployment', 'ui_accessibility', 'performance', 'operations'))
    assert matrix['release_status'] == 'NOT_CERTIFIED'
