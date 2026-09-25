"""Read-only, source-bound repository and environment discovery."""
from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import re
import subprocess
import copy
from pathlib import Path
from urllib.parse import urlsplit

from scripts.release_version import current_release_paths, parse_candidate_version
from scripts.source_manifest import executable_source_commit, source_digest
from scripts.work_qualification.reasons import REASONS
from scripts.work_qualification.safety import safe_path_name, safe_text_hash

ROOT = Path(__file__).resolve().parents[2]
BASE_COMMIT = '67ec2ce5ec44d38ee44d22602035c2554a08e00d'
BASE_TREE = '092a56eb25dab69d1bdcce74f66af4b2dff8dad1'
CHANGE = 'CHG-235'
BRANCH = 'codex/react-fastapi-base-work-env-qualification-harness-v1'
_SECRET_RISK_PATH = re.compile(r'(?i)(?:^|[/_.-])(?:secrets?|credentials?|passwords?|tokens?|sessions?|access[_-]?keys?)(?=$|[/_.-])|(?:^|/)\.env(?:\.|/|$)|(?:^|/)key\.pem$')


def _git(*args: str) -> str:
    result = subprocess.run(['git', *args], cwd=ROOT, capture_output=True, check=False)
    if result.returncode:
        raise ValueError('Repository metadata is unavailable.')
    return result.stdout.decode('utf-8', errors='replace').strip()


def _status_paths() -> list[str]:
    raw = subprocess.run(
        ['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all'],
        cwd=ROOT, capture_output=True, check=False,
    )
    if raw.returncode:
        return []
    parts = raw.stdout.split(b'\x00')
    names: list[str] = []
    index = 0
    while index < len(parts):
        item = parts[index]
        index += 1
        if len(item) >= 4:
            name = item[3:].decode('utf-8', errors='replace')
            if name:
                names.append(name)
            if item[:2] in (b'R ', b' C', b'R?', b'C?') and index < len(parts):
                original = parts[index].decode('utf-8', errors='replace')
                if original:
                    names.append(original)
                index += 1
    return names


def _changed_paths() -> list[str]:
    return sorted({safe_path_name(name) for name in _status_paths()})


def _hash_repo_file(relative: str) -> str | None:
    if relative.startswith('['):
        return None
    path = ROOT / relative
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() and not path.is_symlink() else None
    except OSError:
        return None


def _repository_matches() -> bool:
    try:
        remote = _git('remote', 'get-url', 'origin')
    except ValueError:
        remote = ''
    if remote:
        candidate = remote
        if candidate.startswith('git@') and ':' in candidate:
            host, path = candidate[4:].split(':', 1)
        else:
            parsed = urlsplit(candidate)
            host, path = (parsed.hostname or '').casefold(), parsed.path.lstrip('/')
        path = path.removesuffix('.git').strip('/')
        return host.casefold() in {'github.com', 'www.github.com'} and path.casefold() == 'kimhw8084/react-fastapi-base'
    try:
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        project = (ROOT / 'backend/pyproject.toml').read_text(encoding='utf-8')
        return readme.startswith('# react-fastapi-base') and 'name = "react-fastapi-base-backend"' in project
    except OSError:
        return False


def _api_contract_changed() -> bool:
    try:
        current = json.loads((ROOT / 'contracts/openapi.json').read_text(encoding='utf-8'))
        base_raw = subprocess.run(
            ['git', 'show', f'{BASE_COMMIT}:contracts/openapi.json'], cwd=ROOT,
            capture_output=True, check=False,
        )
        if base_raw.returncode:
            return True
        base = json.loads(base_raw.stdout.decode('utf-8'))
        current = copy.deepcopy(current); base = copy.deepcopy(base)
        current.get('info', {}).pop('version', None)
        base.get('info', {}).pop('version', None)
        return current != base
    except (OSError, json.JSONDecodeError, UnicodeError, AttributeError):
        return True


