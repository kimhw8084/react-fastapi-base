#!/usr/bin/env python3
"""Validate the canonical UI state matrix, executable references and results."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / 'frontend/tests/e2e/ui-state-matrix.json'
SPEC_PATH = ROOT / 'frontend/tests/e2e/uiqa.spec.ts'
RESULTS_PATH = ROOT / 'evidence/current/uiqa/ui-state-matrix-results.json'
REQUIRED_STATE_CLASSES = {'normal', 'loading', 'empty', 'error', 'permission', 'selection'}
DIMENSION_PATTERN = re.compile(r'^[a-z][a-z0-9-]*(?:\.[a-z0-9-]+)*$')
STATE_ID_PATTERN = re.compile(r'^[a-z][a-z0-9-]{2,80}$')
TEST_ID_PATTERN = re.compile(r'^uiqa-[0-9]{3}$')
LEGACY_ID_PATTERN = re.compile(r'^UIQA-[0-9]{3}$')
COMMIT_PATTERN = re.compile(r'^[0-9a-f]{40}$')
SHA256_PATTERN = re.compile(r'^[0-9a-f]{64}$')
SECRET_PATTERN = re.compile(r'(?:accesskey|authorization|bearer|credential|password|secret|token)', re.IGNORECASE)


class MatrixContractError(ValueError):
    """Raised when the matrix or executable/evidence bindings are invalid."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as error:
        raise MatrixContractError(f'Cannot read valid JSON from {path}: {error}') from error
    if not isinstance(value, dict):
        raise MatrixContractError(f'{path} must contain a JSON object.')
    return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise MatrixContractError(message)


def _relative_artifact(locator: str) -> Path:
    path = Path(locator)
    _require(not path.is_absolute(), f'Artifact locator must be relative: {locator!r}')
    _require('..' not in path.parts, f'Artifact locator may not escape the repository: {locator!r}')
    _require(locator.startswith('evidence/current/uiqa/rendered/'), f'Artifact must remain in the UIQA rendered family: {locator!r}')
    _require(not SECRET_PATTERN.search(locator), f'Artifact locator contains secret-like text: {locator!r}')
    return ROOT / path


