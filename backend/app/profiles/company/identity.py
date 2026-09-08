from __future__ import annotations
import os
import re
from typing import Protocol
from app.platform.errors import AppError

class IdentityProvider(Protocol):
    def current_user(self) -> str: ...

def normalize_username(value: str | None) -> str:
    if not value or not value.strip() or len(value) > 200 or any(ord(c) < 32 for c in value):
        raise AppError(401, 'identity_missing', 'The company identity is missing or invalid.')
    return value.strip()

class CompanyIdentity:
    """AccessKey is PROCESS-scoped. Safe multi-user use requires per-user execution."""
    def current_user(self) -> str:
        return normalize_username(os.environ.get('AccessKey'))

class DevelopmentIdentity:
    def __init__(self, username: str):
        self.username = normalize_username(username)
    def current_user(self) -> str:
        return self.username