def repository_identity() -> dict:
    version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    candidate = parse_candidate_version(version)
    head = _git('rev-parse', 'HEAD')
    tree = _git('rev-parse', 'HEAD^{tree}')
    branch = _git('branch', '--show-current')
    commit = executable_source_commit(ROOT)
    digest = source_digest()
    changed = _changed_paths()
    path_hashes = {path: _hash_repo_file(path) for path in changed}
    path_hashes = {key: value for key, value in path_hashes.items() if value}
    try:
        identity_path = current_release_paths(ROOT).identity
        identity = json.loads(identity_path.read_text(encoding='utf-8'))
        identity_ok = (
            identity.get('identity_type') == 'repository_release'
            and identity.get('project') == 'react-fastapi-base'
            and identity.get('candidate_version') == version
            and identity.get('verified_source_commit') == commit
            and identity.get('source_digest') == digest
            and identity.get('production_ready') is False
        )
    except (OSError, ValueError, json.JSONDecodeError, AttributeError):
        identity_path = current_release_paths(ROOT).identity
        identity_ok = False
        identity = {}
    try:
        api = (ROOT / 'backend/app/platform/version.py').read_text(encoding='utf-8')
        backend_major = int(re.search(r'^API_MAJOR\s*=\s*(\d+)', api, re.M).group(1))
        backend_revision = int(re.search(r'^API_CONTRACT_REVISION\s*=\s*(\d+)', api, re.M).group(1))
        generated = (ROOT / 'frontend/src/generated/schema.ts').read_text(encoding='utf-8')
        frontend_major = int(re.search(r'^export const API_MAJOR = (\d+)', generated, re.M).group(1))
        frontend_revision = int(re.search(r'^export const API_CONTRACT_REVISION = (\d+)', generated, re.M).group(1))
        api_compatible = backend_major == frontend_major and backend_revision >= frontend_revision
    except (OSError, AttributeError, ValueError):
        backend_major = backend_revision = frontend_major = frontend_revision = None
        api_compatible = False
    try:
        base_is_ancestor = subprocess.run(
            ['git', 'merge-base', '--is-ancestor', BASE_COMMIT, 'HEAD'], cwd=ROOT,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
        ).returncode == 0
    except OSError:
        base_is_ancestor = False
    try:
        base_tree_matches = _git('rev-parse', f'{BASE_COMMIT}^{{tree}}') == BASE_TREE
    except ValueError:
        base_tree_matches = False
    repository_matches = _repository_matches()
    if not base_is_ancestor or not base_tree_matches or not repository_matches or branch != BRANCH:
        head_reason = 'SRC_HEAD_MISMATCH'
    else:
        head_reason = None
    codes: list[str] = []
    if head_reason:
        codes.append(head_reason)
    if changed:
        codes.append('SRC_DIRTY_WORKTREE')
    if not identity_ok:
        codes.append('SRC_RELEASE_IDENTITY_MISMATCH')
    if not api_compatible:
        codes.append('SRC_API_INCOMPATIBLE')
    if not codes:
        codes.append('SRC_EXACT')
    secret_risk = any(
        _SECRET_RISK_PATH.search(path) and not path.casefold().endswith(('.env.example', '.env.sample', '.env.template'))
        for path in _status_paths()
    )
    return {
        'project': 'react-fastapi-base', 'change': CHANGE, 'candidate_version': candidate.version,
        'branch': branch, 'head': head, 'head_tree': tree,
        'executable_source_commit': commit, 'source_digest': digest,
        'target_base_commit': BASE_COMMIT, 'target_base_tree': BASE_TREE,
        'target_base_is_ancestor': base_is_ancestor,
        'target_base_tree_matches': base_tree_matches,
        'repository_identity_matches': repository_matches,
        'api_contract_changed': _api_contract_changed(),
        'release_identity': {'present': identity_path.is_file(), 'matches_current_source': identity_ok},
        'api': {'backend_major': backend_major, 'backend_revision': backend_revision,
                'frontend_major': frontend_major, 'frontend_revision': frontend_revision,
                'compatible': api_compatible},
        'changed_paths': changed, 'changed_path_hashes': path_hashes,
        'secret_risk_detected': secret_risk,
        'reason_codes': codes,
        'status': (
            'FAIL' if any(code in {'SRC_HEAD_MISMATCH', 'SRC_API_INCOMPATIBLE'} for code in codes)
            else ('ATTENTION' if changed else ('BLOCKED' if 'SRC_RELEASE_IDENTITY_MISMATCH' in codes else 'PASS'))
        ),
    }


