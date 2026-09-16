#!/usr/bin/env python3
"""Compare a generated OpenAPI contract with a Git-resolved review baseline.

The checker intentionally proves only conservative compatibility cases. It
does not invent a baseline from a copied file or compare application semver.
Exit codes are 0 for PASS, 1 for FAIL and 2 for BLOCKED.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / 'contracts/openapi.json'
METHODS = {'get', 'post', 'put', 'delete', 'patch'}
STATUS_CODES = {'PASS': 0, 'FAIL': 1, 'BLOCKED': 2}


def _change(classification: str, kind: str, location: str, message: str) -> dict[str, str]:
    return {'classification': classification, 'kind': kind, 'location': location, 'message': message}


def _metadata(document: dict[str, Any]) -> tuple[int | None, int | None, str]:
    info = document.get('info')
    if not isinstance(info, dict):
        return None, None, 'missing info object'
    major = info.get('x-api-major')
    revision = info.get('x-api-contract-revision')
    if isinstance(major, bool) or not isinstance(major, int):
        major = None
    if isinstance(revision, bool) or not isinstance(revision, int):
        revision = None
    if major is not None and revision is not None:
        return major, revision, 'explicit OpenAPI metadata'

    # The initial repository contract predates explicit metadata. Its v1 path
    # family is a trustworthy major hint, while revision zero means "before
    # the explicit revision policy".
    path_majors = {
        match.group(1)
        for path in document.get('paths', {})
        if isinstance(path, str)
        for match in [re.match(r'^/api/v(\d+)(?:/|$)', path)]
        if match
    }
    if len(path_majors) == 1:
        return int(next(iter(path_majors))), 0, 'legacy API path prefix; revision 0'
    return major, revision, 'missing or ambiguous API metadata'


def _resolved(schema: Any, document: dict[str, Any]) -> Any:
    if not isinstance(schema, dict) or '$ref' not in schema:
        return schema
    reference = schema['$ref']
    if not isinstance(reference, str) or not reference.startswith('#/components/schemas/'):
        return schema
    current: Any = document
    for part in reference[2:].split('/'):
        if not isinstance(current, dict) or part not in current:
            return schema
        current = current[part]
    return current


def _refs(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        reference = value.get('$ref')
        if isinstance(reference, str) and reference.startswith('#/components/schemas/'):
            found.add(reference.rsplit('/', 1)[-1])
        for child in value.values():
            found.update(_refs(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_refs(child))
    return found


def _component_modes(document: dict[str, Any]) -> dict[str, str]:
    modes: dict[str, set[str]] = defaultdict(set)
    for item in document.get('paths', {}).values():
        if not isinstance(item, dict):
            continue
        for method, operation in item.items():
            if method not in METHODS or not isinstance(operation, dict):
                continue
            body = operation.get('requestBody', {}).get('content', {}) if isinstance(operation.get('requestBody'), dict) else {}
            modes_for_body = _refs(body)
            for name in modes_for_body:
                modes[name].add('request')
            responses = operation.get('responses', {})
            for response in responses.values():
                for name in _refs(response):
                    modes[name].add('response')
    return {name: 'response' if 'response' in directions else 'request' for name, directions in modes.items()}


def _semantic(value: Any) -> Any:
    """Remove documentation-only OpenAPI fields before strict comparisons."""
    if isinstance(value, dict):
        return {
            key: _semantic(child)
            for key, child in value.items()
            if key not in {'title', 'description', 'examples', 'deprecated'}
        }
    if isinstance(value, list):
        return [_semantic(child) for child in value]
    return value


def _schema_compare(
    old: Any,
    new: Any,
    old_document: dict[str, Any],
    new_document: dict[str, Any],
    location: str,
    direction: str,
    changes: list[dict[str, str]],
    seen: set[tuple[int, int, str]],
) -> None:
    old = _resolved(old, old_document)
    new = _resolved(new, new_document)
    marker = (id(old), id(new), direction)
    if marker in seen:
        return
    seen.add(marker)
    if not isinstance(old, dict) or not isinstance(new, dict):
        if _semantic(old) != _semantic(new):
            changes.append(_change('breaking', 'schema-change', location, 'Schema shape changed in a way the checker cannot prove compatible.'))
        return

    old_combinator = next((key for key in ('oneOf', 'anyOf', 'allOf') if key in old), None)
    new_combinator = next((key for key in ('oneOf', 'anyOf', 'allOf') if key in new), None)
    if old_combinator or new_combinator:
        if old_combinator == new_combinator and isinstance(old.get(old_combinator), list) and isinstance(new.get(new_combinator), list):
            old_variants = [_semantic(value) for value in old[old_combinator]]
            new_variants = [_semantic(value) for value in new[new_combinator]]
            if direction == 'request' and all(value in new_variants for value in old_variants):
                for index, value in enumerate(old[old_combinator]):
                    match = next(item for item in new[new_combinator] if _semantic(item) == _semantic(value))
                    _schema_compare(value, match, old_document, new_document, f'{location}.{old_combinator}[{index}]', direction, changes, seen)
                if len(new_variants) > len(old_variants):
                    changes.append(_change('compatible_additive', 'schema-variant-addition', location, 'The request accepts an additional schema variant.'))
                return
            if old_variants == new_variants:
                for index, value in enumerate(old[old_combinator]):
                    _schema_compare(value, new[new_combinator][index], old_document, new_document, f'{location}.{old_combinator}[{index}]', direction, changes, seen)
                return
        if _semantic(old) != _semantic(new):
            changes.append(_change('breaking', 'schema-variant-change', location, 'Schema variants changed; existing client meanings are not proven stable.'))
        return

    old_enum = old.get('enum')
    new_enum = new.get('enum')
    if old_enum is not None or new_enum is not None:
        old_values = set(old_enum or []) if isinstance(old_enum, list) else None
        new_values = set(new_enum or []) if isinstance(new_enum, list) else None
        if old_values is None or new_values is None:
            if direction == 'request' and old_values is not None and new_values is None:
                changes.append(_change('compatible_additive', 'request-enum-widening', location, 'The request enum is no longer narrower than before.'))
            else:
                changes.append(_change('breaking', 'enum-change', location, 'Enum behavior changed and is not proven compatible.'))
            return
        if old_values == new_values:
            pass
        elif direction == 'request' and old_values <= new_values:
            changes.append(_change('compatible_additive', 'request-enum-addition', location, 'The request accepts additional enum values while preserving all existing values.'))
        else:
            changes.append(_change('breaking', 'enum-change', location, 'Existing enum values were removed or response enum behavior changed.'))
            return

    old_type = old.get('type')
    new_type = new.get('type')
    if old_type != new_type or old.get('format') != new.get('format'):
        changes.append(_change('breaking', 'type-change', location, 'Existing field type or format changed.'))
        return

    if old_type == 'object' or 'properties' in old or 'properties' in new:
        old_properties = old.get('properties', {})
        new_properties = new.get('properties', {})
        if not isinstance(old_properties, dict) or not isinstance(new_properties, dict):
            changes.append(_change('breaking', 'object-shape-change', location, 'Object properties are not machine-comparable.'))
            return
        old_required = set(old.get('required', []))
        new_required = set(new.get('required', []))
        for name in sorted(old_properties):
            child_location = f'{location}.{name}'
            if name not in new_properties:
                changes.append(_change('breaking', 'field-removal', child_location, 'An existing request/response field was removed or renamed.'))
                continue
            if name in old_required and name not in new_required:
                if direction == 'request':
                    changes.append(_change('compatible_additive', 'request-requiredness-widening', child_location, 'An existing request field became optional.'))
                else:
                    changes.append(_change('breaking', 'response-requiredness-change', child_location, 'An existing response field is no longer guaranteed.'))
            elif name not in old_required and name in new_required:
                changes.append(_change('breaking', 'requiredness-change', child_location, 'An existing field became required.'))
            _schema_compare(old_properties[name], new_properties[name], old_document, new_document, child_location, direction, changes, seen)
        for name in sorted(set(new_properties) - set(old_properties)):
            child_location = f'{location}.{name}'
            if name in new_required:
                changes.append(_change('breaking', 'required-field-addition', child_location, 'A new required request/response field was added.'))
            else:
                changes.append(_change('compatible_additive', 'optional-field-addition', child_location, 'An optional request/response field was added.'))
        old_additional = old.get('additionalProperties', True)
        new_additional = new.get('additionalProperties', True)
        if _semantic(old_additional) != _semantic(new_additional):
            if direction == 'request' and old_additional is False and new_additional is True:
                changes.append(_change('compatible_additive', 'request-object-widening', location, 'The request accepts additional object properties.'))
            else:
                changes.append(_change('breaking', 'object-acceptance-change', location, 'Object property acceptance changed.'))
            if isinstance(old_additional, dict) and isinstance(new_additional, dict):
                _schema_compare(old_additional, new_additional, old_document, new_document, f'{location}.[additionalProperties]', direction, changes, seen)
        return

    if old_type == 'array':
        _schema_compare(old.get('items', {}), new.get('items', {}), old_document, new_document, f'{location}[]', direction, changes, seen)

    constraint_keys = {
        'pattern', 'minLength', 'maxLength', 'minimum', 'maximum',
        'exclusiveMinimum', 'exclusiveMaximum', 'multipleOf', 'minItems',
        'maxItems', 'uniqueItems', 'default', 'const', 'readOnly', 'writeOnly',
    }
    for key in sorted(constraint_keys):
        if old.get(key) == new.get(key):
            continue
        if direction == 'request' and key in {'minLength', 'minimum', 'minItems'}:
            if (new.get(key) is None and old.get(key) is not None) or (new.get(key) is not None and old.get(key) is not None and new[key] < old[key]):
                changes.append(_change('compatible_additive', 'request-constraint-widening', location, f'Request constraint {key} was widened.'))
                continue
        if direction == 'request' and key in {'maxLength', 'maximum', 'maxItems'}:
            if (new.get(key) is None and old.get(key) is not None) or (new.get(key) is not None and old.get(key) is not None and new[key] > old[key]):
                changes.append(_change('compatible_additive', 'request-constraint-widening', location, f'Request constraint {key} was widened.'))
                continue
        changes.append(_change('breaking', 'schema-constraint-change', location, f'Existing schema constraint {key} changed.'))


def _parameters(item: dict[str, Any], operation: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    values = []
    for source in (item.get('parameters', []), operation.get('parameters', [])):
        if isinstance(source, list):
            values.extend(value for value in source if isinstance(value, dict))
    return {(str(value.get('in')), str(value.get('name'))): value for value in values}


def _compare_parameters(
    old: dict[tuple[str, str], dict[str, Any]],
    new: dict[tuple[str, str], dict[str, Any]],
    old_document: dict[str, Any],
    new_document: dict[str, Any],
    location: str,
    changes: list[dict[str, str]],
) -> None:
    for key, old_parameter in sorted(old.items()):
        parameter_location = f'{location}.{key[0]}:{key[1]}'
        new_parameter = new.get(key)
        if new_parameter is None:
            changes.append(_change('breaking', 'parameter-removal', parameter_location, 'An existing parameter was removed or renamed.'))
            continue
        old_required = bool(old_parameter.get('required'))
        new_required = bool(new_parameter.get('required'))
        if not old_required and new_required:
            changes.append(_change('breaking', 'parameter-requiredness', parameter_location, 'An optional parameter became required.'))
        elif old_required and not new_required and key[0] == 'response':
            changes.append(_change('breaking', 'parameter-requiredness', parameter_location, 'A required response parameter became optional.'))
        old_shape = {key: value for key, value in old_parameter.items() if key not in {'description', 'deprecated', 'examples', 'required'}}
        new_shape = {key: value for key, value in new_parameter.items() if key not in {'description', 'deprecated', 'examples', 'required'}}
        old_schema = old_shape.pop('schema', None)
        new_schema = new_shape.pop('schema', None)
        if _semantic(old_shape) != _semantic(new_shape):
            changes.append(_change('breaking', 'parameter-semantics', parameter_location, 'Parameter transport semantics changed.'))
        _schema_compare(old_schema, new_schema, old_document, new_document, parameter_location, 'request', changes, set())
    for key, parameter in sorted(new.items()):
        if key in old:
            continue
        if bool(parameter.get('required')) or key[0] == 'path':
            changes.append(_change('breaking', 'required-parameter-addition', f'{location}.{key[0]}:{key[1]}', 'A required parameter was added.'))
        else:
            changes.append(_change('compatible_additive', 'optional-parameter-addition', f'{location}.{key[0]}:{key[1]}', 'An optional request parameter was added.'))


def _compare_operation(
    path: str,
    method: str,
    old_item: dict[str, Any],
    new_item: dict[str, Any],
    old_operation: dict[str, Any],
    new_operation: dict[str, Any],
    old_document: dict[str, Any],
    new_document: dict[str, Any],
    changes: list[dict[str, str]],
) -> None:
    location = f'{method.upper()} {path}'
    if old_operation.get('operationId') != new_operation.get('operationId'):
        changes.append(_change('breaking', 'operation-rename', location, 'An existing operation was renamed.'))
    _compare_parameters(_parameters(old_item, old_operation), _parameters(new_item, new_operation), old_document, new_document, location, changes)

    old_body = old_operation.get('requestBody')
    new_body = new_operation.get('requestBody')
    if old_body is None and new_body is not None:
        if bool(new_body.get('required')):
            changes.append(_change('breaking', 'required-body-addition', location, 'A required request body was added.'))
        else:
            changes.append(_change('compatible_additive', 'optional-body-addition', location, 'An optional request body was added.'))
    elif old_body is not None and new_body is None:
        changes.append(_change('breaking', 'request-body-removal', location, 'An existing request body was removed.'))
    elif isinstance(old_body, dict) and isinstance(new_body, dict):
        if old_body.get('required') and not new_body.get('required'):
            changes.append(_change('compatible_additive', 'request-body-requiredness-widening', location, 'An existing request body became optional.'))
        elif not old_body.get('required') and new_body.get('required'):
            changes.append(_change('breaking', 'request-body-requiredness', location, 'An existing request body became required.'))
        old_content = old_body.get('content', {})
        new_content = new_body.get('content', {})
        if not isinstance(old_content, dict) or not isinstance(new_content, dict):
            changes.append(_change('breaking', 'request-content-change', location, 'Request content is not machine-comparable.'))
        else:
            for media, old_value in sorted(old_content.items()):
                if media not in new_content:
                    changes.append(_change('breaking', 'request-media-removal', f'{location} request {media}', 'An existing request media type was removed.'))
                    continue
                _schema_compare(old_value.get('schema', {}), new_content[media].get('schema', {}), old_document, new_document, f'{location} request {media}', 'request', changes, set())
            for media in sorted(set(new_content) - set(old_content)):
                changes.append(_change('breaking', 'request-media-addition', f'{location} request {media}', 'A new request media type changes transport behavior.'))

    old_responses = old_operation.get('responses', {})
    new_responses = new_operation.get('responses', {})
    if not isinstance(old_responses, dict) or not isinstance(new_responses, dict):
        changes.append(_change('breaking', 'response-change', location, 'Responses are not machine-comparable.'))
        return
    for status, old_response in sorted(old_responses.items()):
        if status not in new_responses:
            changes.append(_change('breaking', 'response-removal', f'{location} response {status}', 'An existing response variant was removed.'))
            continue
        new_response = new_responses[status]
        old_content = old_response.get('content', {}) if isinstance(old_response, dict) else {}
        new_content = new_response.get('content', {}) if isinstance(new_response, dict) else {}
        if not isinstance(old_content, dict) or not isinstance(new_content, dict):
            changes.append(_change('breaking', 'response-content-change', f'{location} response {status}', 'Response content is not machine-comparable.'))
            continue
        for media, old_value in sorted(old_content.items()):
            if media not in new_content:
                changes.append(_change('breaking', 'response-media-removal', f'{location} response {status} {media}', 'An existing response media type was removed.'))
                continue
            _schema_compare(old_value.get('schema', {}), new_content[media].get('schema', {}), old_document, new_document, f'{location} response {status} {media}', 'response', changes, set())
        for media in sorted(set(new_content) - set(old_content)):
            changes.append(_change('breaking', 'response-media-addition', f'{location} response {status} {media}', 'A new response media type changes transport behavior.'))
    for status in sorted(set(new_responses) - set(old_responses)):
        changes.append(_change('breaking', 'response-addition', f'{location} response {status}', 'A new response variant is not assumed safe for existing clients.'))


def compare_contracts(base: dict[str, Any], candidate: dict[str, Any], *, base_ref: str | None = None) -> dict[str, Any]:
    base_major, base_revision, base_metadata_source = _metadata(base)
    candidate_major, candidate_revision, candidate_metadata_source = _metadata(candidate)
    changes: list[dict[str, str]] = []
    report: dict[str, Any] = {
        'schema_version': 1,
        'result': 'PASS',
        'base_ref': base_ref,
        'base_api_major': base_major,
        'base_contract_revision': base_revision,
        'base_metadata_source': base_metadata_source,
        'api_major': candidate_major,
        'contract_revision': candidate_revision,
        'candidate_metadata_source': candidate_metadata_source,
        'changes': changes,
    }
    if base_major is None or base_revision is None:
        report['result'] = 'BLOCKED'
        report['reason'] = 'Baseline contract has missing or ambiguous API metadata/path family.'
        return report
    if candidate_major is None or candidate_revision is None or candidate_major < 1 or candidate_revision < 1:
        changes.append(_change('breaking', 'metadata-missing', 'info', 'Candidate contract must publish positive API major and contract revision metadata.'))
    elif candidate_major != base_major:
        changes.append(_change('breaking', 'api-major-change', 'info.x-api-major', 'API major changed; use a deliberate v2 path and migration/overlap plan.'))
    elif candidate_revision < base_revision:
        changes.append(_change('breaking', 'revision-regression', 'info.x-api-contract-revision', 'Contract revision moved backwards.'))

    base_paths = base.get('paths')
    candidate_paths = candidate.get('paths')
    if not isinstance(base_paths, dict) or not isinstance(candidate_paths, dict):
        report['result'] = 'BLOCKED'
        report['reason'] = 'Baseline or candidate does not contain a valid OpenAPI paths object.'
        return report
    for path, old_item in sorted(base_paths.items()):
        if path not in candidate_paths:
            changes.append(_change('breaking', 'operation-removal', path, 'An existing API path was removed or renamed.'))
            continue
        new_item = candidate_paths[path]
        if not isinstance(old_item, dict) or not isinstance(new_item, dict):
            changes.append(_change('breaking', 'path-change', path, 'Path item is not machine-comparable.'))
            continue
        for method in sorted(METHODS):
            old_operation = old_item.get(method)
            new_operation = new_item.get(method)
            if old_operation is None:
                continue
            if new_operation is None:
                changes.append(_change('breaking', 'operation-removal', f'{method.upper()} {path}', 'An existing API operation was removed.'))
                continue
            if not isinstance(old_operation, dict) or not isinstance(new_operation, dict):
                changes.append(_change('breaking', 'operation-change', f'{method.upper()} {path}', 'Operation is not machine-comparable.'))
                continue
            _compare_operation(path, method, old_item, new_item, old_operation, new_operation, base, candidate, changes)
        for method in sorted((set(new_item) - set(old_item)) & METHODS):
            changes.append(_change('compatible_additive', 'operation-addition', f'{method.upper()} {path}', 'A new API operation was added.'))
    for path, item in sorted(candidate_paths.items()):
        if path in base_paths or not isinstance(item, dict):
            continue
        for method in sorted(set(item) & METHODS):
            changes.append(_change('compatible_additive', 'operation-addition', f'{method.upper()} {path}', 'A new API operation was added.'))

    base_schemas = base.get('components', {}).get('schemas', {}) if isinstance(base.get('components'), dict) else {}
    candidate_schemas = candidate.get('components', {}).get('schemas', {}) if isinstance(candidate.get('components'), dict) else {}
    if not isinstance(base_schemas, dict) or not isinstance(candidate_schemas, dict):
        report['result'] = 'BLOCKED'
        report['reason'] = 'Baseline or candidate does not contain a valid OpenAPI schema component map.'
        return report
    component_modes = _component_modes(candidate)
    for name, old_schema in sorted(base_schemas.items()):
        location = f'components.schemas.{name}'
        if name not in candidate_schemas:
            changes.append(_change('breaking', 'schema-removal', location, 'An existing schema component was removed or renamed.'))
            continue
        _schema_compare(old_schema, candidate_schemas[name], base, candidate, location, component_modes.get(name, 'response'), changes, set())

    if changes and candidate_revision is not None and base_revision is not None and candidate_revision <= base_revision:
        changes.append(_change('breaking', 'revision-not-incremented', 'info.x-api-contract-revision', 'Any externally observable contract change requires a higher revision.'))
    report['compatible_changes'] = sum(change['classification'] == 'compatible_additive' for change in changes)
    report['breaking_changes'] = sum(change['classification'] == 'breaking' for change in changes)
    report['result'] = 'FAIL' if report['breaking_changes'] else 'PASS'
    return report


def _git_output(*arguments: str) -> tuple[int, str]:
    result = subprocess.run(['git', *arguments], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return result.returncode, result.stdout


def _load_baseline(reference: str) -> tuple[str | None, dict[str, Any] | None, str | None]:
    code, output = _git_output('rev-parse', '--verify', f'{reference}^{{commit}}')
    if code != 0:
        return None, None, f'Unable to resolve Git baseline {reference!r}: {output.strip()}'
    resolved = output.strip()
    ancestor_code, ancestor_output = _git_output('merge-base', '--is-ancestor', resolved, 'HEAD')
    if ancestor_code != 0:
        return resolved, None, f'Git baseline {resolved} is not an ancestor of the candidate HEAD: {ancestor_output.strip()}'
    code, output = _git_output('show', f'{resolved}:contracts/openapi.json')
    if code != 0:
        return resolved, None, f'Git baseline {resolved} does not contain contracts/openapi.json: {output.strip()}'
    try:
        return resolved, json.loads(output), None
    except json.JSONDecodeError as error:
        return resolved, None, f'Git baseline {resolved} contains invalid contracts/openapi.json: {error}'


def _load_candidate(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, f'Candidate contract is missing: {path}'
    try:
        return json.loads(path.read_text(encoding='utf-8')), None
    except (OSError, json.JSONDecodeError) as error:
        return None, f'Candidate contract is unavailable or invalid: {error}'


def _blocked_report(reason: str, base_ref: str, candidate: Path) -> dict[str, Any]:
    return {
        'schema_version': 1,
        'result': 'BLOCKED',
        'base_ref': base_ref,
        'candidate_contract': str(candidate.relative_to(ROOT)) if candidate.is_relative_to(ROOT) else str(candidate),
        'reason': reason,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-ref', '--base-sha', dest='base_ref', default=os.environ.get('API_COMPATIBILITY_BASE_SHA') or 'origin/main')
    parser.add_argument('--candidate', type=Path, default=CONTRACT)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    candidate_path = args.candidate if args.candidate.is_absolute() else ROOT / args.candidate
    output_path = args.output if args.output.is_absolute() else ROOT / args.output
    resolved, base, baseline_error = _load_baseline(args.base_ref)
    if baseline_error:
        report = _blocked_report(baseline_error, args.base_ref, candidate_path)
        if resolved:
            report['resolved_base_sha'] = resolved
    else:
        candidate, candidate_error = _load_candidate(candidate_path)
        if candidate_error:
            report = _blocked_report(candidate_error, args.base_ref, candidate_path)
            report['resolved_base_sha'] = resolved
        else:
            report = compare_contracts(base, candidate, base_ref=resolved)
            report['resolved_base_sha'] = resolved
            report['candidate_contract'] = str(candidate_path.relative_to(ROOT)) if candidate_path.is_relative_to(ROOT) else str(candidate_path)
    source_code, source_output = _git_output('rev-parse', 'HEAD')
    report['source_commit'] = source_output.strip() if source_code == 0 else None
    report['created_at'] = datetime.now(timezone.utc).isoformat()
    report['candidate_contract_sha256'] = hashlib.sha256(candidate_path.read_bytes()).hexdigest() if candidate_path.is_file() else None
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(f"{report['result']} — API compatibility report: {output_path}")
    return STATUS_CODES[report['result']]


if __name__ == '__main__':
    raise SystemExit(main())