def _matrix_rows(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    _require(matrix.get('schema_version') == 1, 'UI state matrix schema_version must be 1.')
    _require(matrix.get('matrix_id') == 'project-os-ui-state-matrix', 'Unexpected UI state matrix identity.')
    _require(matrix.get('source_of_truth') == 'frontend/tests/e2e/ui-state-matrix.json', 'Matrix source_of_truth must name the canonical registry.')
    required_dimensions = matrix.get('required_dimensions')
    _require(isinstance(required_dimensions, list) and required_dimensions, 'Matrix required_dimensions must be a non-empty list.')
    _require(len(required_dimensions) == len(set(required_dimensions)), 'Matrix required_dimensions contain duplicates.')
    _require(all(isinstance(value, str) and DIMENSION_PATTERN.fullmatch(value) for value in required_dimensions), 'Matrix contains an invalid required dimension.')
    state_classes = matrix.get('material_state_classes')
    _require(state_classes == sorted(state_classes), 'Matrix material_state_classes must be deterministic and sorted.')
    _require(set(state_classes) == REQUIRED_STATE_CLASSES, 'Matrix must enumerate exactly the required material state classes.')
    rows = matrix.get('rows')
    _require(isinstance(rows, list) and rows, 'Matrix rows must be a non-empty list.')
    _require(len({row.get('state_id') for row in rows}) == len(rows), 'Matrix contains duplicate state IDs.')
    _require(len({row.get('browser_test_id') for row in rows}) == len(rows), 'Matrix contains duplicate browser test IDs.')
    return rows


def _validate_rows(matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = _matrix_rows(matrix)
    global_dimensions = set(matrix['required_dimensions'])
    by_state: dict[str, dict[str, Any]] = {}
    for row in rows:
        state_id = row.get('state_id')
        _require(isinstance(state_id, str) and STATE_ID_PATTERN.fullmatch(state_id), f'Invalid or missing state_id: {state_id!r}')
        by_state[state_id] = row
        for field in ('surface_component_family', 'material_state_class', 'applicability', 'deterministic_setup_fixture', 'semantic_expectations', 'required_evidence', 'browser_test_id'):
            _require(field in row, f'{state_id} is missing required field {field!r}.')
        state_class = row['material_state_class']
        _require(state_class in REQUIRED_STATE_CLASSES, f'{state_id} uses unknown material state class {state_class!r}.')
        applicability = row['applicability']
        _require(applicability in {'applicable', 'not_applicable'}, f'{state_id} has invalid applicability {applicability!r}.')
        if applicability == 'not_applicable':
            _require(isinstance(row.get('applicability_rationale'), str) and row['applicability_rationale'].strip(), f'{state_id} must explain why it is not applicable.')
        else:
            _require(isinstance(row.get('browser_test_id'), str) and TEST_ID_PATTERN.fullmatch(row['browser_test_id']), f'{state_id} needs a stable browser_test_id.')
        dimensions = row.get('required_dimensions')
        _require(isinstance(dimensions, list) and dimensions, f'{state_id} must require at least one dimension.')
        _require(len(dimensions) == len(set(dimensions)), f'{state_id} contains duplicate required dimensions.')
        _require(set(dimensions) <= global_dimensions, f'{state_id} names a dimension not present in matrix.required_dimensions.')
        semantics = row['semantic_expectations']
        _require(isinstance(semantics, list) and semantics and all(isinstance(value, str) and value.strip() for value in semantics), f'{state_id} must have semantic expectations.')
        evidence = row['required_evidence']
        _require(isinstance(evidence, dict), f'{state_id} required_evidence must be an object.')
        artifacts = evidence.get('artifact_locators')
        _require(isinstance(artifacts, list) and artifacts and len(artifacts) == len(set(artifacts)), f'{state_id} must have unique required evidence artifacts.')
        for artifact in artifacts:
            _require(isinstance(artifact, str), f'{state_id} has a non-string artifact locator.')
            _relative_artifact(artifact)
        claims = evidence.get('claims')
        _require(isinstance(claims, list) and claims and all(isinstance(value, str) and value.strip() for value in claims), f'{state_id} must declare evidence claims.')
        _require(evidence.get('axe_serious_critical') is True, f'{state_id} must retain the serious/critical axe release assertion.')
        test_id = row['browser_test_id']
        legacy = row.get('legacy_uiqa_ids', [])
        _require(isinstance(legacy, list) and all(isinstance(value, str) and LEGACY_ID_PATTERN.fullmatch(value) for value in legacy), f'{state_id} has invalid legacy UIQA IDs.')
    represented = {row['material_state_class'] for row in rows if row['applicability'] == 'applicable'}
    _require(represented == REQUIRED_STATE_CLASSES, 'Every material state class must be represented by an applicable row or explicit inapplicability.')
    represented_dimensions = {dimension for row in rows if row['applicability'] == 'applicable' for dimension in row['required_dimensions']}
    _require(represented_dimensions == global_dimensions, 'A required dimension has disappeared from applicable matrix coverage.')
    return by_state


def _executable_refs(spec_path: Path) -> list[str]:
    try:
        source = spec_path.read_text(encoding='utf-8')
    except OSError as error:
        raise MatrixContractError(f'Cannot read UIQA executable coverage: {error}') from error
    return re.findall(r"matrixTest\(\s*['\"]([^'\"]+)['\"]", source)


def _validate_executable_coverage(by_state: dict[str, dict[str, Any]], spec_path: Path) -> None:
    refs = _executable_refs(spec_path)
    _require(len(refs) == len(set(refs)), 'UIQA executable coverage references a matrix state more than once.')
    known = set(by_state)
    unknown = sorted(set(refs) - known)
    _require(not unknown, f'UIQA executable coverage references unknown state IDs: {", ".join(unknown)}.')
    applicable = {state_id for state_id, row in by_state.items() if row['applicability'] == 'applicable'}
    missing = sorted(applicable - set(refs))
    _require(not missing, f'Applicable matrix rows have no executable browser coverage: {", ".join(missing)}.')
    extra = sorted(set(refs) - applicable)
    _require(not extra, f'Executable coverage references rows that are not applicable: {", ".join(extra)}.')
    expected_by_test = {row['browser_test_id']: state_id for state_id, row in by_state.items() if row['applicability'] == 'applicable'}
    _require(len(expected_by_test) == len(applicable), 'Applicable browser test IDs must be unique.')


def _validate_results(matrix_path: Path, by_state: dict[str, dict[str, Any]], results_path: Path) -> None:
    results = _load(results_path)
    _require(results.get('schema_version') == 1, 'UIQA result manifest schema_version must be 1.')
    _require(results.get('matrix_id') == 'project-os-ui-state-matrix', 'UIQA result manifest matrix_id is unknown.')
    _require(results.get('matrix_sha256') == hashlib.sha256(matrix_path.read_bytes()).hexdigest(), 'UIQA result manifest is not bound to the canonical matrix bytes.')
    _require('timestamp' not in results and 'created_at' not in results, 'UIQA result metadata must be deterministic and may not contain timestamps.')
    source_commit = results.get('source_commit')
    _require(source_commit is None or (isinstance(source_commit, str) and COMMIT_PATTERN.fullmatch(source_commit)), 'UIQA result source_commit must be a full commit SHA or null.')
    rows = results.get('results')
    _require(isinstance(rows, list), 'UIQA result manifest results must be a list.')
    expected_ids = {state_id for state_id, row in by_state.items() if row['applicability'] == 'applicable'}
    actual_ids = [row.get('state_id') for row in rows if isinstance(row, dict)]
    _require(len(actual_ids) == len(set(actual_ids)), 'UIQA result manifest contains duplicate state IDs.')
    _require(set(actual_ids) == expected_ids, 'UIQA result manifest rows do not exactly match applicable matrix rows.')
    for result in rows:
        state_id = result.get('state_id')
        _require(state_id in by_state, f'UIQA result manifest references unknown state ID: {state_id!r}.')
        row = by_state[state_id]
        _require(result.get('browser_test_id') == row['browser_test_id'], f'{state_id} result browser_test_id drifted from the matrix.')
        _require(result.get('status') == 'PASS', f'{state_id} has no passing browser result.')
        _require(sorted(result.get('exercised_dimensions', [])) == sorted(row['required_dimensions']), f'{state_id} result dimensions do not match the matrix.')
        artifacts = result.get('artifact_locators')
        _require(sorted(artifacts or []) == sorted(row['required_evidence']['artifact_locators']), f'{state_id} result artifacts do not match the matrix.')
        for artifact in artifacts:
            _require(_relative_artifact(artifact).is_file(), f'{state_id} evidence artifact is missing: {artifact}.')
    _require(results.get('overall_status') == 'PASS', 'UIQA result manifest overall_status must be PASS.')
    _require(results.get('result_kind') == 'browser-computed-uiqa', 'UIQA result manifest has an unexpected result kind.')
    _require(not SECRET_PATTERN.search(json.dumps(results, sort_keys=True)), 'UIQA result manifest contains secret-like metadata.')


def validate_matrix(matrix_path: Path = MATRIX_PATH, spec_path: Path = SPEC_PATH, results_path: Path | None = None) -> dict[str, Any]:
    matrix = _load(matrix_path)
    by_state = _validate_rows(matrix)
    _validate_executable_coverage(by_state, spec_path)
    if results_path is not None:
        _validate_results(matrix_path, by_state, results_path)
    return {
        'schema_version': 1,
        'matrix_id': matrix['matrix_id'],
        'matrix_sha256': hashlib.sha256(matrix_path.read_bytes()).hexdigest(),
        'rows': len(by_state),
        'state_classes': sorted({row['material_state_class'] for row in by_state.values()}),
        'dimensions': sorted({dimension for row in by_state.values() for dimension in row['required_dimensions']}),
        'executable_coverage': len(_executable_refs(spec_path)),
        'results_checked': results_path is not None,
        'status': 'PASS',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matrix', type=Path, default=MATRIX_PATH)
    parser.add_argument('--spec', type=Path, default=SPEC_PATH)
    parser.add_argument('--results', type=Path, default=None)
    args = parser.parse_args()
    try:
        report = validate_matrix(args.matrix.resolve(), args.spec.resolve(), args.results.resolve() if args.results else None)
    except MatrixContractError as error:
        print(f'UI state matrix contract FAILED: {error}')
        return 1
    print(f"UI state matrix contract PASS: {report['rows']} rows, {report['executable_coverage']} executable references, {len(report['dimensions'])} dimensions.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
