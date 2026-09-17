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
    assert first['gates'][1]['qualification_status'] == 'BLOCKED_EXTERNAL'


def test_local_matrix_keeps_company_gates_unproven_even_when_local_checks_pass():
    results = [{'name': 'all-code-checks', 'status': 'PASS'}]
    matrix = RELEASE.build_readiness_matrix(source_commit='a' * 40, source_digest='b' * 64, version='1.0.0-rc.11', results=results)
    statuses = {row['id']: row['status'] for row in matrix['gates']}
    assert statuses['technical_release'] == 'PASS'
    assert statuses['release_evidence'] == 'PASS'
    assert all(statuses[gate] == 'BLOCKED' for gate in ('identity', 'storage', 'deployment', 'ui_accessibility', 'performance', 'operations'))
    assert matrix['release_status'] == 'NOT_CERTIFIED'


def test_build_evidence_does_not_claim_acceptance_or_integration():
    matrix = RELEASE.build_readiness_matrix(source_commit='a' * 40, source_digest='b' * 64, version='1.0.0-rc.11', results=[{'name': 'all-code-checks', 'status': 'PASS'}])
    assert all('accepted_head' not in row and 'repository_merge_sha' not in row for row in matrix['gates'])
    assert all(row['qualification_status'] == 'BLOCKED_EXTERNAL' for row in matrix['gates'][1:7])


def test_written_build_manifest_uses_target_base_and_not_post_acceptance_fields(tmp_path, monkeypatch):
    release_dir = tmp_path / 'release'
    monkeypatch.setattr(RELEASE, 'ROOT', tmp_path)
    monkeypatch.setattr(RELEASE, 'RELEASE_DIR', release_dir)
    monkeypatch.setattr(RELEASE, 'READINESS_PATH', release_dir / 'rc11-readiness-matrix.json')
    monkeypatch.setattr(RELEASE, 'MANIFEST_PATH', release_dir / 'rc11-manifest.json')
    monkeypatch.setattr(RELEASE, 'BINDING_PATH', release_dir / 'rc11-evidence-binding.json')
    monkeypatch.setattr(RELEASE, 'CHG33_PATH', release_dir / 'CHG-33-company-qualification.json')
    RELEASE.write_repository_release_evidence(
        source_commit='a' * 40,
        source_digest='b' * 64,
        version='1.0.0-rc.11',
        results=[{'name': 'all-code-checks', 'status': 'PASS'}],
        api_compatibility_base_sha='c' * 40,
    )
    manifest = json.loads((release_dir / 'rc11-manifest.json').read_text())
    binding = json.loads((release_dir / 'rc11-evidence-binding.json').read_text())
    for document in (manifest, binding):
        assert 'accepted_head' not in document
        assert 'repository_merge_sha' not in document
        assert document['target_base_sha'] == 'c' * 40
    binder_source = (Path(__file__).resolve().parents[1] / 'scripts/bind_release_evidence.py').read_text()
    assert 'accepted_head' not in binder_source
    assert 'repository_merge_sha' not in binder_source


def test_executable_source_digest_excludes_generated_lab_payload():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts.source_manifest import source_hashes

    assert not any(name.startswith('frontend/public/experience-lab/') for name in source_hashes())
