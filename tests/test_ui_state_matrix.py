from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from scripts.check_ui_state_matrix import MatrixContractError, SPEC_PATH, validate_matrix


ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / 'frontend/tests/e2e/ui-state-matrix.json'


def load_matrix() -> dict:
    return json.loads(MATRIX_PATH.read_text(encoding='utf-8'))


def write_fixture(tmp_path: Path, matrix: dict, spec: str | None = None) -> tuple[Path, Path]:
    matrix_path = tmp_path / 'matrix.json'
    spec_path = tmp_path / 'uiqa.spec.ts'
    matrix_path.write_text(json.dumps(matrix, indent=2) + '\n', encoding='utf-8')
    spec_path.write_text(spec if spec is not None else SPEC_PATH.read_text(encoding='utf-8'), encoding='utf-8')
    return matrix_path, spec_path


def write_result_fixture(tmp_path: Path) -> tuple[Path, Path, Path, dict]:
    matrix = load_matrix()
    for row in matrix['rows']:
        row['required_evidence']['artifact_locators'] = [
            locator for locator in row['required_evidence']['artifact_locators'] if (ROOT / locator).is_file()
        ]
    matrix_path, spec_path = write_fixture(tmp_path, matrix)
    results = {
        'schema_version': 1,
        'result_kind': 'browser-computed-uiqa',
        'proof_model': 'runtime-assertion-v1',
        'matrix_id': matrix['matrix_id'],
        'matrix_sha256': hashlib.sha256(matrix_path.read_bytes()).hexdigest(),
        'source_commit': None,
        'overall_status': 'PASS',
        'results': [
            {
                'state_id': row['state_id'],
                'browser_test_id': row['browser_test_id'],
                'status': 'PASS',
                'exercised_dimensions': sorted(row['required_dimensions']),
                'artifact_locators': sorted(row['required_evidence']['artifact_locators']),
            }
            for row in matrix['rows']
        ],
    }
    results_path = tmp_path / 'results.json'
    results_path.write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    return matrix_path, spec_path, results_path, results


def test_canonical_matrix_has_all_material_classes_and_dimensions():
    report = validate_matrix()
    assert report['status'] == 'PASS'
    assert report['state_classes'] == ['empty', 'error', 'loading', 'normal', 'permission', 'selection']
    assert 'reflow.320-css-px' in report['dimensions']
    assert 'forced-colors.active' in report['dimensions']


def test_duplicate_state_ids_fail_closed(tmp_path: Path):
    matrix = load_matrix()
    matrix['rows'].append(copy.deepcopy(matrix['rows'][0]))
    matrix_path, spec_path = write_fixture(tmp_path, matrix)
    with pytest.raises(MatrixContractError, match='duplicate state IDs'):
        validate_matrix(matrix_path, spec_path)


def test_unknown_test_only_state_reference_fails_closed(tmp_path: Path):
    matrix_path, spec_path = write_fixture(tmp_path, load_matrix(), "matrixTest('test-only-unknown-state', async () => ({}))")
    with pytest.raises(MatrixContractError, match='unknown state IDs'):
        validate_matrix(matrix_path, spec_path)


def test_applicable_rows_cannot_lose_executable_coverage(tmp_path: Path):
    matrix = load_matrix()
    first = matrix['rows'][0]['state_id']
    source = SPEC_PATH.read_text(encoding='utf-8')
    source = source.replace(f"matrixTest('{first}'", "matrixTest('removed-coverage'")
    matrix_path, spec_path = write_fixture(tmp_path, matrix, source)
    with pytest.raises(MatrixContractError, match='unknown state IDs|no executable browser coverage'):
        validate_matrix(matrix_path, spec_path)


def test_required_dimension_disappearance_fails_closed(tmp_path: Path):
    matrix = load_matrix()
    row = next(row for row in matrix['rows'] if 'forced-colors.active' in row['required_dimensions'])
    row['required_dimensions'].remove('forced-colors.active')
    matrix_path, spec_path = write_fixture(tmp_path, matrix)
    with pytest.raises(MatrixContractError, match='required dimension has disappeared'):
        validate_matrix(matrix_path, spec_path)


def test_result_metadata_may_not_contain_timestamps_or_unknown_rows(tmp_path: Path):
    result_path = tmp_path / 'results.json'
    result_path.write_text(json.dumps({'schema_version': 1, 'matrix_id': 'project-os-ui-state-matrix', 'proof_model': 'runtime-assertion-v1', 'matrix_sha256': '0' * 64, 'timestamp': 'never', 'results': []}), encoding='utf-8')
    with pytest.raises(MatrixContractError, match='timestamp|not bound'):
        validate_matrix(MATRIX_PATH, SPEC_PATH, result_path)


@pytest.mark.parametrize(
    ('mutation', 'message'),
    [
        ('missing', 'exact required runtime-proven set'),
        ('extra', 'exact required runtime-proven set'),
        ('unknown', 'unknown dimensions'),
        ('duplicate', 'contain duplicates'),
    ],
)
def test_result_contract_rejects_false_or_unproven_dimension_sets(tmp_path: Path, mutation: str, message: str):
    matrix_path, spec_path, result_path, results = write_result_fixture(tmp_path)
    target = next(row for row in results['results'] if row['state_id'] == 'chg34-theme-operations-primary-action')
    if mutation == 'missing':
        target['exercised_dimensions'].pop()
    elif mutation == 'extra':
        target['exercised_dimensions'] = sorted([*target['exercised_dimensions'], 'theme.light'])
    elif mutation == 'unknown':
        target['exercised_dimensions'] = sorted([*target['exercised_dimensions'], 'unknown.dimension'])
    else:
        target['exercised_dimensions'].append(target['exercised_dimensions'][0])
    result_path.write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    with pytest.raises(MatrixContractError, match=message):
        validate_matrix(matrix_path, spec_path, result_path)


def test_adding_a_matrix_requirement_without_a_runtime_proof_marker_fails_closed(tmp_path: Path):
    matrix = load_matrix()
    first = matrix['rows'][0]
    first['required_dimensions'].append('keyboard.enter')
    matrix_path, spec_path = write_fixture(tmp_path, matrix)
    with pytest.raises(MatrixContractError, match='no executable runtime proof marker'):
        validate_matrix(matrix_path, spec_path)


def test_legacy_automatic_copy_path_is_rejected_by_the_runtime_proof_contract(tmp_path: Path):
    matrix = load_matrix()
    first = matrix['rows'][0]
    first['required_dimensions'].append('keyboard.enter')
    matrix_path, spec_path = write_fixture(tmp_path, matrix)
    old_copy = SPEC_PATH.read_text(encoding='utf-8').replace('proof?.observedDimensions()??[]', '[...row.required_dimensions].sort()')
    spec_path.write_text(old_copy, encoding='utf-8')
    with pytest.raises(MatrixContractError, match='no executable runtime proof marker|may not copy'):
        validate_matrix(matrix_path, spec_path)
