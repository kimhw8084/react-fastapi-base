"""Safe serialization primitives; inputs are projected before reaching here."""
from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any


class UnsafeEvidence(ValueError):
    """An evidence value did not match the safe serialization contract."""


_SECRET_KEY = re.compile(r'(?:access.?key|authorization|bearer|cookie|csrf|jwt|password|credential|session|token|secret|request.?body|raw.?header)', re.I)
_SECRET_TEXT = re.compile(
    r'(?i)(?:bearer\s+[a-z0-9._~+/-]+=*|eyJ[a-zA-Z0-9_-]{8,}\.[a-zA-Z0-9_-]{8,}\.[a-zA-Z0-9_-]{4,}|'
    r'(?:access.?key|authorization|csrf[_-]?token|cookie|jwt|password|credential|session.?token|token|secret)\s*[:=]\s*[^\s,;]+|'
    r'https?://[^\s/?#]+/[^\s?#]*\?[^\s#]+|https?://[^\s/?#]+\?[^\s#]+)'
)
_PATCH_JWT = re.compile(r'eyJ[a-zA-Z0-9_-]{8,}\.[a-zA-Z0-9_-]{8,}\.[a-zA-Z0-9_-]{4,}')
_PATCH_BEARER = re.compile(r'(?i)\bbearer\s+[a-z0-9._~+/-]{16,}=*')
_PATCH_URL_QUERY = re.compile(r'https?://[^\s/?#]+(?:/[^\s?#]*)?\?[^\s#]+', re.I)
_PATCH_SECRET_ASSIGNMENT = re.compile(
    r'''(?im)^\s*(?:export\s+)?['"]?(?:[A-Za-z0-9_-]*(?:access.?key|authorization|csrf[_-]?token|cookie|jwt|password|credential|session.?token|secret|token)[A-Za-z0-9_-]*)['"]?\s*[:=]\s*(?:['"][^'"\r\n]{12,}['"]|[A-Za-z0-9_./+=-]{24,})\s*[,}]?\s*$'''
)
_SENSITIVE_PATH_NAME = re.compile(r'(?i)(?:\.env|access.?key|authorization|bearer|cookie|csrf|jwt|password|credential|session|token|secret|key\.pem)')
_SAFE_SCALAR = (str, int, float, bool, type(None))


def canonical_json(value: Any) -> bytes:
    assert_safe(value)
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True) + '\n').encode('utf-8')


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def assert_safe(value: Any, *, compact: bool = False) -> None:
    """Reject, never echo, data that could carry credential or raw request material."""
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str) or _SECRET_KEY.search(key):
                raise UnsafeEvidence('Unsafe evidence fields are not accepted.')
            if compact and re.search(r'(?:path|hostname|origin|url|username|tenant.?name)', key, re.I):
                raise UnsafeEvidence('Compact output contains a disallowed field.')
            assert_safe(item, compact=compact)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_safe(item, compact=compact)
        return
    if isinstance(value, _SAFE_SCALAR):
        if isinstance(value, float) and not math.isfinite(value):
            raise UnsafeEvidence('Unsafe evidence values are not accepted.')
        if isinstance(value, str) and _SECRET_TEXT.search(value):
            raise UnsafeEvidence('Unsafe evidence values are not accepted.')
        if compact and isinstance(value, str) and (value.startswith('/') or '://' in value or '\\' in value):
            raise UnsafeEvidence('Compact output contains a disallowed value.')
        return
    raise UnsafeEvidence('Unsupported evidence value type.')


def assert_safe_patch(value: str) -> None:
    """Reject concrete credential material without treating source identifiers as values."""
    if not isinstance(value, str):
        raise UnsafeEvidence('Unsafe source patch was not accepted.')
    if any(pattern.search(value) for pattern in (_PATCH_JWT, _PATCH_BEARER, _PATCH_URL_QUERY, _PATCH_SECRET_ASSIGNMENT)):
        raise UnsafeEvidence('Unsafe source patch was not accepted.')


def safe_text_hash(value: str) -> str:
    """Hash a runtime identifier without persisting or displaying its value."""
    if not isinstance(value, str) or not value or _SECRET_TEXT.search(value):
        raise UnsafeEvidence('Unsafe identifier was not accepted.')
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def safe_path_name(value: str) -> str:
    """Keep a repo-relative path unless its name itself resembles secret material."""
    if _SECRET_TEXT.search(value) or _SENSITIVE_PATH_NAME.search(value) or '?' in value or '#' in value:
        return f"[redacted-path-{hashlib.sha256(value.encode('utf-8', errors='replace')).hexdigest()[:8]}]"
    if value.startswith('/') or '\\' in value or '\x00' in value:
        return '[invalid-path]'
    if any(ord(character) < 32 or character in '|`' for character in value):
        return f"[unusual-path-{hashlib.sha256(value.encode('utf-8', errors='replace')).hexdigest()[:8]}]"
    return value[:512]