def configuration_observations() -> dict:
    """Inspect only enumerated settings; never serialize any setting value."""
    environment = os.environ.get('BASE_ENVIRONMENT', '')
    profile = os.environ.get('BASE_PROFILE', '')
    data_root = os.environ.get('BASE_DATA_ROOT', '')
    deployment_id = os.environ.get('BASE_DEPLOYMENT_ID', '')
    origins = _json_list(os.environ.get('BASE_ALLOWED_ORIGINS', ''))
    hosts = _json_list(os.environ.get('BASE_ALLOWED_HOSTS', ''))
    csrf = os.environ.get('BASE_CSRF_SECRET', '')
    scanner = os.environ.get('BASE_ATTACHMENT_UPLOAD_MODE', 'scanner_required')
    prereq = os.environ.get('BASE_QUALIFICATION_PREREQUISITES_FILE', '')
    final = os.environ.get('BASE_QUALIFICATION_FILE', '')
    docs_value = os.environ.get('BASE_ENABLE_DOCS', '').casefold()
    errors: list[str] = []
    if environment != 'qualification': errors.append('CFG_NOT_QUALIFICATION')
    if profile != 'company': errors.append('CFG_PROFILE_NOT_COMPANY')
    if not data_root or not Path(data_root).is_absolute(): errors.append('CFG_DATA_ROOT_INVALID')
    if not deployment_id or deployment_id.casefold() == 'local': errors.append('CFG_DEPLOYMENT_ID_MISSING')
    valid_origins = [item for item in origins if _valid_https_origin(item)]
    valid_hosts = [item for item in hosts if _valid_host(item)]
    if not valid_origins or len(valid_origins) != len(origins) or not valid_hosts or len(valid_hosts) != len(hosts) or any(urlsplit(item).hostname not in valid_hosts for item in valid_origins):
        errors.append('CFG_ORIGIN_OR_HOST_INVALID')
    if len(csrf) < 32: errors.append('CFG_CSRF_INVALID')
    if scanner not in {'scanner_required', 'trusted_types', 'disabled'}: errors.append('CFG_SCANNER_REQUIRED_MISSING')
    if scanner == 'scanner_required':
        errors.append('CFG_SCANNER_REQUIRED_MISSING')
    if environment in {'qualification', 'production'} and docs_value in {'1', 'true', 'yes'}:
        errors.append('CFG_DOCS_EXPOSED')
    prereq_exists = bool(prereq and Path(prereq).is_file())
    final_exists = bool(final and Path(final).is_file())
    if not prereq_exists and environment == 'qualification': errors.append('CFG_QUALIFICATION_PREREQS_MISSING')
    return {
        'status': 'FAIL' if errors else 'PASS', 'reason_codes': sorted(set(errors)),
        'environment': environment if environment in {'development', 'test', 'qualification', 'production'} else 'unknown',
        'profile': profile if profile in {'development', 'company'} else 'unknown',
        'data_root_absolute': bool(data_root and Path(data_root).is_absolute()),
        'deployment_id_present': bool(deployment_id and deployment_id.casefold() != 'local'),
        'deployment_hash': _deployment_hash(deployment_id),
        'https_origin_count': sum(_valid_https_origin(item) for item in origins),
        'allowed_host_count': sum(_valid_host(item) for item in hosts),
        'request_integrity_strength': 'strong' if len(csrf) >= 32 else ('weak' if csrf else 'missing'),
        'attachment_mode': scanner if scanner in {'scanner_required', 'trusted_types', 'disabled'} else 'unknown',
        'scanner_configured': scanner != 'scanner_required',
        'prerequisites_file_present': prereq_exists, 'final_qualification_file_present': final_exists,
        'docs_exposure_expected_disabled': environment in {'qualification', 'production'},
        'docs_enabled': docs_value in {'1', 'true', 'yes'},
        'public_value_data_persisted': False,
    }


def _json_list(value: str) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _valid_https_origin(value: str) -> bool:
    try:
        parsed = urlsplit(value)
        _ = parsed.port
        return parsed.scheme == 'https' and bool(parsed.hostname) and parsed.username is None and parsed.password is None and not parsed.path and not parsed.query and not parsed.fragment
    except ValueError:
        return False


def _valid_host(value: str) -> bool:
    if not value or value == '*' or '/' in value or ':' in value or value.casefold() == 'localhost' or value.startswith('.') or value.endswith('.'):
        return False
    if len(value) > 253 or not re.fullmatch(r'(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)*[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?', value):
        return False
    try:
        ipaddress.ip_address(value)
        return False
    except ValueError:
        return True


def _deployment_hash(value: str) -> str | None:
    if not value or value.casefold() == 'local' or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,160}', value):
        return None
    try:
        return safe_text_hash(value)
    except Exception:
        return None


def safe_url_origin(value: str) -> tuple[str, str] | None:
    """Return only an origin hash and a scheme fact, never a URL or hostname."""
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in {'https', 'http'} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('', '/'):
            return None
        origin = f'{parsed.scheme}://{parsed.netloc}'.rstrip('/')
        return safe_text_hash(origin), parsed.scheme
    except (ValueError, UnicodeError):
        return None
