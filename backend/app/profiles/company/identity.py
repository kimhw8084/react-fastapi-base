from __future__ import annotations
import os
from fastapi import Request

from app.platform.identity import IdentityProvider, normalize_username
from app.profiles.development.identity import DevelopmentIdentity

class CompanyIdentity:
    """AccessKey is PROCESS-scoped. Safe multi-user use requires per-user execution."""
    def resolve(self, request: Request) -> str:
        # AccessKey is deliberately process-scoped; request context cannot
        # safely turn one shared process into a multi-user identity boundary.
        del request
        return self.current_user()

    def current_user(self, request: Request | None = None) -> str:
        del request
        variants = [name for name in os.environ if name.casefold() == 'accesskey' and name != 'AccessKey']
        if variants:
            # POSIX permits case-distinct names; never silently choose one
            # spelling for a platform-owned identity secret.
            raise RuntimeError('Company identity configuration is ambiguous.')
        return normalize_username(os.environ.get('AccessKey'))


__all__ = ['CompanyIdentity', 'DevelopmentIdentity', 'IdentityProvider', 'normalize_username']
