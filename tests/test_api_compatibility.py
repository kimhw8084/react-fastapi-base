from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('check_api_compatibility', ROOT / 'scripts/check_api_compatibility.py')
CHECKER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(CHECKER)


def schema(kind: str = 'string', **extra):
    return {'type': kind, **extra}


def operation(*, request=None, response=None, operation_id='listItems'):
    value = {
        'operationId': operation_id,
        'responses': {'200': {'description': 'OK', 'content': {'application/json': {'schema': response or schema('string')}}}},
    }
    if request is not None:
        value['requestBody'] = {'required': True, 'content': {'application/json': {'schema': request}}}
    return value


def contract(*, revision=1, operations=None):
    return {
        'openapi': '3.1.0',
        'info': {'title': 'Test', 'version': '1.0.0', 'x-api-major': 1, 'x-api-contract-revision': revision},
        'paths': operations or {'/api/v1/items': {'get': operation()}},
        'components': {'schemas': {}},
    }


def result(base, candidate):
    return CHECKER.compare_contracts(base, candidate, base_ref='base-sha')


def test_new_operation_is_compatible():
    base = contract()
    candidate = deepcopy(base)
    candidate['info']['x-api-contract-revision'] = 2
    candidate['paths']['/api/v1/health'] = {'get': operation(operation_id='health')}
    report = result(base, candidate)
    assert report['result'] == 'PASS'
    assert any(change['kind'] == 'operation-addition' for change in report['changes'])


def test_optional_request_and_response_fields_are_compatible():
    request = {'type': 'object', 'required': ['name'], 'properties': {'name': schema()}}
    response = {'type': 'object', 'required': ['id'], 'properties': {'id': schema()}}
    base = contract(operations={'/api/v1/items': {'post': operation(request=request, response=response, operation_id='createItem')}})
    candidate = deepcopy(base)
    candidate['info']['x-api-contract-revision'] = 2
    candidate['paths']['/api/v1/items']['post']['requestBody']['content']['application/json']['schema']['properties']['note'] = schema()
    candidate['paths']['/api/v1/items']['post']['requestBody']['content']['application/json']['schema']['required'] = ['name']
    candidate['paths']['/api/v1/items']['post']['responses']['200']['content']['application/json']['schema']['properties']['label'] = schema()
    report = result(base, candidate)
    assert report['result'] == 'PASS'
    assert report['breaking_changes'] == 0
    assert sum(change['kind'] == 'optional-field-addition' for change in report['changes']) == 2


def test_operation_and_field_removal_or_rename_is_breaking():
    base = contract(operations={'/api/v1/items': {'get': operation()}, '/api/v1/other': {'get': operation(operation_id='other')}})
    candidate = deepcopy(base)
    del candidate['paths']['/api/v1/other']
    candidate['paths']['/api/v1/items']['get']['responses']['200']['content']['application/json']['schema'] = {
        'type': 'object', 'required': ['id'], 'properties': {'renamed': schema()}
    }
    base['paths']['/api/v1/items']['get']['responses']['200']['content']['application/json']['schema'] = {
        'type': 'object', 'required': ['id'], 'properties': {'id': schema()}
    }
    report = result(base, candidate)
    assert report['result'] == 'FAIL'
    assert {change['kind'] for change in report['changes']} >= {'operation-removal', 'field-removal'}


def test_requiredness_type_and_nullability_changes_are_breaking():
    base_schema = {'type': 'object', 'required': ['name'], 'properties': {'name': schema(), 'count': schema('integer')}}
    base = contract(operations={'/api/v1/items': {'post': operation(request=deepcopy(base_schema), response=deepcopy(base_schema), operation_id='saveItem')}})
    candidate = deepcopy(base)
    candidate['info']['x-api-contract-revision'] = 2
    request_schema = candidate['paths']['/api/v1/items']['post']['requestBody']['content']['application/json']['schema']
    request_schema['required'].append('count')
    request_schema['properties']['count'] = {'anyOf': [schema('integer'), {'type': 'null'}]}
    response_schema = candidate['paths']['/api/v1/items']['post']['responses']['200']['content']['application/json']['schema']
    response_schema['properties']['count'] = schema('number')
    report = result(base, candidate)
    assert report['result'] == 'FAIL'
    assert {change['kind'] for change in report['changes']} >= {'requiredness-change', 'schema-variant-change', 'type-change'}


def test_request_enum_widening_is_compatible_but_response_enum_change_is_not():
    base = contract(operations={'/api/v1/items': {'post': operation(request=schema('string', enum=['open']), response=schema('string', enum=['ok']), operation_id='setState')}})
    candidate = deepcopy(base)
    candidate['info']['x-api-contract-revision'] = 2
    candidate['paths']['/api/v1/items']['post']['requestBody']['content']['application/json']['schema']['enum'].append('closed')
    candidate['paths']['/api/v1/items']['post']['responses']['200']['content']['application/json']['schema']['enum'].append('warning')
    report = result(base, candidate)
    assert report['result'] == 'FAIL'
    assert any(change['kind'] == 'request-enum-addition' for change in report['changes'])
    assert any(change['kind'] == 'enum-change' and change['classification'] == 'breaking' for change in report['changes'])


def test_contract_revision_must_increase_for_observable_changes():
    base = contract(revision=4)
    candidate = deepcopy(base)
    candidate['paths']['/api/v1/new'] = {'get': operation(operation_id='new')}
    unchanged_revision = result(base, candidate)
    assert unchanged_revision['result'] == 'FAIL'
    assert any(change['kind'] == 'revision-not-incremented' for change in unchanged_revision['changes'])
    candidate['info']['x-api-contract-revision'] = 5
    assert result(base, candidate)['result'] == 'PASS'
    candidate['info']['x-api-contract-revision'] = 3
    assert result(base, candidate)['result'] == 'FAIL'
    assert any(change['kind'] == 'revision-regression' for change in result(base, candidate)['changes'])


def test_missing_baseline_is_blocked_and_report_is_machine_readable(tmp_path):
    output = tmp_path / 'compatibility.json'
    completed = subprocess.run(
        [sys.executable, 'scripts/check_api_compatibility.py', '--base-ref', 'missing-review-base', '--output', str(output)],
        cwd=ROOT, text=True, capture_output=True,
    )
    assert completed.returncode == 2
    report = json.loads(output.read_text())
    assert report['result'] == 'BLOCKED'
    assert 'Unable to resolve Git baseline' in report['reason']
