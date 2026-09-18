from __future__ import annotations

import copy
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
    result_path.write_text(json.dumps({'schema_version': 1, 'matrix_id': 'project-os-ui-state-matrix', 'matrix_sha256': '0' * 64, 'timestamp': 'never', 'results': []}), encoding='utf-8')
    with pytest.raises(MatrixContractError, match='timestamp|not bound'):
        validate_matrix(MATRIX_PATH, SPEC_PATH, result_path)
