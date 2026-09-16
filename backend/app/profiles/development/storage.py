from __future__ import annotations

from app.profiles.storage import LocalStorageAdapter


class DevelopmentStorageAdapter(LocalStorageAdapter):
    """Disposable local persistence for deterministic development/test runs."""
