"""Platform-owned identity port and safe username normalization."""
from __future__ import annotations

from typing import Protocol

from fastapi import Request

from app.platform.errors import AppError


class IdentityProvider(Protocol):
    """Resolve the current actor from server-owned request context.

    ``current_user`` remains available for trusted startup/tooling checks. It
    must never be implemented by reading a browser-supplied identity header.
    """

    def resolve(self, request: Request) -> str: ...

    def current_user(self, request: Request | None = None) -> str: ...


IdentityPort = IdentityProvider


def normalize_username(value: str | None) -> str:
    if not value or not value.strip() or len(value) > 200 or any(ord(char) < 32 for char in value):
        raise AppError(401, 'identity_missing', 'The company identity is missing or invalid.')
    return value.strip()
