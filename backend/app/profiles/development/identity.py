from __future__ import annotations

from fastapi import Request

from app.platform.identity import IdentityProvider, normalize_username


class DevelopmentIdentity:
    """Deterministic local/test identity; request headers are ignored."""

    def __init__(self, username: str):
        self.username = normalize_username(username)

    def resolve(self, request: Request) -> str:
        return self.current_user(request)

    def current_user(self, request: Request | None = None) -> str:
        del request
        return self.username


__all__ = ['DevelopmentIdentity', 'IdentityProvider']
